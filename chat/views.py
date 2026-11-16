import os
import re
import mimetypes
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, FileResponse, Http404
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.db.models import Q, Count, Subquery, OuterRef

from .models import ChatRoom, ChatMessage, ChatRoomRead
from .forms import ChatRoomForm

MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_ATTACHMENT_EXTENSIONS = {
    'jpg', 'jpeg', 'png', 'gif', 'webp',
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    'txt', 'csv', 'zip', 'rar', '7z'
}


def _get_rooms_with_meta(user):
    """Fetch rooms with last_message and unread_count using fixed queries."""
    latest_msg_subquery = Subquery(
        ChatMessage.objects.filter(room=OuterRef('pk'), is_deleted=False)
        .order_by('-created_at')
        .values('id')[:1]
    )
    rooms = list(
        ChatRoom.objects.filter(members=user)
        .distinct()
        .select_related('created_by')
        .annotate(last_msg_id=latest_msg_subquery)
    )
    if not rooms:
        return []

    room_ids = [r.id for r in rooms]
    last_msg_ids = [r.last_msg_id for r in rooms if r.last_msg_id]

    last_messages = {
        m.id: m
        for m in ChatMessage.objects.filter(id__in=last_msg_ids)
        .select_related('sender', 'sender__profile', 'parent_message')
        .prefetch_related('mentioned_users')
    }

    read_receipts = {
        rr.room_id: rr.last_read_at
        for rr in ChatRoomRead.objects.filter(user=user, room_id__in=room_ids)
    }

    unread_filter = Q()
    for room_id in room_ids:
        last_read = read_receipts.get(room_id)
        if last_read:
            unread_filter |= Q(room_id=room_id, created_at__gt=last_read)
        else:
            unread_filter |= Q(room_id=room_id)

    unread_counts_qs = (
        ChatMessage.objects.filter(is_deleted=False)
        .exclude(sender=user)
        .filter(unread_filter)
        .values('room_id')
        .annotate(count=Count('id'))
    )
    unread_map = {item['room_id']: item['count'] for item in unread_counts_qs}

    results = []
    for r in rooms:
        results.append({
            'room': r,
            'last_message': last_messages.get(r.last_msg_id),
            'unread_count': unread_map.get(r.id, 0),
        })
    return results


# ---------------------------------------------------------------------------
# Admin Views
# ---------------------------------------------------------------------------

@never_cache
@staff_member_required
def admin_chat_hub(request):
    profile = getattr(request.user, 'profile', None)
    if profile and not profile.has_seen_onboarding:
        return redirect('/intro/')

    room_data = _get_rooms_with_meta(request.user)
    profile = getattr(request.user, 'profile', None)
    role = profile.role if profile else 'employee'
    if request.user.is_staff: role = 'manager'
    
    return render(request, 'dashboard/chat.html', {
        'room_data': room_data,
        'current_user_id': request.user.id,
        'user_role': role,
        'is_admin': True,
    })


# --- Admin Create Room: Allows admins to start a new group conversation ---
@never_cache
@staff_member_required
def admin_create_room(request):
    if request.method == 'POST':
        form = ChatRoomForm(request.POST, exclude_user=request.user)
        if form.is_valid():
            room = form.save(commit=False)
            room.created_by = request.user
            room.room_type = 'GROUP'
            room.save()
            form.save_m2m()
            room.members.add(request.user)
            messages.success(request, f'Room "{room.name}" created.')
            return redirect('/dashboard/chat/')
    else:
        form = ChatRoomForm(exclude_user=request.user)
    return render(request, 'dashboard/chat_create.html', {'form': form})


@never_cache
@login_required
def direct_chat_view(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        return redirect('/dashboard/chat/' if request.user.is_staff else '/chat/')
    
    room = ChatRoom.objects.filter(room_type='DIRECT').filter(members=request.user).filter(members=target_user).first()
    
    if not room:
        room = ChatRoom.objects.create(
            name=f"{request.user.username} & {target_user.username}",
            room_type='DIRECT',
            created_by=request.user
        )
        room.members.add(request.user, target_user)
        
    if request.user.is_staff:
        return redirect(f'/dashboard/chat/?room={room.id}')
    return redirect(f'/chat/?room={room.id}')


# ---------------------------------------------------------------------------
# Employee Views
# ---------------------------------------------------------------------------

@never_cache
@login_required
def employee_chat_hub(request):
    profile = getattr(request.user, 'profile', None)
    if profile and not profile.has_seen_onboarding:
        return redirect('/intro/')

    room_data = _get_rooms_with_meta(request.user)
    profile = getattr(request.user, 'profile', None)
    role = profile.role if profile else 'employee'
    if request.user.is_staff: role = 'manager'
    
    return render(request, 'chat/employee_chat.html', {
        'room_data': room_data,
        'current_user_id': request.user.id,
        'user_role': role,
        'is_admin': False,
    })


@never_cache
@login_required
def employee_create_room(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            name = f"Chat from {request.user.username}"
        room = ChatRoom.objects.create(
            name=name,
            room_type='GROUP',
            created_by=request.user,
        )
        room.members.add(request.user)
        staff_users = User.objects.filter(is_staff=True, is_active=True)
        room.members.add(*staff_users)
        messages.success(request, f'Conversation "{room.name}" started.')
        if request.user.is_staff:
            return redirect('/dashboard/chat/')
        return redirect('/chat/')
    return redirect('/chat/')


# ---------------------------------------------------------------------------
# Shared API Endpoints
# ---------------------------------------------------------------------------

@never_cache
@login_required
@require_GET
def api_messages(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id, members=request.user)
    msgs = room.messages.select_related('sender', 'sender__profile', 'parent_message').prefetch_related('mentioned_users')

    ChatRoomRead.objects.update_or_create(
        room=room, user=request.user,
        defaults={'last_read_at': timezone.now()}
    )

    members = list(room.members.values('id', 'username', 'is_staff'))
    is_system_room = room.is_system or bool(room.system_name)

    data = {
        'room_id': room.id,
        'room_name': room.name,
        'room_type': room.room_type,
        'is_system': is_system_room,
        'created_by_id': room.created_by_id,
        'members': members,
        'messages': [_serialize_message(m, request.user) for m in msgs],
    }
    return JsonResponse(data)


# ---------------------------------------------------------------------------
# API V2 (REST-style)
# ---------------------------------------------------------------------------

@never_cache
@login_required
@require_GET
def api_rooms_list(request):
    room_items = _get_rooms_with_meta(request.user)
    data = []
    for item in room_items:
        room = item['room']
        last_msg = item['last_message']
        data.append({
            'id': room.id,
            'name': room.name,
            'room_type': room.room_type,
            'unread_count': item['unread_count'],
            'last_message': last_msg.content[:60] if last_msg and not last_msg.is_deleted else (
                '[attachment]' if last_msg and not last_msg.is_deleted else (
                    '[Message deleted]' if last_msg and last_msg.is_deleted else ''
                )
            ),
            'last_message_time': last_msg.created_at.isoformat() if last_msg else '',
            'last_message_sender': last_msg.sender.username if last_msg else '',
            'online_status': True,
        })
    return JsonResponse({'rooms': data})


@never_cache
@login_required
@require_GET
def api_room_messages(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id, members=request.user)
    
    try:
        page = int(request.GET.get('page', 1))
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1

    page_size = 30
    start = (page - 1) * page_size
    end = start + page_size

    messages = (
        room.messages.all()
        .select_related('sender', 'sender__profile', 'parent_message')
        .prefetch_related('mentioned_users')
        .order_by('-created_at')[start:end]
    )
    
    serialized = [_serialize_message(m, request.user) for m in reversed(messages)]
    is_system_room = room.is_system or bool(room.system_name)
    return JsonResponse({
        'room_name': room.name,
        'room_id': room.id,
        'room_type': room.room_type,
        'is_system': is_system_room,
        'created_by_id': room.created_by_id,
        'members': [{'id': m.id, 'username': m.username, 'is_staff': m.is_staff} for m in room.members.all()],
        'messages': serialized,
        'has_next': room.messages.count() > end
    })


# --- API Message Send: Saves a new message and any attachments ---
@never_cache
@login_required
@require_POST
def api_message_send(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id, members=request.user)
    content = request.POST.get('content', '').strip()
    attachment = request.FILES.get('attachment')
    parent_id = request.POST.get('parent_id')

    if not content and not attachment:
        return JsonResponse({'error': 'Empty message'}, status=400)

    if attachment:
        if attachment.size > MAX_ATTACHMENT_SIZE:
            return JsonResponse({'error': 'Attachment exceeds the 10 MB size limit.'}, status=400)
        ext = attachment.name.rsplit('.', 1)[-1].lower() if '.' in attachment.name else ''
        if not ext or ext not in ALLOWED_ATTACHMENT_EXTENSIONS:
            return JsonResponse({'error': f'File type ".{ext}" is not allowed.' if ext else 'Files without extensions are not allowed.'}, status=400)

    parent_msg = None
    if parent_id:
        parent_msg = ChatMessage.objects.filter(
            id=parent_id,
            room=room,
            room__members=request.user,
            is_deleted=False
        ).first()
        if not parent_msg:
            return JsonResponse({'error': 'Parent message not found in this room.'}, status=400)

    msg = ChatMessage.objects.create(
        room=room,
        sender=request.user,
        content=content,
        attachment=attachment if attachment else None,
        attachment_name=attachment.name if attachment else '',
        parent_message=parent_msg
    )
    msg.parse_mentions()

    ChatRoomRead.objects.update_or_create(
        room=room, user=request.user,
        defaults={'last_read_at': timezone.now()}
    )

    return JsonResponse({
        'status': 'ok',
        'message': _serialize_message(msg, request.user),
    })


# --- API Message Edit: Updates the text of a sent message ---
@never_cache
@login_required
@require_POST
def api_message_edit(request, message_id):
    msg = get_object_or_404(
        ChatMessage,
        id=message_id,
        sender=request.user,
        room__members=request.user,
        is_deleted=False
    )
    
    if (timezone.now() - msg.created_at).total_seconds() > 300:
        return JsonResponse({'error': 'Messages can only be edited within 5 minutes.'}, status=400)
        
    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'error': 'Content required'}, status=400)
    
    msg.content = content
    msg.save()
    msg.parse_mentions()
    
    return JsonResponse({
        'status': 'ok',
        'message': _serialize_message(msg, request.user),
    })


@never_cache
@login_required
@require_POST
def api_message_delete(request, message_id):
    msg = get_object_or_404(
        ChatMessage,
        id=message_id,
        sender=request.user,
        room__members=request.user
    )
    msg.soft_delete()
    return JsonResponse({'status': 'ok'})


@never_cache
@login_required
@require_POST
def api_message_forward(request, message_id):
    room_id = request.POST.get('room_id')
    source_msg = get_object_or_404(
        ChatMessage,
        id=message_id,
        room__members=request.user,
        is_deleted=False
    )
    target_room = get_object_or_404(ChatRoom, id=room_id, members=request.user)
    
    new_msg = ChatMessage.objects.create(
        room=target_room,
        sender=request.user,
        content=source_msg.content,
        attachment=source_msg.attachment,
        attachment_name=source_msg.attachment_name,
        parent_message=source_msg
    )
    new_msg.content = f"*[Forwarded]*\n{new_msg.content}"
    new_msg.save()
    
    return JsonResponse({
        'status': 'ok',
        'message': _serialize_message(new_msg, request.user),
    })


@never_cache
@login_required
@require_POST
def api_mark_read(request, room_id):
    """Update last_read_at for a room."""
    room = get_object_or_404(ChatRoom, id=room_id, members=request.user)
    ChatRoomRead.objects.update_or_create(
        room=room, user=request.user,
        defaults={'last_read_at': timezone.now()}
    )
    return JsonResponse({'status': 'ok'})


@never_cache
@login_required
@require_GET
def api_unread_counts(request):
    """Get total unread counts across all rooms using a single aggregate query."""
    room_ids = list(ChatRoom.objects.filter(members=request.user).values_list('id', flat=True))
    if not room_ids:
        return JsonResponse({'total': 0})

    read_receipts = {
        rr.room_id: rr.last_read_at
        for rr in ChatRoomRead.objects.filter(user=request.user, room_id__in=room_ids)
    }

    unread_filter = Q()
    for room_id in room_ids:
        last_read = read_receipts.get(room_id)
        if last_read:
            unread_filter |= Q(room_id=room_id, created_at__gt=last_read)
        else:
            unread_filter |= Q(room_id=room_id)

    total = (
        ChatMessage.objects.filter(is_deleted=False)
        .exclude(sender=request.user)
        .filter(unread_filter)
        .count()
    )
    return JsonResponse({'total': total})


@never_cache
@login_required
@require_POST
def api_typing(request):
    """Send typing indicator (placeholder for real-time)."""
    room_id = request.POST.get('room_id')
    if room_id:
        get_object_or_404(ChatRoom, id=room_id, members=request.user)
    return JsonResponse({'status': 'ok'})


@never_cache
@login_required
@require_GET
def api_direct_room(request, user_id):
    """Get or create a 1-on-1 chat room with another user."""
    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        return JsonResponse({'error': 'Cannot chat with yourself'}, status=400)
        
    room = ChatRoom.objects.filter(
        room_type='DIRECT', 
        members=request.user
    ).filter(members=target_user).first()
    
    if not room:
        room = ChatRoom.objects.create(
            name=f"DM: {request.user.username} & {target_user.username}",
            room_type='DIRECT',
            created_by=request.user
        )
        room.members.add(request.user, target_user)
        
    return JsonResponse({'room_id': room.id})


@never_cache
@login_required
@require_POST
def api_delete_room(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    
    # Must be a member of the room
    if not room.members.filter(id=request.user.id).exists():
        return JsonResponse({'error': 'You must be a member of this room to delete it.'}, status=403)
        
    # System rooms can never be deleted
    if room.is_system or room.system_name:
        return JsonResponse({'error': 'System rooms cannot be deleted.'}, status=400)
        
    # Direct chats cannot be deleted
    if room.room_type == 'DIRECT':
        return JsonResponse({'error': 'Direct chats cannot be deleted.'}, status=400)

    # Must be room creator or manager/HR/staff
    is_creator = room.created_by_id == request.user.id
    profile = getattr(request.user, 'profile', None)
    is_authorized_role = (profile and profile.role in ['manager', 'hr']) or request.user.is_staff
    
    if not (is_authorized_role or is_creator):
        return JsonResponse({'error': 'Unauthorized to delete this room.'}, status=403)
        
    room.delete()
    return JsonResponse({'status': 'ok'})


@never_cache
@login_required
@require_GET
def api_message_attachment(request, message_id):
    msg = get_object_or_404(ChatMessage, id=message_id, is_deleted=False)
    if not msg.room.members.filter(id=request.user.id).exists():
        raise PermissionDenied("You do not have access to this attachment.")
    if not msg.attachment:
        raise Http404("Attachment not found.")

    try:
        file_handle = msg.attachment.open('rb')
    except (FileNotFoundError, ValueError):
        raise Http404("Attachment file not found on disk.")

    content_type, _ = mimetypes.guess_type(msg.attachment.name)
    content_type = content_type or 'application/octet-stream'

    response = FileResponse(file_handle, content_type=content_type)
    response['X-Content-Type-Options'] = 'nosniff'

    filename = msg.attachment_name or os.path.basename(msg.attachment.name)
    if msg.is_image_attachment:
        response['Content-Disposition'] = f'inline; filename="{filename}"'
    else:
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _serialize_message(msg, current_user):
    mentioned_ids = [u.id for u in msg.mentioned_users.all()]
    
    data = {
        'id': msg.id,
        'sender_id': msg.sender.id,
        'sender_username': msg.sender.username,
        'sender_is_staff': msg.sender.is_staff,
        'sender_role': getattr(msg.sender, 'profile', None).role if hasattr(msg.sender, 'profile') else 'employee',
        'content': msg.content if not msg.is_deleted else '[Message deleted]',
        'is_own': msg.sender.id == current_user.id,
        'is_edited': msg.is_edited,
        'is_deleted': msg.is_deleted,
        'is_mentioned': current_user.id in mentioned_ids,
        'created_at': msg.created_at.isoformat(),
        'edited_at': msg.edited_at.isoformat() if msg.edited_at else None,
        'parent_id': msg.parent_message_id,
    }
    
    if not msg.is_deleted and msg.attachment:
        data['attachment_url'] = f'/chat/api/messages/{msg.id}/attachment/'
        data['attachment_name'] = msg.attachment_name or os.path.basename(msg.attachment.name)
        data['is_image'] = msg.is_image_attachment
        
    return data

import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q

from .models import ChatRoom, ChatMessage, ChatRoomRead
from .forms import ChatRoomForm


# ---------------------------------------------------------------------------
# Admin Views
# ---------------------------------------------------------------------------

# --- Admin Chat Hub: The main dashboard for administrators to see all their conversations ---
@never_cache # UX: Ensure the page always shows fresh data (no old cached copies)
@staff_member_required # Security: Only allow users with staff/admin status
def admin_chat_hub(request):
    # Backend: Find all chat rooms where the current admin is a member
    rooms = ChatRoom.objects.filter(members=request.user).distinct()
    room_data = []
    for room in rooms:
        # Backend: Get the last message to show a "preview" in the sidebar
        last_msg = room.last_message
        room_data.append({
            'room': room,
            'last_message': last_msg,
            # UX: Calculate how many messages this specific user hasn't read yet
            'unread_count': room.unread_count_for(request.user),
        })
    # UI UX: Render the admin dashboard template with the prepared room data
    return render(request, 'dashboard/chat.html', {
        'room_data': room_data,
        'current_user_id': request.user.id,
        'user_role': getattr(request.user.profile, 'role', 'employee'),
        'is_admin': True,
    })


# --- Admin Create Room: Allows admins to start a new group conversation ---
@never_cache
@staff_member_required
def admin_create_room(request):
    if request.method == 'POST':
        # Backend: Process the form data submitted by the admin
        form = ChatRoomForm(request.POST, exclude_user=request.user)
        if form.is_valid():
            # Backend: Save the new room and set the current user as the creator
            room = form.save(commit=False)
            room.created_by = request.user
            room.room_type = 'GROUP' # UX: Explicitly mark this as a group chat
            room.save()
            form.save_m2m() # Backend: Save the list of invited members
            room.members.add(request.user) # UX: Automatically add the creator to the room
            # UX: Show a success toast message
            messages.success(request, f'Room "{room.name}" created.')
            return redirect('/dashboard/chat/')
    else:
        # UI UX: Show an empty form for creating a room
        form = ChatRoomForm(exclude_user=request.user)
    return render(request, 'dashboard/chat_create.html', {'form': form})


# --- Direct Chat View: Handles 1-on-1 private messaging ---
@never_cache
@login_required # Security: User must be signed in
def direct_chat_view(request, user_id):
    # Backend: Get the person you want to chat with
    target_user = get_object_or_404(User, id=user_id)
    # UX Safety: Don't allow users to start a chat with themselves
    if target_user == request.user:
        return redirect('/dashboard/chat/' if request.user.is_staff else '/chat/')
    
    # Backend: Check if a private conversation already exists between these two people
    room = ChatRoom.objects.filter(is_direct=True).filter(members=request.user).filter(members=target_user).first()
    
    # Backend: If no room exists, create a new one automatically
    if not room:
        room = ChatRoom.objects.create(
            name=f"{request.user.username} & {target_user.username}",
            is_direct=True, # UX: Mark as private
            created_by=request.user
        )
        room.members.add(request.user, target_user)
        
    # UI UX: Redirect the user to the appropriate chat hub (Admin or Employee)
    if request.user.is_staff:
        return redirect(f'/dashboard/chat/?room={room.id}')
    return redirect(f'/chat/?room={room.id}')


# ---------------------------------------------------------------------------
# Employee Views
# ---------------------------------------------------------------------------

# --- Employee Chat Hub: The primary chat interface for regular users ---
@never_cache
@login_required
def employee_chat_hub(request):
    # Backend: Get all rooms the employee is part of
    rooms = ChatRoom.objects.filter(members=request.user).distinct()
    room_data = []
    for room in rooms:
        # Backend: Include the last message preview
        last_msg = room.last_message
        room_data.append({
            'room': room,
            'last_message': last_msg,
            # UX: Show the unread count dot/badge
            'unread_count': room.unread_count_for(request.user),
        })
    # UI UX: Render the employee-specific chat interface
    return render(request, 'chat/employee_chat.html', {
        'room_data': room_data,
        'current_user_id': request.user.id,
        'user_role': getattr(request.user.profile, 'role', 'employee'),
        'is_admin': False,
    })


# --- Employee Create Room: Allows employees to start a new support chat or group ---
@never_cache
@login_required
def employee_create_room(request):
    if request.method == 'POST':
        # Backend: Clean up the room name or use a default if empty
        name = request.POST.get('name', '').strip()
        if not name:
            name = f"Chat from {request.user.username}"
        # Backend: Create the group room
        room = ChatRoom.objects.create(
            name=name,
            created_by=request.user,
        )
        room.members.add(request.user)
        # UX Feature: Automatically invite all Admins/Staff to the conversation 
        # so they can see the employee's request and help them.
        staff_users = User.objects.filter(is_staff=True, is_active=True)
        room.members.add(*staff_users)
        # UX: Show a success notification
        messages.success(request, f'Conversation "{room.name}" started.')
        # UI UX: Redirect back to the correct chat hub
        if request.user.is_staff:
            return redirect('/dashboard/chat/')
        return redirect('/chat/')
    return redirect('/chat/')


# ---------------------------------------------------------------------------
# Shared API Endpoints
# ---------------------------------------------------------------------------

# --- API Messages: Fetches the message history for a specific room ---
@never_cache
@login_required
@require_GET # Security: Fetching data only (no changes to database)
def api_messages(request, room_id):
    # Backend: Ensure the user is actually a member of the room they are trying to peek into
    room = get_object_or_404(ChatRoom, id=room_id, members=request.user)
    # Backend: Grab all messages and prepare them for the UI
    msgs = room.messages.select_related('sender').prefetch_related('mentioned_users')

    # UX Feature: Automatically mark the conversation as "Read" when the user opens it
    ChatRoomRead.objects.update_or_create(
        room=room, user=request.user,
        defaults={'last_read_at': timezone.now()}
    )

    # Backend: Prepare a list of all participants to show in the info sidebar
    members = list(room.members.values('id', 'username', 'is_staff'))

    # API response: Send everything back to the frontend (chat.js) as a JSON object
    data = {
        'room_id': room.id,
        'room_name': room.name,
        'members': members,
        'messages': [_serialize_message(m, request.user) for m in msgs],
    }
    return JsonResponse(data)


# ---------------------------------------------------------------------------
# API V2 (REST-style)
# ---------------------------------------------------------------------------

# --- API Rooms List: Fetches all available rooms for the sidebar ---
@never_cache
@login_required
@require_GET
def api_rooms_list(request):
    # Backend: Get all rooms where the user is a participant
    rooms = ChatRoom.objects.filter(members=request.user).distinct().select_related('created_by')
    data = []
    for room in rooms:
        # Backend: Get the most recent message to show a snippet
        last_msg = room.last_message
        data.append({
            'id': room.id,
            'name': room.name,
            'room_type': room.room_type,
            # UX: Show how many messages are waiting to be read
            'unread_count': room.unread_count_for(request.user),
            # UX: The snippet of text shown in the sidebar list
            'last_message': last_msg.content[:60] if last_msg and not last_msg.is_deleted else (
                '[attachment]' if last_msg and not last_msg.is_deleted else (
                    '[Message deleted]' if last_msg and last_msg.is_deleted else ''
                )
            ),
            'last_message_time': last_msg.created_at.isoformat() if last_msg else '',
            'last_message_sender': last_msg.sender.username if last_msg else '',
            'online_status': True, # Feature Placeholder: In the future, this would show if they are active
        })
    return JsonResponse({'rooms': data})


# --- API Room Messages: Used by the infinite scroll to load older messages ---
@never_cache
@login_required
@require_GET
def api_room_messages(request, room_id):
    # Backend: Verify membership
    room = get_object_or_404(ChatRoom, id=room_id, members=request.user)
    # Feature: Pagination. Load 30 messages at a time to keep the website fast.
    page = int(request.GET.get('page', 1))
    page_size = 30
    start = (page - 1) * page_size
    end = start + page_size

    # Backend: Get the specific chunk of messages
    messages = room.messages.all().select_related('sender', 'parent_message').order_by('-created_at')[start:end]
    
    # UI UX: Reverse the list so they appear in chronological order on screen
    serialized = [_serialize_message(m, request.user) for m in reversed(messages)]
    
    # API response: Includes whether there are even older messages to fetch later
    return JsonResponse({
        'room_name': room.name,
        'room_id': room.id,
        'room_type': room.room_type,
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
    # Backend: Verify membership
    room = get_object_or_404(ChatRoom, id=room_id, members=request.user)
    # Backend: Get the text content and the file (if any)
    content = request.POST.get('content', '').strip()
    attachment = request.FILES.get('attachment')
    parent_id = request.POST.get('parent_id') # Feature: Replying to another message

    # UX Check: Prevent sending "nothing"
    if not content and not attachment:
        return JsonResponse({'error': 'Empty message'}, status=400)

    # Backend: Link to the parent message if this is a reply
    parent_msg = None
    if parent_id:
        parent_msg = ChatMessage.objects.filter(id=parent_id, room=room).first()

    # Backend: Create the message record in the database
    msg = ChatMessage.objects.create(
        room=room,
        sender=request.user,
        content=content,
        attachment=attachment if attachment else None,
        attachment_name=attachment.name if attachment else '',
        parent_message=parent_msg
    )
    # Feature: Auto-scan for @mentions to notify users
    msg.parse_mentions()

    # UX UX: Mark the room as "Read" for the sender immediately
    ChatRoomRead.objects.update_or_create(
        room=room, user=request.user,
        defaults={'last_read_at': timezone.now()}
    )

    # API response: Send the new message details back so the UI can draw the bubble
    return JsonResponse({
        'status': 'ok',
        'message': _serialize_message(msg, request.user),
    })


# --- API Message Edit: Updates the text of a sent message ---
@never_cache
@login_required
@require_POST
def api_message_edit(request, message_id):
    # Backend: Find the message. Security: Ensure the user is the one who SENT it.
    msg = get_object_or_404(ChatMessage, id=message_id, sender=request.user, is_deleted=False)
    
    # Feature: Anti-Regret Limit. Only allow editing within the first 5 minutes.
    if (timezone.now() - msg.created_at).total_seconds() > 300:
        return JsonResponse({'error': 'Messages can only be edited within 5 minutes.'}, status=400)
        
    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'error': 'Content required'}, status=400)
    
    # Backend: Update the database record
    msg.content = content
    msg.save() # Note: The model's save method will automatically set is_edited to True
    msg.parse_mentions() # Re-scan for any new @mentions added during the edit
    
    # API response: Send the updated message back to the UI
    return JsonResponse({
        'status': 'ok',
        'message': _serialize_message(msg, request.user),
    })


# --- API Message Delete: Removes a message bubble ---
@never_cache
@login_required
@require_POST
def api_message_delete(request, message_id):
    # Backend: Find the message. Security: Ensure the user is the owner.
    msg = get_object_or_404(ChatMessage, id=message_id, sender=request.user)
    # Backend Logic: "Soft Delete". We don't actually erase it from the DB, 
    # we just mark it as deleted so the UI shows "[Message deleted]".
    msg.soft_delete()
    return JsonResponse({'status': 'ok'})


# --- API Message Forward: Sends an existing message to a different room ---
@never_cache
@login_required
@require_POST
def api_message_forward(request, message_id):
    room_id = request.POST.get('room_id') # UX: Target destination
    # Backend: Find the original message
    source_msg = get_object_or_404(ChatMessage, id=message_id, is_deleted=False)
    # Backend: Ensure the user is allowed to send messages in the target room
    target_room = get_object_or_404(ChatRoom, id=room_id, members=request.user)
    
    # Backend Logic: Create a BRAND NEW message in the target room with the same content
    new_msg = ChatMessage.objects.create(
        room=target_room,
        sender=request.user,
        content=source_msg.content,
        attachment=source_msg.attachment,
        attachment_name=source_msg.attachment_name,
        parent_message=source_msg # Logic: Keep a link to where it originally came from
    )
    # UI UX Detail: Add a tag so people know it wasn't typed fresh
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
    """Get total unread counts across all rooms."""
    rooms = ChatRoom.objects.filter(members=request.user).distinct()
    total = sum(room.unread_count_for(request.user) for room in rooms)
    return JsonResponse({'total': total})


@never_cache
@login_required
@require_POST
def api_typing(request):
    """Send typing indicator (placeholder for real-time)."""
    room_id = request.POST.get('room_id')
    # In a production app, we would broadcast this via WebSockets.
    # For polling, we might store this in Redis or a cache.
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


# --- API Delete Room: Handles the deletion of a chat group ---
@never_cache
@login_required
@require_POST # Security: Only allow POST requests (not bookmarks or links)
def api_delete_room(request, room_id):
    # Backend: Find the room or show a 404 error if it doesn't exist
    room = get_object_or_404(ChatRoom, id=room_id)
    
    # Permission Logic: Check if the user is authorized to delete
    # Feature: Must be the original creator AND have a Manager or HR role
    is_creator = room.created_by == request.user
    role = getattr(request.user.profile, 'role', 'employee')
    is_authorized_role = role in ['manager', 'hr']
    
    # Security: If they don't meet the criteria, block the action
    if not (is_creator and is_authorized_role):
        return JsonResponse({'error': 'Unauthorized to delete this room'}, status=403)
        
    # Safety: Don't allow deleting private 1-on-1 chats, only groups
    if room.room_type != 'GROUP':
        return JsonResponse({'error': 'Only group chats can be deleted'}, status=400)
        
    # Backend: Permanently remove the room and all its messages from the database
    room.delete()
    # UX: Return a success status to the frontend so it can refresh the screen
    return JsonResponse({'status': 'ok'})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# --- Helper: _serialize_message: Converts a database object into a simple JSON format ---
def _serialize_message(msg, current_user):
    # Logic: Get a list of everyone mentioned in this message
    mentioned_ids = list(msg.mentioned_users.values_list('id', flat=True))
    
    # API Structure: This is exactly what the frontend (chat.js) expects to see
    data = {
        'id': msg.id,
        'sender_id': msg.sender.id,
        'sender_username': msg.sender.username,
        'sender_is_staff': msg.sender.is_staff, # UX: To show "admin" badges
        'sender_role': getattr(msg.sender.profile, 'role', 'employee'),
        # UX: If deleted, hide the content and show a placeholder instead
        'content': msg.content if not msg.is_deleted else '[Message deleted]',
        # Logic: Let the frontend know if "I" sent this (for right-side alignment)
        'is_own': msg.sender.id == current_user.id,
        'is_edited': msg.is_edited,
        'is_deleted': msg.is_deleted,
        # UX: Highlight the message if the current user was @mentioned
        'is_mentioned': current_user.id in mentioned_ids,
        'created_at': msg.created_at.isoformat(), # Standards: Use ISO format for dates
        'edited_at': msg.edited_at.isoformat() if msg.edited_at else None,
        'parent_id': msg.parent_message_id,
    }
    
    # Feature: Attachments. If there's a file, provide the download URL and name.
    if not msg.is_deleted and msg.attachment:
        data['attachment_url'] = msg.attachment.url
        data['attachment_name'] = msg.attachment_name or msg.attachment.name.split('/')[-1]
        # UI UX: Let the frontend know if it should draw an <img> or a <a> link
        data['is_image'] = msg.is_image_attachment
        
    return data

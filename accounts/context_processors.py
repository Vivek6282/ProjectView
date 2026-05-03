from .models import SystemMessage


def unread_messages(request):
    if request.user.is_authenticated:
        urgent_messages = SystemMessage.objects.filter(
            recipient=request.user, is_read=False, is_urgent=True
        )

        # Chat unread count (graceful if table doesn't exist yet)
        unread_chat = 0
        try:
            from chat.models import ChatRoom
            rooms = ChatRoom.objects.filter(members=request.user)
            for room in rooms:
                unread_chat += room.unread_count_for(request.user)
        except Exception:
            pass

        return {
            'unread_urgent_messages': urgent_messages,
            'unread_chat_count': unread_chat,
        }
    return {}


from django.contrib import admin
from .models import ChatRoom, ChatMessage, ChatRoomRead


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'room_type', 'created_by', 'created_at')
    filter_horizontal = ('members',)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('room', 'sender', 'short_content', 'created_at')
    list_filter = ('room',)

    def short_content(self, obj):
        return obj.content[:60] if obj.content else '[attachment]'


@admin.register(ChatRoomRead)
class ChatRoomReadAdmin(admin.ModelAdmin):
    list_display = ('room', 'user', 'last_read_at')

import re
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class ChatRoom(models.Model):
    ROOM_TYPES = (
        ('PUBLIC', 'Public Channel'),
        ('DIRECT', 'Direct Message'),
        ('GROUP', 'Private Group'),
    )
    
    name = models.CharField(max_length=200)
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES, default='DIRECT')
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='created_chat_rooms'
    )
    members = models.ManyToManyField(User, related_name='chat_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} ({self.get_room_type_display()})"

    @property
    def last_message(self):
        return self.messages.filter(is_deleted=False).order_by('-created_at').first()

    def unread_count_for(self, user):
        read_receipt = self.read_receipts.filter(user=user).first()
        qs = self.messages.filter(is_deleted=False).exclude(sender=user)
        if read_receipt:
            qs = qs.filter(created_at__gt=read_receipt.last_read_at)
        return qs.count()


class ChatMessage(models.Model):
    room = models.ForeignKey(
        ChatRoom, on_delete=models.CASCADE, related_name='messages'
    )
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='chat_messages_sent'
    )
    content = models.TextField(blank=True)
    attachment = models.FileField(
        upload_to='chat_attachments/%Y/%m/', blank=True, null=True
    )
    attachment_name = models.CharField(max_length=255, blank=True)
    mentioned_users = models.ManyToManyField(
        User, related_name='chat_mentions', blank=True
    )
    
    # New V2 Fields
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    parent_message = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        if self.is_deleted:
            return f"{self.sender.username}: [Message deleted]"
        preview = self.content[:50] if self.content else '[attachment]'
        return f"{self.sender.username}: {preview}"

    def soft_delete(self):
        self.is_deleted = True
        self.content = ""
        self.attachment = None
        self.save()

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                # Check if the content has actually changed since the last save
                old_msg = ChatMessage.objects.get(pk=self.pk)
                if old_msg.content != self.content and not self.is_deleted:
                    # Only mark as edited if it wasn't a brand new message being tagged (like in forwarding)
                    self.is_edited = True
                    self.edited_at = timezone.now()
            except ChatMessage.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    def parse_mentions(self):
        """Parse @username mentions from content and populate mentioned_users."""
        if not self.content or self.is_deleted:
            return
        pattern = r'@(\w+)'
        usernames = re.findall(pattern, self.content)
        if usernames:
            room_members = self.room.members.filter(username__in=usernames)
            self.mentioned_users.set(room_members)

    @property
    def is_image_attachment(self):
        if not self.attachment:
            return False
        ext = self.attachment.name.rsplit('.', 1)[-1].lower()
        return ext in ('jpg', 'jpeg', 'png', 'gif', 'webp', 'svg')


class ChatRoomRead(models.Model):
    room = models.ForeignKey(
        ChatRoom, on_delete=models.CASCADE, related_name='read_receipts'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    last_read_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('room', 'user')

    def __str__(self):
        return f"{self.user.username} read {self.room.name}"

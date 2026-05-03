from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create a UserProfile when a new User is created."""
    if created:
        role = 'employee'
        if instance.is_superuser:
            role = 'manager'
        elif instance.is_staff:
            role = 'manager'
        UserProfile.objects.get_or_create(user=instance, defaults={'role': role})


@receiver(post_save, sender=User)
def manage_global_chat(sender, instance, created, **kwargs):
    """Auto-add users to the #General public room."""
    if created:
        try:
            from chat.models import ChatRoom
            # Use a system-level user or the first superuser as creator
            creator = User.objects.filter(is_superuser=True).first() or instance
            room, _ = ChatRoom.objects.get_or_create(
                name='General',
                defaults={'created_by': creator, 'room_type': 'PUBLIC'},
            )
            room.members.add(instance)
        except Exception:
            pass


@receiver(post_save, sender=UserProfile)
def manage_hr_channel(sender, instance, **kwargs):
    """Auto-add managers and HR users to the HR-Management Bridge private room."""
    if instance.role in ('hr', 'manager'):
        # Ensure is_staff is set for dashboard access
        if not instance.user.is_staff:
            User.objects.filter(pk=instance.user.pk).update(is_staff=True)

        try:
            from chat.models import ChatRoom
            room, created = ChatRoom.objects.get_or_create(
                name='HR-Management Bridge',
                defaults={'created_by': instance.user, 'room_type': 'GROUP'},
            )
            room.members.add(instance.user)
        except Exception:
            pass
    elif instance.role == 'employee':
        # Remove from HR bridge and revoke staff (unless superuser)
        if instance.user.is_staff and not instance.user.is_superuser:
            User.objects.filter(pk=instance.user.pk).update(is_staff=False)
        try:
            from chat.models import ChatRoom
            room = ChatRoom.objects.filter(name='HR-Management Bridge').first()
            if room:
                room.members.remove(instance.user)
        except Exception:
            pass

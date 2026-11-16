import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db import DatabaseError, OperationalError
from .models import UserProfile

logger = logging.getLogger(__name__)


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
            creator = User.objects.filter(is_superuser=True).first() or instance
            room, _ = ChatRoom.objects.get_or_create(
                system_name='general',
                defaults={
                    'name': 'General',
                    'created_by': creator,
                    'room_type': 'PUBLIC',
                    'is_system': True,
                },
            )
            if not room.is_system:
                room.is_system = True
                room.save(update_fields=['is_system'])
            room.members.add(instance)
        except (DatabaseError, OperationalError) as e:
            logger.exception("Database error while managing global chat for user %s: %s", instance.username, e)


@receiver(post_save, sender=UserProfile)
def manage_hr_channel(sender, instance, **kwargs):
    """Auto-add managers and HR users to the HR-Management Bridge private room."""
    if instance.role in ('hr', 'manager'):
        if not instance.user.is_staff:
            User.objects.filter(pk=instance.user.pk).update(is_staff=True)

        try:
            from chat.models import ChatRoom
            room, _ = ChatRoom.objects.get_or_create(
                system_name='hr_bridge',
                defaults={
                    'name': 'HR-Management Bridge',
                    'created_by': instance.user,
                    'room_type': 'GROUP',
                    'is_system': True,
                },
            )
            if not room.is_system:
                room.is_system = True
                room.save(update_fields=['is_system'])
            room.members.add(instance.user)
        except (DatabaseError, OperationalError) as e:
            logger.exception("Database error while adding user %s to HR bridge: %s", instance.user.username, e)
    elif instance.role == 'employee':
        if instance.user.is_staff and not instance.user.is_superuser:
            User.objects.filter(pk=instance.user.pk).update(is_staff=False)
        try:
            from chat.models import ChatRoom
            room = ChatRoom.objects.filter(system_name='hr_bridge').first()
            if room:
                room.members.remove(instance.user)
        except (DatabaseError, OperationalError) as e:
            logger.exception("Database error while removing user %s from HR bridge: %s", instance.user.username, e)

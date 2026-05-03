from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Create UserProfiles for existing users and set up the HR ↔ Management chat channel'

    def handle(self, *args, **options):
        # Create profiles for users who don't have one
        users_without_profile = User.objects.filter(profile__isnull=True)
        created = 0
        for user in users_without_profile:
            role = 'manager' if user.is_staff else 'employee'
            UserProfile.objects.create(user=user, role=role)
            created += 1
            self.stdout.write(f"  Created profile for {user.username} ({role})")

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created {created} user profile(s).'))
        else:
            self.stdout.write('All users already have profiles.')

        # Create HR ↔ Management chat room
        try:
            from chat.models import ChatRoom
            staff_profiles = UserProfile.objects.filter(role__in=['hr', 'manager'])
            staff_users = User.objects.filter(profile__in=staff_profiles, is_active=True)

            if staff_users.exists():
                room, created_room = ChatRoom.objects.get_or_create(
                    name='HR ↔ Management',
                    defaults={'created_by': staff_users.first()},
                )
                room.members.add(*staff_users)
                if created_room:
                    self.stdout.write(self.style.SUCCESS('Created "HR ↔ Management" chat channel.'))
                else:
                    self.stdout.write('Updated "HR ↔ Management" channel membership.')
                self.stdout.write(f'  Members: {", ".join(u.username for u in staff_users)}')
            else:
                self.stdout.write(self.style.WARNING('No HR/Manager users found. Skipping channel creation.'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Could not create chat channel: {e}'))

        self.stdout.write(self.style.SUCCESS('Done.'))

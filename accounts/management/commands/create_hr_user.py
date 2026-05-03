from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile

class Command(BaseCommand):
    help = 'Create a dedicated HR Manager user'

    def handle(self, *args, **options):
        username = 'hr_admin'
        password = 'hr_password123'
        
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            self.stdout.write(self.style.WARNING(f"User {username} already exists."))
        else:
            user = User.objects.create_user(username=username, password=password, is_staff=True)
            self.stdout.write(self.style.SUCCESS(f"Created user {username} with password '{password}'"))
        
        # Ensure role is HR
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.role = 'hr'
        profile.save()
        
        self.stdout.write(self.style.SUCCESS(f"User {username} is now assigned the 'hr' role."))

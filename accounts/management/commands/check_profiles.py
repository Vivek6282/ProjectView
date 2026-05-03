from django.core.management.base import BaseCommand
from accounts.models import UserProfile

class Command(BaseCommand):
    def handle(self, *args, **options):
        count = UserProfile.objects.count()
        self.stdout.write(f"UserProfile count: {count}")

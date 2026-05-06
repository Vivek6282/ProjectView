from django.db import models
from django.contrib.auth.models import User

class SystemMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    is_urgent = models.BooleanField(default=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Message to {self.recipient.username} from {self.sender.username}"


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('employee', 'Employee'),
        ('manager', 'Manager'),
        ('hr', 'HR Manager'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    dark_mode = models.BooleanField(default=False)
    has_seen_onboarding = models.BooleanField(default=False)
    has_seen_tutorial = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} — {self.get_role_display()}"

    @property
    def is_hr(self):
        return self.role == 'hr'

    @property
    def is_manager(self):
        return self.role == 'manager'

    @property
    def is_employee(self):
        return self.role == 'employee'

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date


class Project(models.Model):
    CATEGORY_CHOICES = [
        ('Web Development', 'Web Development'),
        ('Mobile App', 'Mobile App'),
        ('Data Science', 'Data Science'),
        ('DevOps', 'DevOps'),
        ('UI/UX Design', 'UI/UX Design'),
        ('Marketing', 'Marketing'),
        ('Research', 'Research'),
        ('Infrastructure', 'Infrastructure'),
    ]
    STATUS_CHOICES = [
        ('Planned', 'Planned'),
        ('In Progress', 'In Progress'),
        ('Done', 'Done'),
    ]
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    ]

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    details = models.TextField(blank=True)
    deadline = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Planned')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='Medium')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['deadline']

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        return self.deadline < date.today() and self.status != 'Done'

    @property
    def days_left(self):
        delta = (self.deadline - date.today()).days
        return delta

    def save(self, *args, **kwargs):
        if self.status == 'Done' and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status != 'Done':
            self.completed_at = None
        super().save(*args, **kwargs)

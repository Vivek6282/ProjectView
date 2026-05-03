from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from projects.models import Project
from datetime import date, timedelta
import random


class Command(BaseCommand):
    help = 'Seed database with admin, users, and sample projects'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...\n')

        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@projectview.io',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS('  Created admin (admin / admin123)'))
        else:
            self.stdout.write('  Admin already exists')

        user1, created = User.objects.get_or_create(
            username='user1',
            defaults={'email': 'user1@projectview.io'}
        )
        if created:
            user1.set_password('user123')
            user1.save()
            self.stdout.write(self.style.SUCCESS('  Created user1 (user1 / user123)'))

        user2, created = User.objects.get_or_create(
            username='user2',
            defaults={'email': 'user2@projectview.io'}
        )
        if created:
            user2.set_password('user123')
            user2.save()
            self.stdout.write(self.style.SUCCESS('  Created user2 (user2 / user123)'))

        if Project.objects.exists():
            self.stdout.write('  Projects already seeded. Skipping.')
            return

        today = date.today()

        projects_data = [
            {
                'title': 'E-Commerce Platform Redesign',
                'category': 'Web Development',
                'details': 'Complete overhaul of the customer-facing storefront.',
                'deadline': today + timedelta(days=14),
                'status': 'In Progress',
                'priority': 'High',
            },
            {
                'title': 'Mobile Banking App v2',
                'category': 'Mobile App',
                'details': 'Second major release featuring biometric auth.',
                'deadline': today + timedelta(days=30),
                'status': 'Planned',
                'priority': 'High',
            },
            {
                'title': 'Customer Churn Prediction Model',
                'category': 'Data Science',
                'details': 'Build ML model to predict customer churn.',
                'deadline': today - timedelta(days=5),
                'status': 'In Progress',
                'priority': 'High',
            },
            {
                'title': 'CI/CD Pipeline Migration',
                'category': 'DevOps',
                'details': 'Migrate from Jenkins to GitHub Actions.',
                'deadline': today + timedelta(days=7),
                'status': 'In Progress',
                'priority': 'Medium',
            },
            {
                'title': 'API Gateway Implementation',
                'category': 'Infrastructure',
                'details': 'Deploy Kong API Gateway for rate limiting.',
                'deadline': today - timedelta(days=3),
                'status': 'Done',
                'priority': 'High',
                'completed_early': True,
            },
        ]

        for pdata in projects_data:
            completed_early = pdata.pop('completed_early', False)

            project = Project(
                created_by=admin,
                **pdata
            )
            project.save()

            days_ago = random.randint(15, 60)
            created_date = today - timedelta(days=days_ago)
            Project.objects.filter(pk=project.pk).update(
                created_at=timezone.make_aware(
                    timezone.datetime(created_date.year, created_date.month, created_date.day, 9, 0, 0)
                )
            )

            if project.status == 'Done':
                if completed_early:
                    completed_date = project.deadline - timedelta(days=random.randint(1, 3))
                else:
                    completed_date = project.deadline

                Project.objects.filter(pk=project.pk).update(
                    completed_at=timezone.make_aware(
                        timezone.datetime(completed_date.year, completed_date.month, completed_date.day, 17, 0, 0)
                    )
                )

        self.stdout.write(self.style.SUCCESS(f'  Created sample projects'))
        self.stdout.write(self.style.SUCCESS('\nSeed complete!'))

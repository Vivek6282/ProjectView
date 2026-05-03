from django.db import migrations, models
import django.db.models.deletion


def create_profiles_for_existing_users(apps, schema_editor):
    """Create UserProfile for all existing users."""
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('accounts', 'UserProfile')
    for user in User.objects.all():
        if not UserProfile.objects.filter(user=user).exists():
            role = 'manager' if user.is_staff else 'employee'
            UserProfile.objects.create(user=user, role=role)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('employee', 'Employee'), ('manager', 'Manager'), ('hr', 'HR Manager')], default='employee', max_length=20)),
                ('dark_mode', models.BooleanField(default=False)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to='auth.user')),
            ],
        ),
        migrations.RunPython(create_profiles_for_existing_users, migrations.RunPython.noop),
    ]

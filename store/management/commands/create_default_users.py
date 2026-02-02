"""
Create default admin and user accounts in the database.
Admin: username=admin, password=admin (staff + superuser)
User:  username=user,  password=user (regular user)
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Create default admin (admin/admin) and user (user/user) accounts'

    def handle(self, *args, **options):
        # Admin: username=admin, password=admin
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True}
        )
        admin_user.set_password('admin')
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()
        UserProfile.objects.get_or_create(user=admin_user)
        self.stdout.write(self.style.SUCCESS(f'Admin account: username=admin, password=admin ({"created" if created else "updated"})'))

        # User: username=user, password=user
        regular_user, created = User.objects.get_or_create(
            username='user',
            defaults={'email': 'user@example.com'}
        )
        regular_user.set_password('user')
        regular_user.is_staff = False
        regular_user.is_superuser = False
        regular_user.save()
        UserProfile.objects.get_or_create(user=regular_user)
        self.stdout.write(self.style.SUCCESS(f'User account: username=user, password=user ({"created" if created else "updated"})'))

        self.stdout.write(self.style.SUCCESS('Default users are ready.'))

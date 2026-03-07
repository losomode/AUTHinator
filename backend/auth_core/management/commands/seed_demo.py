"""
Management command to populate Authinator with demo authentication data.

Creates demo user accounts with credentials only.
Company assignments and roles are managed in USERinator.
All demo user passwords are 'demo123', admin password is 'admin123'.
Idempotent — safe to run multiple times.
"""
from django.core.management.base import BaseCommand
from users.models import User

# Demo users - credentials only, no company assignments
# Company/role data is managed in USERinator
USERS = [
    # (user_id, username, email, is_admin)
    (1, 'admin', 'admin@example.com', True),
    (101, 'bob.manager', 'bob@acme.example.com', False),
    (102, 'carol', 'carol@acme.example.com', False),
    (103, 'dave', 'dave@acme.example.com', False),
    (104, 'globex.admin', 'admin@globex.example.com', True),
    (105, 'frank', 'frank@globex.example.com', False),
    (106, 'grace', 'grace@globex.example.com', False),
    (107, 'initech.admin', 'admin@initech.example.com', True),
    (108, 'iris', 'iris@initech.example.com', False),
    (109, 'jack', 'jack@initech.example.com', False),
]

DEMO_PASSWORD = 'demo123'


class Command(BaseCommand):
    help = 'Populate Authinator with demo user credentials'

    def handle(self, *args, **options):
        self.stdout.write('Seeding Authinator demo users...')

        # Create demo users (credentials only, no company assignment)
        for user_id, username, email, is_admin in USERS:
            auth_role = 'ADMIN' if is_admin else 'USER'
            
            # Password: admin123 for admin, demo123 for others
            password = 'admin123' if username == 'admin' else DEMO_PASSWORD
            
            # Check if user exists
            try:
                user = User.objects.get(username=username)
                # Update existing user
                user.email = email
                user.role = auth_role
                user.is_verified = True
                user.is_staff = is_admin
                user.save()
                self.stdout.write(f'  User: {username} (updated)')
            except User.DoesNotExist:
                # Create new user
                user = User(
                    id=user_id,
                    username=username,
                    email=email,
                    role=auth_role,
                    is_verified=True,
                    is_staff=is_admin,
                )
                user.set_password(password)
                user.save()
                self.stdout.write(f'  User: {user.username} (created)')

        self.stdout.write(self.style.SUCCESS('✓ Authinator demo users seeded'))
        self.stdout.write('  Note: Company assignments managed in USERinator')

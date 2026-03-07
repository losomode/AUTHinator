"""
Sync demo users from USERinator to AUTHinator.
Creates missing users in AUTHinator with password 'demo123'.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User

# Users from USERinator that need to be in AUTHinator
demo_users = [
    {'user_id': 101, 'username': 'bob.manager', 'email': 'bob@acme.example.com', 'role': 'MANAGER'},
    {'user_id': 102, 'username': 'carol', 'email': 'carol@acme.example.com', 'role': 'MEMBER'},
    {'user_id': 103, 'username': 'dave', 'email': 'dave@acme.example.com', 'role': 'MEMBER'},
    {'user_id': 104, 'username': 'globex.admin', 'email': 'admin@globex.example.com', 'role': 'ADMIN'},
    {'user_id': 105, 'username': 'frank', 'email': 'frank@globex.example.com', 'role': 'MANAGER'},
    {'user_id': 106, 'username': 'grace', 'email': 'grace@globex.example.com', 'role': 'MEMBER'},
    {'user_id': 107, 'username': 'initech.admin', 'email': 'admin@initech.example.com', 'role': 'ADMIN'},
    {'user_id': 108, 'username': 'iris', 'email': 'iris@initech.example.com', 'role': 'MEMBER'},
    {'user_id': 109, 'username': 'jack', 'email': 'jack@initech.example.com', 'role': 'MEMBER'},
]

password = 'demo123'

print("Syncing USERinator demo users to AUTHinator...")
print("=" * 60)

for user_data in demo_users:
    username = user_data['username']
    email = user_data['email']
    role = user_data['role']
    user_id = user_data['user_id']
    
    # Check if user already exists
    if User.objects.filter(username=username).exists():
        print(f"✓ User '{username}' already exists")
        continue
    
    # Create user with specific ID
    user = User(
        id=user_id,
        username=username,
        email=email,
        role=role,
        is_verified=True,
        is_active=True,
    )
    user.set_password(password)
    user.save()
    print(f"✓ Created user '{username}' (role: {role}, password: {password})")

print("=" * 60)
print(f"✓ Sync complete! All users have password: {password}")

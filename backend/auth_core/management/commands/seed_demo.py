"""
Management command to populate Authinator with demo data.

Creates 3 customer companies and 5 demo users across them.
All demo user passwords are 'demo123'.
Idempotent — safe to run multiple times.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import Customer, User


CUSTOMERS = [
    {
        'name': 'Meridian Security Solutions',
        'contact_email': 'info@meridian-sec.com',
        'contact_phone': '555-0100',
        'billing_address': '742 Surveillance Blvd, Austin, TX 78701',
    },
    {
        'name': 'Apex Manufacturing',
        'contact_email': 'orders@apexmfg.com',
        'contact_phone': '555-0200',
        'billing_address': '1200 Industrial Pkwy, Detroit, MI 48201',
    },
    {
        'name': 'Coastal Networks',
        'contact_email': 'support@coastalnet.com',
        'contact_phone': '555-0300',
        'billing_address': '88 Harbor Dr, San Diego, CA 92101',
    },
]

USERS = [
    # (username, email, role, customer_name)
    ('sarah.chen', 'sarah@meridian-sec.com', 'ADMIN', 'Meridian Security Solutions'),
    ('james.wilson', 'james@meridian-sec.com', 'USER', 'Meridian Security Solutions'),
    ('lisa.patel', 'lisa@apexmfg.com', 'USER', 'Apex Manufacturing'),
    ('mike.torres', 'mike@apexmfg.com', 'USER', 'Apex Manufacturing'),
    ('emma.jackson', 'emma@coastalnet.com', 'USER', 'Coastal Networks'),
]

DEMO_PASSWORD = 'demo123'


class Command(BaseCommand):
    help = 'Populate Authinator with demo customers and users'

    def handle(self, *args, **options):
        self.stdout.write('Seeding Authinator demo data...')

        # Create customers
        customers = {}
        for data in CUSTOMERS:
            customer, created = Customer.objects.get_or_create(
                name=data['name'],
                defaults=data,
            )
            customers[customer.name] = customer
            status = 'created' if created else 'exists'
            self.stdout.write(f'  Customer: {customer.name} ({status})')

        # Create demo users
        for username, email, role, customer_name in USERS:
            customer = customers[customer_name]
            if User.objects.filter(username=username).exists():
                self.stdout.write(f'  User: {username} (exists)')
                continue

            user = User.objects.create_user(
                username=username,
                email=email,
                password=DEMO_PASSWORD,
                role=role,
                customer=customer,
                is_verified=True,
                verified_at=timezone.now(),
                is_staff=(role == 'ADMIN'),
            )
            self.stdout.write(f'  User: {user.username} ({role}, {customer_name})')

        self.stdout.write(self.style.SUCCESS('✓ Authinator demo data seeded'))

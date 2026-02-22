"""
python manage.py seed

Seeds initial family members so you can start using the app right away.
Edit this file to match your actual family members.
"""
from django.core.management.base import BaseCommand
from vault.models import FamilyMember


MEMBERS = [
    {'display_name': 'Papa',  'name': 'Rajesh Sharma',  'avatar_letter': 'R', 'avatar_color': 'purple', 'order': 1},
    {'display_name': 'Mummy', 'name': 'Sunita Sharma',  'avatar_letter': 'S', 'avatar_color': 'pink',   'order': 2},
    {'display_name': 'Amit',  'name': 'Amit Sharma',    'avatar_letter': 'A', 'avatar_color': 'green',  'order': 3},
    {'display_name': 'Priya', 'name': 'Priya Sharma',   'avatar_letter': 'P', 'avatar_color': 'gold',   'order': 4},
]


class Command(BaseCommand):
    help = 'Seed initial family members'

    def handle(self, *args, **options):
        created = 0
        for data in MEMBERS:
            _, was_created = FamilyMember.objects.get_or_create(
                display_name=data['display_name'],
                defaults=data,
            )
            if was_created:
                created += 1
                self.stdout.write(f'  ✓ Created: {data["display_name"]}')
            else:
                self.stdout.write(f'  · Exists:  {data["display_name"]}')

        self.stdout.write(self.style.SUCCESS(f'\nDone! {created} new member(s) added.'))

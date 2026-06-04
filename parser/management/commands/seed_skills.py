"""Management command to seed skill normalization mappings"""
from django.core.management.base import BaseCommand
from parser.utils import SKILL_MAPPINGS


class Command(BaseCommand):
    help = 'Display the skill normalization mapping dictionary'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Skill Normalization Mappings:'))
        self.stdout.write(self.style.WARNING('=' * 60))
        
        for original, normalized in sorted(SKILL_MAPPINGS.items()):
            self.stdout.write(f'{original:<30} → {normalized}')
        
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(self.style.SUCCESS(f'\nTotal mappings: {len(SKILL_MAPPINGS)}'))
        
        self.stdout.write(self.style.SUCCESS('\nThese mappings are used to normalize skill names during CV parsing and job scraping.'))
        self.stdout.write(self.style.SUCCESS('To add more mappings, edit parser/utils.py'))

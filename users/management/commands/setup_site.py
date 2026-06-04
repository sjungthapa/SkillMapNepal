"""Management command to setup Django site for allauth"""
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site


class Command(BaseCommand):
    help = 'Setup Django site for allauth'

    def handle(self, *args, **options):
        site = Site.objects.get(id=1)
        site.domain = 'localhost:8000'
        site.name = 'SkillMap Nepal'
        site.save()
        
        self.stdout.write(self.style.SUCCESS(f'✓ Site configured: {site.name} ({site.domain})'))

"""Management command to manually trigger job scraping"""
from django.core.management.base import BaseCommand
from scraper.tasks import scrape_merojob_task, scrape_kumarijob_task


class Command(BaseCommand):
    help = 'Manually trigger job scraping from Merojob and Kumarijob'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            choices=['merojob', 'kumarijob', 'all'],
            default='all',
            help='Specify which source to scrape (default: all)'
        )

    def handle(self, *args, **options):
        source = options['source']

        if source in ['merojob', 'all']:
            self.stdout.write(self.style.WARNING('Triggering Merojob scrape...'))
            scrape_merojob_task.delay()
            self.stdout.write(self.style.SUCCESS('✓ Merojob scrape task queued'))

        if source in ['kumarijob', 'all']:
            self.stdout.write(self.style.WARNING('Triggering Kumarijob scrape...'))
            scrape_kumarijob_task.delay()
            self.stdout.write(self.style.SUCCESS('✓ Kumarijob scrape task queued'))

        self.stdout.write(self.style.SUCCESS('\nScraping tasks have been queued. Check Celery worker logs for progress.'))

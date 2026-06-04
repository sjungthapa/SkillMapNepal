"""Celery tasks for job scraping"""
from celery import shared_task
from django.utils import timezone
from django.db import transaction
import logging

from .models import JobPosting, JobSkill, ScrapeJob
from .scrapers import scrape_merojob_sync, scrape_kumarijob_sync
from parser.utils import normalize_skill, load_models

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def scrape_merojob_task(self):
    """Scrape Merojob.com"""
    scrape_job = ScrapeJob.objects.create(
        source='merojob',
        status='running',
        started_at=timezone.now()
    )
    
    try:
        logger.info("Starting Merojob scrape...")
        jobs = scrape_merojob_sync()
        
        scrape_job.jobs_found = len(jobs)
        jobs_saved = save_jobs(jobs, 'merojob')
        scrape_job.jobs_saved = jobs_saved
        scrape_job.status = 'done'
        scrape_job.completed_at = timezone.now()
        scrape_job.save()
        
        logger.info(f"Merojob scrape completed: {jobs_saved} jobs saved")
        return {'source': 'merojob', 'jobs_saved': jobs_saved}
        
    except Exception as exc:
        logger.error(f"Merojob scrape failed: {str(exc)}")
        scrape_job.status = 'failed'
        scrape_job.error_message = str(exc)
        scrape_job.completed_at = timezone.now()
        scrape_job.save()
        
        raise self.retry(exc=exc, countdown=300 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def scrape_kumarijob_task(self):
    """Scrape Kumarijob.com"""
    scrape_job = ScrapeJob.objects.create(
        source='kumarijob',
        status='running',
        started_at=timezone.now()
    )
    
    try:
        logger.info("Starting Kumarijob scrape...")
        jobs = scrape_kumarijob_sync()
        
        scrape_job.jobs_found = len(jobs)
        jobs_saved = save_jobs(jobs, 'kumarijob')
        scrape_job.jobs_saved = jobs_saved
        scrape_job.status = 'done'
        scrape_job.completed_at = timezone.now()
        scrape_job.save()
        
        logger.info(f"Kumarijob scrape completed: {jobs_saved} jobs saved")
        return {'source': 'kumarijob', 'jobs_saved': jobs_saved}
        
    except Exception as exc:
        logger.error(f"Kumarijob scrape failed: {str(exc)}")
        scrape_job.status = 'failed'
        scrape_job.error_message = str(exc)
        scrape_job.completed_at = timezone.now()
        scrape_job.save()
        
        raise self.retry(exc=exc, countdown=300 * (2 ** self.request.retries))


@shared_task
def scrape_all_sources():
    """Scrape all job sources (called by Celery beat)"""
    logger.info("Starting scheduled scrape of all sources...")
    
    # Trigger both scrapers
    scrape_merojob_task.delay()
    scrape_kumarijob_task.delay()
    
    return {'status': 'triggered', 'sources': ['merojob', 'kumarijob']}


def save_jobs(jobs_data, source):
    """Save scraped jobs to database with deduplication"""
    _, encoder = load_models()
    jobs_saved = 0
    
    for job_data in jobs_data:
        try:
            with transaction.atomic():
                # Check if job already exists
                existing = JobPosting.objects.filter(source_url=job_data['source_url']).first()
                
                if existing:
                    # Update existing job
                    existing.is_active = True
                    existing.scraped_at = timezone.now()
                    existing.save()
                    job_posting = existing
                else:
                    # Create new job posting
                    job_posting = JobPosting.objects.create(
                        title=job_data['title'],
                        company=job_data['company'],
                        source=job_data['source'],
                        source_url=job_data['source_url'],
                        district=job_data.get('district', 'Nepal'),
                        experience_level=job_data.get('experience_level', ''),
                        salary_range=job_data.get('salary_range', ''),
                        is_active=True
                    )
                    jobs_saved += 1
                
                # Delete old skills and add new ones
                JobSkill.objects.filter(job_posting=job_posting).delete()
                
                # Save skills
                for skill in job_data.get('skills', []):
                    normalized = normalize_skill(skill)
                    vector = encoder.encode(normalized)
                    
                    JobSkill.objects.create(
                        job_posting=job_posting,
                        skill_name=skill,
                        normalized_name=normalized,
                        is_required=True,
                        skill_vector=vector.tolist()
                    )
                    
        except Exception as e:
            logger.error(f"Error saving job {job_data.get('title', 'Unknown')}: {e}")
            continue
    
    return jobs_saved

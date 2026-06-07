"""Celery tasks for CV parsing"""
from celery import shared_task
from django.utils import timezone
from django.db import transaction
import logging

from .models import CVUpload, ExtractedSkill
from .utils import parse_cv

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def parse_cv_task(self, cv_upload_id, parsed_data=None):
    """
    Parse CV and extract skills.
    If parsed_data is provided (pre-parsed locally), skip downloading from Cloudinary.
    """
    try:
        cv_upload = CVUpload.objects.get(id=cv_upload_id)
        cv_upload.parse_status = 'processing'
        cv_upload.save()

        logger.info(f"Processing CV upload: {cv_upload_id}")

        # Use pre-parsed data if provided, otherwise download and parse from Cloudinary
        if parsed_data is None:
            result = parse_cv(cv_upload.file_url)
        else:
            result = parsed_data
            logger.info(f"Using pre-parsed data for CV: {cv_upload_id}")

        # Save extracted skills
        with transaction.atomic():
            for skill_data in result['skills']:
                ExtractedSkill.objects.create(
                    cv_upload=cv_upload,
                    skill_name=skill_data['skill_name'],
                    normalized_name=skill_data['normalized_name'],
                    confidence_score=skill_data['confidence_score'],
                    skill_vector=skill_data['skill_vector']
                )

            cv_upload.parse_status = 'done'
            cv_upload.parsed_at = timezone.now()
            cv_upload.save()

        logger.info(
            f"Successfully parsed CV: {cv_upload_id}, "
            f"extracted {len(result['skills'])} skills"
        )

        # Trigger analysis after parsing
        from analysis.tasks import analyze_skill_gap_task
        analyze_skill_gap_task.delay(cv_upload_id)

        return {
            'cv_upload_id': str(cv_upload_id),
            'skills_extracted': len(result['skills']),
            'status': 'success'
        }

    except CVUpload.DoesNotExist:
        logger.error(f"CV upload not found: {cv_upload_id}")
        raise

    except Exception as exc:
        logger.error(f"Error parsing CV {cv_upload_id}: {str(exc)}")

        try:
            cv_upload = CVUpload.objects.get(id=cv_upload_id)
            cv_upload.parse_status = 'failed'
            cv_upload.save()
        except Exception:
            pass

        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
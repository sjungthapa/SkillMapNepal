"""Celery tasks for CV parsing"""
import os
import logging

from celery import shared_task
from django.utils import timezone
from django.db import transaction
from django.conf import settings

import cloudinary
import cloudinary.uploader

from .models import CVUpload, ExtractedSkill
from .utils import parse_cv

logger = logging.getLogger(__name__)


def _get_cloudinary():
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
        api_key=settings.CLOUDINARY_STORAGE['API_KEY'],
        api_secret=settings.CLOUDINARY_STORAGE['API_SECRET']
    )
    return cloudinary


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def parse_cv_task(self, cv_upload_id, tmp_path=None, original_filename=None, parsed_data=None):
    """
    Parse CV and extract skills. Runs entirely in the background so the
    upload view can redirect immediately.

    Args:
        cv_upload_id: ID of the CVUpload record (already created, status='pending')
        tmp_path: path to the locally saved CV file (PDF/DOCX) to parse and upload
        original_filename: original filename, used for logging
        parsed_data: optional pre-parsed data (skips parsing step if provided)
    """
    try:
        cv_upload = CVUpload.objects.get(id=cv_upload_id)
        cv_upload.parse_status = 'processing'
        cv_upload.save()

        logger.info(f"Processing CV upload: {cv_upload_id} ({original_filename})")

        # Parse the CV (local temp file takes priority over pre-parsed data
        # takes priority over downloading from an existing Cloudinary URL)
        if parsed_data is not None:
            result = parsed_data
            logger.info(f"Using pre-parsed data for CV: {cv_upload_id}")
        elif tmp_path:
            result = parse_cv(tmp_path, is_local=True)
        else:
            result = parse_cv(cv_upload.file_url)

        # Upload to Cloudinary now (in the background, not blocking the user)
        if tmp_path and os.path.exists(tmp_path):
            cl = _get_cloudinary()
            upload_result = cl.uploader.upload(
                tmp_path,
                folder='skillmap/cvs',
                resource_type='raw',
                type='upload',
                access_mode='public',
            )
            cv_upload.file_url = upload_result['secure_url']
            logger.info(f"Uploaded to Cloudinary: {cv_upload.file_url}")

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
        logger.error(f"Error parsing CV {cv_upload_id}: {str(exc)}", exc_info=True)

        try:
            cv_upload = CVUpload.objects.get(id=cv_upload_id)
            cv_upload.parse_status = 'failed'
            cv_upload.error_message = str(exc)
            cv_upload.save()
        except Exception:
            pass

        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

    finally:
        # Always clean up the local temp file once we're done with it
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
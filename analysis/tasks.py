"""Celery tasks for skill gap analysis"""
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from django.db.models import Count
import logging
import numpy as np

from .models import SkillGapReport, GapItem
from parser.models import CVUpload, ExtractedSkill
from scraper.models import JobPosting, JobSkill

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def analyze_skill_gap_task(self, cv_upload_id):
    """
    Analyze skill gaps by comparing CV skills with job market demands
    Uses pgvector for cosine similarity search
    """
    try:
        cv_upload = CVUpload.objects.get(id=cv_upload_id)
        
        # Create report
        report = SkillGapReport.objects.create(
            user=cv_upload.user,
            cv_upload=cv_upload,
            status='generating'
        )
        
        logger.info(f"Analyzing skill gap for CV: {cv_upload_id}")
        
        # Get user's skills
        user_skills = ExtractedSkill.objects.filter(cv_upload=cv_upload)
        
        if not user_skills.exists():
            report.status = 'failed'
            report.error_message = 'No skills extracted from CV'
            report.save()
            return
        
        # Get active job postings
        active_jobs = JobPosting.objects.filter(is_active=True)
        
        if not active_jobs.exists():
            report.status = 'failed'
            report.error_message = 'No active job postings found'
            report.save()
            return
        
        # Calculate skill gaps
        gaps = calculate_skill_gaps(user_skills, active_jobs)
        
        # Calculate readiness score
        readiness = calculate_readiness_score(user_skills, active_jobs)
        
        # Save results
        with transaction.atomic():
            report.readiness_score = readiness['score']
            report.total_jobs_matched = readiness['jobs_matched']
            report.status = 'ready'
            report.save()
            
            # Save gap items
            for idx, gap in enumerate(gaps[:20], 1):  # Top 20 gaps
                GapItem.objects.create(
                    report=report,
                    skill_name=gap['skill_name'],
                    demand_frequency=gap['frequency'],
                    similarity_score=gap['similarity'],
                    priority_rank=idx
                )
        
        logger.info(f"Skill gap analysis complete for CV: {cv_upload_id}")
        
        # Trigger roadmap generation
        from roadmap.tasks import generate_roadmap_task
        generate_roadmap_task.delay(str(report.id))
        
        return {
            'report_id': str(report.id),
            'readiness_score': readiness['score'],
            'gaps_found': len(gaps)
        }
        
    except CVUpload.DoesNotExist:
        logger.error(f"CV upload not found: {cv_upload_id}")
        raise
        
    except Exception as exc:
        logger.error(f"Error analyzing skill gap: {str(exc)}")
        
        try:
            report = SkillGapReport.objects.get(cv_upload_id=cv_upload_id, status='generating')
            report.status = 'failed'
            report.error_message = str(exc)
            report.save()
        except:
            pass
        
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


def calculate_skill_gaps(user_skills, active_jobs):
    """
    Calculate which skills are in demand but missing from user's profile
    Uses cosine similarity with pgvector
    """
    # Get all job skills with their frequency
    job_skills_freq = JobSkill.objects.filter(
        job_posting__in=active_jobs
    ).values('normalized_name').annotate(
        frequency=Count('id')
    ).order_by('-frequency')
    
    # Get user's skill names
    user_skill_names = set(user_skills.values_list('normalized_name', flat=True))
    
    gaps = []
    
    for job_skill_data in job_skills_freq:
        skill_name = job_skill_data['normalized_name']
        frequency = job_skill_data['frequency']
        
        # Skip if user already has this skill
        if skill_name in user_skill_names:
            continue
        
        # Get a sample job skill vector
        job_skill = JobSkill.objects.filter(
            normalized_name=skill_name,
            job_posting__in=active_jobs
        ).first()
        
        if not job_skill:
            continue
        
        # Calculate similarity to user's closest skill using pgvector
        max_similarity = 0.0
        for user_skill in user_skills:
            similarity = cosine_similarity(
                np.array(user_skill.skill_vector),
                np.array(job_skill.skill_vector)
            )
            max_similarity = max(max_similarity, similarity)
        
        gaps.append({
            'skill_name': skill_name,
            'frequency': frequency,
            'similarity': max_similarity
        })
    
    # Sort by frequency (demand) and then by dissimilarity (how different it is)
    gaps.sort(key=lambda x: (x['frequency'], -x['similarity']), reverse=True)
    
    return gaps


def calculate_readiness_score(user_skills, active_jobs):
    """
    Calculate user's readiness score based on skill matches
    Returns score (0-100) and number of jobs matched
    """
    user_skill_names = set(user_skills.values_list('normalized_name', flat=True))
    
    jobs_matched = 0
    total_match_percentage = 0.0
    
    for job in active_jobs[:100]:  # Sample 100 jobs
        job_skills = JobSkill.objects.filter(job_posting=job)
        job_skill_names = set(job_skills.values_list('normalized_name', flat=True))
        
        if not job_skill_names:
            continue
        
        # Calculate match percentage
        matched_skills = user_skill_names.intersection(job_skill_names)
        match_pct = len(matched_skills) / len(job_skill_names) * 100
        
        if match_pct >= 30:  # Consider it a match if 30%+ skills overlap
            jobs_matched += 1
            total_match_percentage += match_pct
    
    # Calculate average readiness
    if jobs_matched > 0:
        avg_readiness = total_match_percentage / jobs_matched
    else:
        avg_readiness = 0.0
    
    return {
        'score': round(avg_readiness, 2),
        'jobs_matched': jobs_matched
    }


def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors"""
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)

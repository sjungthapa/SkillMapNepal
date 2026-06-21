"""Dashboard views"""
import os
import tempfile
import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings

from parser.models import CVUpload, ExtractedSkill
from analysis.models import SkillGapReport, GapItem
from roadmap.models import Roadmap, RoadmapItem, Resource
from scraper.models import JobPosting, JobSkill
from parser.tasks import parse_cv_task

logger = logging.getLogger(__name__)


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard_home')
    return render(request, 'home.html')


@login_required
def dashboard_home(request):
    reports = SkillGapReport.objects.filter(
        user=request.user
    ).order_by('-generated_at')[:5]
    latest_report = reports.first() if reports.exists() else None
    context = {
        'reports': reports,
        'latest_report': latest_report,
        'has_reports': reports.exists()
    }
    return render(request, 'dashboard/home.html', context)


@login_required
def upload_cv(request):
    if request.method == 'POST':
        if 'cv_file' not in request.FILES:
            messages.error(request, 'No file uploaded')
            return redirect('dashboard:upload_cv')

        cv_file = request.FILES['cv_file']

        if not cv_file.name.endswith(('.pdf', '.docx')):
            messages.error(request, 'Only PDF and DOCX files are allowed')
            return redirect('dashboard:upload_cv')

        if cv_file.size > settings.MAX_UPLOAD_SIZE:
            messages.error(request, 'File size must be less than 10MB')
            return redirect('dashboard:upload_cv')

        suffix = '.pdf' if cv_file.name.endswith('.pdf') else '.docx'
        tmp_path = None

        try:
            # Only save the file to a temp path here — fast, no parsing/upload yet
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                for chunk in cv_file.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name

            # Create the CVUpload record immediately with 'pending' status
            cv_upload = CVUpload.objects.create(
                user=request.user,
                file_url='',  # filled in by the background task once uploaded to Cloudinary
                original_filename=cv_file.name,
                parse_status='pending'
            )

            # Hand off ALL heavy work (parsing + Cloudinary upload) to Celery.
            # tmp_path is passed so the task can read the file directly without
            # waiting on this request.
            parse_cv_task.delay(
                str(cv_upload.id),
                tmp_path=tmp_path,
                original_filename=cv_file.name,
            )

            # Redirect immediately — don't wait for parsing/upload to finish
            return redirect('dashboard:report_status', report_id=cv_upload.id)

        except Exception as e:
            logger.error(f"Error starting CV upload: {e}", exc_info=True)
            messages.error(request, f'Error uploading CV: {str(e)}')
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
            return redirect('dashboard:upload_cv')

    cv_uploads = CVUpload.objects.filter(
        user=request.user
    ).order_by('-uploaded_at')[:10]
    return render(request, 'dashboard/upload_cv.html', {'cv_uploads': cv_uploads})


@login_required
def report_status(request, report_id):
    cv_upload = get_object_or_404(CVUpload, id=report_id, user=request.user)

    if request.GET.get('format') == 'json':
        report = SkillGapReport.objects.filter(cv_upload=cv_upload).first()
        status_data = {
            'parse_status': cv_upload.parse_status,
            'has_report': report is not None,
            'ready': False,
        }
        if cv_upload.parse_status == 'failed':
            status_data['ready'] = True
            status_data['error_message'] = cv_upload.error_message or 'CV parsing failed.'
        if report:
            status_data.update({
                'report_status': report.status,
                'report_id': str(report.id),
                'readiness_score': report.readiness_score,
                'ready': report.status in ['ready', 'failed'],
            })
            try:
                report.roadmap
                status_data['has_roadmap'] = True
            except Roadmap.DoesNotExist:
                status_data['has_roadmap'] = False
        return JsonResponse(status_data)

    return render(request, 'dashboard/report_status.html', {'cv_upload': cv_upload})


@login_required
def view_report(request, report_id):
    report = get_object_or_404(SkillGapReport, id=report_id, user=request.user)
    gap_items = GapItem.objects.filter(report=report).order_by('priority_rank')[:10]
    user_skills = ExtractedSkill.objects.filter(cv_upload=report.cv_upload)
    user_skill_names = set(user_skills.values_list('normalized_name', flat=True))

    # Get matched jobs with skill overlap
    matched_jobs = []
    for job in JobPosting.objects.filter(is_active=True)[:50]:
        job_skill_names = set(
            JobSkill.objects.filter(job_posting=job)
            .values_list('normalized_name', flat=True)
        )
        if not job_skill_names:
            continue
        matched = user_skill_names.intersection(job_skill_names)
        pct = len(matched) / len(job_skill_names) * 100
        if pct >= 30:
            matched_jobs.append({
                'job': job,
                'match_pct': round(pct),
                'matched_skills': list(matched)[:5],
            })
    matched_jobs.sort(key=lambda x: x['match_pct'], reverse=True)

    # Get roadmap if exists
    roadmap = None
    roadmap_items = []
    try:
        roadmap = report.roadmap
        roadmap_items = RoadmapItem.objects.filter(
            roadmap=roadmap
        ).order_by('week_number')
    except Roadmap.DoesNotExist:
        pass

    context = {
        'report': report,
        'gap_items': gap_items,
        'user_skills': user_skills,
        'matched_jobs': matched_jobs[:10],
        'roadmap': roadmap,
        'roadmap_items': roadmap_items,
    }
    return render(request, 'dashboard/report_detail.html', context)


@login_required
def roadmap_view(request, report_id):
    report = get_object_or_404(SkillGapReport, id=report_id, user=request.user)
    try:
        roadmap = report.roadmap
        roadmap_items = RoadmapItem.objects.filter(
            roadmap=roadmap
        ).order_by('week_number')

        items_with_resources = []
        for item in roadmap_items:
            resources = Resource.objects.filter(roadmap_item=item)
            items_with_resources.append({
                'item': item,
                'resources': resources
            })

        context = {
            'report': report,
            'roadmap': roadmap,
            'items_with_resources': items_with_resources,
        }
        return render(request, 'dashboard/roadmap.html', context)

    except Roadmap.DoesNotExist:
        messages.error(request, 'Roadmap not found for this report')
        return redirect('dashboard:view_report', report_id=report_id)


@login_required
def profile_view(request):
    cv_uploads = CVUpload.objects.filter(
        user=request.user
    ).order_by('-uploaded_at')
    reports = SkillGapReport.objects.filter(
        user=request.user
    ).order_by('-generated_at')
    context = {
        'cv_uploads': cv_uploads,
        'reports': reports,
    }
    return render(request, 'dashboard/profile.html', context)
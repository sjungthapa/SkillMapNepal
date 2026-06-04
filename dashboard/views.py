"""Dashboard views"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.conf import settings
import cloudinary.uploader
import logging

from parser.models import CVUpload, ExtractedSkill
from analysis.models import SkillGapReport, GapItem
from roadmap.models import Roadmap, RoadmapItem, Resource
from parser.tasks import parse_cv_task

logger = logging.getLogger(__name__)


@login_required
def dashboard_home(request):
    """Main dashboard view"""
    # Get user's recent reports
    reports = SkillGapReport.objects.filter(user=request.user).order_by('-generated_at')[:5]
    
    # Get latest report details
    latest_report = reports.first() if reports.exists() else None
    
    context = {
        'reports': reports,
        'latest_report': latest_report,
        'has_reports': reports.exists()
    }
    
    return render(request, 'dashboard/home.html', context)


@login_required
def upload_cv(request):
    """CV upload view"""
    if request.method == 'POST':
        if 'cv_file' not in request.FILES:
            messages.error(request, 'No file uploaded')
            return redirect('dashboard:upload_cv')
        
        cv_file = request.FILES['cv_file']
        
        # Validate file
        if not cv_file.name.endswith(('.pdf', '.docx')):
            messages.error(request, 'Only PDF and DOCX files are allowed')
            return redirect('dashboard:upload_cv')
        
        if cv_file.size > settings.MAX_UPLOAD_SIZE:
            messages.error(request, 'File size must be less than 10MB')
            return redirect('dashboard:upload_cv')
        
        try:
            # Check if Cloudinary is configured
            from django.conf import settings as django_settings
            if not all([
                django_settings.CLOUDINARY_STORAGE.get('CLOUD_NAME'),
                django_settings.CLOUDINARY_STORAGE.get('API_KEY'),
                django_settings.CLOUDINARY_STORAGE.get('API_SECRET')
            ]):
                messages.error(request, 'Cloudinary is not configured. Please contact administrator.')
                return redirect('dashboard:upload_cv')
            
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                cv_file,
                folder='skillmap/cvs',
                resource_type='raw'
            )
            
            # Create CV upload record
            cv_upload = CVUpload.objects.create(
                user=request.user,
                file_url=upload_result['secure_url'],
                original_filename=cv_file.name,
                parse_status='pending'
            )
            
            # Trigger parsing task
            parse_cv_task.delay(str(cv_upload.id))
            
            messages.success(request, 'CV uploaded successfully! Analysis in progress...')
            return redirect('dashboard:report_status', report_id=cv_upload.id)
            
        except Exception as e:
            logger.error(f"Error uploading CV: {e}", exc_info=True)
            messages.error(request, f'Error uploading CV: {str(e)}')
            return redirect('dashboard:upload_cv')
    
    # GET request
    cv_uploads = CVUpload.objects.filter(user=request.user).order_by('-uploaded_at')[:10]
    return render(request, 'dashboard/upload_cv.html', {'cv_uploads': cv_uploads})


@login_required
def report_status(request, report_id):
    """Check report generation status (AJAX endpoint)"""
    cv_upload = get_object_or_404(CVUpload, id=report_id, user=request.user)
    
    # Get associated report if exists
    report = SkillGapReport.objects.filter(cv_upload=cv_upload).first()
    
    # Check if running in eager mode (tasks run synchronously)
    eager_mode = getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False)
    
    status_data = {
        'parse_status': cv_upload.parse_status,
        'has_report': report is not None,
        'eager_mode': eager_mode,
    }
    
    if report:
        status_data.update({
            'report_status': report.status,
            'report_id': str(report.id),
            'readiness_score': report.readiness_score,
            'ready': report.status in ['ready', 'failed'],
        })
        
        # Check if roadmap exists
        try:
            roadmap = report.roadmap
            status_data['has_roadmap'] = True
        except Roadmap.DoesNotExist:
            status_data['has_roadmap'] = False
    
    return JsonResponse(status_data)


@login_required
def view_report(request, report_id):
    """View detailed skill gap report"""
    report = get_object_or_404(SkillGapReport, id=report_id, user=request.user)
    
    # Get gap items
    gap_items = GapItem.objects.filter(report=report).order_by('priority_rank')[:10]
    
    # Get user's skills
    user_skills = ExtractedSkill.objects.filter(cv_upload=report.cv_upload)
    
    # Get roadmap if exists
    roadmap = None
    roadmap_items = []
    try:
        roadmap = report.roadmap
        roadmap_items = RoadmapItem.objects.filter(roadmap=roadmap).order_by('week_number')
    except Roadmap.DoesNotExist:
        pass
    
    context = {
        'report': report,
        'gap_items': gap_items,
        'user_skills': user_skills,
        'roadmap': roadmap,
        'roadmap_items': roadmap_items,
    }
    
    return render(request, 'dashboard/report_detail.html', context)


@login_required
def roadmap_view(request, report_id):
    """View learning roadmap"""
    report = get_object_or_404(SkillGapReport, id=report_id, user=request.user)
    
    try:
        roadmap = report.roadmap
        roadmap_items = RoadmapItem.objects.filter(roadmap=roadmap).order_by('week_number')
        
        # Get resources for each item
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
    """User profile view"""
    cv_uploads = CVUpload.objects.filter(user=request.user).order_by('-uploaded_at')
    reports = SkillGapReport.objects.filter(user=request.user).order_by('-generated_at')
    
    context = {
        'cv_uploads': cv_uploads,
        'reports': reports,
    }
    
    return render(request, 'dashboard/profile.html', context)


def home(request):
    """Landing page"""
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard_home')
    return render(request, 'home.html')

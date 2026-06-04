from django.contrib import admin
from .models import JobPosting, JobSkill, ScrapeJob


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'source', 'district', 'is_active', 'scraped_at')
    list_filter = ('source', 'is_active', 'scraped_at', 'district')
    search_fields = ('title', 'company', 'district')
    readonly_fields = ('id', 'scraped_at')
    ordering = ('-scraped_at',)


@admin.register(JobSkill)
class JobSkillAdmin(admin.ModelAdmin):
    list_display = ('normalized_name', 'job_posting', 'is_required')
    list_filter = ('is_required', 'normalized_name')
    search_fields = ('skill_name', 'normalized_name', 'job_posting__title')
    readonly_fields = ('id',)


@admin.register(ScrapeJob)
class ScrapeJobAdmin(admin.ModelAdmin):
    list_display = ('source', 'status', 'jobs_found', 'jobs_saved', 'started_at', 'completed_at')
    list_filter = ('source', 'status', 'started_at')
    search_fields = ('source',)
    readonly_fields = ('id', 'started_at', 'completed_at')
    ordering = ('-started_at',)
    
    fieldsets = (
        ('Job Info', {
            'fields': ('source', 'status')
        }),
        ('Statistics', {
            'fields': ('jobs_found', 'jobs_saved')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at')
        }),
        ('Error', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )

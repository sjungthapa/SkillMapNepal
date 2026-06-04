from django.contrib import admin
from .models import SkillGapReport, GapItem


@admin.register(SkillGapReport)
class SkillGapReportAdmin(admin.ModelAdmin):
    list_display = ('user', 'readiness_score', 'total_jobs_matched', 'status', 'generated_at')
    list_filter = ('status', 'generated_at')
    search_fields = ('user__email', 'user__full_name')
    readonly_fields = ('id', 'generated_at')
    ordering = ('-generated_at',)
    
    fieldsets = (
        ('Report Info', {
            'fields': ('user', 'cv_upload', 'status')
        }),
        ('Analysis Results', {
            'fields': ('readiness_score', 'total_jobs_matched')
        }),
        ('Metadata', {
            'fields': ('generated_at', 'error_message')
        }),
    )


@admin.register(GapItem)
class GapItemAdmin(admin.ModelAdmin):
    list_display = ('skill_name', 'report', 'priority_rank', 'demand_frequency', 'similarity_score')
    list_filter = ('priority_rank',)
    search_fields = ('skill_name', 'report__user__email')
    readonly_fields = ('id',)
    ordering = ['priority_rank']

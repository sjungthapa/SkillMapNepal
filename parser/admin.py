from django.contrib import admin
from .models import CVUpload, ExtractedSkill


@admin.register(CVUpload)
class CVUploadAdmin(admin.ModelAdmin):
    list_display = ('original_filename', 'user', 'parse_status', 'uploaded_at', 'parsed_at')
    list_filter = ('parse_status', 'uploaded_at')
    search_fields = ('original_filename', 'user__email')
    readonly_fields = ('id', 'uploaded_at', 'parsed_at')
    ordering = ('-uploaded_at',)


@admin.register(ExtractedSkill)
class ExtractedSkillAdmin(admin.ModelAdmin):
    list_display = ('normalized_name', 'skill_name', 'cv_upload', 'confidence_score')
    list_filter = ('normalized_name',)
    search_fields = ('skill_name', 'normalized_name', 'cv_upload__user__email')
    readonly_fields = ('id',)

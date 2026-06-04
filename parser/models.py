import uuid
from django.db import models
from django.conf import settings
from pgvector.django import VectorField


class CVUpload(models.Model):
    """CV upload tracking model"""
    PARSE_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('done', 'Done'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cv_uploads')
    file_url = models.URLField(max_length=500)  # Cloudinary URL
    original_filename = models.CharField(max_length=255)
    parse_status = models.CharField(max_length=20, choices=PARSE_STATUS_CHOICES, default='pending')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    parsed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.original_filename} - {self.user.email}"

    class Meta:
        db_table = 'cv_uploads'
        ordering = ['-uploaded_at']
        verbose_name = 'CV Upload'
        verbose_name_plural = 'CV Uploads'


class ExtractedSkill(models.Model):
    """Skills extracted from CV"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cv_upload = models.ForeignKey(CVUpload, on_delete=models.CASCADE, related_name='extracted_skills')
    skill_name = models.CharField(max_length=255)
    normalized_name = models.CharField(max_length=255)
    confidence_score = models.FloatField(default=1.0)
    skill_vector = VectorField(dimensions=384)  # all-MiniLM-L6-v2 produces 384-dim vectors

    def __str__(self):
        return f"{self.normalized_name} ({self.cv_upload.user.email})"

    class Meta:
        db_table = 'extracted_skills'
        ordering = ['-confidence_score']
        verbose_name = 'Extracted Skill'
        verbose_name_plural = 'Extracted Skills'
        indexes = [
            models.Index(fields=['normalized_name']),
        ]

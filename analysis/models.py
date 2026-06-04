import uuid
from django.db import models
from django.conf import settings
from parser.models import CVUpload


class SkillGapReport(models.Model):
    """Skill gap analysis report"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('generating', 'Generating'),
        ('ready', 'Ready'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='gap_reports')
    cv_upload = models.ForeignKey(CVUpload, on_delete=models.CASCADE, related_name='gap_reports')
    readiness_score = models.FloatField(default=0.0)  # 0-100
    total_jobs_matched = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    generated_at = models.DateTimeField(auto_now_add=True)
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Report for {self.user.email} - Score: {self.readiness_score:.1f}%"

    class Meta:
        db_table = 'skill_gap_reports'
        ordering = ['-generated_at']
        verbose_name = 'Skill Gap Report'
        verbose_name_plural = 'Skill Gap Reports'


class GapItem(models.Model):
    """Individual skill gap item"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(SkillGapReport, on_delete=models.CASCADE, related_name='gap_items')
    skill_name = models.CharField(max_length=255)
    demand_frequency = models.FloatField()  # How often this skill appears in job postings
    similarity_score = models.FloatField()  # Cosine similarity to user's closest skill
    priority_rank = models.IntegerField()  # 1 = highest priority

    def __str__(self):
        return f"Gap: {self.skill_name} (Rank {self.priority_rank})"

    class Meta:
        db_table = 'gap_items'
        ordering = ['priority_rank']
        verbose_name = 'Gap Item'
        verbose_name_plural = 'Gap Items'

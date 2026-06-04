import uuid
from django.db import models
from pgvector.django import VectorField


class JobPosting(models.Model):
    """Job postings scraped from job sites"""
    SOURCE_CHOICES = [
        ('merojob', 'Merojob'),
        ('kumarijob', 'Kumarijob'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=500)
    company = models.CharField(max_length=255)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    source_url = models.URLField(max_length=1000, unique=True)
    experience_level = models.CharField(max_length=100, blank=True, null=True)
    salary_range = models.CharField(max_length=200, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    scraped_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} at {self.company}"

    class Meta:
        db_table = 'job_postings'
        ordering = ['-scraped_at']
        verbose_name = 'Job Posting'
        verbose_name_plural = 'Job Postings'
        indexes = [
            models.Index(fields=['source', 'is_active']),
            models.Index(fields=['-scraped_at']),
        ]


class JobSkill(models.Model):
    """Skills required for a job posting"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_posting = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='required_skills')
    skill_name = models.CharField(max_length=255)
    normalized_name = models.CharField(max_length=255)
    is_required = models.BooleanField(default=True)
    skill_vector = VectorField(dimensions=384)

    def __str__(self):
        return f"{self.normalized_name} - {self.job_posting.title}"

    class Meta:
        db_table = 'job_skills'
        verbose_name = 'Job Skill'
        verbose_name_plural = 'Job Skills'
        indexes = [
            models.Index(fields=['normalized_name']),
        ]


class ScrapeJob(models.Model):
    """Tracking scrape jobs"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('done', 'Done'),
        ('failed', 'Failed'),
    ]

    SOURCE_CHOICES = [
        ('merojob', 'Merojob'),
        ('kumarijob', 'Kumarijob'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    jobs_found = models.IntegerField(default=0)
    jobs_saved = models.IntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.source} - {self.status} ({self.started_at})"

    class Meta:
        db_table = 'scrape_jobs'
        ordering = ['-started_at']
        verbose_name = 'Scrape Job'
        verbose_name_plural = 'Scrape Jobs'

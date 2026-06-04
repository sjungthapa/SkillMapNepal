import uuid
from django.db import models
from analysis.models import SkillGapReport, GapItem


class Roadmap(models.Model):
    """AI-generated learning roadmap"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.OneToOneField(SkillGapReport, on_delete=models.CASCADE, related_name='roadmap')
    generated_by = models.CharField(max_length=100, default='gemini-2.5-flash')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Roadmap for {self.report.user.email}"

    class Meta:
        db_table = 'roadmaps'
        ordering = ['-created_at']
        verbose_name = 'Roadmap'
        verbose_name_plural = 'Roadmaps'


class RoadmapItem(models.Model):
    """Individual item in the roadmap"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    roadmap = models.ForeignKey(Roadmap, on_delete=models.CASCADE, related_name='items')
    gap_item = models.ForeignKey(GapItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='roadmap_items')
    skill_name = models.CharField(max_length=255)
    week_number = models.IntegerField()
    description = models.TextField()

    def __str__(self):
        return f"Week {self.week_number}: {self.skill_name}"

    class Meta:
        db_table = 'roadmap_items'
        ordering = ['week_number']
        verbose_name = 'Roadmap Item'
        verbose_name_plural = 'Roadmap Items'


class Resource(models.Model):
    """Learning resources for roadmap items"""
    PLATFORM_CHOICES = [
        ('youtube', 'YouTube'),
        ('freecodecamp', 'FreeCodeCamp'),
        ('roadmap_sh', 'Roadmap.sh'),
        ('docs', 'Documentation'),
        ('other', 'Other'),
    ]

    RESOURCE_TYPE_CHOICES = [
        ('video', 'Video'),
        ('article', 'Article'),
        ('course', 'Course'),
        ('documentation', 'Documentation'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    roadmap_item = models.ForeignKey(RoadmapItem, on_delete=models.CASCADE, related_name='resources')
    title = models.CharField(max_length=500)
    url = models.URLField(max_length=1000)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default='other')
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPE_CHOICES, default='article')

    def __str__(self):
        return f"{self.title} ({self.platform})"

    class Meta:
        db_table = 'resources'
        verbose_name = 'Resource'
        verbose_name_plural = 'Resources'

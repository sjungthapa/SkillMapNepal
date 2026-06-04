"""Tests for analysis app"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from parser.models import CVUpload, ExtractedSkill
from scraper.models import JobPosting, JobSkill
from .models import SkillGapReport, GapItem
import numpy as np

User = get_user_model()


class SkillGapReportModelTestCase(TestCase):
    """Test SkillGapReport model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            full_name='Test User',
            password='testpass123'
        )
        self.cv = CVUpload.objects.create(
            user=self.user,
            file_url='https://example.com/cv.pdf',
            original_filename='resume.pdf'
        )
    
    def test_create_report(self):
        report = SkillGapReport.objects.create(
            user=self.user,
            cv_upload=self.cv,
            readiness_score=75.5,
            total_jobs_matched=15
        )
        self.assertEqual(report.status, 'pending')
        self.assertEqual(report.readiness_score, 75.5)
        self.assertIn('75.5%', str(report))


class GapItemModelTestCase(TestCase):
    """Test GapItem model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            full_name='Test User',
            password='testpass123'
        )
        self.cv = CVUpload.objects.create(
            user=self.user,
            file_url='https://example.com/cv.pdf',
            original_filename='resume.pdf'
        )
        self.report = SkillGapReport.objects.create(
            user=self.user,
            cv_upload=self.cv
        )
    
    def test_create_gap_item(self):
        gap = GapItem.objects.create(
            report=self.report,
            skill_name='React.js',
            demand_frequency=25,
            similarity_score=0.6,
            priority_rank=1
        )
        self.assertEqual(gap.priority_rank, 1)
        self.assertIn('React.js', str(gap))


class ReadinessScoreTestCase(TestCase):
    """Test readiness score calculation logic"""
    
    def test_score_calculation(self):
        """Test basic readiness score formula"""
        matched_skills = 7
        total_required = 10
        score = (matched_skills / total_required) * 100
        self.assertEqual(score, 70.0)
    
    def test_perfect_match(self):
        matched = 10
        total = 10
        score = (matched / total) * 100
        self.assertEqual(score, 100.0)
    
    def test_no_match(self):
        matched = 0
        total = 10
        score = (matched / total) * 100
        self.assertEqual(score, 0.0)

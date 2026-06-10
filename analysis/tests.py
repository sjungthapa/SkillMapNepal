"""Tests for the analysis app"""
from django.test import TestCase
from django.contrib.auth import get_user_model

from parser.models import CVUpload, ExtractedSkill
from scraper.models import JobPosting, JobSkill
from analysis.models import SkillGapReport, GapItem
from analysis.tasks import calculate_readiness_score

User = get_user_model()

_counter = [0]

def create_test_user(email=None):
    _counter[0] += 1
    email = email or f'user{_counter[0]}@example.com'
    return User.objects.create_user(
        username=f'user{_counter[0]}',
        email=email,
        password='testpass123',
        full_name='Test User'
    )


class SkillGapReportModelTests(TestCase):

    def setUp(self):
        self.user = create_test_user()
        self.cv_upload = CVUpload.objects.create(
            user=self.user,
            file_url='https://res.cloudinary.com/test/raw/upload/test.pdf',
            original_filename='cv.pdf',
        )

    def test_report_created_with_pending_status(self):
        report = SkillGapReport.objects.create(
            user=self.user,
            cv_upload=self.cv_upload,
            status='pending'
        )
        self.assertEqual(report.status, 'pending')
        self.assertEqual(report.readiness_score, 0.0)

    def test_report_status_transitions(self):
        report = SkillGapReport.objects.create(
            user=self.user,
            cv_upload=self.cv_upload,
            status='pending'
        )
        report.status = 'ready'
        report.readiness_score = 75.5
        report.save()
        report.refresh_from_db()
        self.assertEqual(report.status, 'ready')
        self.assertEqual(report.readiness_score, 75.5)


class ReadinessScoreTests(TestCase):

    def setUp(self):
        self.user = create_test_user()
        self.cv_upload = CVUpload.objects.create(
            user=self.user,
            file_url='https://res.cloudinary.com/test/raw/upload/test.pdf',
            original_filename='cv.pdf',
        )
        vector = [0.1] * 384
        for skill in ['React.js', 'JavaScript', 'TypeScript', 'Git', 'CSS']:
            ExtractedSkill.objects.create(
                cv_upload=self.cv_upload,
                skill_name=skill,
                normalized_name=skill,
                confidence_score=1.0,
                skill_vector=vector
            )
        self.job1 = JobPosting.objects.create(
            title='Frontend Developer',
            company='Tech Nepal',
            source='merojob',
            source_url='https://merojob.com/job/frontend-1',
            is_active=True
        )
        for skill in ['React.js', 'JavaScript', 'CSS', 'HTML']:
            JobSkill.objects.create(
                job_posting=self.job1,
                skill_name=skill,
                normalized_name=skill,
                is_required=True,
                skill_vector=vector
            )
        self.job2 = JobPosting.objects.create(
            title='Backend Developer',
            company='Dev Nepal',
            source='merojob',
            source_url='https://merojob.com/job/backend-1',
            is_active=True
        )
        for skill in ['Python', 'Django', 'PostgreSQL', 'Docker']:
            JobSkill.objects.create(
                job_posting=self.job2,
                skill_name=skill,
                normalized_name=skill,
                is_required=True,
                skill_vector=vector
            )

    def test_readiness_score_returns_valid_range(self):
        user_skills = ExtractedSkill.objects.filter(cv_upload=self.cv_upload)
        active_jobs = JobPosting.objects.filter(is_active=True)
        result = calculate_readiness_score(user_skills, active_jobs)
        self.assertIn('score', result)
        self.assertIn('jobs_matched', result)
        self.assertGreaterEqual(result['score'], 0)
        self.assertLessEqual(result['score'], 100)

    def test_readiness_score_matches_frontend_job(self):
        user_skills = ExtractedSkill.objects.filter(cv_upload=self.cv_upload)
        active_jobs = JobPosting.objects.filter(is_active=True)
        result = calculate_readiness_score(user_skills, active_jobs)
        self.assertGreaterEqual(result['jobs_matched'], 1)

    def test_readiness_score_zero_with_no_jobs(self):
        JobPosting.objects.all().delete()
        user_skills = ExtractedSkill.objects.filter(cv_upload=self.cv_upload)
        active_jobs = JobPosting.objects.filter(is_active=True)
        result = calculate_readiness_score(user_skills, active_jobs)
        self.assertEqual(result['score'], 0.0)
        self.assertEqual(result['jobs_matched'], 0)


class GapItemTests(TestCase):

    def setUp(self):
        self.user = create_test_user()
        self.cv_upload = CVUpload.objects.create(
            user=self.user,
            file_url='https://res.cloudinary.com/test/raw/upload/test.pdf',
            original_filename='cv.pdf',
        )
        self.report = SkillGapReport.objects.create(
            user=self.user,
            cv_upload=self.cv_upload,
            status='ready',
            readiness_score=60.0
        )

    def test_gap_items_created(self):
        GapItem.objects.create(
            report=self.report,
            skill_name='Docker',
            demand_frequency=10.0,
            similarity_score=0.3,
            priority_rank=1
        )
        GapItem.objects.create(
            report=self.report,
            skill_name='PostgreSQL',
            demand_frequency=8.0,
            similarity_score=0.4,
            priority_rank=2
        )
        self.assertEqual(GapItem.objects.filter(report=self.report).count(), 2)

    def test_gap_items_ordered_by_rank(self):
        GapItem.objects.create(
            report=self.report, skill_name='Docker',
            demand_frequency=10.0, similarity_score=0.3, priority_rank=2
        )
        GapItem.objects.create(
            report=self.report, skill_name='PostgreSQL',
            demand_frequency=8.0, similarity_score=0.4, priority_rank=1
        )
        items = GapItem.objects.filter(report=self.report).order_by('priority_rank')
        self.assertEqual(items[0].skill_name, 'PostgreSQL')
        self.assertEqual(items[1].skill_name, 'Docker')
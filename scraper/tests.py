"""Tests for the scraper app"""
from django.test import TestCase
from django.utils import timezone

from scraper.models import JobPosting, JobSkill, ScrapeJob
from scraper.tasks import extract_skills_from_text


class JobPostingModelTests(TestCase):

    def test_job_posting_created(self):
        job = JobPosting.objects.create(
            title='React Developer',
            company='Tech Nepal',
            source='merojob',
            source_url='https://merojob.com/job/react-developer-1',
            is_active=True
        )
        self.assertEqual(JobPosting.objects.count(), 1)
        self.assertEqual(job.title, 'React Developer')
        self.assertTrue(job.is_active)

    def test_job_skill_created(self):
        job = JobPosting.objects.create(
            title='Full Stack Developer',
            company='Startup Nepal',
            source='merojob',
            source_url='https://merojob.com/job/fullstack-1',
            is_active=True
        )
        skill = JobSkill.objects.create(
            job_posting=job,
            skill_name='React.js',
            normalized_name='React.js',
            is_required=True,
            skill_vector=[0.1] * 384
        )
        self.assertEqual(JobSkill.objects.filter(job_posting=job).count(), 1)
        self.assertEqual(skill.skill_name, 'React.js')

    def test_multiple_skills_per_job(self):
        job = JobPosting.objects.create(
            title='Frontend Developer',
            company='Agency Nepal',
            source='merojob',
            source_url='https://merojob.com/job/frontend-2',
            is_active=True
        )
        for skill in ['React.js', 'TypeScript', 'CSS', 'HTML', 'Git']:
            JobSkill.objects.create(
                job_posting=job,
                skill_name=skill,
                normalized_name=skill,
                is_required=True,
                skill_vector=[0.1] * 384
            )
        self.assertEqual(JobSkill.objects.filter(job_posting=job).count(), 5)

    def test_inactive_jobs_filtered(self):
        JobPosting.objects.create(
            title='Old Job', company='Old Co',
            source='merojob', source_url='https://merojob.com/job/old-1',
            is_active=False
        )
        JobPosting.objects.create(
            title='Active Job', company='New Co',
            source='merojob', source_url='https://merojob.com/job/active-1',
            is_active=True
        )
        self.assertEqual(JobPosting.objects.filter(is_active=True).count(), 1)
        self.assertEqual(JobPosting.objects.filter(is_active=False).count(), 1)


class ScrapeJobModelTests(TestCase):

    def test_scrape_job_created(self):
        scrape = ScrapeJob.objects.create(
            source='merojob',
            status='running',
            started_at=timezone.now()
        )
        self.assertEqual(scrape.status, 'running')

    def test_scrape_job_completed(self):
        scrape = ScrapeJob.objects.create(
            source='merojob',
            status='running',
            started_at=timezone.now(),
            jobs_found=50,
            jobs_saved=45
        )
        scrape.status = 'done'
        scrape.completed_at = timezone.now()
        scrape.save()
        scrape.refresh_from_db()
        self.assertEqual(scrape.status, 'done')
        self.assertEqual(scrape.jobs_saved, 45)


class ScraperSkillExtractionTests(TestCase):

    def test_extracts_from_job_title(self):
        skills = extract_skills_from_text("React Developer needed")
        self.assertIn('React.js', skills)

    def test_extracts_from_description(self):
        skills = extract_skills_from_text(
            "We need experience with Python, Django, PostgreSQL and Docker"
        )
        self.assertIn('Python', skills)
        self.assertIn('Django', skills)
        self.assertIn('PostgreSQL', skills)
        self.assertIn('Docker', skills)

    def test_no_duplicate_skills(self):
        skills = extract_skills_from_text(
            "Python developer with Python experience in Python projects"
        )
        self.assertEqual(skills.count('Python'), 1)

    def test_empty_text_returns_empty(self):
        skills = extract_skills_from_text("")
        self.assertEqual(skills, [])

    def test_none_text_returns_empty(self):
        skills = extract_skills_from_text(None)
        self.assertEqual(skills, [])
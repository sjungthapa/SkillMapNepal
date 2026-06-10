"""Tests for the parser app — CV upload and skill extraction"""
from django.test import TestCase
from django.contrib.auth import get_user_model

from parser.models import CVUpload, ExtractedSkill
from parser.utils import extract_skills_from_text, normalize_skill

User = get_user_model()


def create_test_user(email='test@example.com', password='testpass123'):
    return User.objects.create_user(
        username=email.split('@')[0],
        email=email,
        password=password,
        full_name='Test User'
    )


class SkillExtractionTests(TestCase):

    def test_extracts_python(self):
        skills = extract_skills_from_text("I have 3 years of Python experience")
        self.assertIn('Python', skills)

    def test_extracts_react(self):
        skills = extract_skills_from_text("Built frontend with React.js and TypeScript")
        self.assertIn('React.js', skills)
        self.assertIn('TypeScript', skills)

    def test_extracts_multiple_skills(self):
        text = "Stack: Django, PostgreSQL, Docker, Redis, React"
        skills = extract_skills_from_text(text)
        self.assertIn('Django', skills)
        self.assertIn('PostgreSQL', skills)
        self.assertIn('Docker', skills)
        self.assertIn('Redis', skills)
        self.assertIn('React.js', skills)

    def test_no_false_positives(self):
        skills = extract_skills_from_text(
            "I am a hardworking individual with great communication skills"
        )
        self.assertNotIn('Communication', skills)
        self.assertNotIn('Hardworking', skills)

    def test_empty_text(self):
        skills = extract_skills_from_text("")
        self.assertEqual(skills, [])

    def test_case_insensitive(self):
        skills = extract_skills_from_text("PYTHON, DJANGO, REACT")
        self.assertIn('Python', skills)
        self.assertIn('Django', skills)
        self.assertIn('React.js', skills)

    def test_extracts_git(self):
        skills = extract_skills_from_text("Version control with Git and GitHub")
        self.assertIn('Git', skills)
        self.assertIn('GitHub', skills)

    def test_extracts_docker(self):
        skills = extract_skills_from_text("Containerized with Docker and Kubernetes")
        self.assertIn('Docker', skills)
        self.assertIn('Kubernetes', skills)


class SkillNormalizationTests(TestCase):

    def test_normalizes_react_variants(self):
        self.assertEqual(normalize_skill('reactjs'), 'React.js')
        self.assertEqual(normalize_skill('react.js'), 'React.js')
        self.assertEqual(normalize_skill('react.js'), 'React.js')

    def test_normalizes_node_variants(self):
        self.assertEqual(normalize_skill('nodejs'), 'Node.js')
        self.assertEqual(normalize_skill('node'), 'Node.js')

    def test_normalizes_postgres_variants(self):
        self.assertEqual(normalize_skill('postgres'), 'PostgreSQL')
        self.assertEqual(normalize_skill('postgresql'), 'PostgreSQL')

    def test_case_insensitive_lookup(self):
        self.assertEqual(normalize_skill('PYTHON'), 'Python')
        self.assertEqual(normalize_skill('Django'), 'Django')


class CVUploadModelTests(TestCase):

    def setUp(self):
        self.user = create_test_user()

    def test_cv_upload_created(self):
        cv = CVUpload.objects.create(
            user=self.user,
            file_url='https://res.cloudinary.com/test/raw/upload/test.pdf',
            original_filename='my_cv.pdf',
            parse_status='pending'
        )
        self.assertEqual(CVUpload.objects.count(), 1)
        self.assertEqual(cv.parse_status, 'pending')
        self.assertEqual(cv.user, self.user)

    def test_cv_upload_default_status(self):
        cv = CVUpload.objects.create(
            user=self.user,
            file_url='https://res.cloudinary.com/test/raw/upload/test.pdf',
            original_filename='cv.pdf',
        )
        self.assertEqual(cv.parse_status, 'pending')

    def test_cv_upload_str(self):
        cv = CVUpload.objects.create(
            user=self.user,
            file_url='https://res.cloudinary.com/test/raw/upload/test.pdf',
            original_filename='cv.pdf',
        )
        self.assertIsNotNone(str(cv))
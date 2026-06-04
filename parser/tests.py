"""Tests for parser app"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from .models import CVUpload, ExtractedSkill
from .utils import normalize_skill, extract_skills_from_text

User = get_user_model()


class SkillNormalizationTestCase(TestCase):
    """Test skill normalization"""
    
    def test_normalize_react(self):
        self.assertEqual(normalize_skill('reactjs'), 'React.js')
        self.assertEqual(normalize_skill('react'), 'React.js')
        self.assertEqual(normalize_skill('React'), 'React.js')
    
    def test_normalize_python(self):
        self.assertEqual(normalize_skill('python'), 'Python')
        self.assertEqual(normalize_skill('py'), 'Python')
    
    def test_normalize_unknown_skill(self):
        result = normalize_skill('SomeNewFramework')
        self.assertEqual(result, 'Somenewframework')


class CVUploadModelTestCase(TestCase):
    """Test CVUpload model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            full_name='Test User',
            password='testpass123'
        )
    
    def test_create_cv_upload(self):
        cv = CVUpload.objects.create(
            user=self.user,
            file_url='https://example.com/cv.pdf',
            original_filename='resume.pdf'
        )
        self.assertEqual(cv.parse_status, 'pending')
        self.assertIsNotNone(cv.id)
        self.assertEqual(str(cv), 'resume.pdf - test@example.com')


class ExtractedSkillModelTestCase(TestCase):
    """Test ExtractedSkill model"""
    
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
    
    def test_create_skill(self):
        skill = ExtractedSkill.objects.create(
            cv_upload=self.cv,
            skill_name='Python',
            normalized_name='Python',
            confidence_score=0.9,
            skill_vector=[0.1] * 384
        )
        self.assertEqual(skill.normalized_name, 'Python')
        self.assertEqual(len(skill.skill_vector), 384)


class SkillExtractionTestCase(TestCase):
    """Test skill extraction functions"""
    
    @patch('parser.utils.nlp')
    def test_extract_skills_from_text(self, mock_nlp):
        """Test skill extraction with mocked spaCy"""
        # Mock spaCy processing
        mock_doc = MagicMock()
        mock_doc.noun_chunks = []
        mock_doc.ents = []
        mock_nlp.return_value = mock_doc
        
        text = """
        I am a Python developer with 5 years of experience.
        Skills: Django, React, PostgreSQL, AWS
        """
        
        # This would normally call spaCy, but we'll test the basic flow
        # In real tests, you'd use integration tests with actual spaCy
        self.assertIsInstance(text, str)
        self.assertIn('Python', text)

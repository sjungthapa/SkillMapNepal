"""Tests for the dashboard app"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
import json

from parser.models import CVUpload
from analysis.models import SkillGapReport
from roadmap.models import Roadmap

User = get_user_model()

_counter = [0]

def create_test_user(email=None, password='testpass123'):
    _counter[0] += 1
    if email is None:
        email = f'testuser{_counter[0]}@example.com'
    username = f'testuser{_counter[0]}'
    return User.objects.create_user(
        username=username,
        email=email,
        password=password,
        full_name='Test User'
    )


class AuthenticationTests(TestCase):

    def setUp(self):
        self.client = Client()

    def test_dashboard_redirects_anonymous(self):
        response = self.client.get(reverse('dashboard:dashboard_home'))
        self.assertEqual(response.status_code, 302)

    def test_upload_cv_redirects_anonymous(self):
        response = self.client.get(reverse('dashboard:upload_cv'))
        self.assertEqual(response.status_code, 302)

    def test_profile_redirects_anonymous(self):
        response = self.client.get(reverse('dashboard:profile'))
        self.assertEqual(response.status_code, 302)


class DashboardHomeTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = create_test_user(email='home@example.com')
        self.client.login(email='home@example.com', password='testpass123')

    def test_dashboard_home_loads(self):
        response = self.client.get(reverse('dashboard:dashboard_home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/home.html')

    def test_dashboard_home_context(self):
        response = self.client.get(reverse('dashboard:dashboard_home'))
        self.assertIn('reports', response.context)
        self.assertIn('has_reports', response.context)

    def test_dashboard_no_reports_initially(self):
        response = self.client.get(reverse('dashboard:dashboard_home'))
        self.assertFalse(response.context['has_reports'])


class CVUploadViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = create_test_user(email='upload@example.com')
        self.client.login(email='upload@example.com', password='testpass123')

    def test_upload_page_loads(self):
        response = self.client.get(reverse('dashboard:upload_cv'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/upload_cv.html')

    def test_upload_no_file_shows_error(self):
        response = self.client.post(reverse('dashboard:upload_cv'), {})
        self.assertEqual(response.status_code, 302)

    def test_upload_invalid_file_type(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        txt_file = SimpleUploadedFile(
            "cv.txt", b"some text content", content_type="text/plain"
        )
        response = self.client.post(
            reverse('dashboard:upload_cv'),
            {'cv_file': txt_file}
        )
        self.assertRedirects(
            response,
            reverse('dashboard:upload_cv'),
            fetch_redirect_response=False
        )

    def test_upload_file_too_large(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        large_content = b"x" * (11 * 1024 * 1024)
        large_file = SimpleUploadedFile(
            "cv.pdf", large_content, content_type="application/pdf"
        )
        response = self.client.post(
            reverse('dashboard:upload_cv'),
            {'cv_file': large_file}
        )
        self.assertRedirects(
            response,
            reverse('dashboard:upload_cv'),
            fetch_redirect_response=False
        )


class ReportStatusViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = create_test_user(email='status@example.com')
        self.client.login(email='status@example.com', password='testpass123')
        self.cv_upload = CVUpload.objects.create(
            user=self.user,
            file_url='https://res.cloudinary.com/test/raw/upload/test.pdf',
            original_filename='cv.pdf',
            parse_status='done'
        )

    def test_status_page_loads(self):
        response = self.client.get(
            reverse('dashboard:report_status', kwargs={'report_id': self.cv_upload.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/report_status.html')

    def test_status_json_endpoint(self):
        response = self.client.get(
            reverse('dashboard:report_status', kwargs={'report_id': self.cv_upload.id}),
            {'format': 'json'}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('parse_status', data)
        self.assertIn('has_report', data)
        self.assertIn('ready', data)

    def test_status_json_parse_status(self):
        response = self.client.get(
            reverse('dashboard:report_status', kwargs={'report_id': self.cv_upload.id}),
            {'format': 'json'}
        )
        data = json.loads(response.content)
        self.assertEqual(data['parse_status'], 'done')

    def test_status_returns_404_for_other_user(self):
        other_user = create_test_user(email='other@example.com')
        other_cv = CVUpload.objects.create(
            user=other_user,
            file_url='https://res.cloudinary.com/test/raw/upload/other.pdf',
            original_filename='other_cv.pdf',
        )
        response = self.client.get(
            reverse('dashboard:report_status', kwargs={'report_id': other_cv.id}),
            {'format': 'json'}
        )
        self.assertEqual(response.status_code, 404)

    def test_status_ready_when_report_exists(self):
        report = SkillGapReport.objects.create(
            user=self.user,
            cv_upload=self.cv_upload,
            readiness_score=75.0,
            status='ready'
        )
        response = self.client.get(
            reverse('dashboard:report_status', kwargs={'report_id': self.cv_upload.id}),
            {'format': 'json'}
        )
        data = json.loads(response.content)
        self.assertTrue(data['ready'])
        self.assertEqual(data['report_status'], 'ready')
        self.assertEqual(data['report_id'], str(report.id))
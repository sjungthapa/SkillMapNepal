"""Tests for the roadmap app"""
from django.test import TestCase
from django.contrib.auth import get_user_model

from parser.models import CVUpload
from analysis.models import SkillGapReport, GapItem
from roadmap.models import Roadmap, RoadmapItem, Resource
from roadmap.tasks import generate_fallback_roadmap

User = get_user_model()

_counter = [0]

def create_test_user():
    _counter[0] += 1
    return User.objects.create_user(
        username=f'user{_counter[0]}',
        email=f'user{_counter[0]}@example.com',
        password='testpass123',
        full_name='Test User'
    )


class RoadmapModelTests(TestCase):

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
            readiness_score=70.0
        )

    def test_roadmap_created(self):
        roadmap = Roadmap.objects.create(
            report=self.report,
            generated_by='llama-3.3-70b-versatile'
        )
        self.assertEqual(Roadmap.objects.count(), 1)
        self.assertEqual(roadmap.generated_by, 'llama-3.3-70b-versatile')

    def test_roadmap_item_created(self):
        roadmap = Roadmap.objects.create(
            report=self.report,
            generated_by='llama-3.3-70b-versatile'
        )
        gap_item = GapItem.objects.create(
            report=self.report, skill_name='Docker',
            demand_frequency=10.0, similarity_score=0.3, priority_rank=1
        )
        item = RoadmapItem.objects.create(
            roadmap=roadmap, gap_item=gap_item,
            skill_name='Docker', week_number=1,
            description='Learn Docker fundamentals'
        )
        self.assertEqual(item.week_number, 1)
        self.assertEqual(item.skill_name, 'Docker')

    def test_resource_created(self):
        roadmap = Roadmap.objects.create(
            report=self.report,
            generated_by='llama-3.3-70b-versatile'
        )
        gap_item = GapItem.objects.create(
            report=self.report, skill_name='Docker',
            demand_frequency=10.0, similarity_score=0.3, priority_rank=1
        )
        item = RoadmapItem.objects.create(
            roadmap=roadmap, gap_item=gap_item,
            skill_name='Docker', week_number=1,
            description='Learn Docker fundamentals'
        )
        resource = Resource.objects.create(
            roadmap_item=item,
            title='Docker Official Docs',
            url='https://docs.docker.com',
            platform='docs',
            resource_type='documentation'
        )
        self.assertEqual(resource.title, 'Docker Official Docs')
        self.assertEqual(resource.platform, 'docs')

    def test_roadmap_onetoone_with_report(self):
        Roadmap.objects.create(
            report=self.report,
            generated_by='llama-3.3-70b-versatile'
        )
        with self.assertRaises(Exception):
            Roadmap.objects.create(
                report=self.report,
                generated_by='llama-3.3-70b-versatile'
            )


class FallbackRoadmapTests(TestCase):

    def test_fallback_roadmap_generated(self):
        missing_skills = [
            {'skill': 'Docker', 'demand': 10.0, 'rank': 1},
            {'skill': 'PostgreSQL', 'demand': 8.0, 'rank': 2},
            {'skill': 'Redis', 'demand': 6.0, 'rank': 3},
        ]
        result = generate_fallback_roadmap(missing_skills)
        self.assertIn('roadmap', result)
        self.assertEqual(len(result['roadmap']), 3)

    def test_fallback_roadmap_structure(self):
        missing_skills = [{'skill': 'Docker', 'demand': 10.0, 'rank': 1}]
        result = generate_fallback_roadmap(missing_skills)
        item = result['roadmap'][0]
        self.assertIn('skill_name', item)
        self.assertIn('week_number', item)
        self.assertIn('description', item)
        self.assertIn('resources', item)

    def test_fallback_has_resources(self):
        missing_skills = [{'skill': 'Docker', 'demand': 10.0, 'rank': 1}]
        result = generate_fallback_roadmap(missing_skills)
        resources = result['roadmap'][0]['resources']
        self.assertGreater(len(resources), 0)
        for resource in resources:
            self.assertIn('title', resource)
            self.assertIn('url', resource)

    def test_fallback_respects_max_10_skills(self):
        missing_skills = [
            {'skill': f'Skill{i}', 'demand': float(10 - i), 'rank': i + 1}
            for i in range(15)
        ]
        result = generate_fallback_roadmap(missing_skills)
        self.assertLessEqual(len(result['roadmap']), 10)

    def test_fallback_week_numbers_sequential(self):
        missing_skills = [
            {'skill': 'Docker', 'demand': 10.0, 'rank': 1},
            {'skill': 'Redis', 'demand': 8.0, 'rank': 2},
            {'skill': 'PostgreSQL', 'demand': 6.0, 'rank': 3},
        ]
        result = generate_fallback_roadmap(missing_skills)
        week_numbers = [item['week_number'] for item in result['roadmap']]
        self.assertEqual(week_numbers, sorted(week_numbers))
"""Celery tasks for roadmap generation using Google Gemini API"""
from celery import shared_task
from django.conf import settings
from django.db import transaction
import logging
import json

import google.generativeai as genai

from .models import Roadmap, RoadmapItem, Resource
from analysis.models import SkillGapReport, GapItem
from parser.models import ExtractedSkill

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def generate_roadmap_task(self, report_id):
    """
    Generate learning roadmap using Google Gemini API
    """
    try:
        report = SkillGapReport.objects.get(id=report_id)

        logger.info(f"Generating roadmap for report: {report_id}")

        # Get user's current skills
        user_skills = ExtractedSkill.objects.filter(
            cv_upload=report.cv_upload
        ).values_list('normalized_name', flat=True)

        # Get top 10 gap items
        gap_items = GapItem.objects.filter(
            report=report
        ).order_by('priority_rank')[:10]

        if not gap_items.exists():
            logger.warning(f"No gap items found for report {report_id}")
            return

        # Generate roadmap using Gemini
        roadmap_data = generate_roadmap_with_gemini(
            current_skills=list(user_skills),
            missing_skills=[
                {
                    'skill': item.skill_name,
                    'demand': item.demand_frequency,
                    'rank': item.priority_rank
                }
                for item in gap_items
            ]
        )

        # Save roadmap to database
        with transaction.atomic():
            roadmap = Roadmap.objects.create(
                report=report,
                generated_by='gemini-2.0-flash'
            )

            for item_data in roadmap_data.get('roadmap', []):
                # Find corresponding gap item
                gap_item = gap_items.filter(
                    skill_name=item_data['skill_name']
                ).first()

                roadmap_item = RoadmapItem.objects.create(
                    roadmap=roadmap,
                    gap_item=gap_item,
                    skill_name=item_data['skill_name'],
                    week_number=item_data['week_number'],
                    description=item_data['description']
                )

                # Save resources for this roadmap item
                for resource_data in item_data.get('resources', []):
                    Resource.objects.create(
                        roadmap_item=roadmap_item,
                        title=resource_data['title'],
                        url=resource_data['url'],
                        platform=resource_data.get('platform', 'other'),
                        resource_type=resource_data.get('type', 'article')
                    )

        logger.info(f"Roadmap generated successfully for report: {report_id}")

        return {
            'report_id': str(report_id),
            'roadmap_id': str(roadmap.id),
            'items_count': len(roadmap_data.get('roadmap', []))
        }

    except SkillGapReport.DoesNotExist:
        logger.error(f"Report not found: {report_id}")
        raise

    except Exception as exc:
        logger.error(f"Error generating roadmap: {str(exc)}")

        # Mark report as failed
        try:
            report = SkillGapReport.objects.get(id=report_id)
            report.error_message = f"Roadmap generation failed: {str(exc)}"
            report.save()
        except Exception:
            pass

        raise self.retry(exc=exc, countdown=120 * (2 ** self.request.retries))


def generate_roadmap_with_gemini(current_skills, missing_skills):
    """
    Use Google Gemini API to generate a structured learning roadmap.
    genai.configure() is called here (not at module level) to ensure
    the API key is always read from settings at call time.
    """
    # ✅ Configure inside the function — not at module load time
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is not set. "
            "Please add it to your .env file and restart the server."
        )

    genai.configure(api_key=api_key)

    # Use gemini-2.0-flash (available on free tier)
    model = genai.GenerativeModel('gemini-2.0-flash')

    prompt = f"""You are an expert tech career advisor creating personalized learning roadmaps for job seekers in Nepal.

Current Skills: {', '.join(current_skills[:20]) if current_skills else 'None listed'}

Missing Skills (ranked by market demand):
{chr(10).join(f"{i+1}. {skill['skill']} (demand: {skill['demand']} jobs)" for i, skill in enumerate(missing_skills[:10]))}

Create a personalized learning roadmap to help acquire these missing skills. Focus on the top 10 skills.

IMPORTANT: Return your response as valid JSON only, with this exact structure:
{{
  "roadmap": [
    {{
      "skill_name": "React.js",
      "week_number": 1,
      "description": "Learn React fundamentals including JSX, components, props, and state management. Build small projects to practice.",
      "resources": [
        {{
          "title": "React Official Tutorial",
          "url": "https://react.dev/learn",
          "platform": "docs",
          "type": "documentation"
        }},
        {{
          "title": "React Course - FreeCodeCamp",
          "url": "https://www.freecodecamp.org/news/react-tutorial/",
          "platform": "freecodecamp",
          "type": "course"
        }}
      ]
    }}
  ]
}}

Guidelines:
1. Create a realistic 8-12 week roadmap
2. Prioritize skills by demand (higher demand = earlier weeks)
3. Organize learning in logical sequence (fundamentals before advanced)
4. Provide 2-3 high-quality free resources per skill
5. Prefer: official docs, FreeCodeCamp, YouTube, Roadmap.sh
6. Each week should focus on 1-2 related skills
7. Keep descriptions practical and actionable
8. Return ONLY valid JSON — no markdown, no extra text"""

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=4000,
            )
        )

        response_text = response.text

        # Strip markdown code fences if Gemini wraps the JSON
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0].strip()

        # Extract JSON object from response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1

        if json_start >= 0 and json_end > json_start:
            json_text = response_text[json_start:json_end]
            roadmap_data = json.loads(json_text)
        else:
            roadmap_data = json.loads(response_text)

        logger.info(
            f"Gemini generated roadmap with "
            f"{len(roadmap_data.get('roadmap', []))} items"
        )

        return roadmap_data

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini response as JSON: {e}")
        logger.error(f"Response text preview: {response_text[:500]}")
        return generate_fallback_roadmap(missing_skills)

    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise


def generate_fallback_roadmap(missing_skills):
    """
    Generate a basic fallback roadmap if Gemini API fails.
    This ensures users always get some output even if the API is down.
    """
    roadmap = []

    for idx, skill_data in enumerate(missing_skills[:10], 1):
        skill = skill_data['skill']
        search_query = skill.replace(' ', '+')

        roadmap.append({
            'skill_name': skill,
            'week_number': idx,
            'description': (
                f'Learn {skill} fundamentals through online tutorials and '
                f'hands-on practice. Focus on core concepts and build small '
                f'projects to reinforce your understanding.'
            ),
            'resources': [
                {
                    'title': f'{skill} - Official Documentation',
                    'url': f'https://www.google.com/search?q={search_query}+official+documentation',
                    'platform': 'docs',
                    'type': 'documentation'
                },
                {
                    'title': f'Learn {skill} - FreeCodeCamp',
                    'url': 'https://www.freecodecamp.org',
                    'platform': 'freecodecamp',
                    'type': 'course'
                },
                {
                    'title': f'{skill} Roadmap',
                    'url': f'https://roadmap.sh',
                    'platform': 'roadmap_sh',
                    'type': 'article'
                }
            ]
        })

    return {'roadmap': roadmap}
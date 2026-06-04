# SkillMap Nepal - API Documentation (Future)

## Overview

This document describes the REST API endpoints that can be implemented using Django REST Framework. Currently, the application uses Django views and templates, but serializers are ready for API implementation.

## Authentication

All API endpoints require authentication using Django session authentication or token-based authentication.

**Headers:**
```
Authorization: Token <your-api-token>
Content-Type: application/json
```

## Base URL

```
https://api.skillmap.np/api/v1/
```

## Endpoints

### Authentication

#### Register User
```http
POST /auth/register/
```

**Request:**
```json
{
  "email": "user@example.com",
  "full_name": "John Doe",
  "phone": "+977-9841234567",
  "password": "SecurePassword123",
  "password_confirm": "SecurePassword123"
}
```

**Response: 201 Created**
```json
{
  "id": "uuid-here",
  "email": "user@example.com",
  "full_name": "John Doe",
  "phone": "+977-9841234567",
  "token": "auth-token-here"
}
```

#### Login
```http
POST /auth/login/
```

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123"
}
```

**Response: 200 OK**
```json
{
  "token": "auth-token-here",
  "user": {
    "id": "uuid-here",
    "email": "user@example.com",
    "full_name": "John Doe"
  }
}
```

### CV Management

#### Upload CV
```http
POST /cv/upload/
```

**Request: Multipart Form Data**
```
cv_file: <file>
```

**Response: 201 Created**
```json
{
  "id": "cv-uuid-here",
  "original_filename": "resume.pdf",
  "file_url": "https://cloudinary.com/...",
  "parse_status": "pending",
  "uploaded_at": "2026-06-03T20:00:00Z"
}
```

#### Get CV Status
```http
GET /cv/{cv_id}/status/
```

**Response: 200 OK**
```json
{
  "id": "cv-uuid-here",
  "parse_status": "done",
  "uploaded_at": "2026-06-03T20:00:00Z",
  "parsed_at": "2026-06-03T20:02:00Z",
  "skills_extracted": 15
}
```

#### List User CVs
```http
GET /cv/
```

**Response: 200 OK**
```json
{
  "count": 5,
  "results": [
    {
      "id": "cv-uuid-1",
      "original_filename": "resume.pdf",
      "parse_status": "done",
      "uploaded_at": "2026-06-03T20:00:00Z"
    },
    {
      "id": "cv-uuid-2",
      "original_filename": "cv_latest.docx",
      "parse_status": "processing",
      "uploaded_at": "2026-06-02T15:00:00Z"
    }
  ]
}
```

### Skills

#### Get Extracted Skills
```http
GET /cv/{cv_id}/skills/
```

**Response: 200 OK**
```json
{
  "cv_id": "cv-uuid-here",
  "skills": [
    {
      "id": "skill-uuid-1",
      "skill_name": "python",
      "normalized_name": "Python",
      "confidence_score": 1.0
    },
    {
      "id": "skill-uuid-2",
      "skill_name": "django",
      "normalized_name": "Django",
      "confidence_score": 0.95
    }
  ]
}
```

### Reports

#### List User Reports
```http
GET /reports/
```

**Query Parameters:**
- `status` (optional): Filter by status (pending, generating, ready, failed)
- `ordering` (optional): Order by field (-generated_at, readiness_score)

**Response: 200 OK**
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "report-uuid-1",
      "readiness_score": 75.5,
      "total_jobs_matched": 15,
      "status": "ready",
      "generated_at": "2026-06-03T20:05:00Z"
    },
    {
      "id": "report-uuid-2",
      "readiness_score": 68.2,
      "total_jobs_matched": 12,
      "status": "ready",
      "generated_at": "2026-06-01T18:00:00Z"
    }
  ]
}
```

#### Get Report Detail
```http
GET /reports/{report_id}/
```

**Response: 200 OK**
```json
{
  "id": "report-uuid-here",
  "user": {
    "id": "user-uuid",
    "email": "user@example.com",
    "full_name": "John Doe"
  },
  "cv_upload": {
    "id": "cv-uuid",
    "original_filename": "resume.pdf"
  },
  "readiness_score": 75.5,
  "total_jobs_matched": 15,
  "status": "ready",
  "generated_at": "2026-06-03T20:05:00Z",
  "gap_items": [
    {
      "skill_name": "React.js",
      "demand_frequency": 45,
      "similarity_score": 0.6,
      "priority_rank": 1
    },
    {
      "skill_name": "Docker",
      "demand_frequency": 38,
      "similarity_score": 0.4,
      "priority_rank": 2
    }
  ]
}
```

### Roadmap

#### Get Roadmap
```http
GET /roadmap/{report_id}/
```

**Response: 200 OK**
```json
{
  "id": "roadmap-uuid-here",
  "report_id": "report-uuid-here",
  "generated_by": "claude-sonnet-4-20250514",
  "created_at": "2026-06-03T20:10:00Z",
  "items": [
    {
      "skill_name": "React.js",
      "week_number": 1,
      "description": "Learn React fundamentals including JSX, components, props, and state...",
      "resources": [
        {
          "title": "React Official Tutorial",
          "url": "https://react.dev/learn",
          "platform": "docs",
          "resource_type": "documentation"
        },
        {
          "title": "React for Beginners",
          "url": "https://www.youtube.com/watch?v=...",
          "platform": "youtube",
          "resource_type": "video"
        }
      ]
    },
    {
      "skill_name": "Docker",
      "week_number": 2,
      "description": "Understand containerization, Dockerfile, docker-compose...",
      "resources": [
        {
          "title": "Docker Documentation",
          "url": "https://docs.docker.com",
          "platform": "docs",
          "resource_type": "documentation"
        }
      ]
    }
  ]
}
```

### Job Market

#### Search Jobs
```http
GET /jobs/
```

**Query Parameters:**
- `skill` (optional): Filter by skill name
- `source` (optional): Filter by source (merojob, kumarijob)
- `district` (optional): Filter by location
- `page` (optional): Page number

**Response: 200 OK**
```json
{
  "count": 150,
  "next": "https://api.skillmap.np/api/v1/jobs/?page=2",
  "previous": null,
  "results": [
    {
      "id": "job-uuid-1",
      "title": "Senior Python Developer",
      "company": "Tech Company Nepal",
      "source": "merojob",
      "district": "Kathmandu",
      "experience_level": "5+ years",
      "salary_range": "NPR 80,000 - 120,000",
      "scraped_at": "2026-06-03T18:00:00Z",
      "required_skills": [
        "Python",
        "Django",
        "PostgreSQL",
        "AWS"
      ]
    }
  ]
}
```

#### Get Job Statistics
```http
GET /jobs/stats/
```

**Response: 200 OK**
```json
{
  "total_jobs": 450,
  "by_source": {
    "merojob": 280,
    "kumarijob": 170
  },
  "top_skills": [
    {"skill": "Python", "count": 85},
    {"skill": "JavaScript", "count": 78},
    {"skill": "React.js", "count": 65},
    {"skill": "Node.js", "count": 58},
    {"skill": "Django", "count": 52}
  ],
  "by_district": {
    "Kathmandu": 320,
    "Lalitpur": 95,
    "Bhaktapur": 35
  }
}
```

## Webhooks (Future)

### CV Processing Complete
```http
POST {your_webhook_url}
```

**Payload:**
```json
{
  "event": "cv.parsed",
  "cv_id": "cv-uuid-here",
  "user_id": "user-uuid-here",
  "status": "done",
  "skills_count": 15,
  "timestamp": "2026-06-03T20:02:00Z"
}
```

### Report Generated
```http
POST {your_webhook_url}
```

**Payload:**
```json
{
  "event": "report.ready",
  "report_id": "report-uuid-here",
  "user_id": "user-uuid-here",
  "readiness_score": 75.5,
  "timestamp": "2026-06-03T20:05:00Z"
}
```

## Error Responses

### 400 Bad Request
```json
{
  "error": "validation_error",
  "message": "Invalid input data",
  "details": {
    "email": ["This field is required"],
    "password": ["Password must be at least 8 characters"]
  }
}
```

### 401 Unauthorized
```json
{
  "error": "authentication_failed",
  "message": "Invalid credentials"
}
```

### 404 Not Found
```json
{
  "error": "not_found",
  "message": "Report not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "internal_error",
  "message": "An unexpected error occurred"
}
```

## Rate Limiting

- **Unauthenticated**: 100 requests/hour
- **Authenticated**: 1000 requests/hour
- **CV Upload**: 10 uploads/hour per user

**Rate Limit Headers:**
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1685820000
```

## Pagination

All list endpoints support pagination:

**Request:**
```http
GET /reports/?page=2&page_size=20
```

**Response:**
```json
{
  "count": 50,
  "next": "https://api.skillmap.np/api/v1/reports/?page=3",
  "previous": "https://api.skillmap.np/api/v1/reports/?page=1",
  "results": [...]
}
```

## Filtering & Sorting

**Filtering:**
```http
GET /jobs/?skill=Python&district=Kathmandu
```

**Sorting:**
```http
GET /reports/?ordering=-readiness_score
GET /reports/?ordering=generated_at
```

## Implementation Guide

To implement these endpoints:

1. **Install Django REST Framework** (already in requirements.txt)

2. **Create ViewSets** in `dashboard/views.py`:
```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .serializers import SkillGapReportSerializer

class ReportViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SkillGapReportSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return SkillGapReport.objects.filter(user=self.request.user)
```

3. **Add API URLs** in `skillmap/urls.py`:
```python
from rest_framework.routers import DefaultRouter
from dashboard import views

router = DefaultRouter()
router.register(r'reports', views.ReportViewSet, basename='report')
router.register(r'roadmaps', views.RoadmapViewSet, basename='roadmap')

urlpatterns = [
    path('api/v1/', include(router.urls)),
]
```

4. **Add Authentication**:
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
}
```

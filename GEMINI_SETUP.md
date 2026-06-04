# Using Google Gemini API (Free Tier)

## Why Gemini?

Google Gemini offers a **FREE tier** with generous limits:
- **Free tier**: 15 requests per minute
- **Model**: gemini-1.5-flash (fast and efficient)
- **No credit card required** for free tier
- Perfect for development and moderate production use

## Setup Instructions

### 1. Get Your Free API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Get API Key"
3. Click "Create API Key" 
4. Choose "Create API key in new project" (or select existing project)
5. Copy your API key (starts with `AIza...`)

**Note**: You need a Google account. No credit card required!

### 2. Update Your `.env` File

```bash
# Replace this line:
ANTHROPIC_API_KEY=your-anthropic-api-key

# With:
GEMINI_API_KEY=AIzaSy...your-actual-key-here
```

### 3. Verify Configuration

The application is already configured to use Gemini! The key changes are:

**roadmap/tasks.py**: Uses `google.generativeai` SDK
**requirements.txt**: Includes `google-generativeai==0.3.2`
**roadmap/models.py**: Default model is `gemini-1.5-flash`

## Features & Capabilities

### What Gemini Does in SkillMap Nepal

1. **Analyzes Skill Gaps**: Receives user's current skills and missing skills
2. **Generates Roadmaps**: Creates week-by-week learning plans
3. **Curates Resources**: Suggests free learning materials
4. **Structured Output**: Returns JSON-formatted roadmaps

### Example Output

```json
{
  "roadmap": [
    {
      "skill_name": "React.js",
      "week_number": 1,
      "description": "Learn React fundamentals including JSX, components, props, and state management.",
      "resources": [
        {
          "title": "React Official Docs",
          "url": "https://react.dev/learn",
          "platform": "docs",
          "type": "documentation"
        },
        {
          "title": "React Tutorial for Beginners",
          "url": "https://www.youtube.com/watch?v=...",
          "platform": "youtube",
          "type": "video"
        }
      ]
    }
  ]
}
```

## Rate Limits & Quotas

### Free Tier Limits
- **15 requests per minute** (RPM)
- **1 million tokens per minute** (TPM)
- **1500 requests per day** (RPD)

**This means**: You can generate ~1500 roadmaps per day for free!

### For Production at Scale

If you need more, upgrade to paid tier:
- Pay-as-you-go pricing
- $0.35 per 1 million input tokens
- $1.05 per 1 million output tokens
- Still very affordable!

## Error Handling

The application includes automatic fallback:

```python
try:
    # Try Gemini API
    roadmap = generate_roadmap_with_gemini(skills)
except Exception as e:
    # Falls back to template-based roadmap
    roadmap = generate_fallback_roadmap(skills)
```

## Testing Your Setup

### 1. Check API Key is Valid

```python
import google.generativeai as genai

genai.configure(api_key='YOUR_API_KEY')
model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content('Hello!')
print(response.text)
```

### 2. Test in Django Shell

```bash
python manage.py shell
```

```python
from roadmap.tasks import generate_roadmap_with_gemini

test_skills = ['Python', 'Django']
test_gaps = [
    {'skill': 'React.js', 'demand': 45},
    {'skill': 'Docker', 'demand': 38}
]

result = generate_roadmap_with_gemini(test_skills, test_gaps)
print(result)
```

## Troubleshooting

### Error: "API key not valid"
- Check your API key is correct
- Verify you copied the entire key
- Ensure no extra spaces in `.env` file

### Error: "Resource exhausted"
- You've hit the rate limit (15 RPM)
- Wait 60 seconds and retry
- The app has automatic retry logic

### Error: "Module not found: google.generativeai"
```bash
pip install google-generativeai==0.3.2
```

### Gemini Returns Invalid JSON
- The app automatically extracts JSON from response
- Fallback roadmap is generated if parsing fails
- Check logs for details

## Comparison: Gemini vs Claude

| Feature | Gemini 1.5 Flash | Claude Sonnet 4 |
|---------|------------------|-----------------|
| **Free Tier** | ✅ Yes (1500/day) | ❌ No |
| **Speed** | Very Fast | Fast |
| **Quality** | Excellent | Excellent |
| **JSON Output** | ✅ Yes | ✅ Yes |
| **Cost (Paid)** | $0.35-1.05/1M tokens | $3-15/1M tokens |
| **Rate Limit** | 15 RPM (free) | Based on plan |

**Recommendation**: Use Gemini for development and small-to-medium production. Only switch to Claude if you need enterprise features.

## Best Practices

### 1. Respect Rate Limits
```python
# Already implemented in tasks.py with retry logic
@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def generate_roadmap_task(self, report_id):
    # Automatic retry with exponential backoff
```

### 2. Cache Results
Since roadmaps don't change frequently, consider caching:
```python
from django.core.cache import cache

cached = cache.get(f'roadmap_{report_id}')
if cached:
    return cached
```

### 3. Monitor Usage
Track API calls in logs:
```python
logger.info(f"Gemini API called for report {report_id}")
```

### 4. Handle Errors Gracefully
The app already does this with fallback roadmaps.

## Production Deployment

### Environment Variables
```bash
# Production .env
GEMINI_API_KEY=AIzaSy...your-prod-key
DEBUG=False
```

### Docker Deployment
No changes needed! The Docker setup already includes google-generativeai.

### Monitoring
Track these metrics:
- Gemini API success rate
- Response times
- Fallback usage frequency
- Daily API call count

## Cost Estimation

### Example Scenario
- 100 users per day
- Each uploads 1 CV
- 100 roadmaps generated per day

**Cost**: $0.00 (within free tier of 1500/day)

### Scaling Up
- 1500 users per day = Still FREE
- 5000 users per day = ~$5-10/month
- 10,000 users per day = ~$15-25/month

**Much cheaper than Claude!**

## Additional Resources

- [Gemini API Documentation](https://ai.google.dev/docs)
- [Python SDK Guide](https://ai.google.dev/tutorials/python_quickstart)
- [Pricing Details](https://ai.google.dev/pricing)
- [Rate Limits](https://ai.google.dev/docs/concepts/rate_limits)

## Support

If you encounter issues:
1. Check Django logs: `docker-compose logs web`
2. Check Celery logs: `docker-compose logs worker`
3. Verify API key in `.env`
4. Test API key independently (see Testing section)

## Conclusion

Google Gemini provides an excellent free alternative to paid AI APIs, making SkillMap Nepal accessible for development, testing, and small-to-medium production deployments without any API costs!

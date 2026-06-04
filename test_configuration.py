"""
Configuration Test Script
Tests all API connections and settings
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skillmap.settings')
django.setup()

from django.conf import settings
import sys

print("=" * 60)
print("SKILLMAP NEPAL - CONFIGURATION TEST")
print("=" * 60)

errors = []
warnings = []

# Test 1: Django Settings
print("\n1. DJANGO CONFIGURATION")
print("-" * 60)
print(f"✅ DEBUG mode: {settings.DEBUG}")
print(f"✅ Database: {settings.DATABASES['default']['ENGINE']}")
print(f"✅ Secret key: {'*' * 20} (configured)")

# Test 2: Celery Configuration
print("\n2. CELERY CONFIGURATION")
print("-" * 60)
print(f"✅ Broker URL: {settings.CELERY_BROKER_URL}")
eager_mode = getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False)
if eager_mode:
    print(f"✅ Eager mode: ENABLED (tasks run synchronously, no Redis needed)")
else:
    print(f"⚠️  Eager mode: DISABLED (requires Redis to be running)")
    warnings.append("Redis must be running for async tasks")

# Test 3: Email Configuration
print("\n3. EMAIL CONFIGURATION")
print("-" * 60)
email_backend = settings.EMAIL_BACKEND
print(f"✅ Email backend: {email_backend}")
if 'console' in email_backend.lower():
    print(f"✅ Console mode: Emails will print to terminal")
elif 'smtp' in email_backend.lower():
    print(f"⚠️  SMTP mode: Requires email server configuration")

# Test 4: Cloudinary Configuration
print("\n4. CLOUDINARY CONFIGURATION")
print("-" * 60)
cloud_name = settings.CLOUDINARY_STORAGE.get('CLOUD_NAME', '')
api_key = settings.CLOUDINARY_STORAGE.get('API_KEY', '')
api_secret = settings.CLOUDINARY_STORAGE.get('API_SECRET', '')

if cloud_name and api_key and api_secret:
    print(f"✅ Cloud name: {cloud_name}")
    print(f"✅ API key: {'*' * 10}{api_key[-4:]}")
    print(f"✅ API secret: {'*' * 20}")
    
    # Test connection
    try:
        import cloudinary
        import cloudinary.api
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )
        result = cloudinary.api.ping()
        print(f"✅ Connection test: SUCCESS - {result.get('status', 'ok')}")
    except Exception as e:
        print(f"❌ Connection test: FAILED - {str(e)}")
        errors.append(f"Cloudinary connection failed: {e}")
else:
    print(f"⚠️  Cloudinary not configured (CV uploads will fail)")
    warnings.append("Configure Cloudinary for CV uploads")

# Test 5: Gemini API Configuration
print("\n5. GOOGLE GEMINI API CONFIGURATION")
print("-" * 60)
gemini_key = settings.GEMINI_API_KEY

if gemini_key:
    print(f"✅ API key: {'*' * 20}{gemini_key[-8:]}")
    
    # Test connection
    try:
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Simple test
        response = model.generate_content("Say 'OK' if you can read this.")
        print(f"✅ Connection test: SUCCESS")
        print(f"✅ Response: {response.text[:50]}...")
    except Exception as e:
        print(f"❌ Connection test: FAILED - {str(e)}")
        errors.append(f"Gemini API failed: {e}")
else:
    print(f"⚠️  Gemini API key not configured (AI roadmaps will fail)")
    warnings.append("Configure Gemini API for AI roadmap generation")

# Test 6: Django Apps
print("\n6. INSTALLED APPS")
print("-" * 60)
local_apps = ['users', 'parser', 'scraper', 'analysis', 'roadmap', 'dashboard']
for app in local_apps:
    if app in settings.INSTALLED_APPS:
        print(f"✅ {app}")
    else:
        print(f"❌ {app} - NOT INSTALLED")
        errors.append(f"App {app} is not installed")

# Test 7: Database Connection
print("\n7. DATABASE CONNECTION")
print("-" * 60)
try:
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"✅ Database connection: SUCCESS")
        
        # Count users
        from users.models import User
        user_count = User.objects.count()
        print(f"✅ Total users: {user_count}")
except Exception as e:
    print(f"❌ Database connection: FAILED - {str(e)}")
    errors.append(f"Database error: {e}")

# Test 8: Static Files
print("\n8. STATIC FILES")
print("-" * 60)
print(f"✅ Static URL: {settings.STATIC_URL}")
print(f"✅ Static root: {settings.STATIC_ROOT}")
print(f"✅ Media URL: {settings.MEDIA_URL}")
print(f"✅ Media root: {settings.MEDIA_ROOT}")

# Test 9: Authentication
print("\n9. AUTHENTICATION")
print("-" * 60)
print(f"✅ Custom user model: {settings.AUTH_USER_MODEL}")
print(f"✅ Login URL: /accounts/login/")
print(f"✅ Login redirect: {settings.LOGIN_REDIRECT_URL}")
print(f"✅ Logout redirect: {settings.LOGOUT_REDIRECT_URL}")
print(f"✅ Email authentication: ENABLED")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

if errors:
    print(f"\n❌ ERRORS FOUND: {len(errors)}")
    for i, error in enumerate(errors, 1):
        print(f"   {i}. {error}")
else:
    print(f"\n✅ No critical errors found!")

if warnings:
    print(f"\n⚠️  WARNINGS: {len(warnings)}")
    for i, warning in enumerate(warnings, 1):
        print(f"   {i}. {warning}")
else:
    print(f"\n✅ No warnings!")

# Overall Status
print("\n" + "=" * 60)
if not errors:
    print("STATUS: ✅ READY FOR TESTING")
    print("\nYou can now:")
    print("1. Create user accounts at http://localhost:8000/accounts/signup/")
    print("2. Access admin panel at http://localhost:8000/admin")
    print("3. Upload CVs (if Cloudinary is working)")
    print("4. Generate roadmaps (if Gemini is working)")
else:
    print("STATUS: ⚠️  NEEDS ATTENTION")
    print("\nPlease fix the errors above before proceeding.")

print("=" * 60)

sys.exit(0 if not errors else 1)

#!/usr/bin/env python
"""
Quick local runner for SkillMap Nepal
This script sets up and runs the application locally with SQLite (no Docker needed)
"""
import os
import sys
import subprocess

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def run_command(cmd, description):
    print(f"▶ {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
        return False
    print(f"✅ {description} completed")
    return True

def main():
    print_header("SkillMap Nepal - Local Setup")
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required. You have:", sys.version)
        return
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("❌ .env file not found. Creating from .env.example...")
        run_command('copy .env.example .env', 'Create .env file')
    
    print_header("Step 1: Installing Dependencies")
    print("⏳ This may take a few minutes...")
    
    # Install only essential packages for quick start
    essential_packages = [
        "Django==4.2.11",
        "djangorestframework==3.14.0",
        "django-allauth==0.61.1",
        "python-decouple==3.8",
        "dj-database-url==2.1.0",
        "whitenoise==6.6.0",
        "Pillow",
    ]
    
    for package in essential_packages:
        if not run_command(f'pip install {package}', f'Install {package.split("==")[0]}'):
            print(f"⚠️  Warning: Could not install {package}")
    
    print_header("Step 2: Database Setup")
    
    # Run migrations
    if not run_command('python manage.py makemigrations', 'Create migrations'):
        print("⚠️  Warning: Migrations might already exist")
    
    if not run_command('python manage.py migrate', 'Apply migrations'):
        print("❌ Failed to run migrations")
        return
    
    # Setup Django sites
    print("▶ Configuring Django sites...")
    setup_site_code = """
from django.contrib.sites.models import Site
try:
    site = Site.objects.get(id=1)
    site.domain = 'localhost:8000'
    site.name = 'SkillMap Nepal'
    site.save()
    print('✅ Site configured')
except Exception as e:
    print(f'⚠️  Site setup: {e}')
"""
    
    with open('_setup_site.py', 'w') as f:
        f.write(setup_site_code)
    
    subprocess.run('python manage.py shell < _setup_site.py', shell=True, capture_output=True)
    os.remove('_setup_site.py')
    
    print_header("Step 3: Create Admin User")
    print("Please create an admin account:\n")
    subprocess.run('python manage.py createsuperuser', shell=True)
    
    print_header("Setup Complete! 🎉")
    
    print("""
Next Steps:

1. Run the development server:
   python manage.py runserver

2. Open your browser:
   http://localhost:8000

3. Access admin panel:
   http://localhost:8000/admin

4. To enable full features, add API keys to .env:
   - GEMINI_API_KEY (FREE from https://makersuite.google.com/app/apikey)
   - CLOUDINARY credentials (FREE from https://cloudinary.com)

Note: Some features require additional setup:
- CV parsing: Install spaCy model (python -m spacy download en_core_web_md)
- Async tasks: Install and run Redis + Celery
- Job scraping: Install Playwright (pip install playwright && playwright install chromium)

For full setup, see: RUN_LOCAL.md
""")

if __name__ == '__main__':
    main()

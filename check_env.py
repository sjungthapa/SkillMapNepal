"""
Simple script to check if .env file is being loaded correctly
"""
import os
from pathlib import Path

print("=" * 60)
print("CHECKING .ENV FILE")
print("=" * 60)

# Check if .env file exists
env_path = Path('.env')
if env_path.exists():
    print(f"\n✅ .env file found at: {env_path.absolute()}")
    print(f"✅ File size: {env_path.stat().st_size} bytes")
    print(f"✅ Last modified: {env_path.stat().st_mtime}")
else:
    print(f"\n❌ .env file NOT found!")
    print(f"❌ Looking in: {Path.cwd()}")
    exit(1)

# Read the file
print("\n" + "-" * 60)
print("GEMINI_API_KEY LINE IN .ENV FILE:")
print("-" * 60)

with open('.env', 'r') as f:
    lines = f.readlines()
    
found_key = False
for i, line in enumerate(lines, 1):
    if 'GEMINI_API_KEY' in line and not line.strip().startswith('#'):
        found_key = True
        print(f"Line {i}: {line.rstrip()}")
        
        # Parse the line
        if '=' in line:
            key_value = line.split('=', 1)[1].strip()
            
            # Check for issues
            issues = []
            
            if not key_value:
                issues.append("❌ Value is EMPTY")
            elif key_value.startswith(' '):
                issues.append("❌ Has SPACE at beginning")
            elif not key_value.startswith('AIza'):
                issues.append(f"⚠️  Doesn't start with 'AIza' (starts with '{key_value[:4]}')")
            elif len(key_value) < 30:
                issues.append(f"⚠️  Too short (only {len(key_value)} chars)")
            else:
                issues.append(f"✅ Format looks correct!")
                issues.append(f"✅ Starts with: {key_value[:10]}")
                issues.append(f"✅ Length: {len(key_value)} characters")
            
            print("\nValidation:")
            for issue in issues:
                print(f"  {issue}")

if not found_key:
    print("❌ GEMINI_API_KEY not found in .env file!")

# Try loading with python-decouple
print("\n" + "-" * 60)
print("LOADING WITH DJANGO SETTINGS:")
print("-" * 60)

try:
    from decouple import config
    api_key = config('GEMINI_API_KEY', default='')
    
    if api_key:
        print(f"✅ Key loaded successfully!")
        print(f"✅ First 10 chars: {api_key[:10]}")
        print(f"✅ Last 8 chars: ...{api_key[-8:]}")
        print(f"✅ Total length: {len(api_key)} characters")
        
        if not api_key.startswith('AIza'):
            print(f"\n⚠️  WARNING: Key doesn't start with 'AIza'")
            print(f"   Your key starts with: {api_key[:4]}")
            print(f"   Expected format: AIzaSy...")
    else:
        print("❌ Key is EMPTY after loading!")
        print("   Make sure the line in .env is: GEMINI_API_KEY=your-key-here")
        
except Exception as e:
    print(f"❌ Error loading: {e}")

# Check Django settings
print("\n" + "-" * 60)
print("CHECKING DJANGO SETTINGS:")
print("-" * 60)

try:
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skillmap.settings')
    django.setup()
    
    from django.conf import settings
    
    if hasattr(settings, 'GEMINI_API_KEY'):
        key = settings.GEMINI_API_KEY
        if key:
            print(f"✅ GEMINI_API_KEY is set in Django settings")
            print(f"✅ First 10 chars: {key[:10]}")
            print(f"✅ Length: {len(key)} characters")
        else:
            print(f"❌ GEMINI_API_KEY is EMPTY in Django settings")
    else:
        print(f"❌ GEMINI_API_KEY not found in Django settings")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

print("\n📝 To fix 'Must supply api_key' error:")
print("   1. Get API key from: https://makersuite.google.com/app/apikey")
print("   2. Key must start with: AIza")
print("   3. Edit .env file: GEMINI_API_KEY=AIzaSy...")
print("   4. NO spaces after the = sign")
print("   5. Save file and restart server")
print("\n   See GET_GEMINI_API_KEY.md for detailed instructions")

print("=" * 60)

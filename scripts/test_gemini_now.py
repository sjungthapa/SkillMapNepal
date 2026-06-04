"""
Test Gemini API configuration RIGHT NOW
Run this to diagnose the exact issue
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skillmap.settings')
django.setup()

from django.conf import settings
import google.generativeai as genai

print("=" * 60)
print("GEMINI API DIAGNOSTIC TEST")
print("=" * 60)

# Step 1: Check if API key is in settings
print("\n1. Checking Django Settings...")
api_key = settings.GEMINI_API_KEY
if api_key:
    print(f"   ✅ API Key found: {api_key[:15]}...{api_key[-5:]}")
    print(f"   ✅ Length: {len(api_key)} characters")
else:
    print(f"   ❌ API Key NOT found in settings!")
    print(f"   ❌ Check your .env file")
    exit(1)

# Step 2: Configure genai
print("\n2. Configuring Google Generative AI...")
try:
    genai.configure(api_key=api_key)
    print(f"   ✅ genai.configure() called successfully")
except Exception as e:
    print(f"   ❌ Configuration failed: {e}")
    exit(1)

# Step 3: List available models
print("\n3. Listing Available Models...")
try:
    models = list(genai.list_models())
    content_models = [m for m in models if 'generateContent' in m.supported_generation_methods]
    print(f"   ✅ Found {len(content_models)} models that support content generation")
    print(f"   Top models:")
    for model in content_models[:5]:
        print(f"      - {model.name}")
except Exception as e:
    print(f"   ❌ Failed to list models: {e}")
    print(f"   This might mean API key is invalid or network issue")

# Step 4: Test simple generation
print("\n4. Testing Simple Content Generation...")
print("   Trying model: gemini-2.5-flash")
try:
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content("Say 'Hello from Nepal!'")
    print(f"   ✅ SUCCESS! Response: {response.text[:100]}")
except Exception as e:
    error_msg = str(e)
    print(f"   ❌ FAILED: {error_msg[:200]}")
    
    if "429" in error_msg or "quota" in error_msg.lower():
        print("\n   💡 This is a QUOTA ERROR, not an API key error!")
        print("   Your API key IS working, you've just hit the daily limit.")
        print("   Wait 24 hours or create a new API key.")
    elif "404" in error_msg or "not found" in error_msg.lower():
        print("\n   💡 Model not found. Trying gemini-2.0-flash...")
        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content("Say 'Hello from Nepal!'")
            print(f"   ✅ SUCCESS with gemini-2.0-flash! Response: {response.text[:100]}")
        except Exception as e2:
            print(f"   ❌ Also failed: {str(e2)[:200]}")
    elif "401" in error_msg or "invalid" in error_msg.lower():
        print("\n   💡 This IS an API key error!")
        print("   Your API key may be invalid or expired.")
        print("   Get a new one from: https://makersuite.google.com/app/apikey")

# Step 5: Test the actual function
print("\n5. Testing Roadmap Generation Function...")
try:
    from roadmap.tasks import generate_roadmap_with_gemini
    print("   ℹ️  Calling generate_roadmap_with_gemini...")
    result = generate_roadmap_with_gemini(
        current_skills=['Python', 'Django'],
        missing_skills=[
            {'skill': 'Docker', 'demand': 10, 'rank': 1},
            {'skill': 'AWS', 'demand': 8, 'rank': 2}
        ]
    )
    print(f"   ✅ Function worked! Generated {len(result.get('roadmap', []))} roadmap items")
except Exception as e:
    error_msg = str(e)
    print(f"   ❌ Function failed: {error_msg[:300]}")
    
    if "must supply" in error_msg.lower():
        print("\n   💡 'Must supply' error detected!")
        print("   This means genai.configure() wasn't called properly")
        print("   OR the API key is empty string")
    elif "429" in error_msg or "quota" in error_msg.lower():
        print("\n   💡 Quota exceeded - your API key IS working!")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

if api_key:
    print("✅ API key is loaded in Django")
else:
    print("❌ API key NOT loaded")

print("\nIf you see 'quota exceeded', your configuration is CORRECT!")
print("If you see 'must supply api_key', there's a configuration issue.")
print("\nFor quota issues: Wait 24h or create new API key")
print("For API key issues: Check .env file and restart server")
print("=" * 60)

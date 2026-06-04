"""
Quick script to create a superuser for SkillMap Nepal
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skillmap.settings')
django.setup()

from users.models import User

# Check if superuser already exists
if User.objects.filter(email='admin@skillmap.com').exists():
    print("✅ Superuser 'admin@skillmap.com' already exists!")
else:
    # Create superuser
    user = User.objects.create_superuser(
        username='admin',
        email='admin@skillmap.com',
        password='admin123',
        full_name='Admin User'
    )
    print("✅ Superuser created successfully!")
    print(f"   Username: admin")
    print(f"   Email: admin@skillmap.com")
    print(f"   Password: admin123")
    print(f"   Name: {user.full_name}")

print("\n🚀 You can now login at: http://localhost:8000/admin")

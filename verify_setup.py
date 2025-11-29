#!/usr/bin/env python
"""
Setup verification script for Chimera Protocol
Run this after setup to verify everything is working
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chimera.settings')
django.setup()

from django.db import connection
from api.models import Memory, Conversation
from api.memory_service import memory_service


def check_database():
    """Check database connection"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✅ Database connection: OK")
        return True
    except Exception as e:
        print(f"❌ Database connection: FAILED - {e}")
        return False


def check_models():
    """Check if models are migrated"""
    try:
        Memory.objects.count()
        Conversation.objects.count()
        print("✅ Database models: OK")
        return True
    except Exception as e:
        print(f"❌ Database models: FAILED - {e}")
        print("   Run: python manage.py migrate")
        return False


def check_kiro_directory():
    """Check if .kiro directory exists with required files"""
    kiro_dir = os.path.join(os.path.dirname(__file__), '.kiro')
    spec_file = os.path.join(kiro_dir, 'spec.md')
    steering_file = os.path.join(kiro_dir, 'steering.md')
    
    if not os.path.exists(kiro_dir):
        print("❌ .kiro directory: NOT FOUND")
        return False
    
    if not os.path.exists(spec_file):
        print("❌ .kiro/spec.md: NOT FOUND")
        return False
    
    if not os.path.exists(steering_file):
        print("❌ .kiro/steering.md: NOT FOUND")
        return False
    
    print("✅ .kiro directory: OK")
    print(f"   - spec.md: {os.path.getsize(spec_file)} bytes")
    print(f"   - steering.md: {os.path.getsize(steering_file)} bytes")
    return True


def check_memory_service():
    """Check if memory service is working"""
    try:
        # Create test memory
        test_memory = Memory.objects.create(
            text="Test memory for verification",
            conversation_id="test-verify",
            tags=["test"]
        )
        
        # Try to search
        results = memory_service.search("verification", top_k=1)
        
        # Cleanup
        test_memory.delete()
        
        print("✅ Memory service: OK")
        return True
    except Exception as e:
        print(f"❌ Memory service: FAILED - {e}")
        return False


def check_env_file():
    """Check if .env file exists"""
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    
    if not os.path.exists(env_file):
        print("⚠️  .env file: NOT FOUND (using defaults)")
        print("   Copy .env.example to .env and configure if needed")
        return True
    
    print("✅ .env file: OK")
    return True


def main():
    """Run all checks"""
    print("=" * 60)
    print("Chimera Protocol - Setup Verification")
    print("=" * 60)
    print()
    
    checks = [
        ("Environment file", check_env_file),
        ("Database connection", check_database),
        ("Database models", check_models),
        (".kiro directory", check_kiro_directory),
        ("Memory service", check_memory_service),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {name}: ERROR - {e}")
            results.append(False)
        print()
    
    print("=" * 60)
    if all(results):
        print("🎉 All checks passed! Your setup is ready.")
        print()
        print("Next steps:")
        print("  1. Start server: python manage.py runserver")
        print("  2. Visit: http://localhost:8000/api/health")
        print("  3. Check API docs: http://localhost:8000/swagger/")
        print("  4. Read README.md for complete guide")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        print()
        print("Common fixes:")
        print("  - Run: python manage.py migrate")
        print("  - Check database credentials in .env")
        print("  - Ensure PostgreSQL is running")
    print("=" * 60)
    
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(main())

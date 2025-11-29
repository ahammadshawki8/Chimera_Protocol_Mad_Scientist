#!/usr/bin/env python
"""
Quick Start Script - Sets up everything automatically
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chimera.settings')
django.setup()

from django.core.management import call_command
from django.contrib.auth.models import User
from api.models import Workspace, TeamMember

def print_header(text):
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60 + "\n")

def main():
    print_header("Chimera Protocol - Quick Start")
    
    # Step 1: Create migrations
    print("Step 1: Creating migrations...")
    try:
        call_command('makemigrations', verbosity=0)
        print("✅ Migrations created")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Step 2: Apply migrations
    print("\nStep 2: Applying migrations...")
    try:
        call_command('migrate', verbosity=0)
        print("✅ Migrations applied")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Step 3: Create demo user and workspace
    print("\nStep 3: Creating demo data...")
    try:
        # Check if demo user exists
        if User.objects.filter(username='demo').exists():
            print("⚠️  Demo user already exists")
            user = User.objects.get(username='demo')
        else:
            user = User.objects.create_user('demo', 'demo@example.com', 'demo123')
            print("✅ Created demo user: demo / demo123")
        
        # Check if demo workspace exists
        if Workspace.objects.filter(name="Demo Workspace").exists():
            print("⚠️  Demo workspace already exists")
            workspace = Workspace.objects.get(name="Demo Workspace")
        else:
            workspace = Workspace.objects.create(
                name="Demo Workspace",
                description="Demo workspace for testing",
                owner=user
            )
            print(f"✅ Created workspace: {workspace.id}")
        
        # Check if team member exists
        if TeamMember.objects.filter(user=user, workspace=workspace).exists():
            print("⚠️  Team member already exists")
        else:
            TeamMember.objects.create(
                user=user,
                workspace=workspace,
                role='admin',
                status='online'
            )
            print("✅ Added user as admin")
        
    except Exception as e:
        print(f"❌ Error creating demo data: {e}")
        return False
    
    # Step 4: Show summary
    print_header("Setup Complete!")
    
    print("📊 Summary:")
    print(f"   - Demo User: demo / demo123")
    print(f"   - Workspace ID: {workspace.id}")
    print(f"   - Workspace Name: {workspace.name}")
    print()
    
    print("🚀 Next Steps:")
    print("   1. Start server: python manage.py runserver")
    print("   2. Visit: http://localhost:8000/api/health")
    print("   3. Login with: demo / demo123")
    print()
    
    print("📡 Test Endpoints:")
    print("   - Health: GET /api/health")
    print("   - Login: POST /api/auth/login")
    print("   - Workspaces: GET /api/workspaces")
    print()
    
    print("📚 Documentation:")
    print("   - README.md - Complete project guide")
    print("   - API_DOCUMENTATION.md - API reference")
    print()
    
    return True

if __name__ == '__main__':
    success = main()
    
    if success:
        print("✅ Quick start completed successfully!")
        print("\nRun: python manage.py runserver")
    else:
        print("❌ Quick start failed. Check errors above.")
    
    sys.exit(0 if success else 1)

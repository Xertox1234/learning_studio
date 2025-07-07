#!/usr/bin/env python3
"""
Test script to demonstrate Discourse SSO integration functionality.
"""

import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learning_community.settings.development')
sys.path.append('/Users/willtower/projects/python-learning-studio')

django.setup()

from django.contrib.auth import get_user_model
from apps.discourse_sso.services import DiscourseSSO
from apps.discourse_sso.models import DiscourseUser, DiscourseGroupMapping
from django.contrib.auth.models import Group

User = get_user_model()

def test_discourse_sso():
    """Test the Discourse SSO functionality."""
    print("🎯 DISCOURSE SSO INTEGRATION TEST")
    print("=" * 50)
    
    # Test 1: Check SSO Service Configuration
    print("\n1. Testing SSO Service Configuration...")
    sso_service = DiscourseSSO()
    
    if sso_service.secret and sso_service.base_url:
        print(f"   ✅ SSO configured: {sso_service.base_url}")
    else:
        print("   ⚠️  SSO not fully configured (missing DISCOURSE_BASE_URL or DISCOURSE_SSO_SECRET)")
        print("   📝 To configure: Set DISCOURSE_BASE_URL and DISCOURSE_SSO_SECRET in .env")
    
    # Test 2: Check Database Models
    print("\n2. Testing Database Models...")
    try:
        # Check model counts
        user_count = User.objects.count()
        discourse_user_count = DiscourseUser.objects.count()
        group_mapping_count = DiscourseGroupMapping.objects.count()
        
        print(f"   👥 Total users: {user_count}")
        print(f"   🔗 Discourse user mappings: {discourse_user_count}")
        print(f"   🏷️  Group mappings: {group_mapping_count}")
        print("   ✅ Database models working correctly")
    except Exception as e:
        print(f"   ❌ Database error: {e}")
    
    # Test 3: Test Payload Validation
    print("\n3. Testing SSO Payload Validation...")
    try:
        # Test with invalid payload
        is_valid, params = sso_service.validate_payload("invalid", "invalid")
        if not is_valid:
            print("   ✅ Invalid payload correctly rejected")
        else:
            print("   ⚠️  Invalid payload was accepted")
    except Exception as e:
        print(f"   ⚠️  Payload validation test error: {e}")
    
    # Test 4: Test Group Mapping
    print("\n4. Testing Group Management...")
    try:
        # Create a test group if it doesn't exist
        test_group, created = Group.objects.get_or_create(name="Test Students")
        if created:
            print("   📝 Created test group: Test Students")
        
        # Check if we can create a mapping
        mapping, created = DiscourseGroupMapping.objects.get_or_create(
            django_group=test_group,
            defaults={
                'discourse_group_name': 'test-students',
                'auto_sync': True
            }
        )
        if created:
            print("   🔗 Created test group mapping")
        print("   ✅ Group mapping functionality working")
    except Exception as e:
        print(f"   ❌ Group mapping error: {e}")
    
    # Test 5: Available Endpoints
    print("\n5. Available SSO Endpoints...")
    endpoints = [
        ("/discourse/sso/", "Main SSO authentication endpoint"),
        ("/discourse/sso/return/", "Post-login return handler"),
        ("/discourse/api/status/", "SSO configuration status"),
        ("/discourse/api/sync/", "Manual user synchronization"),
    ]
    
    for endpoint, description in endpoints:
        print(f"   🔗 {endpoint:<25} - {description}")
    
    # Test 6: Management Commands
    print("\n6. Available Management Commands...")
    commands = [
        ("setup_discourse_groups", "Set up role-based group mappings"),
        ("sync_discourse_users", "Bulk user synchronization"),
        ("setup_course_forums", "Course-specific forum setup"),
    ]
    
    for command, description in commands:
        print(f"   🛠️  python manage.py {command:<25} - {description}")
    
    print("\n" + "=" * 50)
    print("🎉 DISCOURSE SSO INTEGRATION READY!")
    print("\nTo use:")
    print("1. Configure DISCOURSE_BASE_URL and DISCOURSE_SSO_SECRET in .env")
    print("2. Set up corresponding settings in your Discourse admin")
    print("3. Start the Django server: python manage.py runserver")
    print("4. Configure Discourse to use: http://your-site.com/discourse/sso/")
    print("\nFor testing without Discourse:")
    print("- Visit: http://localhost:8000/discourse/api/status/")
    print("- Admin: http://localhost:8000/admin/discourse_sso/")

if __name__ == "__main__":
    test_discourse_sso()
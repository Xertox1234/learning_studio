#!/usr/bin/env python
"""
Setup script to create basic forum structure for testing
"""
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learning_community.settings.development_minimal')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from machina.apps.forum.models import Forum
from machina.apps.forum_permission.shortcuts import assign_perm

def create_forum_structure():
    """Create basic forum structure"""
    print("Creating forum structure...")
    
    # Create main category
    programming_category = Forum.objects.create(
        name="Programming Discussions",
        description="Discuss all things programming",
        type=Forum.FORUM_CAT,
    )
    print(f"Created category: {programming_category.name}")
    
    # Create Python forum
    python_forum = Forum.objects.create(
        name="Python Programming",
        description="Python programming discussions, tips, and help",
        type=Forum.FORUM_POST,
        parent=programming_category,
    )
    print(f"Created forum: {python_forum.name}")
    
    # Create Web Development forum
    web_forum = Forum.objects.create(
        name="Web Development",
        description="HTML, CSS, JavaScript, and web frameworks",
        type=Forum.FORUM_POST,
        parent=programming_category,
    )
    print(f"Created forum: {web_forum.name}")
    
    # Create Data Science forum
    data_forum = Forum.objects.create(
        name="Data Science",
        description="Data analysis, machine learning, and AI discussions",
        type=Forum.FORUM_POST,
        parent=programming_category,
    )
    print(f"Created forum: {data_forum.name}")
    
    # Create General category
    general_category = Forum.objects.create(
        name="General",
        description="General discussions and community",
        type=Forum.FORUM_CAT,
    )
    print(f"Created category: {general_category.name}")
    
    # Create General Discussion forum
    general_forum = Forum.objects.create(
        name="General Discussion",
        description="Off-topic discussions and community chat",
        type=Forum.FORUM_POST,
        parent=general_category,
    )
    print(f"Created forum: {general_forum.name}")
    
    # Create Announcements forum
    announcements_forum = Forum.objects.create(
        name="Announcements",
        description="Important announcements from the team",
        type=Forum.FORUM_POST,
        parent=general_category,
    )
    print(f"Created forum: {announcements_forum.name}")
    
    print(f"\nForum structure created successfully!")
    print(f"Total forums: {Forum.objects.count()}")
    
    # List all forums
    print("\nForum structure:")
    for forum in Forum.objects.all():
        if forum.type == Forum.FORUM_CAT:
            print(f"📁 {forum.name}")
        else:
            print(f"  💬 {forum.name}")

if __name__ == "__main__":
    try:
        create_forum_structure()
    except Exception as e:
        print(f"Error creating forum structure: {e}")
        import traceback
        traceback.print_exc()
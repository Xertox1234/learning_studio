#!/usr/bin/env python
"""
Check if new forum API imports work correctly.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learning_community.settings.development')
django.setup()

# Now import our new modules
try:
    from apps.api.forum.viewsets import ForumViewSet, TopicViewSet, PostViewSet, ModerationQueueViewSet
    print("✓ ViewSets imported successfully")

    from apps.api.forum.serializers import (
        ForumSerializer,
        TopicSerializer,
        PostSerializer,
        UserSerializer
    )
    print("✓ Serializers imported successfully")

    from apps.api.forum.filters import ForumFilter, TopicFilter, PostFilter
    print("✓ Filters imported successfully")

    from apps.api.forum.pagination import (
        ForumStandardPagination,
        TopicPagination,
        PostPagination
    )
    print("✓ Pagination classes imported successfully")

    from apps.api.forum.permissions import (
        IsModeratorOrReadOnly,
        IsOwnerOrModerator,
        CanModerate
    )
    print("✓ Permission classes imported successfully")

    print("\n✅ All forum API modules imported successfully!")
    print("\nNew API endpoints available at:")
    print("  - GET  /api/v2/forum/forums/")
    print("  - GET  /api/v2/forum/forums/{slug}/")
    print("  - GET  /api/v2/forum/topics/")
    print("  - POST /api/v2/forum/topics/")
    print("  - GET  /api/v2/forum/posts/")
    print("  - POST /api/v2/forum/posts/")
    print("  - GET  /api/v2/forum/moderation/")

except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

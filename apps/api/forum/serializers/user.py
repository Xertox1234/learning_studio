"""
User serializers for forum API responses.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class TrustLevelSerializer(serializers.Serializer):
    """Serializer for user trust level information."""
    level = serializers.IntegerField()
    name = serializers.CharField(source='level_name')
    can_moderate = serializers.BooleanField(source='can_moderate_basic')

    class Meta:
        fields = ['level', 'name', 'can_moderate']


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for nested relationships."""
    trust_level = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'avatar', 'trust_level', 'is_staff']
        read_only_fields = fields

    def get_trust_level(self, obj):
        """Get user's trust level information."""
        if hasattr(obj, 'trust_level'):
            return TrustLevelSerializer(obj.trust_level).data
        return {'level': 0, 'name': 'New User', 'can_moderate': False}

    def get_avatar(self, obj):
        """Get user avatar URL."""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None


class UserProfileSerializer(serializers.ModelSerializer):
    """Detailed user profile serializer for profile pages."""
    trust_level = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    forum_stats = serializers.SerializerMethodField()
    badges = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'avatar',
            'date_joined',
            'last_login',
            'is_staff',
            'is_superuser',
            'trust_level',
            'forum_stats',
            'badges',
        ]
        read_only_fields = fields

    def get_trust_level(self, obj):
        """Get detailed trust level information."""
        if hasattr(obj, 'trust_level'):
            tl = obj.trust_level
            return {
                'level': tl.level,
                'name': tl.level_name,
                'posts_read': tl.posts_read,
                'topics_viewed': tl.topics_viewed,
                'posts_created': tl.posts_created,
                'topics_created': tl.topics_created,
                'likes_given': tl.likes_given,
                'likes_received': tl.likes_received,
                'days_visited': tl.days_visited,
                'promoted_at': tl.promoted_at,
                'can_moderate': tl.can_moderate_basic,
            }
        return None

    def get_avatar(self, obj):
        """Get user avatar URL."""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None

    def get_forum_stats(self, obj):
        """Get user's forum activity statistics."""
        from machina.apps.forum_conversation.models import Topic, Post

        return {
            'topics_count': Topic.objects.filter(poster=obj, approved=True).count(),
            'posts_count': Post.objects.filter(poster=obj, approved=True).count(),
            'last_post': self._get_last_post(obj),
        }

    def get_badges(self, obj):
        """Get user's badges."""
        from apps.forum_integration.models import UserBadge

        user_badges = UserBadge.objects.filter(
            user=obj
        ).select_related('badge', 'badge__category')

        return [{
            'id': ub.badge.id,
            'name': ub.badge.name,
            'description': ub.badge.description,
            'icon': ub.badge.icon,
            'category': ub.badge.category.name if ub.badge.category else None,
            'earned_at': ub.earned_at,
        } for ub in user_badges]

    def _get_last_post(self, user):
        """Get user's most recent post."""
        from machina.apps.forum_conversation.models import Post

        last_post = Post.objects.filter(
            poster=user,
            approved=True
        ).select_related('topic', 'topic__forum').order_by('-created').first()

        if last_post:
            return {
                'id': last_post.id,
                'content_preview': last_post.content.raw[:100] if hasattr(last_post.content, 'raw') else str(last_post.content)[:100],
                'created': last_post.created,
                'topic_id': last_post.topic.id,
                'topic_subject': last_post.topic.subject,
                'forum_id': last_post.topic.forum.id,
                'forum_name': last_post.topic.forum.name,
            }
        return None

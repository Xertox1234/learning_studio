"""
Forum serializers for forum list and detail views.
"""
from rest_framework import serializers
from django.db import models
from machina.apps.forum.models import Forum
from machina.apps.forum_conversation.models import Topic
from .user import UserSerializer


class ForumSerializer(serializers.ModelSerializer):
    """Basic forum serializer."""

    class Meta:
        model = Forum
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'type',
            'image',
            'link',
            'link_redirects',
        ]
        read_only_fields = fields


class ForumListSerializer(serializers.ModelSerializer):
    """Serializer for forum list with statistics and last post info."""
    last_post = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()
    icon = serializers.SerializerMethodField()
    color = serializers.SerializerMethodField()
    topics_count = serializers.IntegerField(source='direct_topics_count', read_only=True)
    posts_count = serializers.IntegerField(source='direct_posts_count', read_only=True)

    class Meta:
        model = Forum
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'icon',
            'topics_count',
            'posts_count',
            'last_post',
            'stats',
            'color',
        ]
        read_only_fields = fields

    def get_last_post(self, obj):
        """Get last post information for the forum."""
        # Get latest topic with last post
        latest_topic = Topic.objects.filter(
            forum=obj,
            approved=True
        ).select_related(
            'poster',
            'last_post',
            'last_post__poster',
            'last_post__poster__trust_level'
        ).order_by('-last_post_on').first()

        if latest_topic and latest_topic.last_post:
            return {
                'id': latest_topic.last_post.id,
                'title': latest_topic.subject,
                'author': UserSerializer(latest_topic.last_post.poster).data,
                'created_at': latest_topic.last_post_on.isoformat() if latest_topic.last_post_on else None,
            }
        return None

    def get_stats(self, obj):
        """Get forum statistics."""
        from apps.api.services.container import container

        stats_service = container.get_statistics_service()
        forum_stats = stats_service.get_forum_specific_stats(obj.id)

        return {
            'online_users': forum_stats['online_users'],
            'weekly_posts': forum_stats['weekly_posts'],
            'trending': forum_stats['trending'],
        }

    def get_icon(self, obj):
        """Get forum icon (default emoji for now)."""
        # TODO: Allow custom icons per forum
        return '💬'

    def get_color(self, obj):
        """Get forum color theme."""
        # TODO: Allow custom colors per forum
        return 'bg-blue-500'


class ForumDetailSerializer(serializers.ModelSerializer):
    """Detailed forum serializer with topics."""
    parent = ForumSerializer(read_only=True)
    children = serializers.SerializerMethodField()
    moderators = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()
    topics_count = serializers.IntegerField(source='direct_topics_count', read_only=True)
    posts_count = serializers.IntegerField(source='direct_posts_count', read_only=True)

    class Meta:
        model = Forum
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'type',
            'parent',
            'children',
            'topics_count',
            'posts_count',
            'moderators',
            'stats',
            'image',
            'link',
            'link_redirects',
        ]
        read_only_fields = fields

    def get_children(self, obj):
        """Get child forums."""
        children = obj.get_children().filter(type=Forum.FORUM_POST)
        return ForumListSerializer(children, many=True).data

    def get_moderators(self, obj):
        """Get forum moderators."""
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group

        User = get_user_model()

        # Get users who are staff or have TL4 (Leader) status
        moderators = User.objects.filter(
            models.Q(is_staff=True) |
            models.Q(trust_level__level__gte=4)
        ).select_related('trust_level').distinct()[:10]

        return UserSerializer(moderators, many=True).data

    def get_stats(self, obj):
        """Get detailed forum statistics."""
        from apps.api.services.container import container

        stats_service = container.get_statistics_service()
        forum_stats = stats_service.get_forum_specific_stats(obj.id)

        return {
            'topics_count': obj.direct_topics_count,
            'posts_count': obj.direct_posts_count,
            'online_users': forum_stats['online_users'],
            'weekly_posts': forum_stats['weekly_posts'],
            'trending': forum_stats['trending'],
        }

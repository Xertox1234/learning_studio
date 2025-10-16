"""
Topic serializers for topic list, detail, and create operations.
"""
from rest_framework import serializers
from machina.apps.forum_conversation.models import Topic, Post
from .user import UserSerializer
from .forum import ForumSerializer


class TopicSerializer(serializers.ModelSerializer):
    """Basic topic serializer."""
    poster = UserSerializer(read_only=True)
    forum = ForumSerializer(read_only=True)
    is_locked = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = [
            'id',
            'subject',
            'slug',
            'forum',
            'poster',
            'approved',
            'is_locked',
            'type',
            'status',
            'created',
            'updated',
        ]
        read_only_fields = fields

    def get_is_locked(self, obj):
        """Check if topic is locked."""
        return obj.status == Topic.TOPIC_LOCKED


class TopicListSerializer(serializers.ModelSerializer):
    """Serializer for topic lists with statistics."""
    poster = UserSerializer(read_only=True)
    last_post_info = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()
    is_pinned = serializers.SerializerMethodField()
    is_locked = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = [
            'id',
            'subject',
            'slug',
            'poster',
            'created',
            'updated',
            'last_post_on',
            'views_count',
            'posts_count',
            'is_pinned',
            'is_locked',
            'approved',
            'type',
            'last_post_info',
            'stats',
        ]
        read_only_fields = fields

    def get_last_post_info(self, obj):
        """Get information about the last post in this topic."""
        if obj.last_post:
            return {
                'id': obj.last_post.id,
                'poster': UserSerializer(obj.last_post.poster).data,
                'created': obj.last_post.created,
            }
        return None

    def get_stats(self, obj):
        """Get topic statistics."""
        return {
            'views': obj.views_count,
            'posts': obj.posts_count,
            'participants': self._get_participants_count(obj),
        }

    def get_is_pinned(self, obj):
        """Check if topic is pinned."""
        return obj.type in [Topic.TOPIC_STICKY, Topic.TOPIC_ANNOUNCE]

    def get_is_locked(self, obj):
        """Check if topic is locked."""
        return obj.status == Topic.TOPIC_LOCKED

    def _get_participants_count(self, topic):
        """Count unique participants in the topic."""
        return Post.objects.filter(
            topic=topic,
            approved=True
        ).values('poster').distinct().count()


class TopicDetailSerializer(serializers.ModelSerializer):
    """Detailed topic serializer with all fields and relationships."""
    poster = UserSerializer(read_only=True)
    forum = ForumSerializer(read_only=True)
    subscribers = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    is_locked = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = [
            'id',
            'subject',
            'slug',
            'forum',
            'poster',
            'approved',
            'is_locked',
            'type',
            'status',
            'created',
            'updated',
            'last_post_on',
            'views_count',
            'posts_count',
            'subscribers',
            'is_subscribed',
            'permissions',
        ]
        read_only_fields = fields

    def get_subscribers(self, obj):
        """Get count of users subscribed to this topic."""
        return obj.subscribers.count()

    def get_is_subscribed(self, obj):
        """Check if current user is subscribed to this topic."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.subscribers.filter(id=request.user.id).exists()
        return False

    def get_is_locked(self, obj):
        """Check if topic is locked."""
        return obj.status == Topic.TOPIC_LOCKED

    def get_permissions(self, obj):
        """Get user's permissions for this topic."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return {
                'can_reply': False,
                'can_edit': False,
                'can_delete': False,
                'can_lock': False,
                'can_pin': False,
                'can_move': False,
            }

        user = request.user
        is_moderator = user.is_staff or user.is_superuser or (
            hasattr(user, 'trust_level') and user.trust_level.level >= 3
        )
        is_author = obj.poster == user

        return {
            'can_reply': obj.status != Topic.TOPIC_LOCKED or is_moderator,
            'can_edit': is_author or is_moderator,
            'can_delete': is_author or is_moderator,
            'can_lock': is_moderator,
            'can_pin': is_moderator,
            'can_move': is_moderator,
        }


class TopicCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new topics."""
    forum_id = serializers.IntegerField(write_only=True)
    first_post_content = serializers.CharField(write_only=True)

    class Meta:
        model = Topic
        fields = [
            'subject',
            'forum_id',
            'first_post_content',
            'type',
        ]

    def validate_forum_id(self, value):
        """Validate that the forum exists and user can post to it."""
        from machina.apps.forum.models import Forum

        try:
            forum = Forum.objects.get(id=value, type=Forum.FORUM_POST)
        except Forum.DoesNotExist:
            raise serializers.ValidationError("Forum not found or is not a post forum.")

        # TODO: Check forum permissions
        return value

    def validate_subject(self, value):
        """Validate topic subject."""
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Subject must be at least 3 characters long.")
        if len(value) > 255:
            raise serializers.ValidationError("Subject cannot exceed 255 characters.")
        return value.strip()

    def validate_first_post_content(self, value):
        """Validate first post content."""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Post content must be at least 10 characters long.")
        return value.strip()

    def create(self, validated_data):
        """Create topic with first post."""
        from machina.apps.forum.models import Forum

        forum_id = validated_data.pop('forum_id')
        first_post_content = validated_data.pop('first_post_content')
        forum = Forum.objects.get(id=forum_id)

        # Set poster from request user
        request = self.context.get('request')
        validated_data['poster'] = request.user
        validated_data['forum'] = forum

        # Create topic
        topic = Topic.objects.create(**validated_data)

        # Create first post
        Post.objects.create(
            topic=topic,
            poster=request.user,
            content=first_post_content,
            approved=True,  # TODO: Add moderation logic
        )

        # Update forum trackers
        forum.update_trackers()
        forum.save()

        return topic

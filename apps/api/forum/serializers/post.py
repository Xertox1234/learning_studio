"""
Post serializers for post list, detail, and create operations.
"""
from rest_framework import serializers
from machina.apps.forum_conversation.models import Post
from .user import UserSerializer


class PostSerializer(serializers.ModelSerializer):
    """Basic post serializer."""
    poster = UserSerializer(read_only=True)

    class Meta:
        model = Post
        fields = [
            'id',
            'poster',
            'content',
            'created',
            'updated',
            'approved',
        ]
        read_only_fields = fields


class PostListSerializer(serializers.ModelSerializer):
    """Serializer for post lists with user info."""
    poster = UserSerializer(read_only=True)
    is_topic_head = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id',
            'poster',
            'content',
            'created',
            'updated',
            'approved',
            'position',
            'is_topic_head',
            'permissions',
        ]
        read_only_fields = ['id', 'created', 'updated', 'approved', 'position', 'is_topic_head']

    def get_is_topic_head(self, obj):
        """Check if this is the first post in the topic."""
        return obj.position == 1

    def get_permissions(self, obj):
        """Get user's permissions for this post."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return {
                'can_edit': False,
                'can_delete': False,
                'can_quote': False,
            }

        user = request.user
        is_moderator = user.is_staff or user.is_superuser or (
            hasattr(user, 'trust_level') and user.trust_level.level >= 3
        )
        is_author = obj.poster == user

        return {
            'can_edit': is_author or is_moderator,
            'can_delete': is_author or is_moderator,
            'can_quote': True,
        }


class PostDetailSerializer(serializers.ModelSerializer):
    """Detailed post serializer with all information."""
    poster = UserSerializer(read_only=True)
    topic_info = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    edit_history = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id',
            'poster',
            'content',
            'created',
            'updated',
            'approved',
            'position',
            'topic_info',
            'permissions',
            'edit_history',
        ]
        read_only_fields = fields

    def get_topic_info(self, obj):
        """Get topic information for this post."""
        return {
            'id': obj.topic.id,
            'subject': obj.topic.subject,
            'slug': obj.topic.slug,
            'forum_id': obj.topic.forum.id,
            'forum_name': obj.topic.forum.name,
        }

    def get_permissions(self, obj):
        """Get user's permissions for this post."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return {
                'can_edit': False,
                'can_delete': False,
                'can_quote': False,
            }

        user = request.user
        is_moderator = user.is_staff or user.is_superuser or (
            hasattr(user, 'trust_level') and user.trust_level.level >= 3
        )
        is_author = obj.poster == user

        return {
            'can_edit': is_author or is_moderator,
            'can_delete': is_author or is_moderator,
            'can_quote': True,
        }

    def get_edit_history(self, obj):
        """Get edit history for this post (if implemented)."""
        # TODO: Implement edit history tracking
        return []


class PostCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new posts."""
    topic_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Post
        fields = [
            'topic_id',
            'content',
        ]

    def validate_topic_id(self, value):
        """Validate that the topic exists and is not locked."""
        from machina.apps.forum_conversation.models import Topic

        try:
            topic = Topic.objects.get(id=value, approved=True)
        except Topic.DoesNotExist:
            raise serializers.ValidationError("Topic not found or not approved.")

        if topic.locked:
            # Check if user is moderator
            request = self.context.get('request')
            if request and request.user:
                is_moderator = request.user.is_staff or request.user.is_superuser or (
                    hasattr(request.user, 'trust_level') and request.user.trust_level.level >= 3
                )
                if not is_moderator:
                    raise serializers.ValidationError("This topic is locked.")
            else:
                raise serializers.ValidationError("This topic is locked.")

        return value

    def validate_content(self, value):
        """Validate post content."""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Post content must be at least 10 characters long.")
        return value.strip()

    def create(self, validated_data):
        """Create new post."""
        from machina.apps.forum_conversation.models import Topic

        topic_id = validated_data.pop('topic_id')
        topic = Topic.objects.get(id=topic_id)

        # Set poster from request user
        request = self.context.get('request')
        validated_data['poster'] = request.user
        validated_data['topic'] = topic

        # Check if user needs moderation (TL0 users)
        needs_approval = True
        if hasattr(request.user, 'trust_level'):
            # Auto-approve for TL1+ users
            needs_approval = request.user.trust_level.level < 1

        validated_data['approved'] = not needs_approval

        # Create post
        post = Post.objects.create(**validated_data)

        # Update topic and forum trackers
        topic.update_trackers()
        topic.save(update_fields=['last_post', 'last_post_on'])

        if topic.forum:
            topic.forum.update_trackers()
            topic.forum.save()

        # Add to review queue if needs approval
        if needs_approval:
            from apps.api.services.container import container
            review_service = container.get_review_queue_service()
            review_service.check_new_post(post)

        return post


class PostUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating posts."""

    class Meta:
        model = Post
        fields = ['content']

    def validate_content(self, value):
        """Validate post content."""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Post content must be at least 10 characters long.")
        return value.strip()

    def update(self, instance, validated_data):
        """Update post content."""
        instance.content = validated_data.get('content', instance.content)
        instance.save()

        # TODO: Track edit history
        return instance

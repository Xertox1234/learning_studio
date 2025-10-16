"""
Filters for forum API endpoints.
"""
from django_filters import rest_framework as filters
from machina.apps.forum.models import Forum
from machina.apps.forum_conversation.models import Topic, Post


class ForumFilter(filters.FilterSet):
    """Filter for Forum queryset."""
    name = filters.CharFilter(lookup_expr='icontains')
    type = filters.ChoiceFilter(choices=[
        (Forum.FORUM_CAT, 'Category'),
        (Forum.FORUM_POST, 'Forum'),
        (Forum.FORUM_LINK, 'Link'),
    ])

    class Meta:
        model = Forum
        fields = ['name', 'type']


class TopicFilter(filters.FilterSet):
    """Filter for Topic queryset."""
    subject = filters.CharFilter(lookup_expr='icontains')
    forum = filters.NumberFilter(field_name='forum__id')
    poster = filters.NumberFilter(field_name='poster__id')
    locked = filters.BooleanFilter()
    approved = filters.BooleanFilter()
    type = filters.ChoiceFilter(choices=[
        (Topic.TOPIC_POST, 'Regular'),
        (Topic.TOPIC_STICKY, 'Sticky'),
        (Topic.TOPIC_ANNOUNCE, 'Announcement'),
        (Topic.TOPIC_MOVED, 'Moved'),
    ])
    created_after = filters.DateTimeFilter(field_name='created', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created', lookup_expr='lte')

    class Meta:
        model = Topic
        fields = ['subject', 'forum', 'poster', 'locked', 'approved', 'type']


class PostFilter(filters.FilterSet):
    """Filter for Post queryset."""
    topic = filters.NumberFilter(field_name='topic__id')
    poster = filters.NumberFilter(field_name='poster__id')
    approved = filters.BooleanFilter()
    created_after = filters.DateTimeFilter(field_name='created', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created', lookup_expr='lte')

    class Meta:
        model = Post
        fields = ['topic', 'poster', 'approved']

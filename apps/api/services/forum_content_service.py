"""
Service for handling forum-Wagtail content integration.
Provides unified content creation that publishes to both systems.
"""

import logging
from typing import Dict, Any, Optional, List
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from rest_framework import status

from apps.api.content_serializers.streamfield import serialize_streamfield

logger = logging.getLogger(__name__)
User = get_user_model()


class ForumContentService:
    """Service for handling forum and Wagtail content integration."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_integrated_content(self, user: User, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create content that publishes to both Wagtail and forum systems.
        
        Args:
            user: User creating the content
            content_data: Dictionary containing content information
                - title: Content title
                - intro: Brief introduction
                - body: StreamField content blocks
                - forum_enabled: Whether to create forum discussion
                - forum_id: Target forum ID (optional)
                - trust_level_required: Minimum trust level for participation
                - content_type: 'blog_post' or 'forum_topic'
        
        Returns:
            Dictionary containing created content information
        """
        try:
            with transaction.atomic():
                content_type = content_data.get('content_type', 'blog_post')
                
                if content_type == 'blog_post':
                    return self._create_blog_with_forum(user, content_data)
                elif content_type == 'forum_topic':
                    return self._create_rich_forum_topic(user, content_data)
                else:
                    raise ValueError(f"Unsupported content type: {content_type}")
                    
        except Exception as e:
            self.logger.error(f"Failed to create integrated content: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_blog_with_forum(self, user: User, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a ForumIntegratedBlogPage with automatic forum topic creation."""
        try:
            from apps.blog.models import ForumIntegratedBlogPage, BlogIndexPage
            from machina.apps.forum.models import Forum
            
            # Get parent blog index page
            blog_index = BlogIndexPage.objects.live().first()
            if not blog_index:
                raise ValueError("No blog index page found")
            
            # Get target forum if specified
            discussion_forum = None
            if content_data.get('forum_id'):
                try:
                    discussion_forum = Forum.objects.get(id=content_data['forum_id'])
                except Forum.DoesNotExist:
                    pass
            
            # Create the blog page
            blog_page = ForumIntegratedBlogPage(
                title=content_data['title'],
                slug=self._generate_slug(content_data['title']),
                intro=content_data.get('intro', ''),
                author=user,
                date=timezone.now().date(),
                
                # Forum integration settings
                create_forum_topic=content_data.get('forum_enabled', True),
                discussion_forum=discussion_forum,
                forum_topic_title=content_data.get('forum_topic_title', ''),
                forum_discussion_intro=content_data.get('forum_discussion_intro', ''),
                enable_rich_forum_content=content_data.get('enable_rich_content', True),
                min_trust_level_to_post=content_data.get('trust_level_required', 0),
                
                # Content
                ai_generated=content_data.get('ai_generated', False),
                ai_summary=content_data.get('ai_summary', ''),
            )
            
            # Set body content from StreamField blocks
            if content_data.get('body'):
                blog_page.body = self._process_streamfield_blocks(content_data['body'])
            
            # Add to blog index and save
            blog_index.add_child(instance=blog_page)
            blog_page.save_revision().publish()
            
            # Get forum topic info if created
            forum_topic = blog_page.get_forum_topic()
            forum_url = blog_page.get_forum_url()
            
            return {
                'success': True,
                'content_type': 'blog_post',
                'blog_post': {
                    'id': blog_page.id,
                    'title': blog_page.title,
                    'slug': blog_page.slug,
                    'url': blog_page.url,
                    'intro': blog_page.intro,
                    'author': {
                        'id': user.id,
                        'username': user.username,
                        'display_name': user.get_full_name() or user.username
                    },
                    'created_at': blog_page.first_published_at.isoformat() if blog_page.first_published_at else None
                },
                'forum_topic': {
                    'id': forum_topic.id if forum_topic else None,
                    'url': forum_url,
                    'title': forum_topic.subject if forum_topic else None,
                    'forum_id': forum_topic.forum.id if forum_topic else None,
                    'forum_name': forum_topic.forum.name if forum_topic else None
                } if forum_topic else None
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create blog with forum integration: {e}")
            raise
    
    def _create_rich_forum_topic(self, user: User, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a forum topic with rich content support."""
        try:
            from machina.apps.forum.models import Forum
            from machina.apps.forum_conversation.models import Topic, Post
            
            # Get target forum
            forum_id = content_data.get('forum_id')
            if not forum_id:
                raise ValueError("Forum ID is required for forum topics")
            
            try:
                forum = Forum.objects.get(id=forum_id)
            except Forum.DoesNotExist:
                raise ValueError("Forum not found")
            
            if forum.type != Forum.FORUM_POST:
                raise ValueError("Cannot create topics in this forum type")
            
            # Create topic
            topic = Topic.objects.create(
                forum=forum,
                subject=content_data['title'],
                poster=user,
                type=Topic.TOPIC_POST,
                status=Topic.TOPIC_UNLOCKED,
                approved=True,
                created=timezone.now(),
                updated=timezone.now()
            )
            
            # Generate rich content for forum post
            forum_content = self._generate_rich_forum_content(content_data)
            
            # Create first post
            post = Post.objects.create(
                topic=topic,
                poster=user,
                subject=content_data['title'],
                content=forum_content,
                approved=True,
                enable_signature=content_data.get('enable_signature', False),
                created=timezone.now(),
                updated=timezone.now()
            )
            
            # Update topic references
            topic.first_post = post
            topic.last_post = post
            topic.last_post_on = post.created
            topic.posts_count = 1
            topic.save()
            
            return {
                'success': True,
                'content_type': 'forum_topic',
                'forum_topic': {
                    'id': topic.id,
                    'title': topic.subject,
                    'slug': topic.slug,
                    'forum': {
                        'id': forum.id,
                        'name': forum.name,
                        'slug': forum.slug
                    },
                    'author': {
                        'id': user.id,
                        'username': user.username,
                        'display_name': user.get_full_name() or user.username
                    },
                    'created_at': topic.created.isoformat(),
                    'posts_count': topic.posts_count,
                    'views_count': getattr(topic, 'views_count', 0)
                },
                'first_post': {
                    'id': post.id,
                    'content': str(post.content)[:200] + '...' if len(str(post.content)) > 200 else str(post.content),
                    'created_at': post.created.isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create rich forum topic: {e}")
            raise
    
    def _generate_rich_forum_content(self, content_data: Dict[str, Any]) -> str:
        """Generate rich forum content from structured data."""
        content = f"**{content_data['title']}**\n\n"
        
        if content_data.get('intro'):
            content += f"*{content_data['intro']}*\n\n"
        
        # Process body blocks if present
        if content_data.get('body'):
            content += self._streamfield_blocks_to_markdown(content_data['body'])
        
        # Add discussion prompt
        content += "\n\n---\n\n"
        content += "**What are your thoughts on this topic?**\n"
        content += "Share your experience, ask questions, or provide additional insights!\n\n"
        
        trust_level = content_data.get('trust_level_required', 0)
        if trust_level > 0:
            content += f"*Minimum trust level to participate: TL{trust_level}*"
        
        return content
    
    def _streamfield_blocks_to_markdown(self, blocks: List[Dict[str, Any]]) -> str:
        """Convert StreamField blocks to markdown for forum content."""
        markdown_content = ""
        
        for block in blocks:
            block_type = block.get('type', '')
            value = block.get('value', {})
            
            if block_type == 'paragraph':
                # Extract text from rich text block
                text = self._extract_text_from_richtext(value)
                markdown_content += f"{text}\n\n"
                
            elif block_type == 'heading':
                markdown_content += f"## {value}\n\n"
                
            elif block_type == 'code':
                language = value.get('language', 'python')
                code = value.get('code', '')
                caption = value.get('caption', '')
                
                markdown_content += f"```{language}\n{code}\n```\n"
                if caption:
                    markdown_content += f"*{caption}*\n"
                markdown_content += "\n"
                
            elif block_type == 'quote':
                text = value.get('text', '')
                source = value.get('attribute_name', '')
                markdown_content += f"> {text}\n"
                if source:
                    markdown_content += f"> \n> — {source}\n"
                markdown_content += "\n"
                
            elif block_type == 'callout':
                callout_type = value.get('type', 'info')
                title = value.get('title', '')
                text = self._extract_text_from_richtext(value.get('text', ''))
                
                emoji_map = {
                    'info': 'ℹ️',
                    'warning': '⚠️',
                    'tip': '💡',
                    'danger': '🚨'
                }
                
                emoji = emoji_map.get(callout_type, 'ℹ️')
                markdown_content += f"{emoji} **{title or callout_type.title()}**\n\n"
                markdown_content += f"{text}\n\n"
                
            elif block_type == 'image':
                # For images, we'll just note their presence
                markdown_content += "*[Image content - view full post for images]*\n\n"
        
        return markdown_content
    
    def _extract_text_from_richtext(self, richtext_data) -> str:
        """Extract plain text from Wagtail RichText data."""
        if isinstance(richtext_data, str):
            # Simple text
            return richtext_data
        
        # Handle RichText object - for now, convert to string
        # In a full implementation, you'd parse the HTML to extract clean text
        return str(richtext_data)
    
    def _process_streamfield_blocks(self, blocks_data: List[Dict[str, Any]]) -> List:
        """Process blocks data into Wagtail StreamField format."""
        # This is a simplified version - in production you'd want more robust validation
        processed_blocks = []
        
        for block_data in blocks_data:
            block_type = block_data.get('type')
            value = block_data.get('value')
            
            if block_type and value is not None:
                processed_blocks.append({
                    'type': block_type,
                    'value': value
                })
        
        return processed_blocks
    
    def _generate_slug(self, title: str) -> str:
        """Generate a URL-friendly slug from title."""
        import re
        from django.utils.text import slugify
        
        # Basic slug generation - Wagtail will handle uniqueness
        slug = slugify(title)
        return slug[:50]  # Limit length
    
    def get_forum_statistics(self, forum_id: Optional[int] = None) -> Dict[str, Any]:
        """Get forum statistics including integrated content."""
        try:
            from machina.apps.forum.models import Forum
            from machina.apps.forum_conversation.models import Topic, Post
            from apps.blog.models import ForumIntegratedBlogPage
            from apps.forum_integration.statistics_service import forum_stats_service
            
            # Get base forum statistics
            if forum_id:
                stats = forum_stats_service.get_forum_specific_stats(forum_id)
                
                # Add integrated blog posts count for this forum
                integrated_posts = ForumIntegratedBlogPage.objects.live().filter(
                    discussion_forum_id=forum_id,
                    forum_topic_id__isnull=False
                ).count()
                
                stats['integrated_blog_posts'] = integrated_posts
                
            else:
                stats = forum_stats_service.get_forum_statistics()
                
                # Add overall integrated content stats
                total_integrated = ForumIntegratedBlogPage.objects.live().filter(
                    forum_topic_id__isnull=False
                ).count()
                
                stats['total_integrated_posts'] = total_integrated
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get forum statistics: {e}")
            return {
                'error': str(e),
                'total_topics': 0,
                'total_posts': 0,
                'total_users': 0,
                'online_users': 0
            }
    
    def check_user_permissions(self, user: User, action: str, forum_id: Optional[int] = None) -> Dict[str, Any]:
        """Check user permissions for forum content creation."""
        try:
            from apps.forum_integration.models import TrustLevel
            
            # Get user's trust level
            try:
                trust_level = user.trust_level
                current_level = trust_level.level
            except TrustLevel.DoesNotExist:
                current_level = 0
            
            permissions = {
                'can_create_topics': True,  # Basic permission
                'can_create_blog_posts': current_level >= 1,  # TL1+ can create blog posts
                'can_use_rich_content': current_level >= 1,  # TL1+ can use rich content
                'can_create_integrated_content': current_level >= 2,  # TL2+ can create integrated content
                'can_moderate': current_level >= 3,  # TL3+ can moderate
                'trust_level': current_level,
                'trust_level_name': f"TL{current_level}"
            }
            
            # Check specific action permissions
            action_requirements = {
                'create_blog_post': permissions['can_create_blog_posts'],
                'create_forum_topic': permissions['can_create_topics'],
                'create_integrated_content': permissions['can_create_integrated_content'],
                'use_rich_content': permissions['can_use_rich_content']
            }
            
            can_perform_action = action_requirements.get(action, False)
            
            return {
                'allowed': can_perform_action,
                'permissions': permissions,
                'trust_level': current_level,
                'requirements': {
                    'create_blog_post': 1,
                    'create_integrated_content': 2,
                    'moderate_content': 3
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to check user permissions: {e}")
            return {
                'allowed': False,
                'error': str(e)
            }


# Global service instance
forum_content_service = ForumContentService()
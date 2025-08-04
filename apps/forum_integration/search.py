"""
Advanced search implementation for forum and learning content
"""
import re
from datetime import datetime, timedelta
from django.db.models import Q, F, Count, Case, When, Value, CharField
from django.db.models.functions import Coalesce
from django.contrib.auth import get_user_model
from django.utils import timezone
from machina.apps.forum_conversation.models import Topic, Post
from machina.apps.forum.models import Forum
from apps.learning.models import Course, Lesson, Exercise
from apps.forum_integration.models import TrustLevel

User = get_user_model()


class AdvancedSearchEngine:
    """
    Advanced search engine that works with database queries
    Supports complex query syntax and multiple content types
    """
    
    def __init__(self):
        self.content_types = {
            'posts': {'model': Post, 'fields': ['content', 'subject'], 'weight': 1.0},
            'topics': {'model': Topic, 'fields': ['subject'], 'weight': 1.2},
            'courses': {'model': Course, 'fields': ['title', 'description', 'short_description'], 'weight': 1.5},
            'lessons': {'model': Lesson, 'fields': ['title', 'content'], 'weight': 1.3},
            'exercises': {'model': Exercise, 'fields': ['title', 'description', 'instructions'], 'weight': 1.1},
        }
    
    def search(self, query, filters=None, content_types=None, limit=50, offset=0):
        """
        Perform advanced search across multiple content types
        
        Args:
            query (str): Search query with optional syntax
            filters (dict): Additional filters (author, date_range, etc.)
            content_types (list): Limit search to specific content types
            limit (int): Maximum results to return
            offset (int): Pagination offset
        
        Returns:
            dict: Search results with metadata
        """
        if not query or not query.strip():
            return {'results': [], 'total': 0, 'query_time': 0}
        
        start_time = timezone.now()
        filters = filters or {}
        content_types = content_types or list(self.content_types.keys())
        
        # Parse query syntax
        parsed_query = self._parse_query(query)
        
        # Get results for each content type
        all_results = []
        total_count = 0
        
        for content_type in content_types:
            if content_type in self.content_types:
                results, count = self._search_content_type(
                    content_type, parsed_query, filters, limit, offset
                )
                all_results.extend(results)
                total_count += count
        
        # Sort by relevance score
        all_results.sort(key=lambda x: x['score'], reverse=True)
        
        # Apply pagination
        paginated_results = all_results[offset:offset + limit]
        
        query_time = (timezone.now() - start_time).total_seconds()
        
        return {
            'results': paginated_results,
            'total': total_count,
            'query_time': query_time,
            'parsed_query': parsed_query,
        }
    
    def _parse_query(self, query):
        """
        Parse query syntax:
        - "exact phrase" for exact matches
        - +required -excluded terms
        - author:username
        - category:name
        - date:YYYY-MM-DD or date:>YYYY-MM-DD
        """
        parsed = {
            'terms': [],
            'required': [],
            'excluded': [],
            'exact_phrases': [],
            'author': None,
            'category': None,
            'date_after': None,
            'date_before': None,
        }
        
        # Extract exact phrases
        exact_phrase_pattern = r'"([^"]+)"'
        exact_phrases = re.findall(exact_phrase_pattern, query)
        parsed['exact_phrases'] = exact_phrases
        query = re.sub(exact_phrase_pattern, '', query)
        
        # Extract special filters
        filters = {
            'author': r'author:(\w+)',
            'category': r'category:(\w+)',
            'date': r'date:([><=]?)(\d{4}-\d{2}-\d{2})',
        }
        
        for filter_name, pattern in filters.items():
            matches = re.findall(pattern, query)
            if matches:
                if filter_name == 'author':
                    parsed['author'] = matches[0]
                elif filter_name == 'category':
                    parsed['category'] = matches[0]
                elif filter_name == 'date':
                    operator, date_str = matches[0]
                    try:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                        if operator == '>' or operator == '':
                            parsed['date_after'] = date_obj
                        elif operator == '<':
                            parsed['date_before'] = date_obj
                    except ValueError:
                        pass
                
                # Remove from query
                query = re.sub(pattern, '', query)
        
        # Parse remaining terms
        terms = query.split()
        for term in terms:
            term = term.strip()
            if not term:
                continue
            elif term.startswith('+'):
                parsed['required'].append(term[1:])
            elif term.startswith('-'):
                parsed['excluded'].append(term[1:])
            else:
                parsed['terms'].append(term)
        
        return parsed
    
    def _search_content_type(self, content_type, parsed_query, filters, limit, offset):
        """Search within a specific content type"""
        config = self.content_types[content_type]
        model = config['model']
        fields = config['fields']
        weight = config['weight']
        
        # Build Q object for search
        search_q = Q()
        
        # Add term searches
        for term in parsed_query['terms'] + parsed_query['required']:
            term_q = Q()
            for field in fields:
                term_q |= Q(**{f'{field}__icontains': term})
            search_q &= term_q
        
        # Add exact phrase searches
        for phrase in parsed_query['exact_phrases']:
            phrase_q = Q()
            for field in fields:
                phrase_q |= Q(**{f'{field}__icontains': phrase})
            search_q &= phrase_q
        
        # Exclude terms
        for term in parsed_query['excluded']:
            exclude_q = Q()
            for field in fields:
                exclude_q |= Q(**{f'{field}__icontains': term})
            search_q &= ~exclude_q
        
        # Start with base queryset
        queryset = model.objects.filter(search_q)
        
        # Apply content-type specific filters
        queryset = self._apply_content_filters(
            queryset, content_type, parsed_query, filters
        )
        
        # Count total results
        total_count = queryset.count()
        
        # Apply ordering and pagination
        queryset = self._apply_ordering(queryset, content_type, parsed_query)
        results_queryset = queryset[offset:offset + limit]
        
        # Convert to standardized result format
        results = []
        for obj in results_queryset:
            result = self._format_result(obj, content_type, parsed_query, weight)
            results.append(result)
        
        return results, total_count
    
    def _apply_content_filters(self, queryset, content_type, parsed_query, filters):
        """Apply content-type specific filters"""
        
        # Author filter
        if parsed_query['author'] or filters.get('author'):
            author = parsed_query['author'] or filters['author']
            if content_type in ['posts', 'topics']:
                queryset = queryset.filter(poster__username__icontains=author)
            elif content_type in ['courses', 'lessons', 'exercises']:
                queryset = queryset.filter(instructor__username__icontains=author)
        
        # Date filters
        date_field = 'created' if content_type in ['posts', 'topics'] else 'created_at'
        
        if parsed_query['date_after'] or filters.get('date_after'):
            date_after = parsed_query['date_after'] or filters['date_after']
            queryset = queryset.filter(**{f'{date_field}__gte': date_after})
        
        if parsed_query['date_before'] or filters.get('date_before'):
            date_before = parsed_query['date_before'] or filters['date_before']
            queryset = queryset.filter(**{f'{date_field}__lte': date_before})
        
        # Trust level filter
        if filters.get('min_trust_level') is not None:
            min_level = filters['min_trust_level']
            if content_type in ['posts', 'topics']:
                queryset = queryset.filter(
                    poster__trust_level__level__gte=min_level
                )
        
        # Forum-specific filters
        if content_type in ['posts', 'topics']:
            if filters.get('forum'):
                queryset = queryset.filter(topic__forum__slug=filters['forum'])
            
            if filters.get('has_attachments'):
                # Add attachment filter when implemented
                pass
        
        # Course-specific filters
        if content_type == 'courses':
            if filters.get('difficulty'):
                queryset = queryset.filter(difficulty=filters['difficulty'])
            
            if filters.get('category'):
                queryset = queryset.filter(category=filters['category'])
        
        return queryset
    
    def _apply_ordering(self, queryset, content_type, parsed_query):
        """Apply sorting to results"""
        
        # Default ordering by creation date (newest first)
        date_field = 'created' if content_type in ['posts', 'topics'] else 'created_at'
        return queryset.order_by(f'-{date_field}')
    
    def _format_result(self, obj, content_type, parsed_query, weight):
        """Format a result object into standardized format"""
        
        # Calculate relevance score
        score = self._calculate_relevance_score(obj, content_type, parsed_query, weight)
        
        # Get content preview
        preview = self._get_content_preview(obj, content_type, parsed_query)
        
        # Format based on content type
        if content_type == 'posts':
            return {
                'type': 'post',
                'id': obj.id,
                'title': obj.subject or f"Re: {obj.topic.subject}",
                'content': preview,
                'url': obj.get_absolute_url(),
                'author': obj.poster.username if obj.poster else 'Anonymous',
                'author_trust_level': getattr(obj.poster, 'trust_level', None),
                'created': obj.created,
                'forum': obj.topic.forum.name,
                'topic': obj.topic.subject,
                'score': score,
            }
        
        elif content_type == 'topics':
            return {
                'type': 'topic',
                'id': obj.id,
                'title': obj.subject,
                'content': preview,
                'url': obj.get_absolute_url(),
                'author': obj.poster.username if obj.poster else 'Anonymous',
                'author_trust_level': getattr(obj.poster, 'trust_level', None),
                'created': obj.created,
                'forum': obj.forum.name,
                'posts_count': obj.posts_count,
                'score': score,
            }
        
        elif content_type == 'courses':
            return {
                'type': 'course',
                'id': obj.id,
                'title': obj.title,
                'content': preview,
                'url': obj.get_absolute_url(),
                'author': obj.instructor.username if obj.instructor else 'Anonymous',
                'created': obj.created_at,
                'difficulty': obj.difficulty,
                'category': obj.category,
                'lessons_count': obj.lessons.count(),
                'score': score,
            }
        
        elif content_type == 'lessons':
            return {
                'type': 'lesson',
                'id': obj.id,
                'title': obj.title,
                'content': preview,
                'url': obj.get_absolute_url(),
                'course': obj.course.title,
                'created': obj.created_at,
                'order': obj.order,
                'score': score,
            }
        
        elif content_type == 'exercises':
            return {
                'type': 'exercise',
                'id': obj.id,
                'title': obj.title,
                'content': preview,
                'url': obj.get_absolute_url(),
                'lesson': obj.lesson.title if obj.lesson else None,
                'course': obj.lesson.course.title if obj.lesson else None,
                'difficulty': obj.difficulty,
                'created': obj.created_at,
                'score': score,
            }
        
        return {}
    
    def _calculate_relevance_score(self, obj, content_type, parsed_query, weight):
        """Calculate relevance score for ranking"""
        score = 0.0
        
        # Base weight for content type
        score += weight
        
        # Count term matches in different fields
        config = self.content_types[content_type]
        fields = config['fields']
        
        all_terms = (
            parsed_query['terms'] + 
            parsed_query['required'] + 
            parsed_query['exact_phrases']
        )
        
        for term in all_terms:
            for field in fields:
                content = str(getattr(obj, field, '') or '').lower()
                term_lower = term.lower()
                
                # Exact matches get higher scores
                if term_lower in content:
                    # Title/subject matches get higher weight
                    if field in ['title', 'subject']:
                        score += 2.0
                    else:
                        score += 1.0
                    
                    # Multiple occurrences increase score
                    occurrences = content.count(term_lower)
                    score += occurrences * 0.5
        
        # Boost recent content
        if hasattr(obj, 'created'):
            date_field = obj.created
        elif hasattr(obj, 'created_at'):
            date_field = obj.created_at
        else:
            date_field = timezone.now()
        
        days_ago = (timezone.now().date() - date_field.date()).days
        if days_ago < 7:
            score += 1.0  # Recent content boost
        elif days_ago < 30:
            score += 0.5
        
        # Boost content from trusted users
        if content_type in ['posts', 'topics'] and hasattr(obj, 'poster'):
            try:
                trust_level = obj.poster.trust_level.level
                score += trust_level * 0.2
            except:
                pass
        
        return round(score, 2)
    
    def _get_content_preview(self, obj, content_type, parsed_query, max_length=200):
        """Generate content preview with search term highlighting"""
        config = self.content_types[content_type]
        
        # Get the main content field
        content = ''
        for field in config['fields']:
            field_content = str(getattr(obj, field, '') or '')
            if field_content and len(field_content) > len(content):
                content = field_content
        
        if not content:
            return ''
        
        # Simple preview generation
        if len(content) <= max_length:
            return content
        
        # Try to find content around search terms
        all_terms = (
            parsed_query['terms'] + 
            parsed_query['required'] + 
            parsed_query['exact_phrases']
        )
        
        for term in all_terms:
            term_pos = content.lower().find(term.lower())
            if term_pos >= 0:
                start = max(0, term_pos - max_length // 2)
                end = min(len(content), start + max_length)
                preview = content[start:end]
                
                if start > 0:
                    preview = '...' + preview
                if end < len(content):
                    preview = preview + '...'
                
                return preview
        
        # Fallback to beginning of content
        return content[:max_length] + ('...' if len(content) > max_length else '')


# Global search engine instance
search_engine = AdvancedSearchEngine()
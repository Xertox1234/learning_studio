"""
Pagination classes for forum API endpoints.
"""
from rest_framework.pagination import PageNumberPagination, CursorPagination
from rest_framework.response import Response


class ForumStandardPagination(PageNumberPagination):
    """
    Standard pagination for forum lists.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        """Return paginated response with metadata."""
        return Response({
            'results': data,
            'pagination': {
                'current_page': self.page.number,
                'page_size': self.page.paginator.per_page,
                'total_count': self.page.paginator.count,
                'total_pages': self.page.paginator.num_pages,
                'has_next': self.page.has_next(),
                'has_previous': self.page.has_previous(),
            }
        })


class TopicPagination(PageNumberPagination):
    """
    Pagination for topic lists.
    """
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        """Return paginated response with metadata."""
        return Response({
            'results': data,
            'pagination': {
                'current_page': self.page.number,
                'page_size': self.page.paginator.per_page,
                'total_count': self.page.paginator.count,
                'total_pages': self.page.paginator.num_pages,
                'has_next': self.page.has_next(),
                'has_previous': self.page.has_previous(),
            }
        })


class PostPagination(PageNumberPagination):
    """
    Pagination for post lists.
    Smaller page size for better performance with rich content.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50  # Limit to 50 posts per page

    def get_paginated_response(self, data):
        """Return paginated response with metadata."""
        return Response({
            'results': data,
            'pagination': {
                'current_page': self.page.number,
                'page_size': self.page.paginator.per_page,
                'total_count': self.page.paginator.count,
                'total_pages': self.page.paginator.num_pages,
                'has_next': self.page.has_next(),
                'has_previous': self.page.has_previous(),
            }
        })


class ModerationQueuePagination(PageNumberPagination):
    """
    Pagination for moderation queue.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        """Return paginated response with metadata."""
        return Response({
            'results': data,
            'pagination': {
                'current_page': self.page.number,
                'page_size': self.page.paginator.per_page,
                'total_count': self.page.paginator.count,
                'total_pages': self.page.paginator.num_pages,
                'has_next': self.page.has_next(),
                'has_previous': self.page.has_previous(),
            }
        })


class InfinitePagination(CursorPagination):
    """
    Cursor-based pagination for infinite scroll.
    More efficient for large datasets.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    ordering = '-created'  # Default ordering by created date
    cursor_query_param = 'cursor'

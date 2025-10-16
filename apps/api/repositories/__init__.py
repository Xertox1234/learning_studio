"""
Repository layer for data access abstraction.

This package implements the Repository pattern to:
- Decouple business logic from data access
- Enable unit testing with mock repositories
- Optimize database queries consistently
- Provide a clean API for data operations
"""

from .base import BaseRepository, OptimizedRepository
from .user_repository import UserRepository
from .forum_repository import ForumRepository
from .topic_repository import TopicRepository
from .post_repository import PostRepository
from .review_queue_repository import ReviewQueueRepository

__all__ = [
    'BaseRepository',
    'OptimizedRepository',
    'UserRepository',
    'ForumRepository',
    'TopicRepository',
    'PostRepository',
    'ReviewQueueRepository',
]

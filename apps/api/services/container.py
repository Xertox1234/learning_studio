"""
Dependency Injection Container for services and repositories.

This module implements a simple DI container that:
- Centralizes service and repository instantiation
- Manages dependencies between components
- Enables easy testing with mock objects
- Provides a consistent service access pattern

Usage:
    from apps.api.services.container import container

    # In views:
    stats_service = container.get_statistics_service()
    stats = stats_service.get_forum_statistics()

    # In tests:
    container.register('cache', lambda: MockCache())
    stats_service = container.get_statistics_service()  # Uses mock cache
"""

from typing import Callable, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ServiceContainer:
    """
    Dependency injection container following the Singleton pattern.

    Provides centralized access to services and their dependencies.
    """

    _instance: Optional['ServiceContainer'] = None
    _services: Dict[str, Any] = {}
    _factories: Dict[str, Callable] = {}

    def __new__(cls):
        """Ensure only one instance exists (Singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._services = {}
            cls._instance._factories = {}
        return cls._instance

    def register(self, name: str, factory: Callable, singleton: bool = True):
        """
        Register a service factory.

        Args:
            name: Service identifier
            factory: Callable that returns service instance
            singleton: If True, cache the instance after first creation

        Example:
            container.register('cache', lambda: get_cache('default'))
            container.register('user_repo', UserRepository, singleton=False)
        """
        self._factories[name] = (factory, singleton)

        # Clear cached instance if re-registering
        if name in self._services:
            del self._services[name]

        logger.debug(f"Registered service: {name} (singleton={singleton})")

    def get(self, name: str) -> Any:
        """
        Get service instance.

        Args:
            name: Service identifier

        Returns:
            Service instance

        Raises:
            ValueError: If service not registered
        """
        if name not in self._factories:
            raise ValueError(
                f"Service '{name}' not registered. "
                f"Available services: {list(self._factories.keys())}"
            )

        factory, singleton = self._factories[name]

        # Return cached instance for singletons
        if singleton and name in self._services:
            return self._services[name]

        # Create new instance
        instance = factory()

        # Cache if singleton
        if singleton:
            self._services[name] = instance

        return instance

    def clear(self):
        """
        Clear all cached service instances.

        Useful for testing to ensure clean state between tests.
        """
        self._services.clear()
        logger.debug("Cleared all cached services")

    def reset(self):
        """
        Reset container completely (clear caches and factories).

        Use with caution - mainly for testing.
        """
        self._services.clear()
        self._factories.clear()
        logger.debug("Reset container completely")

    # ===========================
    # Cache Backend
    # ===========================

    def get_cache(self):
        """
        Get Django cache backend.

        Returns:
            Django cache backend (Redis or fallback)
        """
        if 'cache' not in self._services:
            from django.core.cache import caches
            self._services['cache'] = caches['default']
        return self._services['cache']

    # ===========================
    # Repository Layer
    # ===========================

    def get_user_repository(self):
        """
        Get User repository.

        Returns:
            UserRepository instance
        """
        return self.get('user_repository')

    def get_forum_repository(self):
        """
        Get Forum repository.

        Returns:
            ForumRepository instance
        """
        return self.get('forum_repository')

    def get_topic_repository(self):
        """
        Get Topic repository.

        Returns:
            TopicRepository instance
        """
        return self.get('topic_repository')

    def get_post_repository(self):
        """
        Get Post repository.

        Returns:
            PostRepository instance
        """
        return self.get('post_repository')

    def get_review_queue_repository(self):
        """
        Get ReviewQueue repository.

        Returns:
            ReviewQueueRepository instance
        """
        return self.get('review_queue_repository')

    # ===========================
    # Service Layer
    # ===========================

    def get_statistics_service(self):
        """
        Get ForumStatisticsService with injected dependencies.

        Returns:
            ForumStatisticsService instance
        """
        return self.get('statistics_service')

    def get_review_queue_service(self):
        """
        Get ReviewQueueService with injected dependencies.

        Returns:
            ReviewQueueService instance
        """
        return self.get('review_queue_service')

    def get_code_execution_service(self):
        """
        Get CodeExecutionService with injected dependencies.

        Returns:
            CodeExecutionService instance
        """
        return self.get('code_execution_service')

    def get_forum_content_service(self):
        """
        Get ForumContentService with injected dependencies.

        Returns:
            ForumContentService instance
        """
        return self.get('forum_content_service')


def _initialize_container():
    """
    Initialize container with default service registrations.

    This function is called once when the module is imported.
    """
    c = ServiceContainer()

    # Register cache
    c.register('cache', lambda: _get_cache())

    # Register repositories (Phase 3.2)
    from apps.api.repositories import (
        UserRepository,
        ForumRepository,
        TopicRepository,
        PostRepository,
        ReviewQueueRepository,
    )

    c.register('user_repository', UserRepository)
    c.register('forum_repository', ForumRepository)
    c.register('topic_repository', TopicRepository)
    c.register('post_repository', PostRepository)
    c.register('review_queue_repository', ReviewQueueRepository)

    # Register services (Phase 3.3+)
    from apps.api.services.statistics_service import ForumStatisticsService
    from apps.api.services.review_queue_service import ReviewQueueService
    from apps.api.services.forum_content_service import ForumContentService

    c.register('statistics_service', lambda: ForumStatisticsService(
        user_repo=c.get_user_repository(),
        topic_repo=c.get_topic_repository(),
        post_repo=c.get_post_repository(),
        forum_repo=c.get_forum_repository(),
        cache=c.get_cache()
    ))

    c.register('review_queue_service', lambda: ReviewQueueService(
        review_queue_repo=c.get_review_queue_repository(),
        post_repo=c.get_post_repository(),
        topic_repo=c.get_topic_repository(),
        user_repo=c.get_user_repository(),
        cache=c.get_cache()
    ))

    c.register('forum_content_service', ForumContentService)

    logger.info("Service container initialized with repositories and services")


def _get_cache():
    """
    Get cache backend with fallback support.

    Returns:
        Django cache backend
    """
    from django.core.cache import caches

    try:
        cache = caches['default']
        # Test connection
        cache.set('_health_check', 1, timeout=1)
        cache.delete('_health_check')
        return cache
    except Exception as e:
        logger.warning(f"Primary cache unavailable: {e}, using fallback")
        try:
            return caches['fallback']
        except Exception:
            # Ultimate fallback to dummy cache
            from django.core.cache.backends.dummy import DummyCache
            logger.error("All caches unavailable, using DummyCache")
            return DummyCache('dummy', {})


# Initialize container on module import
_initialize_container()

# Export singleton instance
container = ServiceContainer()

__all__ = ['ServiceContainer', 'container']

"""
Caching strategies and utilities for API endpoints.

Provides decorators and utilities for:
- Response caching
- Queryset caching
- Method caching
- Cache invalidation
- Cache key management
"""

import functools
import hashlib
import json
from typing import Any, Callable, Optional, Union

from django.core.cache import cache
from django.conf import settings
from django.db.models import QuerySet
from django.http import JsonResponse
from rest_framework.response import Response

import logging

logger = logging.getLogger(__name__)


class CacheKeyBuilder:
    """
    Utility class for building consistent cache keys.

    Usage:
        key = CacheKeyBuilder.build('courses', 'list', page=1, category='python')
    """

    NAMESPACE = 'api_cache'
    VERSION = getattr(settings, 'CACHE_VERSION', 1)

    @classmethod
    def build(cls, *parts: Any, **params: Any) -> str:
        """
        Build a cache key from parts and parameters.

        Args:
            *parts: Key parts (e.g., 'courses', 'list')
            **params: Additional parameters for the key

        Returns:
            str: Cache key
        """
        # Start with namespace and version
        key_parts = [cls.NAMESPACE, str(cls.VERSION)]

        # Add parts
        key_parts.extend(str(p) for p in parts)

        # Add sorted parameters for consistency
        if params:
            param_str = json.dumps(params, sort_keys=True, default=str)
            param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
            key_parts.append(param_hash)

        return ':'.join(key_parts)

    @classmethod
    def build_user_key(cls, user_id: int, *parts: Any, **params: Any) -> str:
        """
        Build a user-specific cache key.

        Args:
            user_id: User ID
            *parts: Key parts
            **params: Additional parameters

        Returns:
            str: User-specific cache key
        """
        return cls.build('user', user_id, *parts, **params)

    @classmethod
    def pattern(cls, *parts: Any) -> str:
        """
        Build a cache key pattern for wildcard deletion.

        Args:
            *parts: Key parts

        Returns:
            str: Cache key pattern
        """
        key_parts = [cls.NAMESPACE, str(cls.VERSION)]
        key_parts.extend(str(p) for p in parts)
        return ':'.join(key_parts) + ':*'


def cache_response(
    timeout: int = 300,
    key_func: Optional[Callable] = None,
    vary_on_user: bool = False,
    vary_on_query_params: bool = True,
):
    """
    Decorator to cache view responses.

    Args:
        timeout: Cache timeout in seconds (default: 300 = 5 minutes)
        key_func: Optional function to generate cache key
        vary_on_user: Include user ID in cache key
        vary_on_query_params: Include query parameters in cache key

    Usage:
        @cache_response(timeout=600, vary_on_user=True)
        @api_view(['GET'])
        def course_list(request):
            ...
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Build cache key
            if key_func:
                cache_key = key_func(request, *args, **kwargs)
            else:
                key_parts = [
                    view_func.__module__,
                    view_func.__name__,
                ]

                # Add user ID if requested
                if vary_on_user and hasattr(request, 'user') and request.user.is_authenticated:
                    key_parts.append(f'user_{request.user.id}')

                # Add query parameters if requested
                key_params = {}
                if vary_on_query_params and request.GET:
                    key_params = dict(request.GET.items())

                cache_key = CacheKeyBuilder.build(*key_parts, **key_params)

            # Try to get from cache
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return Response(cached_response)

            # Cache miss - call the view
            logger.debug(f"Cache MISS: {cache_key}")
            response = view_func(request, *args, **kwargs)

            # Cache the response if successful
            if isinstance(response, Response) and 200 <= response.status_code < 300:
                cache.set(cache_key, response.data, timeout)

            return response

        return wrapper
    return decorator


def cache_queryset(
    timeout: int = 300,
    key: Optional[str] = None,
):
    """
    Decorator to cache queryset results.

    Args:
        timeout: Cache timeout in seconds
        key: Cache key (auto-generated if not provided)

    Usage:
        @cache_queryset(timeout=600, key='active_courses')
        def get_active_courses():
            return Course.objects.filter(is_published=True)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key
            if key:
                cache_key = CacheKeyBuilder.build('queryset', key)
            else:
                cache_key = CacheKeyBuilder.build(
                    'queryset',
                    func.__module__,
                    func.__name__,
                    *args,
                    **{k: v for k, v in kwargs.items() if isinstance(v, (str, int, float, bool))}
                )

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Queryset cache HIT: {cache_key}")
                return cached_result

            # Cache miss - execute function
            logger.debug(f"Queryset cache MISS: {cache_key}")
            result = func(*args, **kwargs)

            # Convert QuerySet to list for caching
            if isinstance(result, QuerySet):
                result_list = list(result)
                cache.set(cache_key, result_list, timeout)
                return result_list

            cache.set(cache_key, result, timeout)
            return result

        return wrapper
    return decorator


def cache_method(
    timeout: int = 300,
    vary_on_self: bool = True,
):
    """
    Decorator to cache method results.

    Args:
        timeout: Cache timeout in seconds
        vary_on_self: Include instance ID in cache key

    Usage:
        class CourseService:
            @cache_method(timeout=600)
            def get_course_statistics(self, course_id):
                ...
    """
    def decorator(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            # Build cache key
            key_parts = [
                self.__class__.__module__,
                self.__class__.__name__,
                method.__name__,
            ]

            # Add instance ID if requested
            if vary_on_self and hasattr(self, 'id'):
                key_parts.append(f'instance_{self.id}')

            key_params = {
                'args': args,
                'kwargs': kwargs,
            }

            cache_key = CacheKeyBuilder.build(*key_parts, **key_params)

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Method cache HIT: {cache_key}")
                return cached_result

            # Cache miss - execute method
            logger.debug(f"Method cache MISS: {cache_key}")
            result = method(self, *args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result

        return wrapper
    return decorator


def invalidate_cache(*patterns: str):
    """
    Invalidate cache by patterns.

    Args:
        *patterns: Cache key patterns to invalidate

    Usage:
        # Invalidate all course caches
        invalidate_cache('api_cache:*:courses:*')

        # Invalidate specific user caches
        invalidate_cache(CacheKeyBuilder.pattern('user', user_id))
    """
    try:
        # Check if cache backend has _cache attribute (django-redis)
        if not hasattr(cache, '_cache'):
            # For other cache backends or tests, just skip pattern deletion
            logger.debug("Cache backend doesn't support _cache attribute, skipping pattern deletion")
            return

        cache_backend = cache._cache

        # For Redis cache, use delete_pattern
        if hasattr(cache_backend, 'delete_pattern'):
            for pattern in patterns:
                deleted = cache_backend.delete_pattern(pattern)
                logger.info(f"Invalidated {deleted} cache keys matching: {pattern}")
        else:
            # For other backends, clear all (less efficient)
            logger.warning(f"Cache backend doesn't support pattern deletion, clearing all")
            cache.clear()
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")


def invalidate_user_cache(user_id: int, *parts: Any):
    """
    Invalidate all caches for a specific user.

    Args:
        user_id: User ID
        *parts: Optional specific cache parts to invalidate

    Usage:
        # Invalidate all user caches
        invalidate_user_cache(user_id)

        # Invalidate specific user caches
        invalidate_user_cache(user_id, 'progress')
    """
    pattern = CacheKeyBuilder.build_user_key(user_id, *parts, **{}) + '*'
    invalidate_cache(pattern)


def invalidate_model_cache(model_name: str, *parts: Any):
    """
    Invalidate all caches for a specific model.

    Args:
        model_name: Model name (e.g., 'course', 'lesson')
        *parts: Optional specific cache parts to invalidate

    Usage:
        # Invalidate all course caches
        invalidate_model_cache('course')

        # Invalidate course list caches
        invalidate_model_cache('course', 'list')
    """
    pattern = CacheKeyBuilder.pattern(model_name, *parts)
    invalidate_cache(pattern)


# Predefined timeout constants
class CacheTimeout:
    """Predefined cache timeout constants."""
    VERY_SHORT = 30      # 30 seconds - highly dynamic data
    SHORT = 60           # 1 minute - dynamic data
    MEDIUM = 300         # 5 minutes - semi-dynamic data
    LONG = 900           # 15 minutes - semi-static data
    VERY_LONG = 3600     # 1 hour - static data
    DAY = 86400          # 24 hours - very static data

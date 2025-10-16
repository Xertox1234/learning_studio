"""
Base repository pattern for database access abstraction.

This module provides the foundation for the repository pattern, which:
- Abstracts database access from business logic
- Enables unit testing by allowing mock repositories
- Provides a consistent interface for data access
- Optimizes queries with select_related/prefetch_related
"""

from typing import List, Optional, Dict, Any
from django.db.models import QuerySet, Model, Q, Prefetch


class BaseRepository:
    """
    Abstract base repository providing common database operations.

    All repositories should inherit from this class and can override
    methods to add model-specific optimizations.
    """

    def __init__(self, model: type[Model]):
        """
        Initialize repository with a Django model.

        Args:
            model: Django model class to operate on
        """
        self.model = model

    def get_by_id(self, id: int) -> Optional[Model]:
        """
        Get single object by primary key.

        Args:
            id: Primary key value

        Returns:
            Model instance or None if not found
        """
        try:
            return self.model.objects.get(pk=id)
        except self.model.DoesNotExist:
            return None

    def get_by_ids(self, ids: List[int]) -> QuerySet:
        """
        Get multiple objects by primary keys.

        Args:
            ids: List of primary key values

        Returns:
            QuerySet of matching objects
        """
        return self.model.objects.filter(pk__in=ids)

    def filter(self, **kwargs) -> QuerySet:
        """
        Filter objects by field values.

        Args:
            **kwargs: Field lookups (e.g., name='John', age__gte=18)

        Returns:
            QuerySet of matching objects
        """
        return self.model.objects.filter(**kwargs)

    def filter_complex(self, q_filter: Q) -> QuerySet:
        """
        Filter with complex Q objects.

        Args:
            q_filter: Q object for complex queries

        Returns:
            QuerySet of matching objects
        """
        return self.model.objects.filter(q_filter)

    def all(self) -> QuerySet:
        """
        Get all objects.

        Returns:
            QuerySet of all objects
        """
        return self.model.objects.all()

    def count(self, **kwargs) -> int:
        """
        Count objects matching criteria.

        Args:
            **kwargs: Field lookups (empty for total count)

        Returns:
            Count of matching objects
        """
        if kwargs:
            return self.model.objects.filter(**kwargs).count()
        return self.model.objects.count()

    def exists(self, **kwargs) -> bool:
        """
        Check if objects matching criteria exist.

        Args:
            **kwargs: Field lookups

        Returns:
            True if any matching objects exist
        """
        return self.model.objects.filter(**kwargs).exists()

    def create(self, **kwargs) -> Model:
        """
        Create new object.

        Args:
            **kwargs: Field values

        Returns:
            Created model instance
        """
        return self.model.objects.create(**kwargs)

    def bulk_create(self, objects: List[Model]) -> List[Model]:
        """
        Create multiple objects in bulk.

        Args:
            objects: List of unsaved model instances

        Returns:
            List of created model instances
        """
        return self.model.objects.bulk_create(objects)

    def update(self, id: int, **kwargs) -> bool:
        """
        Update single object by ID.

        Args:
            id: Primary key value
            **kwargs: Field values to update

        Returns:
            True if object was updated, False if not found
        """
        updated = self.model.objects.filter(pk=id).update(**kwargs)
        return updated > 0

    def bulk_update(self, objects: List[Model], fields: List[str]) -> int:
        """
        Update multiple objects in bulk.

        Args:
            objects: List of model instances to update
            fields: List of field names to update

        Returns:
            Number of objects updated
        """
        return self.model.objects.bulk_update(objects, fields)

    def delete(self, id: int) -> bool:
        """
        Delete single object by ID.

        Args:
            id: Primary key value

        Returns:
            True if object was deleted, False if not found
        """
        deleted, _ = self.model.objects.filter(pk=id).delete()
        return deleted > 0

    def delete_many(self, **kwargs) -> int:
        """
        Delete multiple objects matching criteria.

        Args:
            **kwargs: Field lookups

        Returns:
            Number of objects deleted
        """
        deleted, _ = self.model.objects.filter(**kwargs).delete()
        return deleted

    def first(self, **kwargs) -> Optional[Model]:
        """
        Get first object matching criteria.

        Args:
            **kwargs: Field lookups

        Returns:
            First matching object or None
        """
        return self.model.objects.filter(**kwargs).first()

    def last(self, **kwargs) -> Optional[Model]:
        """
        Get last object matching criteria.

        Args:
            **kwargs: Field lookups

        Returns:
            Last matching object or None
        """
        return self.model.objects.filter(**kwargs).last()

    def order_by(self, *fields) -> QuerySet:
        """
        Get all objects ordered by specified fields.

        Args:
            *fields: Field names (prefix with '-' for descending)

        Returns:
            QuerySet ordered by specified fields
        """
        return self.model.objects.order_by(*fields)

    def paginate(self, page: int = 1, page_size: int = 20, **kwargs) -> Dict[str, Any]:
        """
        Get paginated results.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            **kwargs: Filter criteria

        Returns:
            Dict with 'results', 'total', 'page', 'pages' keys
        """
        queryset = self.model.objects.filter(**kwargs) if kwargs else self.model.objects.all()
        total = queryset.count()

        start = (page - 1) * page_size
        end = start + page_size
        results = list(queryset[start:end])

        return {
            'results': results,
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': (total + page_size - 1) // page_size,
            'has_next': page * page_size < total,
            'has_prev': page > 1,
        }

    def get_or_create(self, defaults: Optional[Dict[str, Any]] = None, **kwargs) -> tuple[Model, bool]:
        """
        Get existing object or create if doesn't exist.

        Args:
            defaults: Field values for creation if object doesn't exist
            **kwargs: Lookup criteria

        Returns:
            Tuple of (object, created) where created is True if new
        """
        return self.model.objects.get_or_create(defaults=defaults or {}, **kwargs)

    def update_or_create(self, defaults: Optional[Dict[str, Any]] = None, **kwargs) -> tuple[Model, bool]:
        """
        Update existing object or create if doesn't exist.

        Args:
            defaults: Field values for update/creation
            **kwargs: Lookup criteria

        Returns:
            Tuple of (object, created) where created is True if new
        """
        return self.model.objects.update_or_create(defaults=defaults or {}, **kwargs)


class OptimizedRepository(BaseRepository):
    """
    Repository with query optimization helpers.

    Subclasses should override _get_select_related() and _get_prefetch_related()
    to define default query optimizations.
    """

    def _get_select_related(self) -> List[str]:
        """
        Define select_related fields for query optimization.

        Override in subclasses to specify foreign key fields to join.

        Returns:
            List of field names for select_related
        """
        return []

    def _get_prefetch_related(self) -> List[str | Prefetch]:
        """
        Define prefetch_related fields for query optimization.

        Override in subclasses to specify related fields to prefetch.

        Returns:
            List of field names or Prefetch objects
        """
        return []

    def get_optimized_queryset(self) -> QuerySet:
        """
        Get QuerySet with default optimizations applied.

        Returns:
            Optimized QuerySet
        """
        queryset = self.model.objects.all()

        select_related = self._get_select_related()
        if select_related:
            queryset = queryset.select_related(*select_related)

        prefetch_related = self._get_prefetch_related()
        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)

        return queryset

    def all(self) -> QuerySet:
        """
        Get all objects with optimizations.

        Returns:
            Optimized QuerySet of all objects
        """
        return self.get_optimized_queryset()

    def filter(self, **kwargs) -> QuerySet:
        """
        Filter objects with optimizations.

        Args:
            **kwargs: Field lookups

        Returns:
            Optimized QuerySet of matching objects
        """
        return self.get_optimized_queryset().filter(**kwargs)

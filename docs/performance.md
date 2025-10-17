# Performance Optimization Guide

## Overview

This document describes the performance optimization strategies implemented in Python Learning Studio, including caching, query optimization, and monitoring.

---

## 1. Caching Strategy

### Cache Utilities

Located in `apps/api/cache/`, provides comprehensive caching tools:

#### Decorators

```python
from apps.api.cache import cache_response, cache_queryset, cache_method, CacheTimeout

# Cache API responses (5 minutes, vary by user and query params)
@cache_response(timeout=CacheTimeout.MEDIUM, vary_on_user=True)
@api_view(['GET'])
def course_list(request):
    ...

# Cache queryset results
@cache_queryset(timeout=CacheTimeout.LONG, key='active_courses')
def get_active_courses():
    return Course.objects.filter(is_published=True)

# Cache method results
class CourseService:
    @cache_method(timeout=CacheTimeout.MEDIUM)
    def get_statistics(self, course_id):
        ...
```

#### Cache Key Management

```python
from apps.api.cache import CacheKeyBuilder

# Build consistent cache keys
key = CacheKeyBuilder.build('courses', 'list', page=1, category='python')

# User-specific keys
user_key = CacheKeyBuilder.build_user_key(user_id, 'progress')

# Key patterns for invalidation
pattern = CacheKeyBuilder.pattern('courses', 'list')
```

#### Cache Timeouts

```python
from apps.api.cache import CacheTimeout

CacheTimeout.VERY_SHORT = 30      # 30 seconds
CacheTimeout.SHORT = 60           # 1 minute
CacheTimeout.MEDIUM = 300         # 5 minutes (default)
CacheTimeout.LONG = 900           # 15 minutes
CacheTimeout.VERY_LONG = 3600     # 1 hour
CacheTimeout.DAY = 86400          # 24 hours
```

### Cache Warming

Pre-populate caches on server startup or via management command:

```bash
# Warm all caches
python manage.py warm_cache

# Warm specific user caches
python manage.py warm_cache --user-id 123

# Warm on startup (add to wsgi.py or asgi.py)
from apps.api.cache.warming import warmer
warmer.warm_all(verbose=False)
```

### Cache Invalidation

Automatic invalidation via Django signals:

```python
# Signals automatically invalidate caches when models change
# Configured in apps/api/cache/invalidation.py

# Manual invalidation
from apps.api.cache import invalidate_model_cache, invalidate_user_cache

# Invalidate all course caches
invalidate_model_cache('courses')

# Invalidate specific user caches
invalidate_user_cache(user_id, 'progress')
```

---

## 2. Database Query Optimization

### Select Related & Prefetch Related

Always optimize database queries in ViewSets:

```python
class CourseViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Course.objects.filter(
            is_published=True
        ).select_related(
            'instructor',     # ForeignKey - use select_related
            'category'
        ).prefetch_related(
            'lessons',        # Reverse ForeignKey - use prefetch_related
            'enrollments'
        )
```

### Query Optimization Checklist

- [ ] Use `select_related()` for ForeignKey and OneToOne
- [ ] Use `prefetch_related()` for ManyToMany and reverse ForeignKey
- [ ] Use `only()` or `defer()` for large models
- [ ] Add database indexes for frequently queried fields
- [ ] Avoid N+1 queries - check with query logger

### Query Logging

Enable query logging in development to identify N+1 queries:

```bash
# Set in .env
QUERY_LOGGING_ENABLED=True

# View logs in console output
# Shows query count, slow queries, and potential N+1 issues
```

---

## 3. Performance Monitoring

### Django Silk

Access performance profiling at `http://localhost:8000/silk/`

Features:
- Request profiling
- SQL query analysis
- Python profiling
- Performance comparisons

**Requirements:**
- Only available in development
- Must be superuser to access

### Performance Metrics

View performance metrics via response headers (development only):

```
X-Request-Time: 0.123s
X-Query-Count: 15
X-Query-Time: 0.045s
X-Cache-Hits: 3
X-Cache-Misses: 1
X-Cache-Hit-Ratio: 75.0%
```

### Benchmarking

Run performance benchmarks:

```bash
# Run benchmark with 10 iterations per endpoint
python manage.py benchmark

# Run with custom iterations
python manage.py benchmark --iterations 50

# Clear cache before benchmarking
python manage.py benchmark --clear-cache

# Warm cache before benchmarking
python manage.py benchmark --warm-cache

# Verbose output
python manage.py benchmark --verbose
```

---

## 4. Performance Best Practices

### API Endpoints

1. **Use caching for expensive queries**
   - Course listings
   - User profiles
   - Forum statistics
   - Navigation menus

2. **Optimize querysets**
   - Always use select_related/prefetch_related
   - Add database indexes for filtered/sorted fields
   - Use only() for large models

3. **Pagination**
   - Paginate all list endpoints
   - Use standard page sizes (10, 20, 50)
   - Consider cursor pagination for large datasets

### Frontend

1. **Lazy loading**
   - Load content on demand
   - Use infinite scroll for long lists
   - Defer non-critical resources

2. **Asset optimization**
   - Minimize and compress JS/CSS
   - Use CDN for static assets
   - Enable browser caching

### Database

1. **Indexes**
   - See `docs/database-indexes.md` for comprehensive index strategy
   - Add indexes for frequently filtered/sorted fields
   - Use partial indexes where appropriate

2. **Connection pooling**
   - Configure `CONN_MAX_AGE` (default: 60s)
   - Monitor connection usage
   - Adjust based on load

---

## 5. Monitoring Checklist

### Development

- [ ] Enable query logging to identify N+1 queries
- [ ] Use Django Silk for profiling
- [ ] Check performance metrics headers
- [ ] Run benchmarks regularly

### Production

- [ ] Configure Sentry for error tracking
- [ ] Monitor cache hit rates
- [ ] Track slow query logs
- [ ] Set up performance alerts

---

## 6. Performance Targets

| Metric | Target | Excellent | Needs Work |
|--------|--------|-----------|------------|
| Average response time | < 200ms | < 100ms | > 500ms |
| P95 response time | < 500ms | < 300ms | > 1s |
| Database queries per request | < 20 | < 10 | > 50 |
| Cache hit rate | > 70% | > 90% | < 50% |

---

## 7. Troubleshooting

### Slow Requests

1. Check query count and time in logs
2. Profile with Django Silk
3. Identify missing select_related/prefetch_related
4. Add appropriate database indexes

### Cache Issues

1. Verify Redis is running
2. Check cache configuration
3. Monitor cache hit/miss rates
4. Ensure cache invalidation is working

### High Memory Usage

1. Check for large querysets not using pagination
2. Review cache sizes and timeouts
3. Monitor connection pool usage
4. Check for memory leaks in custom code

---

## Additional Resources

- Database indexes: `docs/database-indexes.md`
- Sentry setup: `docs/monitoring.md`
- API documentation: `http://localhost:8000/api/schema/swagger/`
- Silk profiler: `http://localhost:8000/silk/`

# Monitoring Setup Guide

## Overview

This document covers error tracking, performance monitoring, and observability setup for Python Learning Studio using Sentry and other monitoring tools.

---

## 1. Sentry Integration

### Setup

1. **Create Sentry account** at https://sentry.io/

2. **Create new project** for Python Learning Studio

3. **Configure environment variables** in `.env`:

```bash
# Sentry Configuration
SENTRY_DSN=https://your-sentry-dsn-here@sentry.io/project-id
SENTRY_TRACES_SAMPLE_RATE=0.1  # Sample 10% of transactions
SENTRY_PROFILES_SAMPLE_RATE=0.1  # Profile 10% of transactions
SENTRY_RELEASE=v1.0.0  # Optional: track releases
ENVIRONMENT=production  # development, staging, or production
```

### Features

#### Error Tracking

Sentry automatically captures:
- Unhandled exceptions
- HTTP errors (4xx, 5xx)
- Database errors
- Template rendering errors
- Celery task failures

#### Performance Monitoring

Tracks performance for:
- HTTP requests
- Database queries
- Redis cache operations
- Celery tasks
- External API calls

#### Custom Error Tracking

```python
from sentry_sdk import capture_exception, capture_message

try:
    risky_operation()
except Exception as e:
    # Capture with context
    capture_exception(e)

# Log messages
capture_message("Important event occurred", level="info")
```

#### Adding Context

```python
from sentry_sdk import set_user, set_tag, set_context

# User context
set_user({
    "id": user.id,
    "email": user.email,
    "username": user.username,
})

# Custom tags for filtering
set_tag("feature", "course_enrollment")
set_tag("user_type", "student")

# Additional context
set_context("course", {
    "id": course.id,
    "title": course.title,
})
```

### Environment-Specific Configuration

#### Development
- Sentry disabled by default (errors not sent)
- Enable by setting `SENTRY_DSN` in `.env`
- Lower sample rates for testing

#### Production
- Sentry fully enabled
- 10% transaction sampling (configurable)
- All errors captured
- Performance traces enabled

---

## 2. Django Silk (Development Only)

### Access

Visit: `http://localhost:8000/silk/`

**Requirements:**
- Superuser account
- Development environment only

### Features

#### Request Profiling
- View all HTTP requests
- Response times
- SQL queries executed
- Query duplication detection

#### SQL Analysis
- Query execution time
- Query frequency
- N+1 query detection
- Query optimization suggestions

#### Python Profiling
- Function call graphs
- Time spent in each function
- Memory usage
- Bottleneck identification

### Usage

1. **Profile specific requests:**
   - Add `?silk` to any URL
   - View detailed profile in Silk dashboard

2. **Compare requests:**
   - Select multiple requests
   - Click "Compare"
   - Identify performance differences

3. **Generate reports:**
   - Export profiling data
   - Create performance baselines
   - Track improvements over time

---

## 3. Performance Metrics

### Real-Time Metrics

Available via cache (5-minute rolling window):

```python
from django.core.cache import cache

# Get metrics for an endpoint
metrics = cache.get('perf_metrics:/api/v1/courses/')

# Returns:
{
    'count': 50,
    'total_time': 12.5,
    'avg_time': 0.25,
    'max_time': 1.2,
    'min_time': 0.05,
    'total_queries': 750,
    'avg_queries': 15,
}
```

### Response Headers (Development)

Every API response includes performance headers:

```
X-Request-Time: 0.156s
X-Query-Count: 12
X-Query-Time: 0.045s
X-Cache-Hits: 5
X-Cache-Misses: 2
X-Cache-Hit-Ratio: 71.4%
```

---

## 4. Logging Strategy

### Log Levels

```python
import logging

logger = logging.getLogger(__name__)

# Development
logger.debug("Detailed debugging info")  # Verbose
logger.info("General informational messages")

# Production
logger.warning("Warning messages")  # Potential issues
logger.error("Error messages")  # Errors occurred
logger.critical("Critical messages")  # System failures
```

### Log Configuration

#### Development
- Console output (DEBUG level)
- File logging (INFO level)
- Verbose SQL logging (if enabled)

#### Production
- File logging (INFO level)
- Rotating file handler (50MB, 5 backups)
- Sentry integration (ERROR level)
- Structured logging recommended

### Custom Loggers

```python
# App-specific loggers
api_logger = logging.getLogger('apps.api')
forum_logger = logging.getLogger('apps.forum_integration')
cache_logger = logging.getLogger('apps.api.cache')

# Log with context
api_logger.info(
    "Course enrollment",
    extra={
        'user_id': user.id,
        'course_id': course.id,
    }
)
```

---

## 5. Monitoring Dashboard (Sentry)

### Key Metrics to Monitor

#### Error Metrics
- Error rate (errors per minute)
- Error type distribution
- Affected users
- Error frequency trends

#### Performance Metrics
- Average response time
- P50, P75, P95, P99 percentiles
- Slow transaction percentage
- Database query time

#### User Impact
- Users affected by errors
- Features with highest error rates
- Geographic error distribution

### Alerts

Configure alerts for:

1. **Error Spikes**
   - Threshold: 10+ errors in 5 minutes
   - Notify: Email, Slack

2. **Slow Transactions**
   - Threshold: P95 > 1 second
   - Notify: Email

3. **High Error Rate**
   - Threshold: Error rate > 5%
   - Notify: Email, Slack, PagerDuty

4. **Database Issues**
   - Threshold: Query time > 500ms
   - Notify: Email

---

## 6. Performance Benchmarking

### Run Benchmarks

```bash
# Standard benchmark
python manage.py benchmark

# Custom iterations
python manage.py benchmark --iterations 50

# With cache warming
python manage.py benchmark --warm-cache

# Clear cache first
python manage.py benchmark --clear-cache --warm-cache

# Verbose output
python manage.py benchmark --verbose
```

### Benchmark Targets

| Endpoint | Target (avg) | Excellent | Needs Work |
|----------|--------------|-----------|------------|
| Course list | < 200ms | < 100ms | > 500ms |
| Course detail | < 150ms | < 75ms | > 400ms |
| User profile | < 100ms | < 50ms | > 300ms |
| Forum topics | < 250ms | < 125ms | > 600ms |

---

## 7. Cache Monitoring

### Cache Hit Rates

Monitor cache effectiveness:

```python
# Check cache stats (if Redis)
from django.core.cache import cache
cache_backend = cache._cache

# Get cache info
info = cache_backend.get_client().info('stats')

# Calculate hit rate
hits = info.get('keyspace_hits', 0)
misses = info.get('keyspace_misses', 0)
hit_rate = hits / (hits + misses) * 100 if (hits + misses) > 0 else 0
```

### Cache Warming

Automatic cache warming on startup or manual:

```bash
# Warm all caches
python manage.py warm_cache

# Warm specific user
python manage.py warm_cache --user-id 123
```

---

## 8. Production Monitoring Checklist

### Pre-Launch

- [ ] Sentry configured with correct DSN
- [ ] Environment set to `production`
- [ ] Sample rates configured (10% recommended)
- [ ] Alerts configured in Sentry
- [ ] Error notification channels set up
- [ ] Release tracking enabled

### Post-Launch

- [ ] Monitor error dashboard daily
- [ ] Review performance metrics weekly
- [ ] Check slow transaction list
- [ ] Analyze cache hit rates
- [ ] Review database query performance
- [ ] Update performance baselines

### Regular Maintenance

- [ ] Weekly: Review error trends
- [ ] Monthly: Analyze performance metrics
- [ ] Quarterly: Review and optimize slow queries
- [ ] As needed: Adjust cache timeouts
- [ ] As needed: Add/remove monitoring alerts

---

## 9. Troubleshooting

### Sentry Not Receiving Errors

1. Check `SENTRY_DSN` is set correctly
2. Verify `ENVIRONMENT` is not `development` (errors suppressed)
3. Test with: `python manage.py shell -c "import sentry_sdk; sentry_sdk.capture_message('test')"`
4. Check Sentry dashboard for test message

### High Error Rates

1. Review error details in Sentry
2. Check if errors are user-caused or bugs
3. Add more context to errors if needed
4. Prioritize fixes based on user impact

### Slow Performance

1. Check Sentry performance dashboard
2. Identify slow transactions
3. Use Django Silk for detailed profiling (development)
4. Run benchmarks to establish baselines
5. Optimize queries and add caching

---

## 10. Additional Resources

- Sentry Documentation: https://docs.sentry.io/
- Django Silk: https://github.com/jazzband/django-silk
- Performance optimization: `docs/performance.md`
- Database indexes: `docs/database-indexes.md`

---

## Support

For monitoring issues or questions:
- Check Sentry documentation
- Review application logs
- Contact development team
- File GitHub issue if bug suspected

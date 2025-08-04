# Rate Limiting Implementation

This document describes the comprehensive rate limiting system implemented to protect the Python Learning Studio platform from abuse, spam, and DoS attacks.

## Overview

The rate limiting system uses `django-ratelimit` to control request frequency across different types of operations. It provides flexible, configurable limits with user-friendly error handling and automatic retry mechanisms.

## Rate Limit Configuration

### Environment Variables
Configure rate limits via environment variables in `.env` file:

```bash
# Authentication Rate Limits
RATE_LIMIT_LOGIN=5/m          # 5 login attempts per minute
RATE_LIMIT_REGISTER=3/m       # 3 registration attempts per minute

# API Rate Limits  
RATE_LIMIT_API=100/m          # 100 general API calls per minute
RATE_LIMIT_FORUM_POSTS=10/m   # 10 forum posts per minute
RATE_LIMIT_CODE_EXEC=20/m     # 20 code executions per minute
RATE_LIMIT_AI=30/h            # 30 AI assistance requests per hour

# Rate Limiting Control
RATELIMIT_ENABLE=True         # Enable/disable rate limiting
```

### Default Settings
Located in `learning_community/settings/base.py`:

```python
RATE_LIMIT_SETTINGS = {
    'LOGIN_ATTEMPTS': config('RATE_LIMIT_LOGIN', default='5/m', cast=str),
    'REGISTRATION_ATTEMPTS': config('RATE_LIMIT_REGISTER', default='3/m', cast=str),
    'API_CALLS': config('RATE_LIMIT_API', default='100/m', cast=str),
    'FORUM_POSTS': config('RATE_LIMIT_FORUM_POSTS', default='10/m', cast=str),
    'CODE_EXECUTION': config('RATE_LIMIT_CODE_EXEC', default='20/m', cast=str),
    'AI_REQUESTS': config('RATE_LIMIT_AI', default='30/h', cast=str),
}
```

## Protected Endpoints

### Authentication Endpoints
**High Security** - Prevent brute force attacks:

- **Login** (`/api/v1/auth/login/`): 5 attempts/minute per IP
- **Registration** (`/api/v1/auth/register/`): 3 attempts/minute per IP

```python
@ratelimit(key='ip', rate=settings.RATE_LIMIT_SETTINGS['LOGIN_ATTEMPTS'], method='POST', block=True)
def login(request):
    # Login logic with constant-time responses
```

### Code Execution Endpoints
**Resource Protection** - Prevent computational abuse:

- **Code Execution** (`/api/v1/execute-code/`): 20 executions/minute per user

```python
@ratelimit(key='user', rate=settings.RATE_LIMIT_SETTINGS['CODE_EXECUTION'], method='POST', block=True)
def execute_code(request):
    # Docker-based code execution
```

### Forum Endpoints
**Anti-Spam Protection** - Prevent forum abuse:

- **Post Creation** (`/api/v1/posts/`): 10 posts/minute per user

```python
@ratelimit(key='user', rate=settings.RATE_LIMIT_SETTINGS['FORUM_POSTS'], method='POST', block=True)
def post_create(request):
    # Forum post creation logic
```

### AI Assistance Endpoints
**Cost Control** - Manage expensive AI operations:

- **AI Requests** (`/api/v1/ai-assistance/`): 30 requests/hour per user

```python
@method_decorator(ratelimit(key='user', rate=settings.RATE_LIMIT_SETTINGS['AI_REQUESTS'], method='POST', block=True), name='post')
class AIAssistanceView(APIView):
    # AI assistance logic
```

### General API Protection
**Comprehensive Coverage** - Protect all ViewSets:

- **API ViewSets**: 100 requests/minute per user/IP via `RateLimitMixin`

```python
class SubmissionViewSet(RateLimitMixin, viewsets.ModelViewSet):
    # Automatically rate limited
```

## Rate Limiting Keys

### User-Based Limits
For authenticated users, limits are applied per user account:
```python
key='user'  # Uses user.id for rate limiting
```

### IP-Based Limits  
For anonymous users or authentication endpoints:
```python
key='ip'  # Uses client IP address
```

### Hybrid Approach
Automatically chooses user ID or IP address:
```python
def get_user_or_ip(request):
    if request.user.is_authenticated:
        return f"user_{request.user.id}"
    return f"ip_{get_client_ip(request)}"
```

## Rate Limit Formats

### Time Periods
- `s` - seconds
- `m` - minutes  
- `h` - hours
- `d` - days

### Examples
- `5/m` - 5 requests per minute
- `100/h` - 100 requests per hour
- `1000/d` - 1000 requests per day
- `10/10s` - 10 requests per 10 seconds

## Error Handling

### API Responses
For API endpoints, returns JSON with retry information:

```json
{
    "error": "Rate limit exceeded",
    "message": "Too many requests. Please try again later.",
    "retry_after": 60
}
```

### Web Page Responses
For web requests, renders user-friendly error page at `templates/errors/rate_limited.html`.

### Custom Error Handler
Located in `apps/api/views.py`:

```python
def ratelimited(request, exception):
    """Custom view for handling rate limit exceeded responses."""
    if request.content_type == 'application/json' or request.path.startswith('/api/'):
        return JsonResponse({
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please try again later.',
            'retry_after': getattr(exception, 'time_left', 60)
        }, status=429)
    else:
        return render(request, 'errors/rate_limited.html', {
            'retry_after': getattr(exception, 'time_left', 60)
        }, status=429)
```

## Frontend Integration

### Error Handling in React
Handle rate limit errors in API calls:

```javascript
// In frontend/src/utils/api.js
export const apiRequest = async (url, options = {}) => {
    try {
        const response = await fetch(fullUrl, config)
        
        if (response.status === 429) {
            const errorData = await response.json()
            throw new RateLimitError(errorData.message, errorData.retry_after)
        }
        
        return await response.json()
    } catch (error) {
        if (error instanceof RateLimitError) {
            // Show rate limit warning to user
            showRateLimitWarning(error.retryAfter)
        }
        throw error
    }
}

class RateLimitError extends Error {
    constructor(message, retryAfter) {
        super(message)
        this.name = 'RateLimitError'
        this.retryAfter = retryAfter
    }
}
```

### User Feedback
Show helpful messages when rate limits are hit:

```javascript
const showRateLimitWarning = (retryAfter) => {
    toast.warning(
        `Too many requests. Please wait ${retryAfter} seconds before trying again.`,
        { duration: retryAfter * 1000 }
    )
}
```

## IP Address Detection

### Proxy Support
Handles various proxy configurations:

```python
def get_client_ip(request):
    """Get the client IP address from the request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
```

### Production Considerations
- Configure `SECURE_PROXY_SSL_HEADER` for HTTPS
- Set `USE_X_FORWARDED_HOST = True` behind load balancers
- Validate proxy headers to prevent IP spoofing

## Cache Backend

### Development
Uses in-memory cache (local memory):
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
```

### Production
Recommended Redis backend:
```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

## Monitoring and Analytics

### Rate Limit Metrics
Track rate limiting effectiveness:

```python
# Log rate limit hits for monitoring
logger.warning(f"Rate limit exceeded for {key}: {request.path}")

# Metrics to track:
# - Rate limit hits per endpoint
# - Top rate-limited users/IPs  
# - Peak request patterns
# - Cache hit rates
```

### Django Admin Integration
View rate limit statistics in Django admin:

```python
# apps/api/admin.py
@admin.register(RateLimitLog)
class RateLimitLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'endpoint', 'key', 'count']
    list_filter = ['endpoint', 'timestamp']
    search_fields = ['key']
```

## Bypass Mechanisms

### Trusted Users
Allow certain users to bypass rate limits:

```python
def is_trusted_user(user):
    return user.is_staff or user.groups.filter(name='trusted_users').exists()

@ratelimit(
    key='user', 
    rate='100/m', 
    skip_if=lambda request, *args, **kwargs: is_trusted_user(request.user)
)
def protected_view(request):
    # View logic
```

### Development Mode
Disable rate limiting in development:

```python
# learning_community/settings/development.py
RATELIMIT_ENABLE = False
```

## Security Considerations

### Rate Limit Bypass Prevention
- Validate proxy headers to prevent IP spoofing
- Use secure session management
- Monitor for distributed attacks
- Implement progressive penalties for repeat offenders

### DoS Attack Mitigation
- Different limits for different operations
- Shorter time windows for expensive operations
- IP-based blocking for severe abuse
- Integration with CDN/WAF rate limiting

## Testing Rate Limits

### Unit Tests
Test rate limiting functionality:

```python
# apps/api/tests/test_rate_limiting.py
class RateLimitTests(TestCase):
    def test_login_rate_limit(self):
        # Test login rate limiting
        for i in range(6):  # Exceed 5/minute limit
            response = self.client.post('/api/v1/auth/login/', {
                'email': 'test@example.com',
                'password': 'wrong'
            })
            if i < 5:
                self.assertNotEqual(response.status_code, 429)
            else:
                self.assertEqual(response.status_code, 429)
```

### Load Testing
Test rate limits under load:

```bash
# Use artillery.js or similar
artillery quick --count 10 --num 20 http://localhost:8000/api/v1/courses/
```

## Performance Impact

### Minimal Overhead
- Cache-based tracking (sub-millisecond lookups)
- Lightweight Redis operations
- No database queries for rate limiting

### Memory Usage
- ~1KB per tracked key
- Automatic key expiration
- Configurable cache size limits

## Troubleshooting

### Common Issues

**Rate limits not working:**
```bash
# Check cache backend
python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'value')
>>> cache.get('test')
```

**Users getting blocked incorrectly:**
- Check proxy configuration
- Verify IP detection logic
- Review rate limit settings

**Performance issues:**
- Monitor cache hit rates
- Check Redis memory usage
- Review rate limit frequency

### Debug Commands
```bash
# Clear rate limit cache
python manage.py shell -c "from django.core.cache import cache; cache.clear()"

# Check current rate limits
python manage.py shell -c "from django.conf import settings; print(settings.RATE_LIMIT_SETTINGS)"
```

## Best Practices

### Setting Appropriate Limits
1. **Start conservative** - It's easier to raise limits than fix abuse
2. **Monitor usage patterns** - Adjust based on real user behavior  
3. **Different limits for different operations** - Expensive operations need stricter limits
4. **Consider user tiers** - Premium users might get higher limits

### Error Messages
1. **Be helpful** - Explain why limits exist
2. **Provide retry time** - Tell users when they can try again
3. **Suggest alternatives** - Guide users to other actions
4. **Be consistent** - Same format across all endpoints

### Monitoring
1. **Track hit rates** - Monitor how often limits are hit
2. **Identify patterns** - Look for unusual usage patterns
3. **User feedback** - Listen to complaints about limits
4. **Performance impact** - Ensure rate limiting doesn't slow down requests

## Future Enhancements

### Planned Features
1. **Dynamic Rate Limiting** - Adjust limits based on server load
2. **User Tier System** - Different limits for different user types
3. **Geographic Limits** - Different limits by region
4. **Time-based Limits** - Different limits during peak hours
5. **Adaptive Limiting** - Machine learning-based limit adjustment

### Advanced Patterns
1. **Token Bucket Algorithm** - Allow burst requests with sustained limits
2. **Sliding Window** - More precise rate limiting over time
3. **Distributed Rate Limiting** - Coordinate limits across multiple servers
4. **Circuit Breaker Pattern** - Temporarily block users who consistently hit limits
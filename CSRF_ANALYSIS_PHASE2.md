# CSRF Protection Analysis - Phase 2.2

**Date:** 2025-10-16
**Status:** Analysis Complete
**Total @csrf_exempt Found:** 12 instances across 4 files

---

## Executive Summary

### Critical Finding: Incorrect CSRF Protection

All 12 `@csrf_exempt` decorators in the codebase are **incorrectly applied** and should be removed or replaced:

- **11 DRF API views**: Incorrectly bypass CSRF when SessionAuthentication is enabled
- **1 Django view**: Public code execution endpoint with NO authentication (CRITICAL)

### Security Impact

| Issue | Severity | Impact |
|-------|----------|--------|
| DRF views with @csrf_exempt | **HIGH** | Vulnerable to CSRF when using browsable API |
| Public code execution endpoint | **CRITICAL** | Anyone can execute arbitrary Python code |
| Duplicate endpoint implementations | MEDIUM | Maintenance burden, inconsistency |

---

## Detailed Analysis

### 1. DRF API Views (11 instances) - INCORRECT USAGE

All DRF views use:
- `@api_view` decorator
- `@permission_classes([IsAuthenticated])`
- `@csrf_exempt` ⚠️ **INCORRECT**

**Why @csrf_exempt is Wrong:**

Django REST Framework's `SessionAuthentication` class **handles CSRF internally**:
- When SessionAuthentication is active, DRF enforces CSRF by default
- JWT authentication doesn't need CSRF (uses Authorization header)
- Adding `@csrf_exempt` disables CSRF for **all authentication methods**, including SessionAuthentication
- This makes the browsable API vulnerable to CSRF attacks

**Current REST_FRAMEWORK Configuration:**
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',  # No CSRF needed
        'rest_framework.authentication.SessionAuthentication',        # Needs CSRF!
    ],
}
```

**Vulnerability:**
When a logged-in user visits the browsable API (SessionAuthentication), an attacker can craft a malicious page that makes POST/PUT/DELETE requests on behalf of the user without CSRF protection.

---

### 2. Affected Endpoints

#### File: `apps/api/views.py` (6 instances)

| Line | Endpoint | Method | Description | Verdict |
|------|----------|--------|-------------|---------|
| 1202 | `topic_create` | POST | Create forum topic | REMOVE @csrf_exempt |
| 1481 | `post_create` | POST | Create forum post | REMOVE @csrf_exempt |
| 1660 | `post_edit` | PUT/PATCH | Edit forum post | REMOVE @csrf_exempt |
| 1750 | `post_delete` | DELETE | Delete forum post | REMOVE @csrf_exempt |
| 3099 | `wagtail_course_enroll` | POST | Enroll in course | REMOVE @csrf_exempt |
| 3149 | `wagtail_course_unenroll` | DELETE | Unenroll from course | REMOVE @csrf_exempt |

**All endpoints:**
- Require authentication (`IsAuthenticated`)
- Use DRF's `@api_view` decorator
- Support both JWT and Session authentication
- Should rely on DRF's built-in CSRF handling

---

#### File: `apps/api/forum_api.py` (4 instances)

| Line | Endpoint | Method | Description | Verdict |
|------|----------|--------|-------------|---------|
| 312 | `topic_create` | POST | Create forum topic (duplicate) | REMOVE @csrf_exempt |
| 531 | `post_create` | POST | Create forum post (duplicate) | REMOVE @csrf_exempt |
| 680 | `post_edit` | PUT/PATCH | Edit forum post (duplicate) | REMOVE @csrf_exempt |
| 752 | `post_delete` | DELETE | Delete forum post (duplicate) | REMOVE @csrf_exempt |

**Note:** These are **duplicate implementations** of the same endpoints in `apps/api/views.py`. This creates:
- Maintenance burden (need to update in two places)
- Potential inconsistencies
- URL routing conflicts

**Recommendation:** Consolidate or deprecate one set of implementations.

---

#### File: `apps/api/views/integrated_content.py` (1 instance)

| Line | Endpoint | Method | Description | Verdict |
|------|----------|--------|-------------|---------|
| 24 | `create_integrated_content` | POST | Create cross-platform content | REMOVE @csrf_exempt |

**Endpoint details:**
- Requires authentication (`IsAuthenticated`)
- Has rate limiting (`10/h`)
- Uses DRF's `@api_view` decorator
- Should rely on DRF's CSRF handling

---

#### File: `apps/learning/views.py` (1 instance) - CRITICAL

| Line | Endpoint | Method | Description | Severity |
|------|----------|--------|-------------|----------|
| 163 | `execute_code_view` | POST | Execute arbitrary Python code | **CRITICAL** |

**🚨 CRITICAL SECURITY ISSUE:**

```python
@csrf_exempt
def execute_code_view(request):
    """Execute code from playground or exercises."""
    if request.method == 'POST':
        data = json.loads(request.body)
        code = data.get('code', '')
        # Execute the code
        result = code_executor.execute_python_code(code)
```

**Problems:**
1. **No authentication required** - Anyone can call this endpoint
2. **No CSRF protection** - Vulnerable to CSRF attacks
3. **Executes arbitrary code** - Extremely dangerous without auth
4. **Plain Django view** - Not using DRF's protection mechanisms

**Attack Scenario:**
1. Attacker creates malicious website
2. Victim visits while logged into learning platform (if they had sessions)
3. Malicious JS sends POST to `/execute-code/` with dangerous code
4. Code executes on server

**Even worse:** Currently, this endpoint has NO authentication at all, so:
- Anyone on the internet can execute code
- No user account needed
- No rate limiting
- No audit trail

---

## How CSRF Protection Should Work

### For DRF Views (@api_view)

**Correct Configuration:**
```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
# NO @csrf_exempt - let DRF handle it
def my_view(request):
    # DRF automatically:
    # - Enforces CSRF for SessionAuthentication
    # - Allows JWT without CSRF (Authorization header)
    pass
```

**How DRF Handles It:**
1. **JWT Requests:** Token in `Authorization: Bearer <token>` - No CSRF needed
2. **Session Requests:** Cookie-based auth - CSRF token required in header or POST data

### For Django Views (Plain Functions)

**Option 1: Migrate to DRF ViewSet/APIView (RECOMMENDED)**
```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def execute_code_view(request):
    # DRF handles auth and CSRF
    pass
```

**Option 2: Add Authentication + Keep CSRF**
```python
from django.contrib.auth.decorators import login_required

@login_required  # Require authentication
# Remove @csrf_exempt - Django's middleware handles CSRF
def execute_code_view(request):
    pass
```

---

## Recommended Actions

### Priority 1: CRITICAL (Immediate) - execute_code_view

**File:** `apps/learning/views.py:163`

**Action:**
1. Remove `@csrf_exempt`
2. Add authentication (use existing DRF view in `apps/api/views/code_execution.py` instead)
3. OR convert to DRF view with `@api_view` + `@permission_classes([IsAuthenticated])`
4. Add rate limiting
5. Add audit logging

**Alternative:** This endpoint appears to be superseded by:
- `apps/api/views/code_execution.py` - Properly authenticated DRF view

**Recommendation:** Deprecate `apps/learning/views.py:execute_code_view` entirely and redirect to the secure DRF endpoint.

---

### Priority 2: HIGH - Remove @csrf_exempt from DRF Views

**Files:**
- `apps/api/views.py` (6 instances)
- `apps/api/forum_api.py` (4 instances)
- `apps/api/views/integrated_content.py` (1 instance)

**Action:**
Simply remove the `@csrf_exempt` decorator from all DRF views:

```python
# BEFORE:
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt  # ← REMOVE THIS
def topic_create(request):
    pass

# AFTER:
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def topic_create(request):
    pass
```

**Impact:**
- SessionAuthentication will require CSRF token (correct behavior)
- JWT authentication continues to work without CSRF (correct behavior)
- Browsable API becomes CSRF-protected (security improvement)

---

### Priority 3: MEDIUM - Consolidate Duplicate Endpoints

**Issue:** `apps/api/forum_api.py` duplicates 4 endpoints from `apps/api/views.py`:
- `topic_create`
- `post_create`
- `post_edit`
- `post_delete`

**Action:**
1. Determine which implementation is primary
2. Deprecate or remove duplicate
3. Update URL routing to use single implementation

---

## Testing Strategy

### 1. Test JWT Authentication (Should Work)
```bash
# Obtain JWT token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}' \
  | jq -r '.access')

# Test endpoint with JWT (should work without CSRF)
curl -X POST http://localhost:8000/api/v1/forum/topics/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"forum_id": 1, "subject": "Test", "content": "Test"}'
```

### 2. Test Session Authentication (Should Require CSRF)
```python
import requests

# Login to get session cookie
session = requests.Session()
session.post('http://localhost:8000/api/v1/auth/login/', json={
    'email': 'test@example.com',
    'password': 'password'
})

# Try POST without CSRF token (should fail with 403)
response = session.post('http://localhost:8000/api/v1/forum/topics/', json={
    'forum_id': 1,
    'subject': 'Test',
    'content': 'Test'
})
print(response.status_code)  # Should be 403 Forbidden

# Get CSRF token from cookie and retry (should succeed)
csrf_token = session.cookies.get('csrftoken')
response = session.post('http://localhost:8000/api/v1/forum/topics/',
    headers={'X-CSRFToken': csrf_token},
    json={'forum_id': 1, 'subject': 'Test', 'content': 'Test'}
)
print(response.status_code)  # Should be 201 Created
```

### 3. Test Code Execution Endpoint
```bash
# BEFORE fix: Should work (VULNERABILITY)
curl -X POST http://localhost:8000/execute-code/ \
  -H "Content-Type: application/json" \
  -d '{"code": "print(\"Hello\")"}'

# AFTER fix: Should return 401 Unauthorized
curl -X POST http://localhost:8000/execute-code/ \
  -H "Content-Type: application/json" \
  -d '{"code": "print(\"Hello\")"}'
```

---

## Security Implications

### Before Fix:
- ❌ DRF browsable API vulnerable to CSRF
- ❌ Public code execution endpoint (no auth)
- ❌ Inconsistent security posture
- ❌ Violates principle of least privilege

### After Fix:
- ✅ DRF properly enforces CSRF for session auth
- ✅ JWT authentication works without CSRF (correct)
- ✅ Code execution requires authentication
- ✅ Consistent security policy across all endpoints
- ✅ Follows Django and DRF best practices

---

## DRF CSRF Documentation Reference

From [DRF Authentication Documentation](https://www.django-rest-framework.org/api-guide/authentication/#sessionauthentication):

> **SessionAuthentication**
>
> This authentication scheme uses Django's default session backend for authentication. Session authentication is appropriate for AJAX clients that are running in the same session context as your website.
>
> **CSRF validation in REST framework works slightly differently to standard Django due to the need to support both session and non-session based authentication to the same views.** This means that only authenticated requests require CSRF tokens, and anonymous requests may be sent without CSRF tokens. This behavior is not suitable for login views, which should always have CSRF validation applied.

**Key Takeaway:** DRF's SessionAuthentication **automatically handles CSRF**. Adding `@csrf_exempt` disables this protection and is incorrect for authenticated API views.

---

## Implementation Plan

### Phase 1: Remove @csrf_exempt (Estimated: 30 minutes)
1. Remove `@csrf_exempt` from all 11 DRF views
2. Test JWT authentication (should continue working)
3. Test session authentication with CSRF token

### Phase 2: Secure Code Execution Endpoint (Estimated: 1 hour)
1. Option A: Remove `execute_code_view` and use existing secure endpoint
2. Option B: Convert to DRF view with authentication
3. Add rate limiting
4. Add audit logging
5. Update frontend to use secure endpoint

### Phase 3: Consolidate Duplicates (Estimated: 1 hour)
1. Identify primary implementation
2. Update URL routing
3. Remove duplicate code
4. Update tests

### Phase 4: Documentation (Estimated: 30 minutes)
1. Update API documentation
2. Add CSRF requirements to developer docs
3. Document session vs JWT authentication differences

**Total Estimated Time:** 3 hours

---

## Files to Modify

1. ✅ `apps/api/views.py` - Remove 6 @csrf_exempt
2. ✅ `apps/api/forum_api.py` - Remove 4 @csrf_exempt (or deprecate file)
3. ✅ `apps/api/views/integrated_content.py` - Remove 1 @csrf_exempt
4. ⚠️ `apps/learning/views.py` - Remove @csrf_exempt + add authentication
5. 📝 `CLAUDE.md` - Update with CSRF documentation
6. 📝 `apps/api/urls.py` - Review routing (if consolidating duplicates)

---

## Conclusion

The current use of `@csrf_exempt` across the codebase is **fundamentally incorrect** and creates security vulnerabilities:

1. **DRF views** should rely on DRF's built-in CSRF handling via SessionAuthentication
2. **Code execution endpoint** must require authentication
3. **Duplicate implementations** should be consolidated

Removing these decorators will **improve security** while maintaining compatibility with both JWT and session-based authentication.

---

**Next Step:** Proceed with implementation and testing.

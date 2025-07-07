# Discourse SSO Integration Setup Guide

This guide explains how to set up Single Sign-On (SSO) between the Python Learning Studio Django application and a Discourse forum.

## Overview

The Python Learning Studio platform now includes comprehensive Discourse SSO integration that allows users to authenticate with the Django application and seamlessly access the associated Discourse forum without separate login.

### Key Features

- **DiscourseConnect Protocol**: Industry-standard SSO implementation
- **HMAC-SHA256 Security**: Payload signature verification for secure communication
- **User Synchronization**: Automatic user data sync between Django and Discourse
- **Group Mapping**: Map Django groups to Discourse groups for role-based access
- **Email Verification**: Ensures users have verified emails before forum access
- **Audit Logging**: Complete logging of SSO attempts for monitoring and debugging

## Architecture

### Components

1. **Django SSO Provider**: Acts as the authentication source
2. **Discourse Consumer**: Receives authentication from Django
3. **User Synchronization**: Bidirectional user data management
4. **Group Mapping**: Role synchronization between platforms

### Authentication Flow

1. User attempts to login to Discourse
2. Discourse redirects to Django SSO endpoint with signed payload
3. Django validates payload signature using shared secret
4. Django authenticates user (or redirects to login if needed)
5. Django returns signed payload with user data to Discourse
6. Discourse creates/updates user account and logs user in

## Configuration

### Django Settings

Add the following to your Django settings:

```python
# Discourse SSO Configuration
DISCOURSE_BASE_URL = config('DISCOURSE_BASE_URL', default='')
DISCOURSE_SSO_SECRET = config('DISCOURSE_SSO_SECRET', default='')
```

### Environment Variables

Add to your `.env` file:

```bash
# Discourse Integration
DISCOURSE_BASE_URL=https://your-discourse-forum.com
DISCOURSE_SSO_SECRET=your-shared-secret-key-here
```

### Discourse Configuration

In Discourse admin settings:

1. **Enable DiscourseConnect**:
   - Navigate to Admin → Settings → Login
   - Enable `enable discourse connect`

2. **Set SSO URL**:
   - Set `discourse connect url` to: `https://your-django-site.com/discourse/sso/`

3. **Configure Secret**:
   - Set `discourse connect secret` to the same value as `DISCOURSE_SSO_SECRET`

4. **Optional Settings**:
   - Enable `discourse connect overrides bio` if you want Django to control user bios
   - Enable `discourse connect overrides avatar` for avatar synchronization

## Database Models

### DiscourseUser

Tracks the relationship between Django users and Discourse users:

```python
class DiscourseUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    discourse_user_id = models.CharField(max_length=255, unique=True)
    discourse_username = models.CharField(max_length=255)
    last_sync = models.DateTimeField(auto_now=True)
    sync_enabled = models.BooleanField(default=True)
```

### DiscourseGroupMapping

Maps Django groups to Discourse groups:

```python
class DiscourseGroupMapping(models.Model):
    django_group = models.OneToOneField('auth.Group', on_delete=models.CASCADE)
    discourse_group_name = models.CharField(max_length=255)
    auto_sync = models.BooleanField(default=True)
```

### DiscourseSsoLog

Logs all SSO authentication attempts:

```python
class DiscourseSsoLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=50, choices=[...])
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
```

## API Endpoints

### SSO Authentication

- **URL**: `/discourse/sso/`
- **Method**: GET
- **Parameters**: 
  - `sso`: Base64 encoded payload from Discourse
  - `sig`: HMAC signature of the payload
- **Description**: Main SSO endpoint that Discourse calls for authentication

### SSO Status

- **URL**: `/discourse/api/status/`
- **Method**: GET
- **Description**: Returns SSO configuration status
- **Response**:
  ```json
  {
    "sso_configured": true,
    "base_url": "https://your-discourse-forum.com",
    "secret_configured": true
  }
  ```

### Manual User Sync

- **URL**: `/discourse/api/sync/`
- **Method**: POST
- **Parameters**: `user_id` (optional)
- **Description**: Manually sync a user to Discourse (admin only)

## User Flow Examples

### New User Registration

1. User registers on Django application
2. User verifies email address
3. User attempts to access Discourse
4. Discourse redirects to Django SSO
5. Django creates DiscourseUser record and returns user data
6. Discourse creates user account automatically

### Existing User Login

1. User logs into Django application
2. User clicks forum link or visits Discourse directly
3. Discourse recognizes user needs authentication
4. Django SSO returns existing user data
5. User is logged into Discourse seamlessly

### Email Verification Required

1. User attempts forum access but email is unverified
2. Django displays email verification required page
3. User verifies email through Django
4. User can then access forum successfully

## Group Synchronization

### Setting Up Group Mapping

1. **Create Django Groups**: Set up groups in Django admin (e.g., "Instructors", "Students")

2. **Create Discourse Groups**: Create corresponding groups in Discourse admin

3. **Map Groups**: Create DiscourseGroupMapping records:
   ```python
   # In Django shell or admin
   from django.contrib.auth.models import Group
   from apps.discourse_sso.models import DiscourseGroupMapping
   
   django_group = Group.objects.get(name='Instructors')
   mapping = DiscourseGroupMapping.objects.create(
       django_group=django_group,
       discourse_group_name='instructors',
       auto_sync=True
   )
   ```

### Automatic Sync

When `auto_sync=True`, user group memberships are automatically synchronized during SSO login.

## Security Considerations

### Payload Validation

- All payloads are validated using HMAC-SHA256 signatures
- Nonce values prevent replay attacks (10-minute expiration)
- Malformed or expired payloads are rejected

### User Verification

- Email verification is required before forum access
- User data is validated before synchronization
- Error conditions are logged for monitoring

### Audit Trail

- All SSO attempts are logged with timestamps
- IP addresses and user agents are recorded
- Failed attempts include error details

## Troubleshooting

### Common Issues

#### "Email Verification Required" Message

**Cause**: User's email is not verified in Django
**Solution**: 
1. User should check email for verification link
2. Or resend verification email from Django account settings

#### "Invalid payload signature" Error

**Cause**: Secret key mismatch between Django and Discourse
**Solution**: Verify `DISCOURSE_SSO_SECRET` matches in both systems

#### User Not Found in Django

**Cause**: User exists in Discourse but not in Django
**Solution**: User should register in Django first, then access forum

### Debug Mode

Enable detailed logging:

```python
import logging
logging.getLogger('apps.discourse_sso').setLevel(logging.DEBUG)
```

### Monitoring

Check SSO logs in Django admin:
- Navigate to Admin → Discourse SSO → Discourse SSO Logs
- Filter by success/failure, user, or time period
- Review error messages for failed attempts

## Advanced Configuration

### Custom User Attributes

Extend the SSO payload with additional user attributes:

```python
# In services.py - generate_return_payload method
params.update({
    'bio': user.profile.bio if hasattr(user, 'profile') else '',
    'location': user.profile.location if hasattr(user, 'profile') else '',
    'website': user.profile.website if hasattr(user, 'profile') else '',
})
```

### Custom Group Logic

Override group mapping logic:

```python
def get_user_discourse_groups(self, user):
    """Custom group assignment logic"""
    groups = []
    
    # Add all users to general group
    groups.append('general')
    
    # Add instructors to instructor group
    if user.groups.filter(name='Instructors').exists():
        groups.append('instructors')
    
    # Add students to appropriate course groups
    if hasattr(user, 'enrollments'):
        for enrollment in user.enrollments.all():
            groups.append(f"course-{enrollment.course.slug}")
    
    return groups
```

## Course-Specific Forums

To create course-specific forum categories:

### Discourse Setup

1. **Create Categories**: Create a category for each course in Discourse
2. **Set Permissions**: Restrict category access to specific groups
3. **Auto-Assignment**: Use group mapping to automatically assign users

### Django Integration

```python
# Create groups for each course
for course in Course.objects.all():
    group, created = Group.objects.get_or_create(
        name=f"Course-{course.slug}"
    )
    
    # Map to Discourse group
    DiscourseGroupMapping.objects.get_or_create(
        django_group=group,
        defaults={
            'discourse_group_name': f"course-{course.slug}",
            'auto_sync': True
        }
    )
    
    # Add enrolled users to group
    for enrollment in course.enrollments.all():
        group.user_set.add(enrollment.user)
```

## Testing

### Manual Testing

1. **Test SSO Flow**:
   - Logout from both Django and Discourse
   - Visit Discourse and click login
   - Verify redirect to Django
   - Login to Django
   - Verify redirect back to Discourse with successful login

2. **Test Group Sync**:
   - Add user to Django group
   - Login via SSO
   - Check user is added to corresponding Discourse group

3. **Test Email Verification**:
   - Create user with unverified email
   - Attempt SSO login
   - Verify email verification required message

### Automated Testing

Run the included test suite:

```bash
python manage.py test apps.discourse_sso
```

## Production Deployment

### SSL/HTTPS Required

- Both Django and Discourse must use HTTPS in production
- SSO will not work over HTTP due to security restrictions

### Environment Variables

Ensure all required environment variables are set:

```bash
DISCOURSE_BASE_URL=https://forum.yoursite.com
DISCOURSE_SSO_SECRET=your-production-secret-key
```

### Monitoring

Set up monitoring for:
- SSO success/failure rates
- User synchronization errors
- Performance metrics
- Security events

## Support and Maintenance

### Regular Tasks

1. **Monitor SSO Logs**: Review failed authentication attempts
2. **Update Group Mappings**: Add new courses/groups as needed
3. **User Cleanup**: Remove inactive user mappings
4. **Security Audits**: Regular review of SSO configuration

### Backup Considerations

- Include `DiscourseUser` mappings in database backups
- Document group mapping configuration
- Backup SSO configuration settings

## Conclusion

The Discourse SSO integration provides seamless authentication between the Python Learning Studio and its associated forum, creating a unified user experience while maintaining security best practices. The comprehensive logging and monitoring capabilities ensure reliable operation and easy troubleshooting.

For additional support or custom requirements, refer to the Django application documentation or contact the development team.
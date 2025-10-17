# Fix Path Traversal in Avatar File Uploads

**Priority**: 🟡 P1 - HIGH
**Category**: Security
**Effort**: 2-3 hours
**Deadline**: Within 1 week

## Problem

Avatar uploads use user-controlled filenames without sanitization, allowing path traversal attacks that could overwrite system files or access restricted directories.

## Location

`apps/users/models.py:16`

## Current Code

```python
avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
```

## Attack Vector

```python
# Attacker uploads file with malicious filename:
filename = "../../etc/passwd"
# Or:
filename = "../../../var/www/static/malicious.php"
# Django processes without validation, potentially allowing:
# - Directory traversal
# - File overwrite
# - Information disclosure
```

## Impact

- **Directory Traversal**: Access files outside upload directory
- **File Overwrite**: Overwrite application files or static assets
- **Disk Exhaustion**: Filename collisions cause repeated uploads
- **Information Disclosure**: Predictable filenames leak user info
- **Malicious Files**: Upload executable code to web-accessible directories

## Solution

Implement safe filename generation using UUID and proper path sanitization.

## Implementation Steps

### Step 1: Create Safe Upload Path Function

```python
# apps/users/utils.py
import uuid
import os
from pathlib import Path
from django.utils.text import slugify


def avatar_upload_path(instance, filename):
    """
    Generate a safe, unique filename for avatar uploads.

    Args:
        instance: UserProfile instance
        filename: Original filename from upload

    Returns:
        Safe path string like: avatars/123/a1b2c3d4-e5f6.jpg
    """
    # Extract and validate file extension
    ext = Path(filename).suffix.lower()

    # Whitelist allowed extensions
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    if ext not in allowed_extensions:
        # Default to .jpg if invalid extension
        ext = '.jpg'

    # Generate unique filename with UUID
    unique_filename = f"{uuid.uuid4()}{ext}"

    # Organize by user ID for better filesystem organization
    # Format: avatars/{user_id}/{uuid}.{ext}
    return os.path.join('avatars', str(instance.user.id), unique_filename)


def validate_avatar_size(image):
    """
    Validate avatar file size.

    Args:
        image: ImageField file

    Raises:
        ValidationError: If file too large
    """
    from django.core.exceptions import ValidationError

    # Max size: 5MB
    max_size = 5 * 1024 * 1024  # 5MB in bytes

    if image.size > max_size:
        raise ValidationError(
            f'Avatar file size cannot exceed 5MB. '
            f'Current size: {image.size / (1024 * 1024):.2f}MB'
        )


def validate_avatar_dimensions(image):
    """
    Validate avatar image dimensions.

    Args:
        image: ImageField file

    Raises:
        ValidationError: If dimensions too large
    """
    from django.core.exceptions import ValidationError
    from PIL import Image

    # Max dimensions: 2000x2000
    max_width = 2000
    max_height = 2000

    try:
        img = Image.open(image)
        width, height = img.size

        if width > max_width or height > max_height:
            raise ValidationError(
                f'Avatar dimensions cannot exceed {max_width}x{max_height}. '
                f'Current dimensions: {width}x{height}'
            )
    except Exception as e:
        raise ValidationError(f'Invalid image file: {str(e)}')
```

### Step 2: Update UserProfile Model

```python
# apps/users/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from apps.users.utils import (
    avatar_upload_path,
    validate_avatar_size,
    validate_avatar_dimensions
)

User = get_user_model()


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    bio = models.TextField(blank=True, max_length=500)

    avatar = models.ImageField(
        upload_to=avatar_upload_path,  # Safe path function
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp']
            ),
            validate_avatar_size,
            validate_avatar_dimensions,
        ],
        help_text='Profile picture (max 5MB, 2000x2000px, jpg/png/gif/webp)'
    )

    # ... other fields

    def save(self, *args, **kwargs):
        # Delete old avatar when new one is uploaded
        if self.pk:
            try:
                old_avatar = UserProfile.objects.get(pk=self.pk).avatar
                if old_avatar and self.avatar != old_avatar:
                    # Delete old file from storage
                    old_avatar.delete(save=False)
            except UserProfile.DoesNotExist:
                pass

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Delete avatar file when profile is deleted
        if self.avatar:
            self.avatar.delete(save=False)
        super().delete(*args, **kwargs)
```

### Step 3: Create Migration

```bash
# Create migration
DJANGO_SETTINGS_MODULE=learning_community.settings.development python manage.py makemigrations users --name fix_avatar_upload_security

# Review migration
cat apps/users/migrations/00XX_fix_avatar_upload_security.py
```

### Step 4: Add Data Migration for Existing Avatars

```python
# apps/users/migrations/00XX_migrate_existing_avatars.py
from django.db import migrations
import uuid
import os


def migrate_existing_avatars(apps, schema_editor):
    """
    Rename existing avatar files to use UUID naming.
    This prevents path traversal on old uploads.
    """
    UserProfile = apps.get_model('users', 'UserProfile')

    for profile in UserProfile.objects.exclude(avatar=''):
        if profile.avatar:
            old_path = profile.avatar.path
            old_name = profile.avatar.name

            # Generate new safe filename
            ext = os.path.splitext(old_name)[1].lower()
            new_name = f"avatars/{profile.user.id}/{uuid.uuid4()}{ext}"

            # Update in database
            profile.avatar.name = new_name
            profile.save(update_fields=['avatar'])

            # Rename file on disk
            try:
                new_path = os.path.join(
                    os.path.dirname(os.path.dirname(old_path)),
                    new_name
                )
                os.makedirs(os.path.dirname(new_path), exist_ok=True)
                os.rename(old_path, new_path)
            except Exception as e:
                print(f"Failed to migrate avatar for user {profile.user.id}: {e}")


class Migration(migrations.Migration):
    dependencies = [
        ('users', '00XX_fix_avatar_upload_security'),
    ]

    operations = [
        migrations.RunPython(
            migrate_existing_avatars,
            reverse_code=migrations.RunPython.noop
        ),
    ]
```

### Step 5: Update API View/Serializer

```python
# apps/api/serializers.py
from rest_framework import serializers
from apps.users.models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['id', 'bio', 'avatar', 'avatar_url']
        extra_kwargs = {
            'avatar': {'write_only': True}
        }

    def get_avatar_url(self, obj):
        """Return full URL for avatar"""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None

    def validate_avatar(self, value):
        """Additional validation for avatar upload"""
        # File size already validated by model validator
        # But we can add extra checks here if needed

        # Check file type by reading magic bytes
        from PIL import Image
        try:
            img = Image.open(value)
            img.verify()  # Verify it's a valid image
        except Exception:
            raise serializers.ValidationError(
                'Invalid image file. Please upload a valid JPG, PNG, GIF, or WebP image.'
            )

        return value
```

### Step 6: Configure Media File Serving

```python
# learning_community/settings/base.py

# Media files (user uploads)
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# Security settings for file uploads
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
FILE_UPLOAD_PERMISSIONS = 0o644  # Read for all, write for owner
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755


# In production, serve media files via CDN/S3, not Django
# learning_community/settings/production.py
if not DEBUG:
    # Use S3 for media files in production
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
```

### Step 7: Add Cleanup Task for Orphaned Files

```python
# apps/users/management/commands/cleanup_orphaned_avatars.py
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.users.models import UserProfile
import os


class Command(BaseCommand):
    help = 'Remove orphaned avatar files not linked to any profile'

    def handle(self, *args, **options):
        avatars_dir = os.path.join(settings.MEDIA_ROOT, 'avatars')

        if not os.path.exists(avatars_dir):
            self.stdout.write('No avatars directory found')
            return

        # Get all avatar files in database
        db_avatars = set(
            profile.avatar.name
            for profile in UserProfile.objects.exclude(avatar='')
        )

        # Find orphaned files
        orphaned = []
        for root, dirs, files in os.walk(avatars_dir):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, settings.MEDIA_ROOT)

                if relative_path not in db_avatars:
                    orphaned.append(file_path)

        # Delete orphaned files
        for file_path in orphaned:
            try:
                os.remove(file_path)
                self.stdout.write(f'Deleted: {file_path}')
            except Exception as e:
                self.stderr.write(f'Failed to delete {file_path}: {e}')

        self.stdout.write(
            self.style.SUCCESS(f'Cleaned up {len(orphaned)} orphaned files')
        )
```

## Testing

```python
# tests/test_avatar_security.py
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from apps.users.models import UserProfile, User
from PIL import Image
import io


class AvatarSecurityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@test.com',
            password='password123'
        )
        self.profile = UserProfile.objects.create(user=self.user)

    def create_test_image(self, size=(100, 100)):
        """Helper to create test image"""
        file = io.BytesIO()
        image = Image.new('RGB', size, color='red')
        image.save(file, 'JPEG')
        file.seek(0)
        return SimpleUploadedFile(
            'test.jpg',
            file.read(),
            content_type='image/jpeg'
        )

    def test_safe_filename_generated(self):
        """Ensure uploaded files get UUID filenames"""
        image = self.create_test_image()
        self.profile.avatar = image
        self.profile.save()

        # Filename should be UUID-based, not original name
        self.assertNotIn('test.jpg', self.profile.avatar.name)
        self.assertIn('avatars/', self.profile.avatar.name)
        self.assertIn(str(self.user.id), self.profile.avatar.name)

    def test_path_traversal_blocked(self):
        """Ensure path traversal attempts are blocked"""
        # Try malicious filename
        malicious_image = self.create_test_image()
        malicious_image.name = '../../etc/passwd'

        self.profile.avatar = malicious_image
        self.profile.save()

        # Should not contain path traversal
        self.assertNotIn('..', self.profile.avatar.name)
        self.assertNotIn('/etc/', self.profile.avatar.name)

    def test_invalid_extension_rejected(self):
        """Ensure non-image files are rejected"""
        # Try uploading .exe file
        malicious_file = SimpleUploadedFile(
            'malware.exe',
            b'MZ\x90\x00',  # PE header
            content_type='application/x-msdownload'
        )

        self.profile.avatar = malicious_file

        with self.assertRaises(ValidationError):
            self.profile.full_clean()

    def test_file_size_limit_enforced(self):
        """Ensure files over 5MB are rejected"""
        # Create 6MB file
        large_image = self.create_test_image(size=(5000, 5000))

        self.profile.avatar = large_image

        with self.assertRaises(ValidationError) as context:
            self.profile.full_clean()

        self.assertIn('5MB', str(context.exception))

    def test_dimensions_limit_enforced(self):
        """Ensure images over 2000x2000 are rejected"""
        # Create 3000x3000 image
        large_image = self.create_test_image(size=(3000, 3000))

        self.profile.avatar = large_image

        with self.assertRaises(ValidationError) as context:
            self.profile.full_clean()

        self.assertIn('2000', str(context.exception))

    def test_old_avatar_deleted_on_new_upload(self):
        """Ensure old avatar is deleted when new one uploaded"""
        # Upload first avatar
        image1 = self.create_test_image()
        self.profile.avatar = image1
        self.profile.save()
        old_path = self.profile.avatar.path

        # Upload second avatar
        image2 = self.create_test_image()
        self.profile.avatar = image2
        self.profile.save()

        # Old file should be deleted
        import os
        self.assertFalse(os.path.exists(old_path))
```

## Verification Checklist

- [ ] Safe upload path function created with UUID
- [ ] UserProfile model updated with validators
- [ ] File extension whitelist enforced
- [ ] File size limit enforced (5MB)
- [ ] Image dimensions limit enforced (2000x2000)
- [ ] Data migration created for existing files
- [ ] Old avatar cleanup on new upload
- [ ] Orphaned file cleanup command created
- [ ] Security tests added and passing
- [ ] Manual testing with malicious filenames

## Manual Testing

```bash
# Test with curl
curl -X PATCH http://localhost:8000/api/v1/users/profile/ \
  -H "Authorization: Bearer <token>" \
  -F "avatar=@malicious_../../etc/passwd.jpg"

# Verify saved filename is UUID-based
ls media/avatars/*/

# Should see UUID filenames only
```

## References

- OWASP: Path Traversal
- CWE-22: Improper Limitation of a Pathname to a Restricted Directory
- Django File Uploads: https://docs.djangoproject.com/en/stable/topics/http/file-uploads/
- Comprehensive Security Audit 2025, Finding #8

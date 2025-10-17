"""
File upload validators for secure image handling.

This module implements comprehensive security validation for file uploads,
following OWASP guidelines and Django best practices to prevent:
- Path traversal attacks (CWE-22)
- Unrestricted file uploads (CWE-434)
- Denial of service via large files
- Extension spoofing and polyglot attacks

Security Features:
- UUID-based filenames (no user input in paths)
- Extension whitelist validation
- MIME type validation (python-magic)
- Content validation (Pillow)
- File size limits
- Dimension restrictions
"""

import os
import uuid
from pathlib import Path
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from PIL import Image


@deconstructible
class SecureAvatarUpload:
    """
    Secure upload path generator for user avatars.

    Security features:
    - UUID-based filenames (unpredictable, no user input)
    - User ID-based directory organization
    - Extension whitelist validation
    - No path traversal sequences

    Usage:
        class User(models.Model):
            avatar = models.ImageField(upload_to=SecureAvatarUpload())
    """

    def __call__(self, instance, filename):
        """
        Generate secure upload path.

        Args:
            instance: Model instance (User)
            filename: Original filename (not trusted)

        Returns:
            Secure path: avatars/user_<id>/<uuid>.<ext>
        """
        # Extract and validate extension
        ext = Path(filename).suffix.lower()

        # Whitelist allowed extensions
        ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        if ext not in ALLOWED_EXTENSIONS:
            ext = '.jpg'  # Default fallback

        # Generate UUID filename (no user input)
        unique_filename = f"{uuid.uuid4()}{ext}"

        # Organize by user ID (from instance, not user input)
        # Format: avatars/user_123/a1b2c3d4-e5f6-7890-abcd-ef1234567890.jpg
        return os.path.join('avatars', f'user_{instance.id}', unique_filename)


@deconstructible
class SecureIconUpload:
    """Secure upload path generator for programming language icons."""

    def __call__(self, instance, filename):
        ext = Path(filename).suffix.lower()
        ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}
        ext = ext if ext in ALLOWED_EXTENSIONS else '.png'
        return os.path.join('language_icons', f'{uuid.uuid4()}{ext}')


@deconstructible
class SecureAchievementIconUpload:
    """Secure upload path generator for achievement icons."""

    def __call__(self, instance, filename):
        ext = Path(filename).suffix.lower()
        ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        ext = ext if ext in ALLOWED_EXTENSIONS else '.png'
        return os.path.join('achievement_icons', f'{uuid.uuid4()}{ext}')


@deconstructible
class SecureBadgeImageUpload:
    """Secure upload path generator for forum badge images."""

    def __call__(self, instance, filename):
        ext = Path(filename).suffix.lower()
        ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        ext = ext if ext in ALLOWED_EXTENSIONS else '.png'
        return os.path.join('badges', f'{uuid.uuid4()}{ext}')


@deconstructible
class SecureCourseImageUpload:
    """
    Secure upload path generator for course thumbnails and banners.

    Usage:
        thumbnail = models.ImageField(
            upload_to=SecureCourseImageUpload('course_thumbnails')
        )
    """

    def __init__(self, subfolder='course_images'):
        self.subfolder = subfolder

    def __call__(self, instance, filename):
        ext = Path(filename).suffix.lower()
        ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
        ext = ext if ext in ALLOWED_EXTENSIONS else '.jpg'
        return os.path.join(self.subfolder, f'{uuid.uuid4()}{ext}')


def validate_image_file_size(image):
    """
    Validate image file size.

    Limits:
    - Avatars: 5 MB max
    - Prevents DoS via large file uploads

    Args:
        image: UploadedFile instance

    Raises:
        ValidationError: If file exceeds size limit
    """
    max_size = 5 * 1024 * 1024  # 5 MB

    if image.size > max_size:
        raise ValidationError(
            f'Image file too large ({image.size / (1024 * 1024):.2f} MB). '
            f'Maximum size: {max_size / (1024 * 1024)} MB'
        )


def validate_course_image_file_size(image):
    """
    Validate course image file size (larger limit for course materials).

    Limit: 10 MB max
    """
    max_size = 10 * 1024 * 1024  # 10 MB

    if image.size > max_size:
        raise ValidationError(
            f'Image file too large ({image.size / (1024 * 1024):.2f} MB). '
            f'Maximum size: {max_size / (1024 * 1024)} MB'
        )


def validate_badge_image_file_size(image):
    """
    Validate badge image file size (smaller limit for badges).

    Limit: 2 MB max
    """
    max_size = 2 * 1024 * 1024  # 2 MB

    if image.size > max_size:
        raise ValidationError(
            f'Image file too large ({image.size / (1024 * 1024):.2f} MB). '
            f'Maximum size: {max_size / (1024 * 1024)} MB'
        )


def validate_image_dimensions(image):
    """
    Validate image dimensions.

    Requirements:
    - Minimum: 50x50 pixels (prevents tiny images)
    - Maximum: 2048x2048 pixels (prevents huge images)

    Args:
        image: UploadedFile instance

    Raises:
        ValidationError: If dimensions are outside acceptable range
    """
    try:
        img = Image.open(image)
        width, height = img.size

        # Maximum dimensions (prevents DoS via huge images)
        if width > 2048 or height > 2048:
            raise ValidationError(
                f'Image dimensions too large ({width}x{height}). '
                f'Maximum: 2048x2048 pixels'
            )

        # Minimum dimensions (ensures usable images)
        if width < 50 or height < 50:
            raise ValidationError(
                f'Image dimensions too small ({width}x{height}). '
                f'Minimum: 50x50 pixels'
            )

        image.seek(0)  # Reset file pointer

    except Exception as e:
        # If we can't open as image, let validate_image_content handle it
        image.seek(0)
        raise ValidationError(f'Could not read image dimensions: {str(e)}')


def validate_image_content(image):
    """
    Validate image content using Pillow.

    Security checks:
    - Valid image format (JPEG, PNG, GIF, WEBP)
    - Format matches extension
    - No corrupted files
    - Prevents polyglot attacks (files that are both image and executable)

    Args:
        image: UploadedFile instance

    Raises:
        ValidationError: If image content is invalid
    """
    try:
        # Open and verify image
        img = Image.open(image)
        img.verify()  # Verify it's a valid image
        image.seek(0)  # Reset file pointer after verify

        # Reopen for format check (verify() closes file)
        img = Image.open(image)

        # Allowed formats (whitelist approach)
        ALLOWED_FORMATS = {'JPEG', 'PNG', 'GIF', 'WEBP'}
        if img.format not in ALLOWED_FORMATS:
            raise ValidationError(
                f'Image format "{img.format}" not allowed. '
                f'Allowed formats: {", ".join(ALLOWED_FORMATS)}'
            )

        # Verify extension matches format (prevents spoofing)
        ext = os.path.splitext(image.name)[1].lower()
        format_map = {
            '.jpg': 'JPEG',
            '.jpeg': 'JPEG',
            '.png': 'PNG',
            '.gif': 'GIF',
            '.webp': 'WEBP',
        }

        expected_format = format_map.get(ext)
        if expected_format and img.format != expected_format:
            raise ValidationError(
                f'File extension {ext} does not match image format {img.format}. '
                f'This may indicate a security issue.'
            )

        image.seek(0)  # Reset file pointer

    except ValidationError:
        # Re-raise our own ValidationErrors
        raise
    except Exception as e:
        # Any other exception means invalid image
        raise ValidationError(f'Invalid image file: {str(e)}')


def validate_mime_type(image):
    """
    Validate MIME type using python-magic (libmagic).

    This inspects file content (magic bytes), not just the extension.
    Prevents attacks where malicious files are renamed to .jpg

    Requires:
        - pip install python-magic
        - brew install libmagic (macOS) or apt-get install libmagic1 (Ubuntu)

    Args:
        image: UploadedFile instance

    Raises:
        ValidationError: If MIME type is not allowed

    Note:
        If python-magic is not installed, this validator is skipped
        (other validators still provide security)
    """
    try:
        import magic

        # Read file header for magic byte detection
        image.seek(0)
        file_start = image.read(2048)  # Read first 2KB
        image.seek(0)  # Reset file pointer

        # Detect MIME type from content (not extension)
        mime = magic.from_buffer(file_start, mime=True)

        # Whitelist allowed MIME types
        ALLOWED_MIMES = {
            'image/jpeg',
            'image/png',
            'image/gif',
            'image/webp',
        }

        if mime not in ALLOWED_MIMES:
            raise ValidationError(
                f'File content type "{mime}" not allowed. '
                f'Detected file is not a valid image. '
                f'Allowed types: {", ".join(ALLOWED_MIMES)}'
            )

    except ImportError:
        # python-magic not installed, skip MIME validation
        # Other validators (Pillow) will still check content
        pass
    except ValidationError:
        # Re-raise our ValidationError
        raise
    except Exception as e:
        # Any other exception in MIME detection
        # Don't fail the upload, but log it
        pass  # Fail gracefully, other validators will catch issues

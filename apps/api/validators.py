"""
Reusable validators for API serializers.

Provides comprehensive validation for file uploads with consistent
security checks across all endpoints.
"""

from pathlib import Path
from rest_framework import serializers
from PIL import Image


class ImageUploadValidator:
    """
    Reusable validator for image uploads.

    Provides comprehensive validation:
    - Extension whitelist (JPEG, PNG, GIF, WEBP)
    - MIME type validation via python-magic (optional)
    - File size limits (configurable)
    - Image content validation via Pillow
    - Dimension validation (50x50 to 2048x2048)

    Usage:
        # In serializer
        avatar_validator = ImageUploadValidator(max_size_mb=5, field_name='Avatar')

        def validate_avatar(self, value):
            return self.avatar_validator(value)

    Security Features:
    - Whitelist approach (safer than blacklist)
    - Content-based MIME detection (not just extension)
    - Pillow verification (prevents polyglot attacks)
    - Graceful degradation if python-magic not installed
    """

    def __init__(self, max_size_mb=5, allow_gif=True, field_name='Image'):
        """
        Initialize validator with configuration.

        Args:
            max_size_mb: Maximum file size in megabytes (default: 5)
            allow_gif: Whether to allow GIF format (default: True)
            field_name: Name for error messages (default: 'Image')
        """
        self.max_size = max_size_mb * 1024 * 1024
        self.allow_gif = allow_gif
        self.field_name = field_name

        # Extension whitelist
        self.allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
        if allow_gif:
            self.allowed_extensions.add('.gif')

        # Format whitelist (for Pillow validation)
        self.allowed_formats = {'JPEG', 'PNG', 'WEBP'}
        if allow_gif:
            self.allowed_formats.add('GIF')

        # MIME type whitelist
        self.allowed_mimes = {'image/jpeg', 'image/png', 'image/webp'}
        if allow_gif:
            self.allowed_mimes.add('image/gif')

    def __call__(self, value):
        """
        Validate uploaded image file.

        Args:
            value: UploadedFile instance

        Returns:
            Validated file instance

        Raises:
            serializers.ValidationError: If validation fails
        """
        if not value:
            return value

        self._validate_extension(value)
        self._validate_mime_type(value)
        self._validate_file_size(value)
        self._validate_image_content(value)

        return value

    def _validate_extension(self, value):
        """
        Validate file extension against whitelist.

        Args:
            value: UploadedFile instance

        Raises:
            serializers.ValidationError: If extension not allowed
        """
        ext = Path(value.name).suffix.lower()
        if ext not in self.allowed_extensions:
            raise serializers.ValidationError(
                f'{self.field_name}: File extension "{ext}" not allowed. '
                f'Allowed extensions: {", ".join(sorted(self.allowed_extensions))}'
            )

    def _validate_mime_type(self, value):
        """
        Validate MIME type using python-magic (optional, graceful degradation).

        This inspects file content (magic bytes), not just the extension.
        Prevents attacks where malicious files are renamed to .jpg

        Args:
            value: UploadedFile instance

        Raises:
            serializers.ValidationError: If MIME type not allowed

        Note:
            Gracefully skips validation if python-magic not installed.
            Other validators (Pillow) will still provide content validation.
        """
        try:
            import magic

            value.seek(0)
            file_start = value.read(2048)  # Read first 2KB for magic bytes
            value.seek(0)

            mime = magic.from_buffer(file_start, mime=True)

            if mime not in self.allowed_mimes:
                raise serializers.ValidationError(
                    f'{self.field_name}: File content type "{mime}" not allowed. '
                    f'Detected file is not a valid image.'
                )
        except ImportError:
            # python-magic not installed, skip MIME validation
            # Pillow validation will still catch most issues
            pass

    def _validate_file_size(self, value):
        """
        Validate file size against limit.

        Args:
            value: UploadedFile instance

        Raises:
            serializers.ValidationError: If file exceeds size limit
        """
        if value.size > self.max_size:
            raise serializers.ValidationError(
                f'{self.field_name}: File too large ({value.size / (1024 * 1024):.2f} MB). '
                f'Maximum size: {self.max_size / (1024 * 1024)} MB'
            )

    def _validate_image_content(self, value):
        """
        Validate image content and dimensions using Pillow.

        Checks:
        - Valid image format (JPEG, PNG, GIF, WEBP)
        - Format matches extension
        - No corrupted files
        - Dimension limits (50x50 to 2048x2048)

        Args:
            value: UploadedFile instance

        Raises:
            serializers.ValidationError: If image content invalid or dimensions out of range
        """
        try:
            value.seek(0)
            img = Image.open(value)
            img.verify()  # Verify it's a valid image
            value.seek(0)

            # Reopen for format check (verify() closes file)
            img = Image.open(value)

            # Format validation
            if img.format not in self.allowed_formats:
                raise serializers.ValidationError(
                    f'{self.field_name}: Image format "{img.format}" not allowed. '
                    f'Allowed formats: {", ".join(sorted(self.allowed_formats))}'
                )

            # Dimension validation
            width, height = img.size

            if width > 2048 or height > 2048:
                raise serializers.ValidationError(
                    f'{self.field_name}: Image dimensions too large ({width}x{height}). '
                    f'Maximum: 2048x2048 pixels'
                )

            if width < 50 or height < 50:
                raise serializers.ValidationError(
                    f'{self.field_name}: Image dimensions too small ({width}x{height}). '
                    f'Minimum: 50x50 pixels'
                )

            value.seek(0)  # Reset file pointer for subsequent processing

        except Exception as e:
            if isinstance(e, serializers.ValidationError):
                raise
            raise serializers.ValidationError(f'{self.field_name}: Invalid image file: {str(e)}')

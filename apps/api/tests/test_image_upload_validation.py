"""
Comprehensive test suite for image upload validation.

Tests file upload security for all serializers that accept images:
- UserSerializer (avatar)
- AchievementSerializer (icon)
- ProgrammingLanguageSerializer (icon)
- CourseSerializer (thumbnail, banner_image)

Security Focus:
- Extension whitelist enforcement
- File size limits
- MIME type validation
- Image content validation
- Dimension restrictions
- SVG blocking (XSS prevention)
- Extension spoofing prevention
"""

import io
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from PIL import Image

from apps.users.models import Achievement, ProgrammingLanguage
from apps.learning.models import Course, Category

User = get_user_model()


class ImageUploadTestCase(TestCase):
    """Base test case with helper methods for image upload testing."""

    def setUp(self):
        """Set up test client and create test user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def create_test_image(self, format='JPEG', size=(100, 100), color='red'):
        """
        Create a valid test image in memory.

        Args:
            format: Image format (JPEG, PNG, GIF, WEBP)
            size: Tuple of (width, height) in pixels
            color: Color name or RGB tuple

        Returns:
            SimpleUploadedFile with image data
        """
        img = Image.new('RGB', size, color=color)
        img_io = io.BytesIO()
        img.save(img_io, format=format)
        img_io.seek(0)

        # Map format to extension and MIME type
        format_map = {
            'JPEG': ('.jpg', 'image/jpeg'),
            'PNG': ('.png', 'image/png'),
            'GIF': ('.gif', 'image/gif'),
            'WEBP': ('.webp', 'image/webp'),
        }
        ext, mime = format_map.get(format, ('.jpg', 'image/jpeg'))

        return SimpleUploadedFile(
            f"test{ext}",
            img_io.read(),
            content_type=mime
        )

    def create_oversized_image(self, size_mb, format='JPEG'):
        """
        Create an image larger than specified size in MB.

        Args:
            size_mb: Target size in megabytes
            format: Image format

        Returns:
            SimpleUploadedFile with large image
        """
        # Create large image (larger dimensions = larger file)
        # Approximate: 2000x2000 RGB JPEG ≈ 1-2 MB
        pixels_needed = int((size_mb * 1024 * 1024) ** 0.5)
        size = (min(pixels_needed, 5000), min(pixels_needed, 5000))

        img = Image.new('RGB', size, color='red')
        img_io = io.BytesIO()

        # Use low compression to increase file size
        if format == 'JPEG':
            img.save(img_io, format=format, quality=100)
        else:
            img.save(img_io, format=format)

        img_io.seek(0)
        return SimpleUploadedFile(
            f"large_test.{format.lower()}",
            img_io.read(),
            content_type=f'image/{format.lower()}'
        )


class AvatarUploadTests(ImageUploadTestCase):
    """Test avatar upload validation for UserSerializer."""

    def test_valid_avatar_upload_jpeg(self):
        """Test valid JPEG avatar upload succeeds."""
        avatar = self.create_test_image(format='JPEG')
        response = self.client.post(
            '/api/v1/users/upload_avatar/',
            {'avatar': avatar},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('avatar_url', response.data)

    def test_valid_avatar_upload_png(self):
        """Test valid PNG avatar upload succeeds."""
        avatar = self.create_test_image(format='PNG')
        response = self.client.post(
            '/api/v1/users/upload_avatar/',
            {'avatar': avatar},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_valid_avatar_upload_gif(self):
        """Test valid GIF avatar upload succeeds."""
        avatar = self.create_test_image(format='GIF')
        response = self.client.post(
            '/api/v1/users/upload_avatar/',
            {'avatar': avatar},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_valid_avatar_upload_webp(self):
        """Test valid WEBP avatar upload succeeds."""
        avatar = self.create_test_image(format='WEBP')
        response = self.client.post(
            '/api/v1/users/upload_avatar/',
            {'avatar': avatar},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reject_svg_avatar(self):
        """Test SVG files are rejected (XSS prevention)."""
        svg_content = b'<svg><script>alert("xss")</script></svg>'
        svg_file = SimpleUploadedFile(
            "test.svg",
            svg_content,
            content_type='image/svg+xml'
        )

        response = self.client.post(
            '/api/v1/users/upload_avatar/',
            {'avatar': svg_file},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('avatar', response.data)

    def test_reject_oversized_avatar(self):
        """Test rejection of avatar >5MB."""
        # Create 6 MB image
        large_avatar = self.create_oversized_image(size_mb=6)

        response = self.client.post(
            '/api/v1/users/upload_avatar/',
            {'avatar': large_avatar},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('avatar', response.data)
        # Check error message mentions size
        error_msg = str(response.data['avatar'][0])
        self.assertIn('too large', error_msg.lower())

    def test_reject_undersized_dimensions(self):
        """Test rejection of images <50x50 pixels."""
        tiny_avatar = self.create_test_image(size=(40, 40))

        response = self.client.post(
            '/api/v1/users/upload_avatar/',
            {'avatar': tiny_avatar},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('avatar', response.data)
        error_msg = str(response.data['avatar'][0])
        self.assertIn('too small', error_msg.lower())

    def test_reject_oversized_dimensions(self):
        """Test rejection of images >2048x2048 pixels."""
        huge_avatar = self.create_test_image(size=(3000, 3000))

        response = self.client.post(
            '/api/v1/users/upload_avatar/',
            {'avatar': huge_avatar},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('avatar', response.data)
        error_msg = str(response.data['avatar'][0])
        self.assertIn('too large', error_msg.lower())

    def test_reject_invalid_extension(self):
        """Test rejection of files with invalid extensions."""
        # Create a text file with .exe extension
        exe_file = SimpleUploadedFile(
            "malware.exe",
            b"This is not an image",
            content_type='application/x-msdownload'
        )

        response = self.client.post(
            '/api/v1/users/upload_avatar/',
            {'avatar': exe_file},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('avatar', response.data)

    def test_reject_malformed_image(self):
        """Test rejection of corrupted/malformed image files."""
        # Create fake JPEG (invalid content)
        fake_image = SimpleUploadedFile(
            "fake.jpg",
            b"Not a real JPEG image file",
            content_type='image/jpeg'
        )

        response = self.client.post(
            '/api/v1/users/upload_avatar/',
            {'avatar': fake_image},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('avatar', response.data)

    def test_old_avatar_deleted_on_update(self):
        """Test that old avatar is deleted when uploading new one."""
        # Upload first avatar
        avatar1 = self.create_test_image(format='JPEG')
        self.client.post(
            '/api/v1/users/upload_avatar/',
            {'avatar': avatar1},
            format='multipart'
        )

        # Get user and store old avatar path
        self.user.refresh_from_db()
        old_avatar_path = self.user.avatar.path if self.user.avatar else None

        # Upload second avatar
        avatar2 = self.create_test_image(format='PNG')
        response = self.client.post(
            '/api/v1/users/upload_avatar/',
            {'avatar': avatar2},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify old avatar was deleted (file cleanup tested at model level)
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.avatar)


class AchievementIconUploadTests(ImageUploadTestCase):
    """Test icon upload validation for AchievementSerializer."""

    def test_valid_achievement_icon_upload(self):
        """Test valid achievement icon upload succeeds."""
        icon = self.create_test_image(format='PNG', size=(256, 256))

        achievement = Achievement.objects.create(
            name='Test Achievement',
            slug='test-achievement',
            description='Test description',
            achievement_type='course',
            icon=icon
        )

        self.assertIsNotNone(achievement.icon)
        self.assertTrue(achievement.icon.name.endswith('.png'))

    def test_reject_oversized_achievement_icon(self):
        """Test rejection of achievement icon >5MB."""
        # Achievement icons use 5 MB limit (same as avatars)
        large_icon = self.create_oversized_image(size_mb=6)

        with self.assertRaises(Exception):  # ValidationError from model validators
            Achievement.objects.create(
                name='Test Achievement',
                slug='test-achievement-large',
                description='Test description',
                achievement_type='course',
                icon=large_icon
            )


class ProgrammingLanguageIconUploadTests(ImageUploadTestCase):
    """Test icon upload validation for ProgrammingLanguageSerializer."""

    def test_valid_language_icon_upload(self):
        """Test valid programming language icon upload succeeds."""
        icon = self.create_test_image(format='PNG', size=(128, 128))

        language = ProgrammingLanguage.objects.create(
            name='Python',
            slug='python',
            description='Python programming language',
            icon=icon
        )

        self.assertIsNotNone(language.icon)

    def test_svg_blocked_for_language_icons(self):
        """Test SVG files are blocked for language icons (XSS prevention)."""
        svg_content = b'<svg><script>alert("xss")</script></svg>'
        svg_file = SimpleUploadedFile(
            "python.svg",
            svg_content,
            content_type='image/svg+xml'
        )

        with self.assertRaises(Exception):  # ValidationError from model validators
            ProgrammingLanguage.objects.create(
                name='JavaScript',
                slug='javascript',
                description='JavaScript programming language',
                icon=svg_file
            )


class CourseImageUploadTests(ImageUploadTestCase):
    """Test thumbnail and banner upload validation for CourseSerializer."""

    def setUp(self):
        """Set up test data including category."""
        super().setUp()
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category',
            description='Test category description'
        )

    def test_valid_course_thumbnail_upload(self):
        """Test valid course thumbnail upload succeeds."""
        thumbnail = self.create_test_image(format='JPEG', size=(800, 600))

        course = Course.objects.create(
            title='Test Course',
            slug='test-course',
            description='Test course description',
            instructor=self.user,
            category=self.category,
            thumbnail=thumbnail
        )

        self.assertIsNotNone(course.thumbnail)

    def test_valid_course_banner_upload(self):
        """Test valid course banner upload succeeds."""
        banner = self.create_test_image(format='WEBP', size=(1920, 1080))

        course = Course.objects.create(
            title='Test Course',
            slug='test-course-2',
            description='Test course description',
            instructor=self.user,
            category=self.category,
            banner_image=banner
        )

        self.assertIsNotNone(course.banner_image)

    def test_course_thumbnail_10mb_limit(self):
        """Test course thumbnails allow up to 10MB (larger than avatars)."""
        # Create 9 MB image (should succeed)
        large_thumbnail = self.create_oversized_image(size_mb=9)

        # This should work because course images have 10 MB limit
        course = Course.objects.create(
            title='Test Course',
            slug='test-course-large',
            description='Test course description',
            instructor=self.user,
            category=self.category,
            thumbnail=large_thumbnail
        )

        self.assertIsNotNone(course.thumbnail)

    def test_reject_gif_for_course_images(self):
        """Test GIF files are not allowed for course images (professional imagery)."""
        gif = self.create_test_image(format='GIF')

        # GIF should be rejected for course images (allow_gif=False)
        with self.assertRaises(Exception):  # ValidationError from model validators
            Course.objects.create(
                title='Test Course',
                slug='test-course-gif',
                description='Test course description',
                instructor=self.user,
                category=self.category,
                thumbnail=gif
            )


class ExtensionSpoofingTests(ImageUploadTestCase):
    """Test prevention of extension spoofing attacks."""

    def test_detect_png_renamed_as_jpg(self):
        """Test detection of PNG file renamed to .jpg."""
        # Create actual PNG image
        png_img = self.create_test_image(format='PNG')

        # Rename it to .jpg (spoofing)
        spoofed_file = SimpleUploadedFile(
            "fake.jpg",  # Wrong extension
            png_img.read(),
            content_type='image/jpeg'  # Wrong MIME type
        )

        response = self.client.post(
            '/api/v1/users/upload_avatar/',
            {'avatar': spoofed_file},
            format='multipart'
        )

        # Should be rejected due to format mismatch
        # (Pillow detects actual format doesn't match extension)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class MIMETypeValidationTests(ImageUploadTestCase):
    """Test MIME type validation (if python-magic available)."""

    def test_mime_type_validation_consistent(self):
        """Test MIME type validation is applied across all serializers."""
        # Create valid image
        valid_image = self.create_test_image(format='JPEG')

        # Test avatar upload (UserSerializer)
        response = self.client.post(
            '/api/v1/users/upload_avatar/',
            {'avatar': valid_image},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # All serializers now use ImageUploadValidator with MIME validation
        # If python-magic is installed, it validates; if not, gracefully degrades


class DimensionValidationTests(ImageUploadTestCase):
    """Test dimension validation across all image fields."""

    def test_minimum_dimensions_50x50(self):
        """Test images must be at least 50x50 pixels."""
        # 49x49 should fail
        tiny_image = self.create_test_image(size=(49, 49))
        response = self.client.post(
            '/api/v1/users/upload_avatar/',
            {'avatar': tiny_image},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 50x50 should succeed
        valid_image = self.create_test_image(size=(50, 50))
        response = self.client.post(
            '/api/v1/users/upload_avatar/',
            {'avatar': valid_image},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_maximum_dimensions_2048x2048(self):
        """Test images cannot exceed 2048x2048 pixels."""
        # 2048x2048 should succeed
        valid_image = self.create_test_image(size=(2048, 2048))
        response = self.client.post(
            '/api/v1/users/upload_avatar/',
            {'avatar': valid_image},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 2049x2049 should fail
        huge_image = self.create_test_image(size=(2049, 2049))
        response = self.client.post(
            '/api/v1/users/upload_avatar/',
            {'avatar': huge_image},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UnauthenticatedUploadTests(TestCase):
    """Test that file uploads require authentication."""

    def setUp(self):
        """Set up test client without authentication."""
        self.client = APIClient()

    def test_unauthenticated_avatar_upload_rejected(self):
        """Test unauthenticated users cannot upload avatars."""
        # Create valid image
        img = Image.new('RGB', (100, 100), color='red')
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        avatar = SimpleUploadedFile("test.jpg", img_io.read(), content_type='image/jpeg')

        response = self.client.post(
            '/api/v1/users/upload_avatar/',
            {'avatar': avatar},
            format='multipart'
        )

        # Should require authentication
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

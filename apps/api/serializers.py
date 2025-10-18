"""
Serializers for Python Learning Studio API.
Handles serialization/deserialization of all model data.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from apps.learning.models import *
from apps.users.models import UserProfile, Achievement, UserFollow, ProgrammingLanguage
from .validators import ImageUploadValidator

User = get_user_model()


# User Management Serializers
class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model with secure avatar upload validation.

    Security Features:
    - Extension whitelist (JPEG, PNG, GIF, WEBP only)
    - MIME type validation via python-magic
    - File size limits (5 MB max)
    - Image content validation via Pillow
    - Dimension restrictions (50x50 to 2048x2048)
    """
    avatar_url = serializers.SerializerMethodField()
    avatar_validator = ImageUploadValidator(max_size_mb=5, allow_gif=True, field_name='Avatar')

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                 'avatar', 'avatar_url', 'date_joined', 'is_active']
        read_only_fields = ['id', 'date_joined', 'avatar_url']
        extra_kwargs = {
            'avatar': {'write_only': True}  # Don't expose file path in responses
        }

    def get_avatar_url(self, obj):
        """Return avatar URL or None."""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None

    def validate_avatar(self, value):
        """
        Comprehensive avatar validation using reusable validator.

        Validates:
        1. File extension (whitelist approach)
        2. MIME type (content-based detection)
        3. File size (5 MB limit)
        4. Image content (Pillow verification)
        5. Image dimensions (50x50 to 2048x2048)

        Args:
            value: UploadedFile instance

        Returns:
            Validated file instance

        Raises:
            serializers.ValidationError: If validation fails
        """
        return self.avatar_validator(value)


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']


class AchievementSerializer(serializers.ModelSerializer):
    """
    Serializer for Achievement model with secure icon upload validation.

    Security Features:
    - Extension whitelist (JPEG, PNG, GIF, WEBP only)
    - MIME type validation via python-magic
    - File size limits (5 MB max)
    - Image content validation via Pillow
    - Dimension restrictions (50x50 to 2048x2048)
    """
    icon_url = serializers.SerializerMethodField()
    icon_validator = ImageUploadValidator(max_size_mb=5, allow_gif=True, field_name='Achievement Icon')

    class Meta:
        model = Achievement
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'icon_url']
        extra_kwargs = {
            'icon': {'write_only': True}
        }

    def get_icon_url(self, obj):
        """Return icon URL or None."""
        if obj.icon:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.icon.url)
            return obj.icon.url
        return None

    def validate_icon(self, value):
        """
        Comprehensive icon validation using reusable validator.

        Validates:
        1. File extension (whitelist approach)
        2. MIME type (content-based detection)
        3. File size (5 MB limit)
        4. Image content (Pillow verification)
        5. Image dimensions (50x50 to 2048x2048)

        Args:
            value: UploadedFile instance

        Returns:
            Validated file instance

        Raises:
            serializers.ValidationError: If validation fails
        """
        return self.icon_validator(value)


# Learning Management Serializers
class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""
    subcategories = serializers.StringRelatedField(many=True, read_only=True)
    course_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_course_count(self, obj):
        return obj.courses.filter(is_published=True).count()


class CourseSerializer(serializers.ModelSerializer):
    """
    Serializer for Course model with secure image upload validation.

    Security Features:
    - Extension whitelist (JPEG, PNG, WEBP only for course images)
    - MIME type validation via python-magic
    - File size limits (10 MB max for course materials)
    - Image content validation via Pillow
    - Dimension restrictions (50x50 to 2048x2048)
    """
    instructor = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)
    instructor_id = serializers.IntegerField(write_only=True)
    enrollment_count = serializers.SerializerMethodField()
    user_enrolled = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    banner_url = serializers.SerializerMethodField()
    # Course images have higher size limit (10 MB) and no GIF support
    course_image_validator = ImageUploadValidator(max_size_mb=10, allow_gif=False, field_name='Course Image')

    class Meta:
        model = Course
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'published_at', 'total_lessons',
                           'total_enrollments', 'average_rating', 'total_reviews',
                           'thumbnail_url', 'banner_url']
        extra_kwargs = {
            'thumbnail': {'write_only': True},
            'banner_image': {'write_only': True}
        }

    def get_enrollment_count(self, obj):
        return obj.enrollments.count()

    def get_user_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.enrollments.filter(user=request.user).exists()
        return False

    def get_thumbnail_url(self, obj):
        """Return thumbnail URL or None."""
        if obj.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        return None

    def get_banner_url(self, obj):
        """Return banner image URL or None."""
        if obj.banner_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.banner_image.url)
            return obj.banner_image.url
        return None

    def validate_thumbnail(self, value):
        """
        Validate course thumbnail image using reusable validator.

        Validates:
        1. File extension (whitelist approach)
        2. MIME type (content-based detection)
        3. File size (10 MB limit for course materials)
        4. Image content (Pillow verification)
        5. Image dimensions (50x50 to 2048x2048)

        Args:
            value: UploadedFile instance

        Returns:
            Validated file instance

        Raises:
            serializers.ValidationError: If validation fails
        """
        # Use shared validator with custom field name
        validator = ImageUploadValidator(max_size_mb=10, allow_gif=False, field_name='Thumbnail')
        return validator(value)

    def validate_banner_image(self, value):
        """
        Validate course banner image using reusable validator.

        Validates:
        1. File extension (whitelist approach)
        2. MIME type (content-based detection)
        3. File size (10 MB limit for course materials)
        4. Image content (Pillow verification)
        5. Image dimensions (50x50 to 2048x2048)

        Args:
            value: UploadedFile instance

        Returns:
            Validated file instance

        Raises:
            serializers.ValidationError: If validation fails
        """
        # Use shared validator with custom field name
        validator = ImageUploadValidator(max_size_mb=10, allow_gif=False, field_name='Banner')
        return validator(value)


class LessonSerializer(serializers.ModelSerializer):
    """Serializer for Lesson model."""
    course = CourseSerializer(read_only=True)
    course_id = serializers.IntegerField(write_only=True)
    next_lesson = serializers.SerializerMethodField()
    previous_lesson = serializers.SerializerMethodField()
    user_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_next_lesson(self, obj):
        next_lesson = obj.get_next_lesson()
        if next_lesson:
            return {'id': next_lesson.id, 'title': next_lesson.title, 'slug': next_lesson.slug}
        return None
    
    def get_previous_lesson(self, obj):
        prev_lesson = obj.get_previous_lesson()
        if prev_lesson:
            return {'id': prev_lesson.id, 'title': prev_lesson.title, 'slug': prev_lesson.slug}
        return None
    
    def get_user_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                progress = UserProgress.objects.get(user=request.user, lesson=obj)
                return {
                    'started': progress.started,
                    'completed': progress.completed,
                    'time_spent': progress.time_spent,
                    'bookmarked': progress.bookmarked
                }
            except UserProgress.DoesNotExist:
                return None
        return None


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for CourseEnrollment model."""
    user = UserSerializer(read_only=True)
    course = CourseSerializer(read_only=True)
    course_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = CourseEnrollment
        fields = '__all__'
        read_only_fields = ['user', 'enrolled_at', 'last_activity', 'progress_percentage']


class UserProgressSerializer(serializers.ModelSerializer):
    """Serializer for UserProgress model."""
    user = UserSerializer(read_only=True)
    lesson = LessonSerializer(read_only=True)
    lesson_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = UserProgress
        fields = '__all__'
        read_only_fields = ['user', 'started_at', 'completed_at', 'last_accessed']


class LearningPathSerializer(serializers.ModelSerializer):
    """Serializer for LearningPath model."""
    creator = UserSerializer(read_only=True)
    courses = CourseSerializer(many=True, read_only=True)
    
    class Meta:
        model = LearningPath
        fields = '__all__'
        read_only_fields = ['creator', 'created_at', 'updated_at']


class CourseReviewSerializer(serializers.ModelSerializer):
    """Serializer for CourseReview model."""
    user = UserSerializer(read_only=True)
    course = CourseSerializer(read_only=True)
    course_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = CourseReview
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']


# Exercise System Serializers
class ProgrammingLanguageSerializer(serializers.ModelSerializer):
    """
    Serializer for ProgrammingLanguage model with secure icon upload validation.

    Security Features:
    - Extension whitelist (JPEG, PNG, GIF, WEBP only)
    - MIME type validation via python-magic
    - File size limits (5 MB max)
    - Image content validation via Pillow
    - Dimension restrictions (50x50 to 2048x2048)

    Note: SVG support removed due to XSS risk (embedded JavaScript)
    """
    exercise_count = serializers.SerializerMethodField()
    icon_url = serializers.SerializerMethodField()
    icon_validator = ImageUploadValidator(max_size_mb=5, allow_gif=True, field_name='Language Icon')

    class Meta:
        model = ProgrammingLanguage
        fields = '__all__'
        read_only_fields = ['created_at', 'icon_url']
        extra_kwargs = {
            'icon': {'write_only': True}
        }

    def get_exercise_count(self, obj):
        return obj.exercises.filter(is_published=True).count()

    def get_icon_url(self, obj):
        """Return icon URL or None."""
        if obj.icon:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.icon.url)
            return obj.icon.url
        return None

    def validate_icon(self, value):
        """
        Comprehensive icon validation using reusable validator.

        Validates:
        1. File extension (whitelist approach, no SVG for XSS prevention)
        2. MIME type (content-based detection)
        3. File size (5 MB limit)
        4. Image content (Pillow verification)
        5. Image dimensions (50x50 to 2048x2048)

        Args:
            value: UploadedFile instance

        Returns:
            Validated file instance

        Raises:
            serializers.ValidationError: If validation fails
        """
        return self.icon_validator(value)


class ExerciseTypeSerializer(serializers.ModelSerializer):
    """Serializer for ExerciseType model."""
    class Meta:
        model = ExerciseType
        fields = '__all__'


class TestCaseSerializer(serializers.ModelSerializer):
    """Serializer for TestCase model."""
    class Meta:
        model = TestCase
        fields = '__all__'
        read_only_fields = ['created_at']


class ExerciseSerializer(serializers.ModelSerializer):
    """Serializer for Exercise model."""
    lesson = LessonSerializer(read_only=True)
    exercise_type = ExerciseTypeSerializer(read_only=True)
    programming_language = ProgrammingLanguageSerializer(read_only=True)
    lesson_id = serializers.IntegerField(write_only=True)
    exercise_type_id = serializers.IntegerField(write_only=True)
    programming_language_id = serializers.IntegerField(write_only=True)
    
    test_cases = TestCaseSerializer(many=True, read_only=True)
    user_progress = serializers.SerializerMethodField()
    success_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = Exercise
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'total_submissions', 
                           'successful_submissions', 'average_attempts']
    
    def get_user_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                progress = StudentProgress.objects.get(user=request.user, exercise=obj)
                return {
                    'started': progress.started,
                    'completed': progress.completed,
                    'best_score': progress.best_score,
                    'total_attempts': progress.total_attempts
                }
            except StudentProgress.DoesNotExist:
                return None
        return None
    
    def get_success_rate(self, obj):
        return obj.get_success_rate()


class SubmissionSerializer(serializers.ModelSerializer):
    """Serializer for Submission model."""
    user = UserSerializer(read_only=True)
    exercise = ExerciseSerializer(read_only=True)
    exercise_id = serializers.IntegerField(write_only=True)
    test_results = serializers.SerializerMethodField()
    
    class Meta:
        model = Submission
        fields = '__all__'
        read_only_fields = ['user', 'submission_id', 'submitted_at', 'processed_at',
                           'status', 'score', 'passed_tests', 'total_tests',
                           'execution_time', 'memory_used', 'output', 'error_message']
    
    def get_test_results(self, obj):
        return [
            {
                'test_case_name': result.test_case.name,
                'passed': result.passed,
                'actual_output': result.actual_output,
                'execution_time': result.execution_time,
                'error_message': result.error_message
            }
            for result in obj.test_results.all()
        ]


class StudentProgressSerializer(serializers.ModelSerializer):
    """Serializer for StudentProgress model."""
    user = UserSerializer(read_only=True)
    exercise = ExerciseSerializer(read_only=True)
    exercise_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = StudentProgress
        fields = '__all__'
        read_only_fields = ['user', 'started_at', 'completed_at', 'last_attempt_at', 'created_at']


class ExerciseHintSerializer(serializers.ModelSerializer):
    """Serializer for ExerciseHint model."""
    exercise = ExerciseSerializer(read_only=True)
    exercise_id = serializers.IntegerField(write_only=True)
    is_unlocked = serializers.SerializerMethodField()
    
    class Meta:
        model = ExerciseHint
        fields = '__all__'
        read_only_fields = ['created_at']
    
    def get_is_unlocked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                progress = StudentProgress.objects.get(
                    user=request.user, 
                    exercise=obj.exercise
                )
                return progress.total_attempts >= obj.unlock_after_attempts
            except StudentProgress.DoesNotExist:
                return False
        return False


# Community Features Serializers
class DiscussionSerializer(serializers.ModelSerializer):
    """Serializer for Discussion model."""
    author = UserSerializer(read_only=True)
    course = CourseSerializer(read_only=True)
    lesson = LessonSerializer(read_only=True)
    exercise = ExerciseSerializer(read_only=True)
    
    course_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    lesson_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    exercise_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    reply_count = serializers.IntegerField(read_only=True)
    context_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Discussion
        fields = '__all__'
        read_only_fields = ['author', 'slug', 'created_at', 'updated_at', 'last_activity_at',
                           'reply_count', 'view_count', 'upvotes', 'downvotes']
    
    def get_context_display(self, obj):
        return obj.get_context_display()


class DiscussionReplySerializer(serializers.ModelSerializer):
    """Serializer for DiscussionReply model."""
    author = UserSerializer(read_only=True)
    discussion = DiscussionSerializer(read_only=True)
    parent_reply = serializers.PrimaryKeyRelatedField(read_only=True)
    discussion_id = serializers.IntegerField(write_only=True)
    parent_reply_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    child_replies = serializers.SerializerMethodField()
    
    class Meta:
        model = DiscussionReply
        fields = '__all__'
        read_only_fields = ['author', 'created_at', 'updated_at', 'upvotes', 'downvotes']
    
    def get_child_replies(self, obj):
        if hasattr(obj, 'child_replies'):
            return DiscussionReplySerializer(obj.child_replies.all(), many=True, context=self.context).data
        return []


class StudyGroupSerializer(serializers.ModelSerializer):
    """Serializer for StudyGroup model."""
    creator = UserSerializer(read_only=True)
    course = CourseSerializer(read_only=True)
    course_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    member_count = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()
    
    class Meta:
        model = StudyGroup
        fields = '__all__'
        read_only_fields = ['creator', 'created_at', 'updated_at']
    
    def get_member_count(self, obj):
        return obj.member_count
    
    def get_is_member(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.members.filter(id=request.user.id).exists()
        return False


class StudyGroupPostSerializer(serializers.ModelSerializer):
    """Serializer for StudyGroupPost model."""
    author = UserSerializer(read_only=True)
    study_group = StudyGroupSerializer(read_only=True)
    study_group_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = StudyGroupPost
        fields = '__all__'
        read_only_fields = ['author', 'created_at', 'updated_at', 'likes', 'replies_count']


class PeerReviewSerializer(serializers.ModelSerializer):
    """Serializer for PeerReview model."""
    author = UserSerializer(read_only=True)
    programming_language = ProgrammingLanguageSerializer(read_only=True)
    exercise = ExerciseSerializer(read_only=True)
    lesson = LessonSerializer(read_only=True)
    
    programming_language_id = serializers.IntegerField(write_only=True)
    exercise_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    lesson_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    review_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PeerReview
        fields = '__all__'
        read_only_fields = ['author', 'created_at', 'updated_at', 'completed_reviews']
    
    def get_review_count(self, obj):
        return obj.reviews.count()


class CodeReviewSerializer(serializers.ModelSerializer):
    """Serializer for CodeReview model."""
    reviewer = UserSerializer(read_only=True)
    peer_review = PeerReviewSerializer(read_only=True)
    peer_review_id = serializers.IntegerField(write_only=True)
    
    average_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = CodeReview
        fields = '__all__'
        read_only_fields = ['reviewer', 'created_at', 'updated_at']
    
    def get_average_rating(self, obj):
        return obj.average_rating


class LearningBuddySerializer(serializers.ModelSerializer):
    """Serializer for LearningBuddy model."""
    user1 = UserSerializer(read_only=True)
    user2 = UserSerializer(read_only=True)
    user2_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = LearningBuddy
        fields = '__all__'
        read_only_fields = ['user1', 'created_at', 'updated_at']


class LearningSessionSerializer(serializers.ModelSerializer):
    """Serializer for LearningSession model."""
    organizer = UserSerializer(read_only=True)
    participants = UserSerializer(many=True, read_only=True)
    participant_count = serializers.SerializerMethodField()
    is_participant = serializers.SerializerMethodField()
    
    class Meta:
        model = LearningSession
        fields = '__all__'
        read_only_fields = ['organizer', 'created_at', 'updated_at']
    
    def get_participant_count(self, obj):
        return obj.participant_count
    
    def get_is_participant(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.participants.filter(id=request.user.id).exists()
        return False


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model."""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'read_at']


# Custom API Response Serializers
class CodeExecutionRequestSerializer(serializers.Serializer):
    """Serializer for code execution requests."""
    code = serializers.CharField()
    language = serializers.CharField(default='python')
    test_inputs = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    timeout = serializers.IntegerField(default=10, min_value=1, max_value=60)


class CodeExecutionResponseSerializer(serializers.Serializer):
    """Serializer for code execution responses."""
    success = serializers.BooleanField()
    output = serializers.CharField()
    error = serializers.CharField()
    execution_time = serializers.FloatField()
    memory_used = serializers.FloatField()


class AIAssistanceRequestSerializer(serializers.Serializer):
    """Serializer for AI assistance requests."""
    assistance_type = serializers.ChoiceField(choices=[
        ('code_explanation', 'Code Explanation'),
        ('error_help', 'Error Help'),
        ('hint_generation', 'Hint Generation'),
        ('code_review', 'Code Review'),
        ('exercise_generation', 'Exercise Generation')
    ])
    content = serializers.CharField()
    context = serializers.CharField(required=False, default='')
    difficulty_level = serializers.CharField(required=False, default='beginner')


class AIAssistanceResponseSerializer(serializers.Serializer):
    """Serializer for AI assistance responses."""
    assistance_type = serializers.CharField()
    response = serializers.CharField()
    success = serializers.BooleanField()
    error_message = serializers.CharField(required=False)
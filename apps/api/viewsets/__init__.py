"""
ViewSet modules for REST API.
"""

from .user import UserViewSet, UserProfileViewSet
from .learning import (
    CategoryViewSet, CourseViewSet, LessonViewSet,
    CourseEnrollmentViewSet, UserProgressViewSet,
    LearningPathViewSet, CourseReviewViewSet
)
from .exercises import (
    ProgrammingLanguageViewSet, ExerciseTypeViewSet,
    ExerciseViewSet, SubmissionViewSet, TestCaseViewSet,
    StudentProgressViewSet, ExerciseHintViewSet
)
from .community import (
    DiscussionViewSet, DiscussionReplyViewSet,
    StudyGroupViewSet, StudyGroupPostViewSet,
    PeerReviewViewSet, CodeReviewViewSet,
    LearningBuddyViewSet, LearningSessionViewSet,
    NotificationViewSet
)

__all__ = [
    # User ViewSets
    'UserViewSet', 'UserProfileViewSet',
    
    # Learning ViewSets
    'CategoryViewSet', 'CourseViewSet', 'LessonViewSet',
    'CourseEnrollmentViewSet', 'UserProgressViewSet',
    'LearningPathViewSet', 'CourseReviewViewSet',
    
    # Exercise ViewSets
    'ProgrammingLanguageViewSet', 'ExerciseTypeViewSet',
    'ExerciseViewSet', 'SubmissionViewSet', 'TestCaseViewSet',
    'StudentProgressViewSet', 'ExerciseHintViewSet',
    
    # Community ViewSets
    'DiscussionViewSet', 'DiscussionReplyViewSet',
    'StudyGroupViewSet', 'StudyGroupPostViewSet',
    'PeerReviewViewSet', 'CodeReviewViewSet',
    'LearningBuddyViewSet', 'LearningSessionViewSet',
    'NotificationViewSet'
]
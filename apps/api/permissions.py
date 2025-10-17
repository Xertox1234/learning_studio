"""
Custom permission classes for Python Learning Studio API.
"""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the object.
        # Handle different object types
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'author'):
            return obj.author == request.user
        elif hasattr(obj, 'creator'):
            return obj.creator == request.user
        elif hasattr(obj, 'organizer'):
            return obj.organizer == request.user
        elif hasattr(obj, 'instructor'):
            return obj.instructor == request.user
        elif hasattr(obj, 'user1'):
            return obj.user1 == request.user or obj.user2 == request.user
        
        # Default to checking if the object is the user themselves
        return obj == request.user


class IsInstructorOrReadOnly(permissions.BasePermission):
    """
    Custom permission for course instructors.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for the instructor
        if hasattr(obj, 'instructor'):
            return obj.instructor == request.user
        elif hasattr(obj, 'course'):
            return obj.course.instructor == request.user
        elif hasattr(obj, 'lesson'):
            return obj.lesson.course.instructor == request.user
        
        return False


class IsStudentEnrolled(permissions.BasePermission):
    """
    Permission to check if user is enrolled in a course.
    """
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Get the course from different object types
        course = None
        if hasattr(obj, 'course'):
            course = obj.course
        elif hasattr(obj, 'lesson'):
            course = obj.lesson.course
        elif hasattr(obj, 'exercise'):
            course = obj.exercise.lesson.course
        
        if course:
            return course.enrollments.filter(user=request.user).exists()
        
        return False


class IsStudyGroupMember(permissions.BasePermission):
    """
    Permission to check if user is a member of a study group.
    """
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        if hasattr(obj, 'study_group'):
            return obj.study_group.members.filter(id=request.user.id).exists()
        elif hasattr(obj, 'members'):
            return obj.members.filter(id=request.user.id).exists()
        
        return False


class IsModerator(permissions.BasePermission):
    """
    Permission for moderators and staff.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        return request.user.is_staff or request.user.is_superuser

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        return request.user.is_staff or request.user.is_superuser


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission to only allow owners or admins to access.

    This permission provides IDOR/BOLA protection by ensuring users can only
    access their own resources, while allowing staff/superusers full access.

    Usage:
        class MyViewSet(viewsets.ModelViewSet):
            permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    Security:
        - Implements has_permission() to require authentication
        - Implements has_object_permission() for object-level checks
        - Checks multiple ownership patterns (user, author, creator, etc.)
        - Grants full access to staff/superusers
    """
    message = 'You must be the owner or an administrator to access this resource.'
    code = 'not_owner_or_admin'

    def has_permission(self, request, view):
        """
        View-level permission check.
        Requires user to be authenticated.
        """
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Object-level permission check.
        Admin/staff can access all resources.
        Regular users can only access their own resources.
        """
        # Staff and superusers can access everything
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Check multiple possible owner attributes
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'author'):
            return obj.author == request.user
        elif hasattr(obj, 'creator'):
            return obj.creator == request.user
        elif hasattr(obj, 'reviewer'):
            return obj.reviewer == request.user
        elif hasattr(obj, 'organizer'):
            return obj.organizer == request.user

        # Default to checking if object is the user themselves
        return obj == request.user
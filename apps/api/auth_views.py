"""
Authentication views for the React frontend API.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from django.conf import settings
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited
from apps.users.models import UserProfile
from apps.users.serializers import UserSerializer, UserProfileSerializer
import json
import time
import logging

logger = logging.getLogger(__name__)

User = get_user_model()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    """
    Get the current authenticated user data.
    This is the endpoint React calls at /api/v1/auth/user/
    """
    try:
        user = request.user
        profile = user.userprofile if hasattr(user, 'userprofile') else None
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'date_joined': user.date_joined,
        }
        
        if profile:
            user_data.update({
                'bio': profile.bio,
                'location': profile.location,
                'github_username': profile.github_username,
                'linkedin_profile': profile.linkedin_profile,
                'preferred_language': profile.preferred_language,
                'learning_goals': profile.learning_goals,
                'skill_level': profile.skill_level,
            })
        
        return Response({
            'user': user_data,
            'authenticated': True
        })
    except Exception as e:
        logger.error(f"Current user fetch error: {str(e)}")
        return Response({
            'error': 'Failed to fetch user data'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate=settings.RATE_LIMIT_SETTINGS['LOGIN_ATTEMPTS'], method='POST', block=True)
def login(request):
    """
    Login endpoint for React frontend.
    Returns JWT tokens on successful authentication.
    Prevents user enumeration through constant-time responses.
    """
    try:
        data = json.loads(request.body)
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        
        if not email or not password:
            return Response({
                'error': 'Email and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Ensure minimum response time to prevent timing attacks
        start_time = time.time()
        
        # Use Django's authenticate which handles user lookup and password checking
        # This prevents user enumeration by using consistent timing
        user = authenticate(request, username=email, password=password)
        
        # Ensure minimum response time (100ms) regardless of success/failure
        elapsed = time.time() - start_time
        if elapsed < 0.1:
            time.sleep(0.1 - elapsed)
        
        if user and user.is_active:
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            # Get user profile data
            profile = user.userprofile if hasattr(user, 'userprofile') else None
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
            
            if profile:
                user_data.update({
                    'bio': profile.bio,
                    'skill_level': profile.skill_level,
                })
            
            logger.info(f"Successful login for user: {email}")
            
            return Response({
                'token': str(access_token),
                'refresh': str(refresh),
                'user': user_data,
                'success': True
            })
        else:
            # Always return the same error message regardless of whether 
            # user exists or password is wrong
            logger.warning(f"Failed login attempt for email: {email}")
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
    except json.JSONDecodeError:
        return Response({
            'error': 'Invalid JSON data'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return Response({
            'error': 'Login failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate=settings.RATE_LIMIT_SETTINGS['REGISTRATION_ATTEMPTS'], method='POST', block=True)
def register(request):
    """
    Registration endpoint for React frontend.
    Creates a new user and returns JWT tokens.
    """
    try:
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        
        if not username or not email or not password:
            return Response({
                'error': 'Username, email, and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user already exists (prevent enumeration by being generic)
        if User.objects.filter(username=username).exists() or User.objects.filter(email=email).exists():
            return Response({
                'error': 'User with these credentials already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
        
        return Response({
            'token': str(access_token),
            'refresh': str(refresh),
            'user': user_data,
            'success': True
        })
        
    except json.JSONDecodeError:
        return Response({
            'error': 'Invalid JSON data'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return Response({
            'error': 'Registration failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout endpoint for React frontend.
    Blacklists the refresh token.
    """
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return Response({
            'success': True,
            'message': 'Successfully logged out'
        })
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return Response({
            'error': 'Logout failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def auth_status(request):
    """
    Check authentication status - useful for testing.
    """
    return Response({
        'authenticated': request.user.is_authenticated,
        'user_id': request.user.id if request.user.is_authenticated else None,
        'username': request.user.username if request.user.is_authenticated else None,
    })
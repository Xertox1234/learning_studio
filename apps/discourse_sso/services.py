"""
Discourse SSO service layer for handling authentication and user synchronization.
"""

import base64
import hmac
import hashlib
import logging
from urllib import parse
from typing import Dict, Optional, Tuple
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import DiscourseUser, DiscourseGroupMapping, DiscourseSsoLog

User = get_user_model()
logger = logging.getLogger(__name__)


class DiscourseSSO:
    """
    Service class for handling Discourse SSO authentication and user synchronization.
    """
    
    def __init__(self):
        self.secret = getattr(settings, 'DISCOURSE_SSO_SECRET', '')
        self.base_url = getattr(settings, 'DISCOURSE_BASE_URL', '')
        
        if not self.secret:
            logger.warning("DISCOURSE_SSO_SECRET not configured")
        if not self.base_url:
            logger.warning("DISCOURSE_BASE_URL not configured")
    
    def validate_payload(self, payload: str, signature: str) -> Tuple[bool, Optional[Dict]]:
        """
        Validate the SSO payload signature and extract parameters.
        
        Args:
            payload: Base64 encoded SSO payload
            signature: HMAC signature of the payload
            
        Returns:
            Tuple of (is_valid, decoded_params)
        """
        try:
            # Decode the payload
            payload_bytes = bytes(parse.unquote(payload), encoding='utf-8')
            decoded = base64.decodebytes(payload_bytes).decode('utf-8')
            
            # Validate payload contains required data
            if len(payload_bytes) == 0 or 'nonce' not in decoded:
                logger.warning("Invalid SSO payload: missing nonce")
                return False, None
            
            # Verify HMAC signature
            key = bytes(self.secret, encoding='utf-8')
            expected_signature = hmac.new(
                key, payload_bytes, digestmod=hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(expected_signature, signature):
                logger.warning("Invalid SSO signature")
                return False, None
            
            # Parse query string parameters
            params = parse.parse_qs(decoded)
            return True, params
            
        except Exception as e:
            logger.error(f"Error validating SSO payload: {e}")
            return False, None
    
    def generate_return_payload(self, user, nonce: str, **extra_params) -> str:
        """
        Generate the return payload for successful SSO authentication.
        
        Args:
            user: Django User instance
            nonce: Original nonce from Discourse
            **extra_params: Additional parameters to include
            
        Returns:
            URL with signed SSO payload
        """
        try:
            # Get or create Discourse user profile
            discourse_user, created = DiscourseUser.objects.get_or_create(
                user=user,
                defaults={
                    'discourse_user_id': str(user.id),
                    'discourse_username': user.username,
                }
            )
            
            # Build payload parameters
            params = {
                'nonce': nonce,
                'email': user.email,
                'external_id': str(user.id),
                'username': user.username,
                'require_activation': 'true' if not user.email_verified else 'false',
                'name': user.get_full_name() or user.username,
            }
            
            # Add optional user attributes
            if hasattr(user, 'avatar') and user.avatar:
                params['avatar_url'] = user.avatar.url
            
            if hasattr(user, 'bio') and user.bio:
                params['bio'] = user.bio[:3000]  # Discourse limit
            
            # Add group memberships
            groups = self.get_user_discourse_groups(user)
            if groups:
                params['groups'] = ','.join(groups)
            
            # Add extra parameters
            params.update(extra_params)
            
            # Encode and sign the payload
            return_payload = base64.encodebytes(
                bytes(parse.urlencode(params), 'utf-8')
            ).strip()
            
            key = bytes(self.secret, encoding='utf-8')
            signature = hmac.new(
                key, return_payload, digestmod=hashlib.sha256
            ).hexdigest()
            
            # Build return URL
            query_params = parse.urlencode({
                'sso': return_payload.decode('utf-8'),
                'sig': signature
            })
            
            return f"{self.base_url}/session/sso_login?{query_params}"
            
        except Exception as e:
            logger.error(f"Error generating SSO return payload: {e}")
            raise
    
    def get_user_discourse_groups(self, user) -> list:
        """
        Get the list of Discourse groups for a Django user.
        
        Args:
            user: Django User instance
            
        Returns:
            List of Discourse group names
        """
        discourse_groups = []
        
        for group in user.groups.all():
            try:
                mapping = DiscourseGroupMapping.objects.get(
                    django_group=group,
                    auto_sync=True
                )
                discourse_groups.append(mapping.discourse_group_name)
            except DiscourseGroupMapping.DoesNotExist:
                continue
        
        return discourse_groups
    
    def log_sso_attempt(
        self, 
        user=None, 
        action='login', 
        success=True, 
        error_message='',
        request=None,
        nonce=''
    ):
        """
        Log SSO authentication attempt for monitoring and debugging.
        
        Args:
            user: Django User instance (optional)
            action: Type of SSO action
            success: Whether the action succeeded
            error_message: Error details if unsuccessful
            request: HTTP request object for IP/user agent
            nonce: SSO nonce value
        """
        try:
            log_data = {
                'user': user,
                'action': action,
                'success': success,
                'error_message': error_message,
                'nonce': nonce,
            }
            
            if request:
                log_data.update({
                    'ip_address': self.get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                })
            
            DiscourseSsoLog.objects.create(**log_data)
            
        except Exception as e:
            logger.error(f"Error logging SSO attempt: {e}")
    
    def get_client_ip(self, request) -> str:
        """
        Get the client IP address from the request.
        
        Args:
            request: HTTP request object
            
        Returns:
            Client IP address
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def sync_user_to_discourse(self, user) -> bool:
        """
        Manually sync a Django user to Discourse (for bulk operations).
        
        Args:
            user: Django User instance
            
        Returns:
            True if sync was successful
        """
        try:
            discourse_user, created = DiscourseUser.objects.get_or_create(
                user=user,
                defaults={
                    'discourse_user_id': str(user.id),
                    'discourse_username': user.username,
                }
            )
            
            if not created:
                discourse_user.discourse_username = user.username
                discourse_user.last_sync = timezone.now()
                discourse_user.save()
            
            self.log_sso_attempt(
                user=user,
                action='sync',
                success=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing user {user.id} to Discourse: {e}")
            self.log_sso_attempt(
                user=user,
                action='sync',
                success=False,
                error_message=str(e)
            )
            return False
"""
Discourse SSO views for handling authentication requests.
"""

import logging
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth import authenticate, login
from django.urls import reverse
from django.utils import timezone
from .services import DiscourseSSO
from .models import DiscourseSsoLog

logger = logging.getLogger(__name__)


class DiscourseSSOView(View):
    """
    Main SSO endpoint for Discourse authentication.
    """
    
    def __init__(self):
        super().__init__()
        self.sso_service = DiscourseSSO()
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request):
        """
        Handle SSO authentication request from Discourse.
        """
        payload = request.GET.get('sso')
        signature = request.GET.get('sig')
        
        # Validate required parameters
        if not payload or not signature:
            self.sso_service.log_sso_attempt(
                action='login',
                success=False,
                error_message='Missing SSO payload or signature',
                request=request
            )
            return HttpResponseBadRequest('Missing SSO payload or signature.')
        
        # Validate the payload signature
        is_valid, params = self.sso_service.validate_payload(payload, signature)
        if not is_valid:
            self.sso_service.log_sso_attempt(
                action='login',
                success=False,
                error_message='Invalid payload signature',
                request=request
            )
            return HttpResponseBadRequest('Invalid payload signature.')
        
        nonce = params.get('nonce', [''])[0]
        
        # Check if user is authenticated
        if request.user.is_authenticated:
            return self._handle_authenticated_user(request, nonce)
        else:
            return self._handle_unauthenticated_user(request, payload, signature, nonce)
    
    def _handle_authenticated_user(self, request, nonce):
        """
        Handle SSO for already authenticated users.
        """
        try:
            user = request.user
            
            # Check if user email is verified
            if not getattr(user, 'email_verified', True):
                self.sso_service.log_sso_attempt(
                    user=user,
                    action='login',
                    success=False,
                    error_message='Email not verified',
                    request=request,
                    nonce=nonce
                )
                return render(request, 'discourse_sso/email_verification_required.html', {
                    'user': user,
                    'discourse_url': self.sso_service.base_url
                })
            
            # Generate return payload
            return_url = self.sso_service.generate_return_payload(user, nonce)
            
            # Log successful SSO
            self.sso_service.log_sso_attempt(
                user=user,
                action='login',
                success=True,
                request=request,
                nonce=nonce
            )
            
            return HttpResponseRedirect(return_url)
            
        except Exception as e:
            logger.error(f"Error handling authenticated SSO: {e}")
            self.sso_service.log_sso_attempt(
                user=request.user,
                action='login',
                success=False,
                error_message=str(e),
                request=request,
                nonce=nonce
            )
            return HttpResponseBadRequest('SSO processing error.')
    
    def _handle_unauthenticated_user(self, request, payload, signature, nonce):
        """
        Handle SSO for unauthenticated users - redirect to login.
        """
        # Store SSO parameters in session for after login
        request.session['discourse_sso_payload'] = payload
        request.session['discourse_sso_signature'] = signature
        request.session['discourse_sso_nonce'] = nonce
        
        # Redirect to login with return URL
        login_url = reverse('account_login')
        return_url = reverse('discourse_sso')
        redirect_url = f"{login_url}?next={return_url}"
        
        return HttpResponseRedirect(redirect_url)


@login_required
def discourse_sso_return(request):
    """
    Handle the return from login for pending SSO requests.
    """
    sso_service = DiscourseSSO()
    
    # Check for stored SSO parameters
    payload = request.session.get('discourse_sso_payload')
    signature = request.session.get('discourse_sso_signature')
    nonce = request.session.get('discourse_sso_nonce')
    
    if not all([payload, signature, nonce]):
        return HttpResponseBadRequest('No pending SSO request found.')
    
    # Clear session data
    for key in ['discourse_sso_payload', 'discourse_sso_signature', 'discourse_sso_nonce']:
        request.session.pop(key, None)
    
    try:
        # Validate payload again (security)
        is_valid, params = sso_service.validate_payload(payload, signature)
        if not is_valid:
            return HttpResponseBadRequest('Invalid SSO payload.')
        
        user = request.user
        
        # Check email verification
        if not getattr(user, 'email_verified', True):
            return render(request, 'discourse_sso/email_verification_required.html', {
                'user': user,
                'discourse_url': sso_service.base_url
            })
        
        # Generate return payload
        return_url = sso_service.generate_return_payload(user, nonce)
        
        # Log successful SSO
        sso_service.log_sso_attempt(
            user=user,
            action='login',
            success=True,
            request=request,
            nonce=nonce
        )
        
        return HttpResponseRedirect(return_url)
        
    except Exception as e:
        logger.error(f"Error processing SSO return: {e}")
        sso_service.log_sso_attempt(
            user=request.user,
            action='login',
            success=False,
            error_message=str(e),
            request=request,
            nonce=nonce
        )
        return HttpResponseBadRequest('SSO processing error.')


@require_http_methods(["GET"])
def discourse_sso_status(request):
    """
    API endpoint to check SSO configuration status.
    """
    sso_service = DiscourseSSO()
    
    status = {
        'sso_configured': bool(sso_service.secret and sso_service.base_url),
        'base_url': sso_service.base_url,
        'secret_configured': bool(sso_service.secret),
    }
    
    if request.user.is_authenticated and request.user.is_staff:
        # Additional debug info for staff users
        try:
            recent_logs = DiscourseSsoLog.objects.filter(
                timestamp__gte=timezone.now() - timedelta(hours=24)
            ).count()
            
            status.update({
                'recent_sso_attempts': recent_logs,
                'user_has_discourse_profile': hasattr(request.user, 'discourse_profile'),
            })
        except Exception:
            pass
    
    return JsonResponse(status)


class DiscourseUserSyncView(View):
    """
    Admin view for manually syncing users to Discourse.
    """
    
    def post(self, request):
        """
        Manually sync current user or specified user to Discourse.
        """
        if not request.user.is_staff:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        sso_service = DiscourseSSO()
        user_id = request.POST.get('user_id')
        
        if user_id:
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User not found'}, status=404)
        else:
            user = request.user
        
        success = sso_service.sync_user_to_discourse(user)
        
        if success:
            return JsonResponse({
                'success': True,
                'message': f'User {user.username} synced successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Sync failed - check logs for details'
            }, status=500)
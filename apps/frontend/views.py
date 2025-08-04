from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings
from django.views.generic import TemplateView
import os
import json

def react_app_view(request, path=''):
    """
    Serve the React application for all frontend routes.
    In development, this will proxy to the Vite dev server.
    In production, this will serve the built React files.
    """
    if settings.DEBUG:
        # In development, redirect to React dev server
        context = {
            'REACT_DEV_SERVER': 'http://localhost:3000',
            'path': path,
        }
        return render(request, 'frontend/dev_proxy.html', context)
    else:
        # In production, serve the built React app
        # This would serve the built files from static/react/
        return render(request, 'frontend/index.html', {
            'path': path,
        })

def api_status_view(request):
    """
    API endpoint to check backend status
    """
    return HttpResponse(
        json.dumps({
            'status': 'ok',
            'version': '1.0.0',
            'mode': 'development' if settings.DEBUG else 'production'
        }),
        content_type='application/json'
    )


class ReactAuthView(TemplateView):
    """
    Serve React authentication pages (login/register).
    """
    template_name = 'auth/react_auth.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_type'] = 'auth'
        return context


def react_login_view(request):
    """
    Serve the React login page.
    """
    return render(request, 'auth/react_auth.html', {
        'page_type': 'login',
        'title': 'Login - Python Learning Studio'
    })


def react_register_view(request):
    """
    Serve the React register page.
    """
    return render(request, 'auth/react_auth.html', {
        'page_type': 'register', 
        'title': 'Register - Python Learning Studio'
    })
from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings
from django.views.generic import TemplateView
import os
import json

def react_app_view(request, path=''):
    """
    Serve the React SPA for all frontend routes.
    In development, this proxies to the Vite dev server.
    In production, this serves the built React files.

    This is the catch-all view for the React SPA routing.
    """
    if settings.DEBUG:
        # Development: Proxy to Vite dev server (http://localhost:3000)
        context = {
            'REACT_DEV_SERVER': 'http://localhost:3000',
            'path': path,
        }
        return render(request, 'frontend/dev_proxy.html', context)
    else:
        # Production: Serve built React app from static/react/
        # The index.html references assets with absolute paths
        react_html_path = os.path.join(settings.BASE_DIR, 'static', 'react', 'index.html')

        if os.path.exists(react_html_path):
            with open(react_html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Update asset paths to work with Django static files
            html_content = html_content.replace('="/assets/', f'="{settings.STATIC_URL}react/assets/')
            html_content = html_content.replace("='/assets/", f"='{settings.STATIC_URL}react/assets/")

            return HttpResponse(html_content, content_type='text/html')
        else:
            return HttpResponse(
                '<h1>React App Not Built</h1><p>Please run: cd frontend && npm run build</p>',
                status=503
            )

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
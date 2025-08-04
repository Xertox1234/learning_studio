"""
ASGI config for learning_community project.
Supports both HTTP and WebSocket protocols for real-time functionality.
"""

import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learning_community.settings.development')

# Initialize Django ASGI application early
django.setup()

# Import WebSocket routing after Django setup
from apps.forum_integration.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    # HTTP requests
    'http': get_asgi_application(),
    
    # WebSocket requests
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})

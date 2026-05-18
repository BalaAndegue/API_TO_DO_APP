"""
ASGI config — supports HTTP and WebSocket (Django Channels).

Development:
    python manage.py runserver        (Channels uses ASGI_APPLICATION automatically)

Production (install daphne first):
    pip install daphne
    daphne -b 0.0.0.0 -p 8000 AuthenticationProject.asgi:application

For multi-process production, use Redis channel layer:
    pip install channels-redis
    See CHANNEL_LAYERS in settings.py
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from Core.middleware import TokenAuthMiddleware
import Core.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AuthenticationProject.settings')

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AllowedHostsOriginValidator(
        TokenAuthMiddleware(
            URLRouter(Core.routing.websocket_urlpatterns)
        )
    ),
})

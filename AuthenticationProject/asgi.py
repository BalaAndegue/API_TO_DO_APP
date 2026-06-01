"""
ASGI config — supports HTTP and WebSocket (Django Channels).

Development:
    python manage.py runserver

Production:
    daphne -b 0.0.0.0 -p 8000 AuthenticationProject.asgi:application
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AuthenticationProject.settings')

# django.setup() must be called before any app-level imports (models, middleware…)
django.setup()

from django.core.asgi import get_asgi_application          # noqa: E402
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.security.websocket import AllowedHostsOriginValidator  # noqa: E402
from Core.middleware import TokenAuthMiddleware              # noqa: E402
import Core.routing                                         # noqa: E402

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AllowedHostsOriginValidator(
        TokenAuthMiddleware(
            URLRouter(Core.routing.websocket_urlpatterns)
        )
    ),
})

"""
WebSocket token authentication middleware.

The browser WebSocket API can't set custom headers, so the token is
passed as a query parameter:  ws://host/ws/boards/42/?token=<token>

This middleware resolves the token to a User and attaches it to scope['user'].
Unauthenticated connections receive an AnonymousUser — the consumer closes them.
"""

from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token


@database_sync_to_async
def _get_user(token_key):
    try:
        token = Token.objects.select_related('user').get(key=token_key)
        return token.user if token.user.is_active else AnonymousUser()
    except Token.DoesNotExist:
        return AnonymousUser()


class TokenAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        qs     = parse_qs(scope.get('query_string', b'').decode())
        token  = qs.get('token', [None])[0]
        scope['user'] = await _get_user(token) if token else AnonymousUser()
        return await super().__call__(scope, receive, send)

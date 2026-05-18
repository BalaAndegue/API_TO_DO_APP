"""
BoardConsumer — WebSocket consumer scoped to a single board.

Connection URL:
    ws://<host>/ws/boards/<board_id>/?token=<auth_token>

Channel group:
    board_<board_id>   — one group per board, all members share it

Events broadcast (type → payload):
    card.moved      { card_id, list_id, position }
    card.created    { card_id, list_id, title }
    card.updated    { card_id, fields: {...} }
    card.deleted    { card_id }
    list.moved      { list_id, position }
    list.created    { list_id, board_id, name }
    list.updated    { list_id, fields: {...} }
    list.deleted    { list_id }

Frontend usage (JavaScript):
    const ws = new WebSocket(`ws://localhost:8000/ws/boards/1/?token=${token}`);
    ws.onmessage = (e) => {
        const { type, ...payload } = JSON.parse(e.data);
        // dispatch to your state management
    };

    // Send a move event after DnD:
    ws.send(JSON.stringify({ type: 'card.move', card_id: 5, list_id: 2, position: 1 }));
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from Core.models import Board, BoardMember

logger = logging.getLogger(__name__)


@database_sync_to_async
def _can_access_board(user, board_id):
    """Return True if user may connect to this board's channel."""
    try:
        board = Board.objects.get(pk=board_id)
    except Board.DoesNotExist:
        return False
    if board.visibility == 'public':
        return True
    return (
        board.creator == user or
        BoardMember.objects.filter(board=board, user=user).exists()
    )


class BoardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.board_id   = self.scope['url_route']['kwargs']['board_id']
        self.group_name = f'board_{self.board_id}'
        user            = self.scope.get('user')

        # Reject unauthenticated / unauthorized connections immediately
        if isinstance(user, AnonymousUser) or not await _can_access_board(user, self.board_id):
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.debug("WS connect: user=%s board=%s", user, self.board_id)

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.debug("WS disconnect: board=%s code=%s", self.board_id, code)

    # ── Messages received from the client ─────────────────────────────────────

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data or '{}')
        except json.JSONDecodeError:
            return

        event_type = data.get('type')
        if not event_type:
            return

        # Forward to the group so every member sees the change
        await self.channel_layer.group_send(
            self.group_name,
            {'type': event_type.replace('.', '_'), **data},
        )

    # ── Handlers for group messages (one per event type) ──────────────────────
    # Each handler must match the "type" key with dots replaced by underscores.

    async def card_moved(self, event):
        await self.send(text_data=json.dumps({
            'type': 'card.moved',
            'card_id':  event['card_id'],
            'list_id':  event['list_id'],
            'position': event['position'],
        }))

    async def card_created(self, event):
        await self.send(text_data=json.dumps({
            'type': 'card.created',
            'card_id': event['card_id'],
            'list_id': event['list_id'],
            'title':   event['title'],
        }))

    async def card_updated(self, event):
        await self.send(text_data=json.dumps({
            'type':    'card.updated',
            'card_id': event['card_id'],
            'fields':  event.get('fields', {}),
        }))

    async def card_deleted(self, event):
        await self.send(text_data=json.dumps({
            'type':    'card.deleted',
            'card_id': event['card_id'],
        }))

    async def list_moved(self, event):
        await self.send(text_data=json.dumps({
            'type':     'list.moved',
            'list_id':  event['list_id'],
            'position': event['position'],
        }))

    async def list_created(self, event):
        await self.send(text_data=json.dumps({
            'type':     'list.created',
            'list_id':  event['list_id'],
            'board_id': event['board_id'],
            'name':     event['name'],
        }))

    async def list_updated(self, event):
        await self.send(text_data=json.dumps({
            'type':    'list.updated',
            'list_id': event['list_id'],
            'fields':  event.get('fields', {}),
        }))

    async def list_deleted(self, event):
        await self.send(text_data=json.dumps({
            'type':    'list.deleted',
            'list_id': event['list_id'],
        }))

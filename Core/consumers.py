"""
BoardConsumer — WebSocket consumer scoped to a single board.

Connection URL:
    ws://<host>/ws/boards/<board_id>/?token=<auth_token>

Channel group:
    board_<board_id>   — one group per board, all members share it

Events broadcast to the client (type → payload shape):
    card_created    { type, data: Card }
    card_updated    { type, data: Card }
    card_moved      { type, data: Card }
    card_deleted    { type, data: { card_id } }
    list_created    { type, data: List }
    list_updated    { type, data: List }
    list_moved      { type, data: List }
    list_deleted    { type, data: { list_id } }
    comment_created { type, data: Comment }
    comment_updated { type, data: Comment }
    comment_deleted { type, data: { comment_id, card_id } }
    member_added    { type, data: BoardMember }
    member_updated  { type, data: BoardMember }
    member_removed  { type, data: { member_id } }
    board_updated   { type, data: { board_id, fields } }
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

        if isinstance(user, AnonymousUser) or not await _can_access_board(user, self.board_id):
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.debug("WS connect: user=%s board=%s", user, self.board_id)

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.debug("WS disconnect: board=%s code=%s", self.board_id, code)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data or '{}')
        except json.JSONDecodeError:
            return

        event_type = data.get('type')
        if not event_type:
            return

        await self.channel_layer.group_send(
            self.group_name,
            {'type': event_type.replace('.', '_'), **data},
        )

    # ── Generic forwarder — sends {type, data} to the client ─────────────────

    async def _forward(self, event_type, event):
        await self.send(text_data=json.dumps({
            'type': event_type,
            'data': event.get('data'),
        }))

    # ── Card events ───────────────────────────────────────────────────────────

    async def card_created(self, event):
        await self._forward('card_created', event)

    async def card_updated(self, event):
        await self._forward('card_updated', event)

    async def card_moved(self, event):
        await self._forward('card_moved', event)

    async def card_deleted(self, event):
        await self._forward('card_deleted', event)

    # ── List events ───────────────────────────────────────────────────────────

    async def list_created(self, event):
        await self._forward('list_created', event)

    async def list_updated(self, event):
        await self._forward('list_updated', event)

    async def list_moved(self, event):
        await self._forward('list_moved', event)

    async def list_deleted(self, event):
        await self._forward('list_deleted', event)

    # ── Comment events ────────────────────────────────────────────────────────

    async def comment_created(self, event):
        await self._forward('comment_created', event)

    async def comment_updated(self, event):
        await self._forward('comment_updated', event)

    async def comment_deleted(self, event):
        await self._forward('comment_deleted', event)

    # ── Member events ─────────────────────────────────────────────────────────

    async def member_added(self, event):
        await self._forward('member_added', event)

    async def member_updated(self, event):
        await self._forward('member_updated', event)

    async def member_removed(self, event):
        await self._forward('member_removed', event)

    # ── Board events ──────────────────────────────────────────────────────────

    async def board_updated(self, event):
        await self._forward('board_updated', event)

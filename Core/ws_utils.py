import logging

logger = logging.getLogger(__name__)


def ws_broadcast(board_id, payload):
    """Push a WebSocket event to all board_<id> group members.

    Silently no-ops when the channel layer is not configured (e.g. during
    unit tests that don't set up CHANNEL_LAYERS).
    """
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        if channel_layer is None:
            return
        event_type = payload['type'].replace('.', '_')
        async_to_sync(channel_layer.group_send)(
            f'board_{board_id}',
            {'type': event_type, **payload},
        )
    except Exception:
        logger.debug("ws_broadcast failed for board %s", board_id, exc_info=True)

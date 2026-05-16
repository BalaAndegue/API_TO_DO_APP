from rest_framework import viewsets, permissions, mixins
from django.db.models import Q
from Core.models import Activity
from Core.serializers import ActivitySerializer


class ActivityViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Read-only activity feed. Activities are auto-created by signals.
    Supports filtering by ?board=<id> or ?card=<id>.
    """
    serializer_class = ActivitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Activity.objects.none()
        user = self.request.user
        accessible = Q(
            Q(board__visibility='public') |
            Q(board__board_members__user=user) |
            Q(board__creator=user)
        )
        qs = Activity.objects.filter(accessible).distinct()
        board_id = self.request.query_params.get('board')
        card_id = self.request.query_params.get('card')
        if board_id:
            qs = qs.filter(board_id=board_id)
        if card_id:
            qs = qs.filter(card_id=card_id)
        return qs.select_related('board', 'card', 'list', 'user')

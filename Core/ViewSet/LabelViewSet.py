from rest_framework import viewsets, permissions
from django.db.models import Q
from Core.models import Label
from Core.serializers import LabelSerializer
from Core.permissions import _is_board_admin_or_creator


def _accessible_boards_q(user):
    return (
        Q(board__visibility='public') |
        Q(board__board_members__user=user) |
        Q(board__creator=user)
    )


class LabelViewSet(viewsets.ModelViewSet):
    serializer_class = LabelSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Label.objects.none()
        user = self.request.user
        qs = Label.objects.filter(_accessible_boards_q(user)).distinct()
        board_id = self.request.query_params.get('board')
        if board_id:
            qs = qs.filter(board_id=board_id)
        return qs.select_related('board')

    def perform_create(self, serializer):
        board = serializer.validated_data['board']
        if not _is_board_admin_or_creator(board, self.request.user):
            raise permissions.PermissionDenied("Seuls les admins peuvent créer des labels.")
        serializer.save()

    def perform_update(self, serializer):
        board = self.get_object().board
        if not _is_board_admin_or_creator(board, self.request.user):
            raise permissions.PermissionDenied("Seuls les admins peuvent modifier des labels.")
        serializer.save()

    def perform_destroy(self, instance):
        if not _is_board_admin_or_creator(instance.board, self.request.user):
            raise permissions.PermissionDenied("Seuls les admins peuvent supprimer des labels.")
        instance.delete()

from rest_framework import viewsets, permissions
from django.db.models import Q
from Core.models import List, Board
from Core.serializers import ListSerializer


def _user_accessible_boards_q(user):
    return (
        Q(board__visibility='public') |
        Q(board__board_members__user=user) |
        Q(board__creator=user)
    )


class ListViewSet(viewsets.ModelViewSet):
    serializer_class = ListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return List.objects.none()
        user = self.request.user
        qs = List.objects.filter(_user_accessible_boards_q(user)).distinct()

        board_id = self.request.query_params.get('board')
        if board_id:
            qs = qs.filter(board_id=board_id)

        archived = self.request.query_params.get('archived')
        if archived is not None:
            qs = qs.filter(archived=(archived.lower() == 'true'))

        return qs.select_related('board').prefetch_related(
            'cards__card_labels__label',
            'cards__card_members__user',
        )

    def perform_create(self, serializer):
        board = serializer.validated_data['board']
        is_member = (
            board.creator == self.request.user or
            board.board_members.filter(user=self.request.user).exists()
        )
        if board.visibility != 'public' and not is_member:
            raise permissions.PermissionDenied("Vous n'êtes pas membre de ce tableau.")
        serializer.save()

    def perform_update(self, serializer):
        board = self.get_object().board
        is_member = (
            board.creator == self.request.user or
            board.board_members.filter(user=self.request.user).exists()
        )
        if not is_member:
            raise permissions.PermissionDenied("Vous n'êtes pas membre de ce tableau.")
        serializer.save()

    def perform_destroy(self, instance):
        board = instance.board
        is_admin = (
            board.creator == self.request.user or
            board.board_members.filter(user=self.request.user, role='admin').exists()
        )
        if not is_admin:
            raise permissions.PermissionDenied("Seuls les admins peuvent supprimer une liste.")
        instance.delete()

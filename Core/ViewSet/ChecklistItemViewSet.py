from rest_framework import viewsets, permissions
from django.db.models import Q
from Core.models import ChecklistItem
from Core.serializers import ChecklistItemSerializer


def _accessible_boards_q(user):
    return (
        Q(checklist__card__board__visibility='public') |
        Q(checklist__card__board__board_members__user=user) |
        Q(checklist__card__board__creator=user)
    )


class ChecklistItemViewSet(viewsets.ModelViewSet):
    serializer_class = ChecklistItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ChecklistItem.objects.none()
        user = self.request.user
        qs = ChecklistItem.objects.filter(_accessible_boards_q(user)).distinct()
        checklist_id = self.request.query_params.get('checklist')
        if checklist_id:
            qs = qs.filter(checklist_id=checklist_id)
        return qs.select_related('checklist__card__board')

    def _check_board_membership(self, checklist):
        board = checklist.card.board
        if board.visibility == 'public':
            return
        is_member = (
            board.creator == self.request.user or
            board.board_members.filter(user=self.request.user).exists()
        )
        if not is_member:
            raise permissions.PermissionDenied("Vous n'êtes pas membre de ce tableau.")

    def perform_create(self, serializer):
        self._check_board_membership(serializer.validated_data['checklist'])
        serializer.save()

    def perform_update(self, serializer):
        self._check_board_membership(self.get_object().checklist)
        serializer.save()

    def perform_destroy(self, instance):
        self._check_board_membership(instance.checklist)
        instance.delete()

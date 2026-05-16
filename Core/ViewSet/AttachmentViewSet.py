from rest_framework import viewsets, permissions
from django.db.models import Q
from Core.models import Attachment
from Core.serializers import AttachmentSerializer


def _accessible_boards_q(user):
    return (
        Q(card__board__visibility='public') |
        Q(card__board__board_members__user=user) |
        Q(card__board__creator=user)
    )


class AttachmentViewSet(viewsets.ModelViewSet):
    serializer_class = AttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Attachment.objects.none()
        user = self.request.user
        qs = Attachment.objects.filter(_accessible_boards_q(user)).distinct()
        card_id = self.request.query_params.get('card')
        if card_id:
            qs = qs.filter(card_id=card_id)
        return qs.select_related('card__board', 'uploaded_by')

    def _check_board_membership(self, card):
        board = card.board
        if board.visibility == 'public':
            return
        is_member = (
            board.creator == self.request.user or
            board.board_members.filter(user=self.request.user).exists()
        )
        if not is_member:
            raise permissions.PermissionDenied("Vous n'êtes pas membre de ce tableau.")

    def perform_create(self, serializer):
        card = serializer.validated_data['card']
        self._check_board_membership(card)
        serializer.save(uploaded_by=self.request.user)

    def perform_destroy(self, instance):
        is_uploader = instance.uploaded_by == self.request.user
        board = instance.card.board
        is_admin = board.creator == self.request.user or board.board_members.filter(
            user=self.request.user, role='admin'
        ).exists()
        if not (is_uploader or is_admin):
            raise permissions.PermissionDenied("Seul le déposant ou un admin peut supprimer ce fichier.")
        instance.delete()

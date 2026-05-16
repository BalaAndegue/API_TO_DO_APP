from rest_framework import viewsets, permissions
from django.db.models import Q
from Core.models import Comment
from Core.serializers import CommentSerializer


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Comment.objects.none()
        user = self.request.user
        qs = Comment.objects.filter(
            Q(card__board__visibility='public') |
            Q(card__board__board_members__user=user) |
            Q(card__board__creator=user)
        ).distinct()

        card_id = self.request.query_params.get('card')
        if card_id:
            qs = qs.filter(card_id=card_id)

        return qs.select_related('card__board', 'user')

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
        self._check_board_membership(serializer.validated_data['card'])
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        obj = self.get_object()
        board = obj.card.board
        is_author = obj.user == self.request.user
        is_admin = (
            board.creator == self.request.user or
            board.board_members.filter(user=self.request.user, role='admin').exists()
        )
        if not (is_author or is_admin):
            raise permissions.PermissionDenied("Vous ne pouvez modifier que vos propres commentaires.")
        serializer.save()

    def perform_destroy(self, instance):
        board = instance.card.board
        is_author = instance.user == self.request.user
        is_admin = (
            board.creator == self.request.user or
            board.board_members.filter(user=self.request.user, role='admin').exists()
        )
        if not (is_author or is_admin):
            raise permissions.PermissionDenied("Vous ne pouvez supprimer que vos propres commentaires.")
        instance.delete()

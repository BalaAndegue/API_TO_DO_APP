from rest_framework import viewsets, permissions
from django.db.models import Q
from Core.models import CardMember
from Core.serializers import CardMemberSerializer


def _accessible_boards_q(user):
    return (
        Q(card__board__visibility='public') |
        Q(card__board__board_members__user=user) |
        Q(card__board__creator=user)
    )


class CardMemberViewSet(viewsets.ModelViewSet):
    serializer_class = CardMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return CardMember.objects.none()
        user = self.request.user
        qs = CardMember.objects.filter(_accessible_boards_q(user)).distinct()
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
        card = serializer.validated_data['card']
        self._check_board_membership(card)
        user_to_add = serializer.validated_data['user']
        board = card.board
        if not board.board_members.filter(user=user_to_add).exists() and board.creator != user_to_add:
            raise permissions.PermissionDenied("L'utilisateur assigné doit être membre du tableau.")
        serializer.save()

    def perform_destroy(self, instance):
        self._check_board_membership(instance.card)
        instance.delete()

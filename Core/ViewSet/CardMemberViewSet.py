from django.utils.decorators import method_decorator
from rest_framework import viewsets, permissions
from django.db.models import Q
from Core.models import CardMember
from Core.serializers import CardMemberSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

_CARDMEMBER_FILTERS = [
    openapi.Parameter('card', openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                      description='Filtrer par carte (card_id).'),
]


@method_decorator(name='list', decorator=swagger_auto_schema(
    operation_summary='Lister les membres assignés aux cartes',
    operation_description='Retourne les assignations des cartes accessibles. Utiliser **?card=<id>**.',
    manual_parameters=_CARDMEMBER_FILTERS,
    tags=['Card Members'],
))
@method_decorator(name='create', decorator=swagger_auto_schema(
    operation_summary='Assigner un membre à une carte',
    operation_description=(
        'Assigne un utilisateur à une carte. '
        'L\'utilisateur doit être membre du tableau contenant la carte.'
    ),
    tags=['Card Members'],
))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(
    operation_summary='Détail d\'une assignation',
    tags=['Card Members'],
))
@method_decorator(name='update', decorator=swagger_auto_schema(
    operation_summary='Remplacer une assignation',
    tags=['Card Members'],
))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(
    operation_summary='Modifier partiellement une assignation',
    tags=['Card Members'],
))
@method_decorator(name='destroy', decorator=swagger_auto_schema(
    operation_summary='Retirer un membre d\'une carte',
    operation_description='Désassigne l\'utilisateur de la carte. L\'utilisateur reste membre du tableau.',
    tags=['Card Members'],
))
class CardMemberViewSet(viewsets.ModelViewSet):
    serializer_class = CardMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return CardMember.objects.none()
        user = self.request.user
        qs = CardMember.objects.filter(
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
        if not (board.creator == self.request.user or
                board.board_members.filter(user=self.request.user).exists()):
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

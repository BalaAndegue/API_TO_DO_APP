from django.utils.decorators import method_decorator
from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q
from Core.models import CardLabel
from Core.serializers import CardLabelSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

_CARDLABEL_FILTERS = [
    openapi.Parameter('card', openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                      description='Filtrer par carte (card_id).'),
]


@method_decorator(name='list', decorator=swagger_auto_schema(
    operation_summary='Lister les associations carte-label',
    operation_description='Retourne les labels appliqués aux cartes accessibles. Utiliser **?card=<id>**.',
    manual_parameters=_CARDLABEL_FILTERS,
    tags=['Card Labels'],
))
@method_decorator(name='create', decorator=swagger_auto_schema(
    operation_summary='Appliquer un label à une carte',
    operation_description=(
        'Associe un label existant à une carte. '
        'Le label doit appartenir au même tableau que la carte.'
    ),
    tags=['Card Labels'],
))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(
    operation_summary='Détail d\'une association carte-label',
    tags=['Card Labels'],
))
@method_decorator(name='update', decorator=swagger_auto_schema(
    operation_summary='Remplacer une association carte-label',
    tags=['Card Labels'],
))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(
    operation_summary='Modifier partiellement une association carte-label',
    tags=['Card Labels'],
))
@method_decorator(name='destroy', decorator=swagger_auto_schema(
    operation_summary='Retirer un label d\'une carte',
    operation_description='Supprime l\'association. Le label du tableau n\'est pas supprimé.',
    tags=['Card Labels'],
))
class CardLabelViewSet(viewsets.ModelViewSet):
    serializer_class = CardLabelSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return CardLabel.objects.none()
        user = self.request.user
        qs = CardLabel.objects.filter(
            Q(card__board__visibility='public') |
            Q(card__board__board_members__user=user) |
            Q(card__board__creator=user)
        ).distinct()
        card_id = self.request.query_params.get('card')
        if card_id:
            qs = qs.filter(card_id=card_id)
        return qs.select_related('card__board', 'label')

    def _check_board_membership(self, card):
        board = card.board
        if board.visibility == 'public':
            return
        if not (board.creator == self.request.user or
                board.board_members.filter(user=self.request.user).exists()):
            raise PermissionDenied("Vous n'êtes pas membre de ce tableau.")

    def perform_create(self, serializer):
        self._check_board_membership(serializer.validated_data['card'])
        serializer.save()

    def perform_destroy(self, instance):
        self._check_board_membership(instance.card)
        instance.delete()

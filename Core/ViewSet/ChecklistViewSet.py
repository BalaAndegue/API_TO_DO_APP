from django.utils.decorators import method_decorator
from rest_framework import viewsets, permissions
from django.db.models import Q
from Core.models import Checklist
from Core.serializers import ChecklistSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

_CHECKLIST_FILTERS = [
    openapi.Parameter('card', openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                      description='Filtrer par carte (card_id).'),
]


@method_decorator(name='list', decorator=swagger_auto_schema(
    operation_summary='Lister les checklists',
    operation_description=(
        'Retourne les checklists des cartes accessibles. '
        'Chaque checklist inclut **items_total** et **items_checked** pour afficher une barre de progression.'
    ),
    manual_parameters=_CHECKLIST_FILTERS,
    tags=['Checklists'],
))
@method_decorator(name='create', decorator=swagger_auto_schema(
    operation_summary='Créer une checklist',
    operation_description='Ajoute une checklist à une carte. Requiert d\'être membre du tableau.',
    tags=['Checklists'],
))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(
    operation_summary='Détail d\'une checklist',
    operation_description='Retourne la checklist avec tous ses items et les compteurs de progression.',
    tags=['Checklists'],
))
@method_decorator(name='update', decorator=swagger_auto_schema(
    operation_summary='Mettre à jour une checklist (remplacement complet)',
    tags=['Checklists'],
))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(
    operation_summary='Renommer ou repositionner une checklist',
    tags=['Checklists'],
))
@method_decorator(name='destroy', decorator=swagger_auto_schema(
    operation_summary='Supprimer une checklist',
    operation_description='Supprime la checklist et tous ses items.',
    tags=['Checklists'],
))
class ChecklistViewSet(viewsets.ModelViewSet):
    serializer_class = ChecklistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Checklist.objects.none()
        user = self.request.user
        qs = Checklist.objects.filter(
            Q(card__board__visibility='public') |
            Q(card__board__board_members__user=user) |
            Q(card__board__creator=user)
        ).distinct()
        card_id = self.request.query_params.get('card')
        if card_id:
            qs = qs.filter(card_id=card_id)
        return qs.select_related('card__board').prefetch_related('items')

    def _check_board_membership(self, card):
        board = card.board
        if board.visibility == 'public':
            return
        if not (board.creator == self.request.user or
                board.board_members.filter(user=self.request.user).exists()):
            raise permissions.PermissionDenied("Vous n'êtes pas membre de ce tableau.")

    def perform_create(self, serializer):
        self._check_board_membership(serializer.validated_data['card'])
        serializer.save()

    def perform_update(self, serializer):
        self._check_board_membership(self.get_object().card)
        serializer.save()

    def perform_destroy(self, instance):
        self._check_board_membership(instance.card)
        instance.delete()

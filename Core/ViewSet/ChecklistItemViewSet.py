from django.utils.decorators import method_decorator
from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q
from Core.models import ChecklistItem
from Core.serializers import ChecklistItemSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

_ITEM_FILTERS = [
    openapi.Parameter('checklist', openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                      description='Filtrer par checklist (checklist_id).'),
]


@method_decorator(name='list', decorator=swagger_auto_schema(
    operation_summary='Lister les items de checklist',
    operation_description='Retourne les items accessibles. Utiliser **?checklist=<id>** pour filtrer.',
    manual_parameters=_ITEM_FILTERS,
    tags=['Checklist Items'],
))
@method_decorator(name='create', decorator=swagger_auto_schema(
    operation_summary='Ajouter un item à une checklist',
    operation_description='Crée un item (non coché par défaut). Requiert d\'être membre du tableau.',
    tags=['Checklist Items'],
))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(
    operation_summary='Détail d\'un item de checklist',
    tags=['Checklist Items'],
))
@method_decorator(name='update', decorator=swagger_auto_schema(
    operation_summary='Mettre à jour un item (remplacement complet)',
    tags=['Checklist Items'],
))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(
    operation_summary='Cocher/décocher ou renommer un item',
    operation_description=(
        'Exemple pour cocher : `{"checked": true}`. '
        'Le signal Django crée automatiquement une entrée dans le fil d\'activité.'
    ),
    tags=['Checklist Items'],
))
@method_decorator(name='destroy', decorator=swagger_auto_schema(
    operation_summary='Supprimer un item de checklist',
    tags=['Checklist Items'],
))
class ChecklistItemViewSet(viewsets.ModelViewSet):
    serializer_class = ChecklistItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ChecklistItem.objects.none()
        user = self.request.user
        qs = ChecklistItem.objects.filter(
            Q(checklist__card__board__visibility='public') |
            Q(checklist__card__board__board_members__user=user) |
            Q(checklist__card__board__creator=user)
        ).distinct()
        checklist_id = self.request.query_params.get('checklist')
        if checklist_id:
            qs = qs.filter(checklist_id=checklist_id)
        return qs.select_related('checklist__card__board')

    def _check_board_membership(self, checklist):
        board = checklist.card.board
        if board.visibility == 'public':
            return
        if not (board.creator == self.request.user or
                board.board_members.filter(user=self.request.user).exists()):
            raise PermissionDenied("Vous n'êtes pas membre de ce tableau.")

    def perform_create(self, serializer):
        self._check_board_membership(serializer.validated_data['checklist'])
        serializer.save()

    def perform_update(self, serializer):
        self._check_board_membership(self.get_object().checklist)
        serializer.save()

    def perform_destroy(self, instance):
        self._check_board_membership(instance.checklist)
        instance.delete()

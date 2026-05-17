from django.utils.decorators import method_decorator
from rest_framework import viewsets, permissions
from django.db.models import Q
from Core.models import List
from Core.serializers import ListSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

_LIST_FILTERS = [
    openapi.Parameter('board', openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                      description='Filtrer par tableau (board_id).'),
    openapi.Parameter('archived', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN,
                      description='true = listes archivées, false = actives.'),
]


@method_decorator(name='list', decorator=swagger_auto_schema(
    operation_summary='Lister les listes accessibles',
    operation_description='Retourne les listes des tableaux accessibles. Utiliser **?board=<id>** pour filtrer.',
    manual_parameters=_LIST_FILTERS,
    tags=['Lists'],
))
@method_decorator(name='create', decorator=swagger_auto_schema(
    operation_summary='Créer une liste',
    operation_description='Crée une colonne dans un tableau. Requiert d\'être membre du tableau.',
    tags=['Lists'],
))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(
    operation_summary='Détail d\'une liste',
    operation_description='Retourne la liste avec ses cartes (données légères : titre, position, labels, membres).',
    tags=['Lists'],
))
@method_decorator(name='update', decorator=swagger_auto_schema(
    operation_summary='Mettre à jour une liste (remplacement complet)',
    tags=['Lists'],
))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(
    operation_summary='Renommer ou repositionner une liste',
    operation_description='Modification partielle : nom, position, archived.',
    tags=['Lists'],
))
@method_decorator(name='destroy', decorator=swagger_auto_schema(
    operation_summary='Supprimer une liste',
    operation_description='Supprime la liste et toutes ses cartes. Requiert le rôle **admin**.',
    tags=['Lists'],
))
class ListViewSet(viewsets.ModelViewSet):
    serializer_class = ListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return List.objects.none()
        user = self.request.user
        qs = List.objects.filter(
            Q(board__visibility='public') |
            Q(board__board_members__user=user) |
            Q(board__creator=user)
        ).distinct()
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

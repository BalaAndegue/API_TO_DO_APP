from django.utils.decorators import method_decorator
from rest_framework import viewsets, permissions
from django.db.models import Q
from Core.models import Label
from Core.serializers import LabelSerializer
from Core.permissions import _is_board_admin_or_creator
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

_LABEL_FILTERS = [
    openapi.Parameter('board', openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                      description='Filtrer par tableau (board_id).'),
]


@method_decorator(name='list', decorator=swagger_auto_schema(
    operation_summary='Lister les labels accessibles',
    operation_description='Retourne les labels des tableaux accessibles. Utiliser **?board=<id>** pour filtrer.',
    manual_parameters=_LABEL_FILTERS,
    tags=['Labels'],
))
@method_decorator(name='create', decorator=swagger_auto_schema(
    operation_summary='Créer un label',
    operation_description='Crée un label coloré pour un tableau. Requiert le rôle **admin**.',
    tags=['Labels'],
))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(
    operation_summary='Détail d\'un label',
    tags=['Labels'],
))
@method_decorator(name='update', decorator=swagger_auto_schema(
    operation_summary='Mettre à jour un label (remplacement complet)',
    operation_description='Requiert le rôle **admin** sur le tableau.',
    tags=['Labels'],
))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(
    operation_summary='Modifier le nom ou la couleur d\'un label',
    operation_description='Requiert le rôle **admin** sur le tableau.',
    tags=['Labels'],
))
@method_decorator(name='destroy', decorator=swagger_auto_schema(
    operation_summary='Supprimer un label',
    operation_description='Supprime le label et le retire automatiquement des cartes associées. Requiert **admin**.',
    tags=['Labels'],
))
class LabelViewSet(viewsets.ModelViewSet):
    serializer_class = LabelSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Label.objects.none()
        user = self.request.user
        qs = Label.objects.filter(
            Q(board__visibility='public') |
            Q(board__board_members__user=user) |
            Q(board__creator=user)
        ).distinct()
        board_id = self.request.query_params.get('board')
        if board_id:
            qs = qs.filter(board_id=board_id)
        return qs.select_related('board')

    def perform_create(self, serializer):
        board = serializer.validated_data['board']
        if not _is_board_admin_or_creator(board, self.request.user):
            raise permissions.PermissionDenied("Seuls les admins peuvent créer des labels.")
        serializer.save()

    def perform_update(self, serializer):
        board = self.get_object().board
        if not _is_board_admin_or_creator(board, self.request.user):
            raise permissions.PermissionDenied("Seuls les admins peuvent modifier des labels.")
        serializer.save()

    def perform_destroy(self, instance):
        if not _is_board_admin_or_creator(instance.board, self.request.user):
            raise permissions.PermissionDenied("Seuls les admins peuvent supprimer des labels.")
        instance.delete()

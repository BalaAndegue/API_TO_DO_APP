from django.utils.decorators import method_decorator
from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from Core.models import BoardMember
from Core.serializers import BoardMemberSerializer
from Core.permissions import IsBoardAdmin
from Core.ws_utils import ws_broadcast
from drf_yasg.utils import swagger_auto_schema


@method_decorator(name='list', decorator=swagger_auto_schema(
    operation_summary='Lister les membres des tableaux',
    operation_description='Retourne tous les membres des tableaux auxquels l\'utilisateur appartient.',
    tags=['Board Members'],
))
@method_decorator(name='create', decorator=swagger_auto_schema(
    operation_summary='Ajouter un membre directement',
    operation_description=(
        'Ajoute un utilisateur comme membre d\'un tableau sans passer par une invitation. '
        'Requiert le rôle **admin**. Préférer **POST /boards/{id}/invite/** pour envoyer un email.'
    ),
    tags=['Board Members'],
))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(
    operation_summary='Détail d\'un membre',
    tags=['Board Members'],
))
@method_decorator(name='update', decorator=swagger_auto_schema(
    operation_summary='Remplacer le rôle d\'un membre (remplacement complet)',
    operation_description='Requiert le rôle **admin** sur le tableau.',
    tags=['Board Members'],
))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(
    operation_summary='Changer le rôle d\'un membre',
    operation_description=(
        'Change le rôle d\'un membre (`admin`, `member`, `observer`). '
        'Requiert le rôle **admin** sur le tableau.'
    ),
    tags=['Board Members'],
))
@method_decorator(name='destroy', decorator=swagger_auto_schema(
    operation_summary='Retirer un membre du tableau',
    operation_description='Requiert le rôle **admin** sur le tableau.',
    tags=['Board Members'],
))
class BoardMemberViewSet(viewsets.ModelViewSet):
    serializer_class = BoardMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return BoardMember.objects.none()
        user = self.request.user
        return BoardMember.objects.filter(
            board__board_members__user=user
        ).distinct().select_related('board', 'user')

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update']:
            return [IsBoardAdmin()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        board = serializer.validated_data['board']
        if not (board.creator == self.request.user or
                board.board_members.filter(user=self.request.user, role='admin').exists()):
            raise PermissionDenied("Seul un admin peut ajouter des membres.")
        instance = serializer.save()
        ws_broadcast(board.pk, {
            'type': 'member.added',
            'data': BoardMemberSerializer(instance).data,
        })

    def perform_update(self, serializer):
        instance = serializer.save()
        ws_broadcast(instance.board_id, {
            'type': 'member.updated',
            'data': BoardMemberSerializer(instance).data,
        })

    def perform_destroy(self, instance):
        board = instance.board
        is_self_removal = instance.user == self.request.user
        is_admin = (
            board.creator == self.request.user or
            board.board_members.filter(user=self.request.user, role='admin').exists()
        )
        if not (is_admin or is_self_removal):
            raise PermissionDenied("Seul un admin peut retirer des membres.")
        board_id = board.pk
        member_id = instance.pk
        instance.delete()
        ws_broadcast(board_id, {
            'type': 'member.removed',
            'data': {'member_id': member_id},
        })

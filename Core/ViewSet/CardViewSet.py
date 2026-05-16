from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.db import transaction
from Core.models import Card, List
from Core.serializers import CardSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


def _user_accessible_boards_q(user):
    return (
        Q(board__visibility='public') |
        Q(board__board_members__user=user) |
        Q(board__creator=user)
    )


class CardViewSet(viewsets.ModelViewSet):
    serializer_class = CardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Card.objects.none()
        user = self.request.user
        qs = Card.objects.filter(_user_accessible_boards_q(user)).distinct()

        list_id = self.request.query_params.get('list')
        if list_id:
            qs = qs.filter(list_id=list_id)

        board_id = self.request.query_params.get('board')
        if board_id:
            qs = qs.filter(board_id=board_id)

        archived = self.request.query_params.get('archived')
        if archived is not None:
            qs = qs.filter(archived=(archived.lower() == 'true'))

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))

        return qs.select_related('list', 'board').prefetch_related(
            'card_labels__label',
            'card_members__user',
            'checklists__items',
            'attachments__uploaded_by',
        )

    def perform_create(self, serializer):
        list_obj = serializer.validated_data['list']
        board = list_obj.board
        is_member = (
            board.creator == self.request.user or
            board.board_members.filter(user=self.request.user).exists()
        )
        if board.visibility != 'public' and not is_member:
            raise permissions.PermissionDenied("Vous n'êtes pas membre de ce tableau.")
        serializer.save(board=board)

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
        is_member = (
            board.creator == self.request.user or
            board.board_members.filter(user=self.request.user).exists()
        )
        if not is_member:
            raise permissions.PermissionDenied("Vous n'êtes pas membre de ce tableau.")
        instance.delete()

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['position'],
            properties={
                'position': openapi.Schema(type=openapi.TYPE_INTEGER, description="Nouvelle position dans la liste"),
                'list_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID de la liste cible (même tableau)"),
            },
        ),
        responses={200: CardSerializer, 400: "Bad Request", 404: "Liste introuvable"},
        operation_summary="Déplacer une carte",
        tags=["Cartes"],
    )
    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        """
        Move a card to a new position and/or a different list within the same board.
        Body: { position: int, list_id?: int }
        """
        card = self.get_object()
        new_position = request.data.get('position')
        new_list_id = request.data.get('list_id')

        if new_position is None:
            return Response(
                {'success': False, 'message': "Le champ 'position' est requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            if new_list_id and int(new_list_id) != card.list_id:
                try:
                    new_list = List.objects.select_related('board').get(pk=new_list_id)
                except List.DoesNotExist:
                    return Response(
                        {'success': False, 'message': "Liste introuvable."},
                        status=status.HTTP_404_NOT_FOUND,
                    )
                if new_list.board_id != card.board_id:
                    return Response(
                        {'success': False, 'message': "Impossible de déplacer vers un tableau différent."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                card.list = new_list

            card.position = int(new_position)
            card.save(update_fields=['list', 'position', 'updated_at'])

        return Response(
            {'success': True, 'data': CardSerializer(card).data},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive (soft-delete) a card."""
        card = self.get_object()
        card.archived = True
        card.save(update_fields=['archived', 'updated_at'])
        return Response({'success': True, 'message': "Carte archivée."})

    @action(detail=True, methods=['post'])
    def unarchive(self, request, pk=None):
        """Restore an archived card."""
        card = self.get_object()
        card.archived = False
        card.save(update_fields=['archived', 'updated_at'])
        return Response({'success': True, 'message': "Carte restaurée."})

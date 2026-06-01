from django.utils.decorators import method_decorator
from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, F
from django.db import transaction
from Core.models import Card, List
from Core.serializers import CardSerializer
from Core.ws_utils import ws_broadcast
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

_CARD_FILTERS = [
    openapi.Parameter('list', openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                      description='Filtrer par liste (list_id).'),
    openapi.Parameter('board', openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                      description='Filtrer par tableau (board_id).'),
    openapi.Parameter('archived', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN,
                      description='true = cartes archivées, false = actives.'),
    openapi.Parameter('search', openapi.IN_QUERY, type=openapi.TYPE_STRING,
                      description='Recherche plein-texte sur le titre et la description.'),
]


@method_decorator(name='list', decorator=swagger_auto_schema(
    operation_summary='Lister les cartes accessibles',
    operation_description=(
        'Retourne les cartes des tableaux accessibles. '
        'Filtres disponibles : **?list**, **?board**, **?archived**, **?search**.'
    ),
    manual_parameters=_CARD_FILTERS,
    tags=['Cards'],
))
@method_decorator(name='create', decorator=swagger_auto_schema(
    operation_summary='Créer une carte',
    operation_description=(
        'Crée une carte dans une liste. Le champ **board** est déduit automatiquement '
        'depuis la liste — inutile de le fournir.'
    ),
    tags=['Cards'],
))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(
    operation_summary='Détail complet d\'une carte',
    operation_description=(
        'Retourne la carte avec : labels, membres assignés, checklists (avec items '
        'et progression), pièces jointes, et le nombre de commentaires.'
    ),
    tags=['Cards'],
))
@method_decorator(name='update', decorator=swagger_auto_schema(
    operation_summary='Mettre à jour une carte (remplacement complet)',
    tags=['Cards'],
))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(
    operation_summary='Modifier partiellement une carte',
    operation_description='Met à jour un ou plusieurs champs : titre, description, due_date, cover_image_url, etc.',
    tags=['Cards'],
))
@method_decorator(name='destroy', decorator=swagger_auto_schema(
    operation_summary='Supprimer définitivement une carte',
    operation_description='Supprime la carte et tout son contenu (checklists, commentaires, pièces jointes).',
    tags=['Cards'],
))
class CardViewSet(viewsets.ModelViewSet):
    serializer_class = CardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Card.objects.none()
        user = self.request.user
        qs = Card.objects.filter(
            Q(board__visibility='public') |
            Q(board__board_members__user=user) |
            Q(board__creator=user)
        ).distinct()
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
            raise PermissionDenied("Vous n'êtes pas membre de ce tableau.")
        instance = serializer.save(board=board)
        ws_broadcast(board.pk, {
            'type': 'card.created',
            'data': CardSerializer(instance).data,
        })

    def perform_update(self, serializer):
        board = self.get_object().board
        is_member = (
            board.creator == self.request.user or
            board.board_members.filter(user=self.request.user).exists()
        )
        if not is_member:
            raise PermissionDenied("Vous n'êtes pas membre de ce tableau.")
        instance = serializer.save()
        ws_broadcast(instance.board_id, {
            'type': 'card.updated',
            'data': CardSerializer(instance).data,
        })

    def perform_destroy(self, instance):
        board = instance.board
        is_member = (
            board.creator == self.request.user or
            board.board_members.filter(user=self.request.user).exists()
        )
        if not is_member:
            raise PermissionDenied("Vous n'êtes pas membre de ce tableau.")
        board_id = board.pk
        card_id = instance.pk
        instance.delete()
        ws_broadcast(board_id, {
            'type': 'card.deleted',
            'data': {'card_id': card_id},
        })

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['position'],
            properties={
                'position': openapi.Schema(type=openapi.TYPE_INTEGER,
                                           description='Nouvelle position (index 0) dans la liste.'),
                'list_id': openapi.Schema(type=openapi.TYPE_INTEGER,
                                          description='ID de la liste cible (optionnel, même tableau uniquement).'),
            },
        ),
        responses={
            200: CardSerializer,
            400: 'Position manquante ou liste dans un autre tableau.',
            404: 'Liste introuvable.',
        },
        operation_summary='Déplacer une carte',
        operation_description=(
            'Change la position d\'une carte dans sa liste ou la déplace dans une autre liste '
            'du même tableau. Utiliser un **PATCH** standard pour modifier les champs de la carte.'
        ),
        tags=['Cards'],
    )
    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        card = self.get_object()
        new_position = request.data.get('position')
        new_list_id  = request.data.get('list_id')

        if new_position is None:
            return Response(
                {'success': False, 'message': "Le champ 'position' est requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_position = int(new_position)

        with transaction.atomic():
            old_list_id  = card.list_id
            old_position = card.position

            if new_list_id and int(new_list_id) != old_list_id:
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
                Card.objects.filter(
                    list_id=old_list_id, position__gt=old_position
                ).update(position=F('position') - 1)
                Card.objects.filter(
                    list_id=new_list_id, position__gte=new_position
                ).update(position=F('position') + 1)
                card.list = new_list
            else:
                if new_position < old_position:
                    Card.objects.filter(
                        list_id=old_list_id,
                        position__gte=new_position,
                        position__lt=old_position,
                    ).exclude(pk=card.pk).update(position=F('position') + 1)
                elif new_position > old_position:
                    Card.objects.filter(
                        list_id=old_list_id,
                        position__gt=old_position,
                        position__lte=new_position,
                    ).exclude(pk=card.pk).update(position=F('position') - 1)
                else:
                    return Response({'success': True, 'data': CardSerializer(card).data})

            card.position = new_position
            card.save(update_fields=['list', 'position', 'updated_at'])

        serialized = CardSerializer(card).data
        ws_broadcast(card.board_id, {
            'type': 'card.moved',
            'data': serialized,
        })
        return Response({'success': True, 'data': serialized})

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(type=openapi.TYPE_OBJECT, properties={}),
        responses={200: 'Carte archivée.'},
        operation_summary='Archiver une carte (soft delete)',
        operation_description='Masque la carte sans la supprimer. Récupérable via **unarchive**.',
        tags=['Cards'],
    )
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        card = self.get_object()
        card.archived = True
        card.save(update_fields=['archived', 'updated_at'])
        ws_broadcast(card.board_id, {
            'type': 'card.updated',
            'data': CardSerializer(card).data,
        })
        return Response({'success': True, 'message': "Carte archivée."})

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(type=openapi.TYPE_OBJECT, properties={}),
        responses={200: 'Carte restaurée.'},
        operation_summary='Restaurer une carte archivée',
        operation_description='Remet la carte dans sa liste d\'origine.',
        tags=['Cards'],
    )
    @action(detail=True, methods=['post'])
    def unarchive(self, request, pk=None):
        card = self.get_object()
        card.archived = False
        card.save(update_fields=['archived', 'updated_at'])
        ws_broadcast(card.board_id, {
            'type': 'card.updated',
            'data': CardSerializer(card).data,
        })
        return Response({'success': True, 'message': "Carte restaurée."})

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(type=openapi.TYPE_OBJECT, properties={}),
        responses={201: CardSerializer},
        operation_summary='Copier une carte',
        operation_description=(
            'Crée une copie de la carte (titre, description, due_date) dans la même liste. '
            'Les checklists, labels et membres ne sont pas copiés.'
        ),
        tags=['Cards'],
    )
    @action(detail=True, methods=['post'])
    def copy(self, request, pk=None):
        card = self.get_object()
        board = card.board
        is_member = (
            board.creator == request.user or
            board.board_members.filter(user=request.user).exists()
        )
        if not is_member:
            raise PermissionDenied("Vous n'êtes pas membre de ce tableau.")
        # Insert copy after the original card
        Card.objects.filter(
            list_id=card.list_id, position__gt=card.position
        ).update(position=F('position') + 1)
        copy = Card.objects.create(
            title=f"{card.title} (copie)",
            description=card.description,
            list=card.list,
            board=board,
            position=card.position + 1,
            due_date=card.due_date,
            start_date=card.start_date,
        )
        serialized = CardSerializer(copy).data
        ws_broadcast(board.pk, {
            'type': 'card.created',
            'data': serialized,
        })
        return Response({'success': True, 'data': serialized}, status=status.HTTP_201_CREATED)

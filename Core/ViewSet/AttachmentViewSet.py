from django.utils.decorators import method_decorator
from rest_framework import viewsets, permissions
from django.db.models import Q
from Core.models import Attachment
from Core.serializers import AttachmentSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

_ATTACH_FILTERS = [
    openapi.Parameter('card', openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                      description='Filtrer par carte (card_id).'),
]


@method_decorator(name='list', decorator=swagger_auto_schema(
    operation_summary='Lister les pièces jointes',
    operation_description='Retourne les pièces jointes des cartes accessibles. Utiliser **?card=<id>**.',
    manual_parameters=_ATTACH_FILTERS,
    tags=['Attachments'],
))
@method_decorator(name='create', decorator=swagger_auto_schema(
    operation_summary='Enregistrer une pièce jointe',
    operation_description=(
        'Enregistre les métadonnées d\'un fichier déjà hébergé (S3, Cloudinary…). '
        'Le champ **uploaded_by** est automatiquement défini sur l\'utilisateur connecté. '
        'Fournir : **card**, **filename**, **url**, **mime_type**, **size** (en octets).'
    ),
    tags=['Attachments'],
))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(
    operation_summary='Détail d\'une pièce jointe',
    tags=['Attachments'],
))
@method_decorator(name='update', decorator=swagger_auto_schema(
    operation_summary='Remplacer les métadonnées d\'une pièce jointe',
    tags=['Attachments'],
))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(
    operation_summary='Modifier partiellement les métadonnées d\'une pièce jointe',
    tags=['Attachments'],
))
@method_decorator(name='destroy', decorator=swagger_auto_schema(
    operation_summary='Supprimer une pièce jointe',
    operation_description='Réservé au déposant ou à un admin du tableau.',
    tags=['Attachments'],
))
class AttachmentViewSet(viewsets.ModelViewSet):
    serializer_class = AttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Attachment.objects.none()
        user = self.request.user
        qs = Attachment.objects.filter(
            Q(card__board__visibility='public') |
            Q(card__board__board_members__user=user) |
            Q(card__board__creator=user)
        ).distinct()
        card_id = self.request.query_params.get('card')
        if card_id:
            qs = qs.filter(card_id=card_id)
        return qs.select_related('card__board', 'uploaded_by')

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
        serializer.save(uploaded_by=self.request.user)

    def perform_destroy(self, instance):
        is_uploader = instance.uploaded_by == self.request.user
        board = instance.card.board
        is_admin = board.creator == self.request.user or board.board_members.filter(
            user=self.request.user, role='admin'
        ).exists()
        if not (is_uploader or is_admin):
            raise permissions.PermissionDenied("Seul le déposant ou un admin peut supprimer ce fichier.")
        instance.delete()

from django.utils.decorators import method_decorator
from rest_framework import viewsets, permissions, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from Core.models import BoardInvitation, BoardMember
from Core.serializers import BoardInvitationSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

logger = logging.getLogger(__name__)


@method_decorator(name='list', decorator=swagger_auto_schema(
    operation_summary='Lister les invitations',
    operation_description=(
        'Retourne les invitations des tableaux que vous administrez. '
        'Utiliser **?pending=true** pour filtrer les non acceptées. '
        'Pour inviter quelqu\'un, utiliser **POST /boards/{id}/invite/**.'
    ),
    tags=['Invitations'],
))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(
    operation_summary='Détail d\'une invitation',
    tags=['Invitations'],
))
@method_decorator(name='destroy', decorator=swagger_auto_schema(
    operation_summary='Annuler une invitation',
    operation_description='Supprime l\'invitation. L\'email invité ne pourra plus accepter le token.',
    tags=['Invitations'],
))
class BoardInvitationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = BoardInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return BoardInvitation.objects.none()
        user = self.request.user
        qs = BoardInvitation.objects.filter(
            board__board_members__user=user,
            board__board_members__role=BoardMember.Role.ADMIN,
        ).select_related('board', 'inviter').distinct()
        pending = self.request.query_params.get('pending')
        if pending is not None:
            qs = qs.filter(accepted=not (pending.lower() == 'true'))
        return qs

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['token'],
            properties={
                'token': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format='uuid',
                    description='Token UUID reçu dans l\'email d\'invitation.',
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description='Invitation acceptée — utilisateur ajouté au tableau.',
                examples={'application/json': {
                    'success': True,
                    'message': "Invitation acceptée. Bienvenue dans le tableau !",
                    'board_id': 1,
                    'board_name': 'Mon tableau',
                }},
            ),
            400: 'Token manquant.',
            404: 'Token invalide ou invitation déjà utilisée.',
        },
        operation_summary='Accepter une invitation',
        operation_description=(
            'Valide le token UUID reçu par email et ajoute l\'utilisateur connecté '
            'comme **member** du tableau correspondant.\n\n'
            'L\'opération est atomique : si l\'utilisateur est déjà membre, '
            'l\'invitation est quand même marquée comme acceptée.'
        ),
        tags=['Invitations'],
    )
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def accept(self, request):
        token = request.data.get('token')
        if not token:
            return Response(
                {'success': False, 'message': 'Le token est requis.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            invitation = BoardInvitation.objects.select_related('board').get(
                token=token, accepted=False
            )
        except BoardInvitation.DoesNotExist:
            return Response(
                {'success': False, 'message': 'Token invalide ou invitation déjà utilisée.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        with transaction.atomic():
            if BoardMember.objects.filter(board=invitation.board, user=request.user).exists():
                invitation.accepted = True
                invitation.save()
                return Response(
                    {'success': True, 'message': 'Vous êtes déjà membre de ce tableau.'},
                    status=status.HTTP_200_OK,
                )
            invitation.accepted = True
            invitation.save()
            BoardMember.objects.create(
                board=invitation.board,
                user=request.user,
                role=invitation.role,
            )

        logger.info("User %s accepted invitation to board %s", request.user, invitation.board)
        return Response(
            {
                'success': True,
                'message': "Invitation acceptée. Bienvenue dans le tableau !",
                'board_id': invitation.board.pk,
                'board_name': invitation.board.name,
            },
            status=status.HTTP_200_OK,
        )

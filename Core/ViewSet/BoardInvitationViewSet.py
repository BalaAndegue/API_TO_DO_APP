from rest_framework import viewsets, permissions, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from Core.models import BoardInvitation, BoardMember
from Core.serializers import BoardInvitationSerializer
import logging

logger = logging.getLogger(__name__)


class BoardInvitationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    Invitations management.
    - List: shows invitations for boards the user administers.
    - accept: POST /invitations/accept/ with {token} to join a board.
    """
    serializer_class = BoardInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return BoardInvitation.objects.none()
        user = self.request.user
        # Only see invitations for boards you administer
        return BoardInvitation.objects.filter(
            board__board_members__user=user,
            board__board_members__role=BoardMember.Role.ADMIN,
        ).select_related('board', 'inviter').distinct()

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
                role=BoardMember.Role.MEMBER,
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

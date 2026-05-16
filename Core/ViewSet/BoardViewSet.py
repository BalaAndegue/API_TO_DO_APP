from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from Core.models import Board, BoardMember, BoardInvitation
from Core.serializers import BoardSerializer, BoardListSerializer, BoardMemberSerializer, BoardInvitationSerializer
from Core.permissions import IsBoardAdmin
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

logger = logging.getLogger(__name__)


def _user_accessible_boards(user):
    return Board.objects.filter(
        Q(visibility='public') |
        Q(board_members__user=user) |
        Q(creator=user)
    ).distinct()


class BoardViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return BoardListSerializer
        return BoardSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Board.objects.none()
        user = self.request.user
        qs = _user_accessible_boards(user)
        is_closed = self.request.query_params.get('is_closed')
        if is_closed is not None:
            qs = qs.filter(is_closed=(is_closed.lower() == 'true'))
        visibility = self.request.query_params.get('visibility')
        if visibility:
            qs = qs.filter(visibility=visibility)
        if self.action == 'list':
            return qs.select_related('creator')
        return qs.select_related('creator').prefetch_related(
            'lists', 'board_members__user',
        )

    def perform_create(self, serializer):
        board = serializer.save(creator=self.request.user)
        BoardMember.objects.create(board=board, user=self.request.user, role=BoardMember.Role.ADMIN)

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email'),
                'role': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['member', 'observer'],
                    default='member',
                ),
            },
        ),
        responses={201: BoardInvitationSerializer, 400: 'Bad Request'},
        operation_summary="Inviter un utilisateur par email",
        tags=["Tableaux"],
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsBoardAdmin])
    def invite(self, request, pk=None):
        board = self.get_object()
        email = request.data.get('email', '').strip().lower()
        if not email:
            return Response({'success': False, 'message': "L'email est requis."}, status=status.HTTP_400_BAD_REQUEST)

        if BoardMember.objects.filter(board=board, user__email=email).exists():
            return Response({'success': False, 'message': "Cet utilisateur est déjà membre."}, status=status.HTTP_400_BAD_REQUEST)

        if BoardInvitation.objects.filter(board=board, email=email, accepted=False).exists():
            return Response({'success': False, 'message': "Une invitation est déjà en attente pour cet email."}, status=status.HTTP_400_BAD_REQUEST)

        invitation = BoardInvitation.objects.create(board=board, inviter=request.user, email=email)

        try:
            accept_url = f"{request.scheme}://{request.get_host()}/api/invitations/accept/"
            send_mail(
                subject=f"Invitation au tableau « {board.name} »",
                message=(
                    f"{request.user.get_full_name() or request.user.username} vous invite à rejoindre"
                    f" le tableau « {board.name} ».\n\n"
                    f"Utilisez le token suivant via POST {accept_url} :\n"
                    f"  token: {invitation.token}\n\n"
                    "Cette invitation est valable 7 jours."
                ),
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=True,
            )
        except Exception:
            logger.warning("Échec d'envoi d'email d'invitation pour %s", email)

        return Response(BoardInvitationSerializer(invitation).data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        method='get',
        responses={200: BoardMemberSerializer(many=True)},
        operation_summary="Lister les membres du tableau",
        tags=["Tableaux"],
    )
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        board = self.get_object()
        members = BoardMember.objects.filter(board=board).select_related('user')
        return Response(BoardMemberSerializer(members, many=True).data)

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Archive (close) the board."""
        board = self.get_object()
        if not (board.creator == request.user or
                board.board_members.filter(user=request.user, role=BoardMember.Role.ADMIN).exists()):
            return Response({'success': False, 'message': "Permission refusée."}, status=status.HTTP_403_FORBIDDEN)
        board.is_closed = True
        board.save(update_fields=['is_closed', 'updated_at'])
        return Response({'success': True, 'message': "Tableau archivé."})

    @action(detail=True, methods=['post'])
    def reopen(self, request, pk=None):
        """Reopen a closed board."""
        board = self.get_object()
        if not (board.creator == request.user or
                board.board_members.filter(user=request.user, role=BoardMember.Role.ADMIN).exists()):
            return Response({'success': False, 'message': "Permission refusée."}, status=status.HTTP_403_FORBIDDEN)
        board.is_closed = False
        board.save(update_fields=['is_closed', 'updated_at'])
        return Response({'success': True, 'message': "Tableau réouvert."})

from django.utils.decorators import method_decorator
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

_BOARD_FILTERS = [
    openapi.Parameter('is_closed', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN,
                      description='Filtrer les tableaux archivés (true) ou actifs (false).'),
    openapi.Parameter('visibility', openapi.IN_QUERY, type=openapi.TYPE_STRING,
                      enum=['public', 'private', 'workspace'],
                      description='Filtrer par visibilité.'),
]


def _user_accessible_boards(user):
    return Board.objects.filter(
        Q(visibility='public') |
        Q(board_members__user=user) |
        Q(creator=user)
    ).distinct()


@method_decorator(name='list', decorator=swagger_auto_schema(
    operation_summary='Lister les tableaux accessibles',
    operation_description=(
        'Retourne tous les tableaux publics + les tableaux dont l\'utilisateur '
        'est membre ou créateur. Résultats paginés (20/page).'
    ),
    manual_parameters=_BOARD_FILTERS,
    tags=['Boards'],
))
@method_decorator(name='create', decorator=swagger_auto_schema(
    operation_summary='Créer un tableau',
    operation_description=(
        'Crée un nouveau tableau. Le créateur est automatiquement ajouté '
        'comme membre avec le rôle **admin**.'
    ),
    tags=['Boards'],
))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(
    operation_summary='Détail d\'un tableau',
    operation_description='Retourne le tableau avec ses listes (résumé) et la liste de ses membres.',
    tags=['Boards'],
))
@method_decorator(name='update', decorator=swagger_auto_schema(
    operation_summary='Mettre à jour un tableau (remplacement complet)',
    tags=['Boards'],
))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(
    operation_summary='Mettre à jour un tableau (partiel)',
    operation_description='Met à jour un ou plusieurs champs du tableau.',
    tags=['Boards'],
))
@method_decorator(name='destroy', decorator=swagger_auto_schema(
    operation_summary='Supprimer un tableau',
    operation_description='Supprime définitivement le tableau et tout son contenu (listes, cartes, etc.).',
    tags=['Boards'],
))
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
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email',
                                        description='Email de l\'utilisateur à inviter.'),
                'role': openapi.Schema(type=openapi.TYPE_STRING, enum=['member', 'observer'],
                                       default='member', description='Rôle attribué à l\'invité.'),
            },
        ),
        responses={
            201: BoardInvitationSerializer,
            400: 'Email manquant, utilisateur déjà membre, ou invitation déjà en attente.',
        },
        operation_summary='Inviter un utilisateur par email',
        operation_description=(
            'Crée une invitation avec un token UUID unique et envoie un email à l\'adresse indiquée. '
            'Requiert le rôle **admin** sur le tableau.'
        ),
        tags=['Boards'],
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
        operation_summary='Lister les membres du tableau',
        operation_description='Retourne tous les membres avec leur rôle et la date d\'adhésion.',
        tags=['Boards'],
    )
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        board = self.get_object()
        members = BoardMember.objects.filter(board=board).select_related('user')
        return Response(BoardMemberSerializer(members, many=True).data)

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(type=openapi.TYPE_OBJECT, properties={}),
        responses={200: 'Tableau archivé.', 403: 'Permission refusée.'},
        operation_summary='Archiver (fermer) un tableau',
        operation_description='Marque le tableau comme fermé. Requiert le rôle **admin**.',
        tags=['Boards'],
    )
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        board = self.get_object()
        if not (board.creator == request.user or
                board.board_members.filter(user=request.user, role=BoardMember.Role.ADMIN).exists()):
            return Response({'success': False, 'message': "Permission refusée."}, status=status.HTTP_403_FORBIDDEN)
        board.is_closed = True
        board.save(update_fields=['is_closed', 'updated_at'])
        return Response({'success': True, 'message': "Tableau archivé."})

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(type=openapi.TYPE_OBJECT, properties={}),
        responses={200: 'Tableau réouvert.', 403: 'Permission refusée.'},
        operation_summary='Réouvrir un tableau archivé',
        operation_description='Restaure un tableau fermé. Requiert le rôle **admin**.',
        tags=['Boards'],
    )
    @action(detail=True, methods=['post'])
    def reopen(self, request, pk=None):
        board = self.get_object()
        if not (board.creator == request.user or
                board.board_members.filter(user=request.user, role=BoardMember.Role.ADMIN).exists()):
            return Response({'success': False, 'message': "Permission refusée."}, status=status.HTTP_403_FORBIDDEN)
        board.is_closed = False
        board.save(update_fields=['is_closed', 'updated_at'])
        return Response({'success': True, 'message': "Tableau réouvert."})

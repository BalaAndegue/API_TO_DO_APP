from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from Core.models import Board, BoardMember, BoardInvitation, User
from Core.serializers import BoardSerializer, BoardMemberSerializer, BoardInvitationSerializer
from Core.permissions import IsBoardMember, IsBoardAdmin
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class BoardViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing boards.
    """
    serializer_class = BoardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Return public boards or boards where user is a member
        return Board.objects.filter(
            Q(visibility='public') | 
            Q(board_members__user=user) | 
            Q(creator=user)
        ).distinct()

    def perform_create(self, serializer):
        board = serializer.save(creator=self.request.user)
        # Add creator as admin member
        BoardMember.objects.create(board=board, user=self.request.user, role='admin')

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email of the user to invite'),
            },
            required=['email']
        ),
        responses={
            201: BoardInvitationSerializer,
            400: 'Bad Request'
        },
        operation_description="Invite a user to the board by email."
    )
    @action(detail=True, methods=['post'], permission_classes=[IsBoardAdmin])
    def invite(self, request, pk=None):
        board = self.get_object()
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user already member
        if BoardMember.objects.filter(board=board, user__email=email).exists():
            return Response({'error': 'User is already a member'}, status=status.HTTP_400_BAD_REQUEST)

        # Check existing invitation
        if BoardInvitation.objects.filter(board=board, email=email, accepted=False).exists():
             return Response({'error': 'Invitation pending'}, status=status.HTTP_400_BAD_REQUEST)

        invitation = BoardInvitation.objects.create(board=board, inviter=request.user, email=email)
        # Here we would send email
        return Response(BoardInvitationSerializer(invitation).data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        method='get',
        responses={200: BoardMemberSerializer(many=True)},
        operation_description="Get all members of the board."
    )
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        board = self.get_object()
        members = BoardMember.objects.filter(board=board)
        serializer = BoardMemberSerializer(members, many=True)
        return Response(serializer.data)

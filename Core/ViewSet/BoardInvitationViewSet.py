from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from Core.models import BoardInvitation, BoardMember, User
from Core.serializers import BoardInvitationSerializer
import logging

logger = logging.getLogger(__name__)

class BoardInvitationViewSet(viewsets.ModelViewSet):
    queryset = BoardInvitation.objects.all()
    serializer_class = BoardInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'])
    def accept(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            invitation = BoardInvitation.objects.get(token=token, accepted=False)
            invitation.accepted = True
            invitation.save()
            
            # Add user to board
            user = request.user
            if BoardMember.objects.filter(board=invitation.board, user=user).exists():
                 return Response({'message': 'Already a member'}, status=status.HTTP_200_OK)

            BoardMember.objects.create(board=invitation.board, user=user, role='member')
            return Response({'message': 'Invitation accepted', 'board_id': invitation.board.pk}, status=status.HTTP_200_OK)
        except BoardInvitation.DoesNotExist:
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_404_NOT_FOUND)

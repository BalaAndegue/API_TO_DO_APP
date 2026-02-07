from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from Core.models import Card, List, Board, update_position
from Core.serializers import CardSerializer
from Core.permissions import IsBoardMember
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class CardViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing cards.
    """
    serializer_class = CardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Card.objects.filter(
            Q(board__visibility='public') | 
            Q(board__board_members__user=user) | 
            Q(board__creator=user)
        ).distinct()

    def perform_create(self, serializer):
        list_obj = serializer.validated_data['list'] # 'list' is a keyword, better use list_obj
        board = list_obj.board
        
        # Verify access
        if board.visibility != 'public' and not (
            board.creator == self.request.user or 
            board.board_members.filter(user=self.request.user).exists()
        ):
             raise permissions.PermissionDenied("You are not a member of this board.")
        
        # Auto-assign board from list
        serializer.save(board=board)

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'position': openapi.Schema(type=openapi.TYPE_INTEGER, description='New position of the card'),
                'list_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the new list to move to (optional)'),
            },
            required=['position']
        ),
        responses={
            200: CardSerializer,
            400: 'Bad Request',
            404: 'List not found'
        },
        operation_description="Move a card to a new position or list."
    )
    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        """
        Move card to a new position or new list.
        Payload: { 'position': int, 'list_id': int (optional) }
        """
        card = self.get_object()
        new_position = request.data.get('position')
        new_list_id = request.data.get('list_id')

        if new_list_id:
            try:
                new_list = List.objects.get(pk=new_list_id)
                # Ensure new list is in same board or user has access
                if new_list.board != card.board: 
                     # Could allow moving between boards if user is member of both
                     # For now, restrict to same board for simplicity unless requested
                     return Response({'error': 'Cannot move to a different board (yet)'}, status=status.HTTP_400_BAD_REQUEST)
                
                card.list = new_list
            except List.DoesNotExist:
                return Response({'error': 'List not found'}, status=status.HTTP_404_NOT_FOUND)

        if new_position is not None:
            card.position = new_position

        card.save()
        return Response(CardSerializer(card).data)

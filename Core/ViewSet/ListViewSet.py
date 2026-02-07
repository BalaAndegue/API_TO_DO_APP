from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.db.models import Q
from Core.models import List, Board
from Core.serializers import ListSerializer
from Core.permissions import IsBoardMember

class ListViewSet(viewsets.ModelViewSet):
    serializer_class = ListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Return lists of boards where user is a member or public
        return List.objects.filter(
            Q(board__visibility='public') | 
            Q(board__board_members__user=user) | 
            Q(board__creator=user)
        ).distinct()

    def perform_create(self, serializer):
        # Additional check: User must be member of the board to add list
        board = serializer.validated_data['board']
        if board.visibility != 'public' and not (
            board.creator == self.request.user or 
            board.board_members.filter(user=self.request.user).exists()
        ):
             raise permissions.PermissionDenied("You are not a member of this board.")
        serializer.save()

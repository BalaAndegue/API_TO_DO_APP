from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from Core.models import BoardMember
from Core.serializers import BoardMemberSerializer
from Core.permissions import IsBoardAdmin

class BoardMemberViewSet(viewsets.ModelViewSet):
    serializer_class = BoardMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Show members of boards current user is a member of
        user = self.request.user
        return BoardMember.objects.filter(board__board_members__user=user).distinct()

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsBoardAdmin()] # Only admins can manage members directly
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        # Ensure only members can be added to boards user is admin of
        board = serializer.validated_data['board']
         # Check if current user is admin of this board
        if not (board.creator == self.request.user or 
                board.board_members.filter(user=self.request.user, role='admin').exists()):
             raise permissions.PermissionDenied("Must be an admin to add members.")
        serializer.save()

    def perform_destroy(self, instance):
        # Check permissions
        board = instance.board
        if not (board.creator == self.request.user or 
                board.board_members.filter(user=self.request.user, role='admin').exists()):
             raise permissions.PermissionDenied("Must be an admin to remove members.")
        instance.delete()

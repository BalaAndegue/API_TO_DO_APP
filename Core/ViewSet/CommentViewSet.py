from rest_framework import viewsets, permissions, status
from django.db.models import Q
from Core.models import Comment
from Core.serializers import CommentSerializer
from Core.permissions import IsBoardMember

class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Comment.objects.filter(
            Q(card__board__visibility='public') | 
            Q(card__board__board_members__user=user) | 
            Q(card__board__creator=user)
        ).distinct()

    def perform_create(self, serializer):
        # Additional check: User must be member of the board to comment
        card = serializer.validated_data['card']
        board = card.board
        if board.visibility != 'public' and not (
            board.creator == self.request.user or 
            board.board_members.filter(user=self.request.user).exists()
        ):
             raise permissions.PermissionDenied("You are not a member of this board.")
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        obj = self.get_object()
        # Only comment author or board admin can edit
        is_author = obj.user == self.request.user
        is_admin = obj.card.board.board_members.filter(user=self.request.user, role='admin').exists()
        
        if not (is_author or is_admin):
            raise permissions.PermissionDenied("Not allowed to edit this comment.")
        
        serializer.save()

    def perform_destroy(self, instance):
        # Only comment author or board admin can delete
        is_author = instance.user == self.request.user
        is_admin = instance.card.board.board_members.filter(user=self.request.user, role='admin').exists()
        
        if not (is_author or is_admin):
             raise permissions.PermissionDenied("Not allowed to delete this comment.")
        instance.delete()

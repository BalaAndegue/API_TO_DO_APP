from rest_framework import viewsets, permissions
from Core.models import Board
from Core.serializers import BoardSerializer

class BoardViewSet(viewsets.ModelViewSet):
    queryset = Board.objects.all()
    serializer_class = BoardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Ensure the board.creator is set from the authenticated user
        serializer.save(creator=self.request.user)

from rest_framework import viewsets, permissions
from Core.models import BoardMember
from Core.serializers import BoardMemberSerializer

class BoardMemberViewSet(viewsets.ModelViewSet):
    queryset = BoardMember.objects.all()
    serializer_class = BoardMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

from rest_framework import viewsets, permissions
from Core.models import CardMember
from Core.serializers import CardMemberSerializer

class CardMemberViewSet(viewsets.ModelViewSet):
    queryset = CardMember.objects.all()
    serializer_class = CardMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

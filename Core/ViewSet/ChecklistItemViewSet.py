from rest_framework import viewsets, permissions
from Core.models import ChecklistItem
from Core.serializers import ChecklistItemSerializer

class ChecklistItemViewSet(viewsets.ModelViewSet):
    queryset = ChecklistItem.objects.all()
    serializer_class = ChecklistItemSerializer
    permission_classes = [permissions.IsAuthenticated]

from rest_framework import viewsets, permissions
from Core.models import Checklist
from Core.serializers import ChecklistSerializer

class ChecklistViewSet(viewsets.ModelViewSet):
    queryset = Checklist.objects.all()
    serializer_class = ChecklistSerializer
    permission_classes = [permissions.IsAuthenticated]

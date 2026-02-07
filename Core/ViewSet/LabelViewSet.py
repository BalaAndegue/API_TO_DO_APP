from rest_framework import viewsets, permissions
from Core.models import Label
from Core.serializers import LabelSerializer

class LabelViewSet(viewsets.ModelViewSet):
    queryset = Label.objects.all()
    serializer_class = LabelSerializer
    permission_classes = [permissions.IsAuthenticated]

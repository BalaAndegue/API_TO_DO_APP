from rest_framework import viewsets, permissions
from Core.models import CardLabel
from Core.serializers import CardLabelSerializer

class CardLabelViewSet(viewsets.ModelViewSet):
    queryset = CardLabel.objects.all()
    serializer_class = CardLabelSerializer
    permission_classes = [permissions.IsAuthenticated]

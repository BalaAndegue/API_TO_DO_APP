from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from Core.models import Category
from Core.serializers import CategorySerializer


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les catégories des taches."""
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
            user = self.request.user
            if user.is_anonymous: # Si l'utilisateur n'est pas authentifié, ne pas retourner categorii de tâches
                return Category.objects.none()  
            return Category.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
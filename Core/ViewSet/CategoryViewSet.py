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
        """
        Ne renvoyer que les catégories de l'utilisateur connecté"""
        return Category.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
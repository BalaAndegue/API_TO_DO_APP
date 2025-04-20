from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from Core.models import Category
from Core.serializers import CategorySerializer


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les catégories des tâches (CRUD sécurisé pour l'utilisateur connecté).
    """
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retourne uniquement les catégories appartenant à l'utilisateur connecté.
        """
        user = self.request.user
        if user.is_anonymous:
            return Category.objects.none()
        return Category.objects.filter(user=user)

    def perform_create(self, serializer):
        """
        Lors de la création, associe la catégorie à l'utilisateur connecté.
        """
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """
        Lors de la mise à jour, vérifie que l'utilisateur est bien le créateur.
        """
        if serializer.instance.user != self.request.user:
            raise PermissionDenied("Vous ne pouvez modifier que vos propres catégories.")
        serializer.save()

    def perform_destroy(self, instance):
        """
        Lors de la suppression, vérifie que l'utilisateur est bien le créateur.
        """
        if instance.user != self.request.user:
            raise PermissionDenied("Vous ne pouvez supprimer que vos propres catégories.")
        instance.delete()

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from Core.models import Category
from Core.serializers import CategorySerializer

class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les catégories des tâches :
    - CRUD complet avec réponse personnalisée pour chaque action.
    """
    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    permission_classes = [AllowAny]
    def list(self, request, *args, **kwargs):
        """
        Liste toutes les catégories avec une réponse formatée.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'message': 'Liste des catégories récupérée avec succès',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """
        Récupère une seule catégorie par son ID.
        """
        category = self.get_object()
        serializer = self.get_serializer(category)
        return Response({
            'success': True,
            'message': 'Catégorie récupérée avec succès',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """
        Crée une nouvelle catégorie.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            'success': True,
            'message': 'Catégorie créée avec succès',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """
        Met à jour une catégorie existante.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            'success': True,
            'message': 'Catégorie mise à jour avec succès',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """
        Supprime une catégorie.
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'success': True,
            'message': 'Catégorie supprimée avec succès'
        }, status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        """
        Enregistre la nouvelle catégorie dans la base de données.
        """
        serializer.save()

    def perform_update(self, serializer):
        """
        Applique les modifications à une catégorie existante.
        """
        serializer.save()

    def perform_destroy(self, instance):
        """
        Supprime la catégorie de la base de données.
        """
        instance.delete()

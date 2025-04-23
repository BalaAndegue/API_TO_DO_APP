from rest_framework import viewsets, status
from rest_framework.response import Response
from Core.models import Category
from Core.serializers import CategorySerializer
from rest_framework.permissions import AllowAny

class ContextViewSet(viewsets.ViewSet):
    """
    ViewSet pour récupérer le contexte (ex: catégories).
    """
    permission_classes = [AllowAny]
    def list(self, request, *args, **kwargs):
        """
        Liste toutes les catégories avec une réponse formatée.
        """
        queryset = Category.objects.all()
        serializer = CategorySerializer(queryset, many=True)
        return Response({
            'success': True,
            'message': 'Liste des catégories récupérée avec succès',
            'data': {
                'categories': serializer.data
            }
        }, status=status.HTTP_200_OK)

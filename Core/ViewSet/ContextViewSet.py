from rest_framework import viewsets,status
from rest_framework.response import Response
from Core.models import Category
from Core.serializers import CategorySerializer



class ContextViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour récupérer le contexte
    """
    serializer_class = CategorySerializer
    queryset = Category.objects.all()

    def list(self, request, *args, **kwargs):
        """
        Liste toutes les catégories avec une réponse formatée.
        """
       
        return Response({
            'success': True,
            'message': 'Liste des catégories récupérée avec succès',
            'data': {
                'categories':self.queryset
            }
        }, status=status.HTTP_200_OK)

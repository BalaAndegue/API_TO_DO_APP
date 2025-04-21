from rest_framework import viewsets

from Core.models import Category
from Core.serializers import CategorySerializer



class ContextViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour récupérer le contexte
    """
    serializer_class = CategorySerializer
    def get_queryset(self):
        """
        Retourne uniquement les catégories  pour le moment
        """
        
        return Category.objects.all()

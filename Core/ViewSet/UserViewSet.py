from rest_framework import viewsets

from Core.models import User
from Core.serializers import UserSerializer

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les utilisateurs.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer


    def get_queryset(self):
        """
        Retourne la liste des utilisateurs.
        """
        return User.objects.all() 
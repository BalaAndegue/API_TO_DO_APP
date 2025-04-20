from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404

from Core.models import User
from Core.serializers import UserSerializer, LoginSerializer


class RegisterAPIView(APIView):
    """
    API pour enregistrer un nouvel utilisateur.
    """
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    """
    API pour se connecter avec nom d'utilisateur et mot de passe.
    """
    def post(self, request):
        """
        Format d'entrée :
        {
            "username": "votreUsername",
            "password": "votreMotDePasse"
        }
        """
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    """
    API pour se déconnecter (nécessite d'être authentifié).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response({"message": "Déconnexion réussie"}, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    """
    CRUD complet pour les utilisateurs.
    Accessible uniquement à un utilisateur authentifié.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # 👤 Par défaut, un utilisateur ne peut voir que ses propres infos (modifiable si admin)
        user = self.request.user
        if user.is_superuser:
            return User.objects.all()
        return User.objects.filter(id=user.id)

    def perform_create(self, serializer):
        # Optionnel, car le registre se fait via RegisterAPIView
        serializer.save()

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def reset_password(self, request, pk=None):
        """
        Action personnalisée : réinitialisation de mot de passe.
        """
        user = get_object_or_404(User, pk=pk)
        new_password = request.data.get("new_password")
        if not new_password:
            return Response({"error": "Nouveau mot de passe requis."}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        return Response({"message": "Mot de passe mis à jour."}, status=status.HTTP_200_OK)

from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from Core.models import User
from Core.serializers import UserSerializer, LoginSerializer


class RegisterAPIView(APIView):
    """
    API pour enregistrer un nouvel utilisateur.
    """

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            # Création et sauvegarde de l'utilisateur
            user = serializer.save()

            # Génération d'un token d'authentification
            token, _ = Token.objects.get_or_create(user=user)

            # Réponse avec token + données utilisateur
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)

        # En cas d'erreur de validation
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    """
    API pour se connecter avec nom d'utilisateur et mot de passe.
    """

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            # Si authentification réussie
            user = serializer.validated_data

            # Création ou récupération du token
            token, _ = Token.objects.get_or_create(user=user)

            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)

        # Identifiants invalides
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    """
    API pour se déconnecter (nécessite d'être authentifié).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Suppression du token de l'utilisateur
        request.user.auth_token.delete()
        return Response({"message": "Déconnexion réussie"}, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour accéder aux utilisateurs (admin/dev seulement).
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

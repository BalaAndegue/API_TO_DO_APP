from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError, PermissionDenied, NotAuthenticated
from Core.models import User
from Core.serializers import UserSerializer, LoginSerializer
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from drf_spectacular.utils import extend_schema


class RegisterAPIView(APIView):
    """
    API pour enregistrer un nouvel utilisateur.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=UserSerializer,
        responses={
            200: openapi.Response(description="Utilisateur créé avec succès"),
            400: openapi.Response(description="Erreur de validation"),
        }
    )
    def post(self, request):
        try:
            serializer = UserSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'success': True,
                'message': 'Utilisateur créé avec succès',
                'data': {
                    'token': token.key,
                    'user': UserSerializer(user).data
                }
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({
                'success': False,
                'message': "Échec de l'enregistrement",
                'error': e.detail
            }, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    """
    API pour se connecter avec email et mot de passe.
    """
    permission_classes = [AllowAny]
    @swagger_auto_schema(
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(description="Connexion réussie"),
            400: openapi.Response(description="Échec de connexion"),
        }
    )
    def post(self, request):
        try:
            serializer = LoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'success': True,
                'message': 'Connexion réussie',
                'data': {
                    'token': token.key,
                    'user': UserSerializer(user).data
                }
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({
                'success': False,
                'message': "Connexion échouée",
                'error': e.detail.get('non_field_errors', ["Erreur inconnue"])[0]
            }, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    """
    API pour se déconnecter (nécessite d'être authentifié).
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=None,
        responses={200: None},
        tags=["Authentification"],
        summary="Déconnexion",
        description="Supprime le token d'authentification de l'utilisateur connecté."
    )
    def post(self, request):
        try:
            request.user.auth_token.delete()
            return Response({
                'success': True,
                'message': 'Déconnexion réussie'
            }, status=status.HTTP_200_OK)
        except AttributeError:
            return Response({
                'success': False,
                'message': 'Aucun token à supprimer'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({
                'success': False,
                'message': 'Erreur lors de la déconnexion'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    # permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        try:
            users = self.get_queryset()
            serializer = self.get_serializer(users, many=True)
            return Response({
                'success': True,
                'message': 'Liste des utilisateurs récupérée avec succès',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception:
            return Response({
                'success': False,
                'message': 'Erreur lors de la récupération des utilisateurs'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, *args, **kwargs):
        try:
            user = self.get_object()
            serializer = self.get_serializer(user)
            return Response({
                'success': True,
                'message': 'Utilisateur récupéré avec succès',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception:
            return Response({
                'success': False,
                'message': 'Utilisateur introuvable'
            }, status=status.HTTP_404_NOT_FOUND)

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response({
                'success': True,
                'message': 'Utilisateur créé avec succès',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({
                'success': False,
                'message': "Échec de la création",
                'error': e.detail
            }, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response({
                'success': True,
                'message': 'Utilisateur mis à jour avec succès',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({
                'success': False,
                'message': "Échec de la mise à jour",
                'error': e.detail
            }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response({
                'success': True,
                'message': 'Utilisateur supprimé avec succès'
            }, status=status.HTTP_204_NO_CONTENT)
        except Exception:
            return Response({
                'success': False,
                'message': 'Erreur lors de la suppression'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def reset_password(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)
        new_password = request.data.get("new_password")
        if not new_password:
            return Response({
                'success': False,
                'message': 'Nouveau mot de passe requis'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user.set_password(new_password)
            user.save()
            return Response({
                'success': True,
                'message': 'Mot de passe mis à jour avec succès'
            }, status=status.HTTP_200_OK)
        except Exception:
            return Response({
                'success': False,
                'message': 'Erreur lors de la mise à jour du mot de passe'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

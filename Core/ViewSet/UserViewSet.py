from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from Core.models import User
from Core.serializers import UserSerializer, LoginSerializer
from Core.permissions import IsOwner
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=UserSerializer,
        responses={
            201: openapi.Response("Utilisateur créé avec succès"),
            400: openapi.Response("Erreur de validation"),
        },
        operation_summary="Créer un compte",
        tags=["Authentification"],
    )
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'message': "Échec de l'enregistrement.", 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                'success': True,
                'message': 'Compte créé avec succès.',
                'data': {'token': token.key, 'user': UserSerializer(user).data},
            },
            status=status.HTTP_201_CREATED,
        )


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=LoginSerializer,
        responses={
            200: openapi.Response("Connexion réussie"),
            400: openapi.Response("Identifiants invalides"),
        },
        operation_summary="Se connecter",
        tags=["Authentification"],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'message': "Connexion échouée.", 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = serializer.validated_data
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                'success': True,
                'message': 'Connexion réussie.',
                'data': {'token': token.key, 'user': UserSerializer(user).data},
            },
            status=status.HTTP_200_OK,
        )


class LogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            request.user.auth_token.delete()
            return Response({'success': True, 'message': 'Déconnexion réussie.'}, status=status.HTTP_200_OK)
        except AttributeError:
            return Response({'success': False, 'message': 'Aucun token actif.'}, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """
    Endpoints utilisateur. Chaque utilisateur ne peut modifier/supprimer que son propre profil.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()
        return User.objects.all()

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsOwner()]
        return [permissions.IsAuthenticated()]

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'success': True, 'message': 'Profil mis à jour.', 'data': serializer.data},
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        instance.delete()
        return Response({'success': True, 'message': 'Compte supprimé.'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Return the authenticated user's profile."""
        return Response(
            {'success': True, 'data': UserSerializer(request.user).data},
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['new_password'],
            properties={
                'new_password': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        responses={200: "Mot de passe mis à jour.", 400: "Validation échouée."},
        operation_summary="Changer son mot de passe",
        tags=["Utilisateurs"],
    )
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request):
        """Change the authenticated user's own password."""
        new_password = request.data.get('new_password')
        if not new_password:
            return Response(
                {'success': False, 'message': 'Le nouveau mot de passe est requis.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            validate_password(new_password, user=request.user)
        except DjangoValidationError as e:
            return Response(
                {'success': False, 'message': 'Mot de passe invalide.', 'errors': list(e.messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        request.user.set_password(new_password)
        request.user.save()
        Token.objects.filter(user=request.user).delete()
        token = Token.objects.create(user=request.user)
        return Response(
            {
                'success': True,
                'message': 'Mot de passe mis à jour. Reconnectez-vous avec votre nouveau token.',
                'data': {'token': token.key},
            },
            status=status.HTTP_200_OK,
        )

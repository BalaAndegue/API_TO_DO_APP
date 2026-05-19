from django.utils.decorators import method_decorator
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from Core.models import User
from Core.serializers import UserSerializer, LoginSerializer
from Core.permissions import IsOwner
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


# ---------------------------------------------------------------------------
# Auth endpoints (APIView — pas dans le router)
# ---------------------------------------------------------------------------

class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=UserSerializer,
        responses={
            201: openapi.Response(
                description='Compte créé — token retourné.',
                examples={'application/json': {
                    'token': '<token>', 'user': {},
                }},
            ),
            400: 'Erreur de validation (email ou username déjà utilisé, mot de passe trop faible…)',
        },
        operation_summary='Créer un compte utilisateur',
        operation_description=(
            'Enregistre un nouvel utilisateur et retourne immédiatement un token d\'authentification.\n\n'
            'Champs requis : **username**, **email**, **password**.\n'
            'Champs optionnels : **first_name**, **last_name**, **bio**, **avatar_url**.'
        ),
        tags=['Authentification'],
    )
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {'token': token.key, 'user': UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                description='Connexion réussie — token retourné.',
                examples={'application/json': {'token': '<token>', 'user': {}}},
            ),
            400: 'Email ou mot de passe invalide.',
        },
        operation_summary='Se connecter',
        operation_description=(
            'Authentifie l\'utilisateur avec **email** + **password** et retourne le token.\n\n'
            '`Authorization: Token <token>`'
        ),
        tags=['Authentification'],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.validated_data
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {'token': token.key, 'user': UserSerializer(user).data},
            status=status.HTTP_200_OK,
        )


class LogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(type=openapi.TYPE_OBJECT, properties={}),
        responses={204: 'Déconnexion réussie.'},
        operation_summary='Se déconnecter',
        operation_description='Invalide le token courant.',
        tags=['Authentification'],
    )
    def post(self, request):
        try:
            request.user.auth_token.delete()
        except AttributeError:
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# UserViewSet (router)
# ---------------------------------------------------------------------------

@method_decorator(name='list', decorator=swagger_auto_schema(
    operation_summary='Lister / rechercher les utilisateurs',
    operation_description='Utiliser **?search=** pour chercher par username ou email (ex. pour inviter).',
    tags=['Utilisateurs'],
))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(
    operation_summary='Profil d\'un utilisateur',
    tags=['Utilisateurs'],
))
@method_decorator(name='update', decorator=swagger_auto_schema(
    operation_summary='Mettre à jour son profil (remplacement complet)',
    tags=['Utilisateurs'],
))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(
    operation_summary='Modifier partiellement son profil',
    tags=['Utilisateurs'],
))
@method_decorator(name='destroy', decorator=swagger_auto_schema(
    operation_summary='Supprimer son compte',
    tags=['Utilisateurs'],
))
class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ['username', 'email']

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
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        methods=['get', 'patch'],
        responses={200: UserSerializer},
        operation_summary='Mon profil (lecture et mise à jour)',
        operation_description=(
            'GET  — retourne le profil complet de l\'utilisateur connecté.\n'
            'PATCH — met à jour username, first_name, last_name, bio, avatar_url.'
        ),
        tags=['Utilisateurs'],
    )
    @action(detail=False, methods=['get', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        if request.method == 'GET':
            return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['new_password'],
            properties={
                'new_password': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        responses={
            200: openapi.Response(
                description='Mot de passe changé — nouveau token retourné.',
                examples={'application/json': {
                    'success': True, 'message': 'Mot de passe modifié.', 'data': {'token': '<new_token>'},
                }},
            ),
            400: 'Mot de passe invalide ou non fourni.',
        },
        operation_summary='Changer son mot de passe',
        tags=['Utilisateurs'],
    )
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request):
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
            {'success': True, 'message': 'Mot de passe modifié.', 'data': {'token': token.key}},
            status=status.HTTP_200_OK,
        )

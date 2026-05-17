from django.utils.decorators import method_decorator
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
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
                    'success': True,
                    'message': 'Compte créé avec succès.',
                    'data': {'token': '<token>', 'user': {}},
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
            200: openapi.Response(
                description='Connexion réussie — token retourné.',
                examples={'application/json': {
                    'success': True,
                    'message': 'Connexion réussie.',
                    'data': {'token': '<token>', 'user': {}},
                }},
            ),
            400: 'Email ou mot de passe invalide.',
        },
        operation_summary='Se connecter',
        operation_description=(
            'Authentifie l\'utilisateur avec **email** + **password** et retourne le token.\n\n'
            'Inclure ce token dans toutes les requêtes suivantes :\n'
            '`Authorization: Token <token>`'
        ),
        tags=['Authentification'],
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

    @swagger_auto_schema(
        request_body=openapi.Schema(type=openapi.TYPE_OBJECT, properties={}),
        responses={
            200: openapi.Response(description='Déconnexion réussie.'),
            400: 'Aucun token actif.',
        },
        operation_summary='Se déconnecter',
        operation_description='Invalide le token d\'authentification courant. L\'utilisateur doit se reconnecter pour obtenir un nouveau token.',
        tags=['Authentification'],
    )
    def post(self, request):
        try:
            request.user.auth_token.delete()
            return Response({'success': True, 'message': 'Déconnexion réussie.'}, status=status.HTTP_200_OK)
        except AttributeError:
            return Response({'success': False, 'message': 'Aucun token actif.'}, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# UserViewSet (router)
# ---------------------------------------------------------------------------

@method_decorator(name='list', decorator=swagger_auto_schema(
    operation_summary='Lister les utilisateurs',
    operation_description=(
        'Retourne tous les utilisateurs enregistrés (données publiques uniquement). '
        'Utile pour la recherche d\'utilisateurs à inviter sur un tableau.'
    ),
    tags=['Utilisateurs'],
))
@method_decorator(name='create', decorator=swagger_auto_schema(
    operation_summary='Créer un utilisateur (admin)',
    operation_description='Créer un compte via l\'admin. Préférer **POST /register/** pour l\'inscription normale.',
    tags=['Utilisateurs'],
))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(
    operation_summary='Profil d\'un utilisateur',
    operation_description='Retourne le profil public d\'un utilisateur par son ID.',
    tags=['Utilisateurs'],
))
@method_decorator(name='update', decorator=swagger_auto_schema(
    operation_summary='Mettre à jour son profil (remplacement complet)',
    operation_description='Réservé au propriétaire du compte.',
    tags=['Utilisateurs'],
))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(
    operation_summary='Modifier partiellement son profil',
    operation_description=(
        'Met à jour un ou plusieurs champs du profil (bio, avatar_url, first_name…). '
        'Réservé au propriétaire du compte.'
    ),
    tags=['Utilisateurs'],
))
@method_decorator(name='destroy', decorator=swagger_auto_schema(
    operation_summary='Supprimer son compte',
    operation_description='Supprime définitivement le compte. Réservé au propriétaire.',
    tags=['Utilisateurs'],
))
class UserViewSet(viewsets.ModelViewSet):
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

    @swagger_auto_schema(
        method='get',
        responses={200: UserSerializer},
        operation_summary='Mon profil',
        operation_description='Retourne le profil complet de l\'utilisateur connecté.',
        tags=['Utilisateurs'],
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
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
                'new_password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Nouveau mot de passe (soumis aux validateurs Django).',
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description='Mot de passe changé — nouveau token retourné.',
                examples={'application/json': {
                    'success': True,
                    'message': 'Mot de passe mis à jour. Reconnectez-vous avec votre nouveau token.',
                    'data': {'token': '<new_token>'},
                }},
            ),
            400: 'Mot de passe invalide ou non fourni.',
        },
        operation_summary='Changer son mot de passe',
        operation_description=(
            'Change le mot de passe de l\'utilisateur connecté. '
            'Le token actuel est invalidé et un nouveau token est retourné. '
            'Le frontend doit stocker le nouveau token et l\'utiliser pour les requêtes suivantes.'
        ),
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
            {
                'success': True,
                'message': 'Mot de passe mis à jour. Reconnectez-vous avec votre nouveau token.',
                'data': {'token': token.key},
            },
            status=status.HTTP_200_OK,
        )

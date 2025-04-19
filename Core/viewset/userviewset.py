
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from ..models import User
from ..serializers import UserSerializer
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login, logout
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from ..models import *






# ✅ Enregistrement utilisateur
class RegisterAPIView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Utilisateur créé avec succès", "user": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ✅ Authentification utilisateur
class LoginAPIView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            Token.objects.filter(user=user).delete()
            token, created = Token.objects.get_or_create(user=user)
            return Response({"message": "Connexion réussie", "token": token.key}, status=status.HTTP_200_OK)
        return Response({"error": "Identifiants incorrects"}, status=status.HTTP_400_BAD_REQUEST)

# ✅ Déconnexion utilisateur
class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        logout(request)
        return Response({"message": "Déconnexion réussie"}, status=status.HTTP_200_OK)

# ✅ Demande de réinitialisation de mot de passe
class ForgotPasswordAPIView(APIView):
    def post(self, request):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
            new_password_reset = PasswordReset(user=user)
            new_password_reset.save()
            password_reset_url = reverse('reset-password', kwargs={'reset_id': new_password_reset.reset_id})
            full_password_reset_url = f'{request.scheme}://{request.get_host()}{password_reset_url}'
            email_body = f'Reset your password using the link below:\n\n{full_password_reset_url}'
            email_message = EmailMessage('Reset your password', email_body, settings.EMAIL_HOST_USER, [email])
            email_message.send()
            return Response({"message": "Email de réinitialisation envoyé"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": f"Aucun utilisateur trouvé avec l'email {email}"}, status=status.HTTP_404_NOT_FOUND)

# ✅ Réinitialisation du mot de passe
class ResetPasswordAPIView(APIView):
    def post(self, request, reset_id):
        try:
            password_reset_id = PasswordReset.objects.get(reset_id=reset_id)
            password = request.data.get('password')
            confirm_password = request.data.get('confirm_password')

            if password != confirm_password or len(password) < 5:
                return Response({"error": "Les mots de passe ne correspondent pas ou sont trop courts"}, status=status.HTTP_400_BAD_REQUEST)

            expiration_time = password_reset_id.created_when + timezone.timedelta(minutes=10)
            if timezone.now() > expiration_time:
                password_reset_id.delete()
                return Response({"error": "Le lien de réinitialisation a expiré"}, status=status.HTTP_400_BAD_REQUEST)

            user = password_reset_id.user
            user.set_password(password)
            user.save()
            password_reset_id.delete()
            return Response({"message": "Mot de passe réinitialisé avec succès"}, status=status.HTTP_200_OK)
        except PasswordReset.DoesNotExist:
            return Response({"error": "Lien de réinitialisation invalide"}, status=status.HTTP_404_NOT_FOUND)

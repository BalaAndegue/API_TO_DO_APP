
#from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import User, Task
from .serializers import UserSerializer, TaskSerializer,  InvitedUserOnTaskSerializer
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib import messages
from django.conf import settings
from django.core.mail import EmailMessage, send_mail
from django.utils import timezone
from django.urls import reverse
from .models import *





@login_required
def Home(request):
    return render(request, 'index.html')

def RegisterView(request):

    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        profile_photo = request.FILES.get('profile_photo')  # Récupérer la photo

        

        user_data_has_error = False

        if User.objects.filter(username=username).exists():
            user_data_has_error = True
            messages.error(request, "Username already exists")

        if User.objects.filter(email=email).exists():
            user_data_has_error = True
            messages.error(request, "Email already exists")

        if len(password) < 5:
            user_data_has_error = True
            messages.error(request, "Password must be at least 5 characters")

        if user_data_has_error:
            return redirect('register')
        else:
            new_user = User.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                email=email, 
                username=username,
                password=password,
                avatar = profile_photo
            )

            if profile_photo:  # Vérifier si une photo a été envoyée
                new_user.profile_photo = profile_photo
                new_user.save()
            messages.success(request, "Account created. Login now")
            return redirect('login')

    return render(request, 'register.html')

def LoginView(request):

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        

        user = authenticate(request, username=username, password=password)

        if user is not None:
            

            login(request, user)

            #  Supprimer le token existant pour éviter les duplications
            Token.objects.filter(user=user).delete()

            #  Générer un nouveau token
            token, created = Token.objects.get_or_create(user=user)

            return redirect('home')
        
        else:
            messages.error(request, "Invalid login credentials")
            return redirect('login')

    return render(request, 'login.html')

def LogoutView(request):

    user = request.user

     # Supprimer le token de l'utilisateur
    Token.objects.filter(user=user).delete()

    logout(request)

    return redirect('login')

def ForgotPassword(request):

    if request.method == "POST":
        email = request.POST.get('email')

        try:
            user = User.objects.get(email=email)

            new_password_reset = PasswordReset(user=user)
            new_password_reset.save()

            password_reset_url = reverse('reset-password', kwargs={'reset_id': new_password_reset.reset_id})

            full_password_reset_url = f'{request.scheme}://{request.get_host()}{password_reset_url}'

            email_body = f'Reset your password using the link below:\n\n\n{full_password_reset_url}'
        
            email_message = EmailMessage(
                'Reset your password', # email subject
                email_body,
                settings.EMAIL_HOST_USER, # email sender
                [email] # email  receiver 
            )
            '''email_messages = send_mail(
                'RESET PASSWORD',
                email_body,
                settings.EMAIL_HOST_USER,
                {email}
            )'''
            email_message.fail_silently = True
            email_message.send()

            return redirect('password-reset-sent', reset_id=new_password_reset.reset_id)

        except User.DoesNotExist:
            messages.error(request, f"No user with email '{email}' found")
            return redirect('forgot-password')

    return render(request, 'forgot_password.html')

def PasswordResetSent(request, reset_id):

    if PasswordReset.objects.filter(reset_id=reset_id).exists():
        return render(request, 'password_reset_sent.html')
    else:
        # redirect to forgot password page if code does not exist
        #rediriger vers la page forgot password si le code n'existe pas.

        messages.error(request, 'Invalid reset id')
        return redirect('forgot-password')

def ResetPassword(request, reset_id):

    try:
        #verifie si l'identifiant de reinitialisation existe
        password_reset_id = PasswordReset.objects.get(reset_id=reset_id)

        if request.method == "POST":

            #verifie si les mots de passe eet ceux de confirmations sont les meme
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')

            passwords_have_error = False

            if password != confirm_password:
                passwords_have_error = True
                messages.error(request, 'Passwords do not match')
            
            #on verifie la taille du mot de passe
            if len(password) < 5:
                passwords_have_error = True
                messages.error(request, 'Password must be at least 5 characters long')
            
            #on verifie la date d'expiration de la requete de reinitialisation
            expiration_time = password_reset_id.created_when + timezone.timedelta(minutes=10)

            if timezone.now() > expiration_time:
                passwords_have_error = True
                messages.error(request, 'Reset link has expired')

                password_reset_id.delete()

            if not passwords_have_error:
                user = password_reset_id.user
                user.set_password(password)
                user.save()

                password_reset_id.delete()

                messages.success(request, 'Password reset. Proceed to login')
                return redirect('login')
            else:
                
                #rediriger vers la page password reset et afficher les erreurs 
                return redirect('reset-password', reset_id=reset_id)

    
    except PasswordReset.DoesNotExist:
        
     
        #rediriger vers la page forgot password si le code n'existe pas.
        messages.error(request, 'Invalid reset id')
        return redirect('forgot-password')

    return render(request, 'reset_password.html')




@api_view(['POST'])
@permission_classes([IsAuthenticated])  # 🔒 L'utilisateur doit être connecté
def create_task(request):
    serializer = TaskSerializer(data=request.data)
    if serializer.is_valid():
        task = serializer.save(user=request.user)  # Associer la tâche à l’utilisateur connecté
        return Response({"message": "Tâche créée avec succès", "task": serializer.data}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])  # 🔒 L'utilisateur doit être connecté
def delete_task(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
        if task.user == request.user:  # 🔒 Vérifier que l'utilisateur est bien le créateur
            task.delete()
            return Response({"message": "Tâche supprimée"}, status=status.HTTP_204_NO_CONTENT)
        return Response({"error": "Vous n'avez pas la permission de supprimer cette tâche."}, status=status.HTTP_403_FORBIDDEN)
    except Task.DoesNotExist:
        return Response({"error": "Tâche introuvable"}, status=status.HTTP_404_NOT_FOUND)



@api_view(['POST'])
@permission_classes([IsAuthenticated])  # 🔒 Seuls les utilisateurs connectés peuvent inviter
def invite_user(request):
    serializer = InvitedUserOnTaskSerializer(data=request.data, context={"request": request})
    if serializer.is_valid():
        invitation = serializer.save()
        return Response({"message": "Utilisateur invité avec succès", "invitation": serializer.data}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])  # 🔒 Seuls les invités peuvent accepter ou refuser
def accept_invitation(request, invitation_id):
    try:
        invitation = InvitedUserOnTask.objects.get(id=invitation_id)
        if invitation.invited_user == request.user:  # 🔒 Vérifier que l’utilisateur est bien celui invité
            invitation.accepted = True
            invitation.save()
            return Response({"message": "Invitation acceptée"}, status=status.HTTP_200_OK)
        return Response({"error": "Vous ne pouvez pas accepter cette invitation."}, status=status.HTTP_403_FORBIDDEN)
    except InvitedUserOnTask.DoesNotExist:
        return Response({"error": "Invitation introuvable"}, status=status.HTTP_404_NOT_FOUND)













import json
from django.shortcuts import render, redirect
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone
from django.urls import reverse
from .models import *
from .models import PasswordReset
import requests

API_BASE_URL = 'http://localhost:8000/api/'

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
        profile_photo = request.FILES.get('profile_photo')

        files = {'profile_photo': profile_photo} if profile_photo else None

        data = {
            'first_name': first_name,
            'last_name': last_name,
            'username': username,
            'email': email,
            'password': password
        }

        try:
            response = requests.post(API_BASE_URL + 'register/', data=data, files=files)

            try:
                response_data = response.json()
            except json.JSONDecodeError:
                messages.error(request, "Erreur : réponse invalide de l’API.")
                return redirect('register')

            if response.status_code == 200:
                messages.success(request, "Compte créé avec succès. Connectez-vous maintenant.")
                print(f"STATUT : {response.status_code}, Data: {response_data}")
                return redirect('login')
            else:
                message = response_data.get('message', "Erreur lors de la création du compte.")
                errors = response_data.get('error')
                if errors:
                    for field, error_list in errors.items():
                        for err in error_list:
                            messages.error(request, f"{field}: {err}")
                else:
                    messages.error(request, message)

        except requests.exceptions.RequestException as e:
            messages.error(request, f"Erreur réseau : {e}")

    return render(request, 'register.html')

def LoginView(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        data = {
            "email": email,
            "password": password
        }

        try:
            response = requests.post(
                API_BASE_URL + 'login/',
                json=data,
                headers={"Content-Type": "application/json"}
            )

            print(f"STATUS: {response.status_code}")
            print(f"RAW RESPONSE: {response.text}")

            if response.status_code == 200:
                response_data = response.json()
                token = response_data.get('access') or response_data.get('data', {}).get('token')

                user = User.objects.filter(email=email).first()
                if user:
                    login(request, user)

                    Token.objects.filter(user=user).delete()
                    Token.objects.create(user=user, key=token)

                    return redirect('home')
                else:
                    messages.error(request, "Utilisateur introuvable.")
            else:
                messages.error(request, "Email ou mot de passe incorrect.")

        except requests.exceptions.RequestException as e:
            print("Erreur lors de la requête API :", str(e))
            messages.error(request, "Erreur de connexion à l'API.")
        except json.JSONDecodeError:
            print("Réponse non JSON :", response.text)
            messages.error(request, "Erreur inattendue du serveur.")

        return redirect('login')

    return render(request, 'login.html')

def LogoutView(request):
    if not request.user.is_authenticated:
        return redirect('login')

    token = Token.objects.filter(user=request.user).first()
    if token:
        headers = {'Authorization': f'Token {token.key}'}
        try:
            response = requests.post(API_BASE_URL + 'logout/', headers=headers)
            if response.status_code == 200:
                messages.success(request, "Déconnexion réussie.")
            else:
                messages.warning(request, "Erreur lors de la déconnexion de l'API.")
        except requests.exceptions.RequestException as e:
            messages.error(request, f"Erreur réseau : {e}")
        token.delete()

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
                'Reset your password',
                email_body,
                settings.EMAIL_HOST_USER,
                [email]
            )
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
        messages.error(request, 'Invalid reset id')
        return redirect('forgot-password')

def ResetPassword(request, reset_id):
    try:
        password_reset_id = PasswordReset.objects.get(reset_id=reset_id)

        if request.method == "POST":
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')

            passwords_have_error = False

            if password != confirm_password:
                passwords_have_error = True
                messages.error(request, 'Passwords do not match')

            if len(password) < 5:
                passwords_have_error = True
                messages.error(request, 'Password must be at least 5 characters long')

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
                return redirect('reset-password', reset_id=reset_id)

    except PasswordReset.DoesNotExist:
        messages.error(request, 'Invalid reset id')
        return redirect('forgot-password')

    return render(request, 'reset_password.html')

@login_required
def board_list(request):
    token, _ = Token.objects.get_or_create(user=request.user)
    headers = {'Authorization': f'Token {token}'}
    response = requests.get(API_BASE_URL + 'boards/', headers=headers)
    boards = response.json().get('results', []) if response.status_code == 200 else []
    return render(request, 'boards/board_list.html', {'boards': boards})

@login_required
def create_board(request):
    token, _ = Token.objects.get_or_create(user=request.user)
    headers = {'Authorization': f'Token {token}'}
    if request.method == 'POST':
        data = {
            'name': request.POST.get('name'),
            'description': request.POST.get('description'),
            'visibility': request.POST.get('visibility', 'private'),
        }
        response = requests.post(API_BASE_URL + 'boards/', headers=headers, data=data)
        if response.status_code in (200, 201):
            return redirect('board-list')
        else:
            messages.error(request, 'Erreur lors de la création du board')
    return render(request, 'boards/create_board.html')

@login_required
def list_list(request, board_id):
    token, _ = Token.objects.get_or_create(user=request.user)
    headers = {'Authorization': f'Token {token}'}
    response = requests.get(f'{API_BASE_URL}lists/?board={board_id}', headers=headers)
    lists = response.json().get('results', []) if response.status_code == 200 else []
    return render(request, 'lists/list_list.html', {'lists': lists, 'board_id': board_id})

@login_required
def create_list(request, board_id):
    token, _ = Token.objects.get_or_create(user=request.user)
    headers = {'Authorization': f'Token {token}'}
    if request.method == 'POST':
        data = {
            'name': request.POST.get('name'),
            'board': board_id,
            'position': request.POST.get('position', 0),
        }
        response = requests.post(API_BASE_URL + 'lists/', headers=headers, data=data)
        if response.status_code in (200, 201):
            return redirect('list-list', board_id=board_id)
        else:
            messages.error(request, 'Erreur lors de la création de la liste')
    return render(request, 'lists/create_list.html', {'board_id': board_id})

@login_required
def card_list(request, list_id):
    token, _ = Token.objects.get_or_create(user=request.user)
    headers = {'Authorization': f'Token {token}'}
    response = requests.get(f'{API_BASE_URL}cards/?list={list_id}', headers=headers)
    cards = response.json().get('results', []) if response.status_code == 200 else []
    return render(request, 'cards/card_list.html', {'cards': cards, 'list_id': list_id})

@login_required
def create_card(request, list_id):
    token, _ = Token.objects.get_or_create(user=request.user)
    headers = {'Authorization': f'Token {token}'}
    if request.method == 'POST':
        data = {
            'title': request.POST.get('title'),
            'list': list_id,
            'board': request.POST.get('board'),
            'description': request.POST.get('description'),
            'due_date': request.POST.get('due_date'),
            'position': request.POST.get('position', 0),
        }
        response = requests.post(API_BASE_URL + 'cards/', headers=headers, data=data)
        if response.status_code in (200, 201):
            return redirect('card-list', list_id=list_id)
        else:
            messages.error(request, 'Erreur lors de la création de la carte')
    return render(request, 'cards/create_card.html', {'list_id': list_id})

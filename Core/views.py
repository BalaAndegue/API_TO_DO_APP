"""
Frontend template views — these render Django HTML templates that call
the REST API internally via the requests library.

The REST API logic (authentication, user management, etc.) lives in
Core/ViewSet/ and is consumed by the frontend React/Next.js app directly.
These views are kept for the optional server-side Django template frontend.
"""

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
from .models import User, PasswordReset
import requests
import os

API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8000/api/')


@login_required
def Home(request):
    return render(request, 'index.html')


def RegisterView(request):
    if request.method == "POST":
        data = {
            'first_name': request.POST.get('first_name'),
            'last_name': request.POST.get('last_name'),
            'username': request.POST.get('username'),
            'email': request.POST.get('email'),
            'password': request.POST.get('password'),
        }
        try:
            response = requests.post(API_BASE_URL + 'register/', json=data, timeout=10)
            response_data = response.json()
            if response.status_code in (200, 201):
                messages.success(request, "Compte créé avec succès. Connectez-vous maintenant.")
                return redirect('login')
            errors = response_data.get('errors', {})
            for field, error_list in errors.items():
                for err in error_list:
                    messages.error(request, f"{field}: {err}")
        except requests.exceptions.RequestException as e:
            messages.error(request, f"Erreur réseau : {e}")
    return render(request, 'register.html')


def LoginView(request):
    if request.method == "POST":
        data = {'email': request.POST.get('email'), 'password': request.POST.get('password')}
        try:
            response = requests.post(
                API_BASE_URL + 'login/',
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            if response.status_code == 200:
                response_data = response.json()
                token = response_data.get('data', {}).get('token')
                user = User.objects.filter(email=data['email']).first()
                if user and token:
                    login(request, user)
                    Token.objects.filter(user=user).delete()
                    Token.objects.create(user=user, key=token)
                    return redirect('home')
            messages.error(request, "Email ou mot de passe incorrect.")
        except requests.exceptions.RequestException as e:
            messages.error(request, f"Erreur de connexion à l'API : {e}")
        except (json.JSONDecodeError, KeyError):
            messages.error(request, "Erreur inattendue du serveur.")
        return redirect('login')
    return render(request, 'login.html')


def LogoutView(request):
    if not request.user.is_authenticated:
        return redirect('login')
    token = Token.objects.filter(user=request.user).first()
    if token:
        try:
            requests.post(
                API_BASE_URL + 'logout/',
                headers={'Authorization': f'Token {token.key}'},
                timeout=10,
            )
        except requests.exceptions.RequestException:
            pass
        token.delete()
    logout(request)
    return redirect('login')


def ForgotPassword(request):
    if request.method == "POST":
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            reset = PasswordReset.objects.create(user=user)
            reset_url = request.build_absolute_uri(
                reverse('reset-password', kwargs={'reset_id': reset.reset_id})
            )
            EmailMessage(
                subject='Réinitialisation de votre mot de passe',
                body=f"Réinitialisez votre mot de passe via ce lien :\n\n{reset_url}\n\n(valable 10 minutes)",
                from_email=settings.EMAIL_HOST_USER,
                to=[email],
            ).send(fail_silently=True)
            return redirect('password-reset-sent', reset_id=reset.reset_id)
        except User.DoesNotExist:
            messages.error(request, f"Aucun compte associé à « {email} ».")
            return redirect('forgot-password')
    return render(request, 'forgot_password.html')


def PasswordResetSent(request, reset_id):
    if PasswordReset.objects.filter(reset_id=reset_id).exists():
        return render(request, 'password_reset_sent.html')
    messages.error(request, 'Lien invalide.')
    return redirect('forgot-password')


def ResetPassword(request, reset_id):
    try:
        password_reset = PasswordReset.objects.get(reset_id=reset_id)
    except PasswordReset.DoesNotExist:
        messages.error(request, 'Lien invalide ou expiré.')
        return redirect('forgot-password')

    if request.method == "POST":
        password = request.POST.get('password')
        confirm = request.POST.get('confirm_password')
        error = False
        if password != confirm:
            messages.error(request, 'Les mots de passe ne correspondent pas.')
            error = True
        if len(password) < 8:
            messages.error(request, 'Le mot de passe doit contenir au moins 8 caractères.')
            error = True
        expiry = password_reset.created_when + timezone.timedelta(minutes=10)
        if timezone.now() > expiry:
            messages.error(request, 'Ce lien a expiré. Faites une nouvelle demande.')
            password_reset.delete()
            error = True
        if not error:
            password_reset.user.set_password(password)
            password_reset.user.save()
            password_reset.delete()
            messages.success(request, 'Mot de passe réinitialisé. Connectez-vous.')
            return redirect('login')
        return redirect('reset-password', reset_id=reset_id)

    return render(request, 'reset_password.html')


@login_required
def board_list(request):
    token, _ = Token.objects.get_or_create(user=request.user)
    response = requests.get(API_BASE_URL + 'boards/', headers={'Authorization': f'Token {token}'}, timeout=10)
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
        response = requests.post(API_BASE_URL + 'boards/', headers=headers, json=data, timeout=10)
        if response.status_code in (200, 201):
            return redirect('board-list')
        messages.error(request, 'Erreur lors de la création du tableau.')
    return render(request, 'boards/create_board.html')


@login_required
def list_list(request, board_id):
    token, _ = Token.objects.get_or_create(user=request.user)
    response = requests.get(
        f'{API_BASE_URL}lists/?board={board_id}',
        headers={'Authorization': f'Token {token}'},
        timeout=10,
    )
    lists = response.json().get('results', []) if response.status_code == 200 else []
    return render(request, 'lists/list_list.html', {'lists': lists, 'board_id': board_id})


@login_required
def create_list(request, board_id):
    token, _ = Token.objects.get_or_create(user=request.user)
    headers = {'Authorization': f'Token {token}'}
    if request.method == 'POST':
        data = {'name': request.POST.get('name'), 'board': board_id, 'position': 0}
        response = requests.post(API_BASE_URL + 'lists/', headers=headers, json=data, timeout=10)
        if response.status_code in (200, 201):
            return redirect('list-list', board_id=board_id)
        messages.error(request, 'Erreur lors de la création de la liste.')
    return render(request, 'lists/create_list.html', {'board_id': board_id})


@login_required
def card_list(request, list_id):
    token, _ = Token.objects.get_or_create(user=request.user)
    response = requests.get(
        f'{API_BASE_URL}cards/?list={list_id}',
        headers={'Authorization': f'Token {token}'},
        timeout=10,
    )
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
            'description': request.POST.get('description', ''),
            'due_date': request.POST.get('due_date') or None,
            'position': 0,
        }
        response = requests.post(API_BASE_URL + 'cards/', headers=headers, json=data, timeout=10)
        if response.status_code in (200, 201):
            return redirect('card-list', list_id=list_id)
        messages.error(request, 'Erreur lors de la création de la carte.')
    return render(request, 'cards/create_card.html', {'list_id': list_id})


@login_required
def label_list(request):
    token, _ = Token.objects.get_or_create(user=request.user)
    response = requests.get(API_BASE_URL + 'labels/', headers={'Authorization': f'Token {token}'}, timeout=10)
    labels = response.json().get('results', []) if response.status_code == 200 else []
    return render(request, 'labels/label_list.html', {'labels': labels})

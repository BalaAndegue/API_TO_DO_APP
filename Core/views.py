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

        response = requests.post(API_BASE_URL + 'register/', data=data, files=files)
        if response.status_code == 201:
            messages.success(request, "Account created. Login now")
            print(f" STATUT : {response.status_code}, Data: {response.json()}")

            return redirect('login')
        print(f" STATUT : {response.status_code}, Data: {response.json()}")
    return render(request, 'register.html')

def LoginView(request):
    if request.method == "POST":
        # Recuperation des données
        username = request.POST.get("username")
        password = request.POST.get("password")

        # formatage en JSON
        data = {
            "username": username,
            "password": password
        }

        response = requests.post(API_BASE_URL + 'login/', data=data)

        if response.status_code == 200 and response.json().get('token'):
            token = response.json().get('token')
            user = User.objects.filter(username=username).first()

            print(f"""
                      STATUT: {response.json().get('success')}
                    message  : {response.json().get("message")}
                      Data  : {response.json().get("data")}""")

            if user:
                login(request, user)
                Token.objects.filter(user=user).delete()
                Token.objects.create(user=user, key=token)
                return redirect('home')

        print(f" STATUT : {response.status_code}, Data: {response.json()}")

        messages.error(request, "Invalid login credentials")
        return redirect('login')

    return render(request, 'login.html')

def LogoutView(request):
    #Recuperation du token de l'utilisateur , et par la suite suppression
    token = Token.objects.filter(user=request.user).first()
    if token:
        headers = {'Authorization': f'Token {token.key}'}
        requests.post(API_BASE_URL + 'logout/', headers=headers)
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
def task_list(request):
    token, _ = Token.objects.get_or_create(user=request.user)
    headers = {'Authorization': f'Token {token}'}

    response = requests.get(API_BASE_URL + 'tasks/', headers=headers)
    tasks = response.json() if response.status_code == 200 else []
    return render(request, 'tasks/task_list.html', {'tasks': tasks})
@login_required
def create_task(request):
    token = Token.objects.get(user=request.user).key
    headers = {'Authorization': f'Token {token}'}

    if request.method == 'POST':
        data = {
            'title': request.POST.get('title'),
            'category': request.POST.get('category'),  # Doit être l'ID maintenant
            'description': request.POST.get('description'),
            'start_date': request.POST.get('start_date'),
            'end_date': request.POST.get('end_date'),
            'priority': request.POST.get('priority'),
        }
        response = requests.post(API_BASE_URL + 'tasks/', headers=headers, data=data)

        if response.status_code == 201:
            return redirect('tasks-list')
        else:
            print(response.status_code)
            print(response.text)
            messages.error(request, 'Erreur lors de la création')

    # On récupère les catégories de l’API
    categories_response = requests.get(API_BASE_URL + 'categories/', headers=headers)
    categories = categories_response.json() if categories_response.status_code == 200 else []

    return render(request, 'tasks/create_task.html', {'categories': categories})

@login_required
def delete_task(request, task_id):
    token = Token.objects.get(user=request.user).key
    headers = {'Authorization': f'Token {token}'}

    response = requests.delete(f'{API_BASE_URL}tasks/{task_id}/', headers=headers)

    if response.status_code == 204:
        messages.success(request, 'Tâche supprimée')
    else:
        messages.error(request, 'Erreur de suppression')

    return redirect('tasks-list')


@login_required
def category_list(request):
    token, _ = Token.objects.get_or_create(user=request.user)
 
    response = requests.get(API_BASE_URL + 'categories/')
    categories = response.json() if response.status_code == 200 else []
    return render(request, 'categories/category_list.html', {'categories': categories})
from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.Home, name='home'),

    # Auth Frontend
    path('login/', views.LoginView, name='login'),
    path('logout/', views.LogoutView, name='logout'),
    path('register/', views.RegisterView, name='register'),

    # Password Reset
    path('forgot-password/', views.ForgotPassword, name='forgot-password'),
    path('password-reset-sent/<str:reset_id>/', views.PasswordResetSent, name='password-reset-sent'),
    path('reset-password/<str:reset_id>/', views.ResetPassword, name='reset-password'),

    # Task Frontend
    path('tasks-list/', views.task_list, name='tasks-list'),
    path('tasks-create/', views.create_task, name='tasks-create'),
]

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

    

    # Trello-like objects (à implémenter dans views.py si besoin)
    path('boards/', views.board_list, name='board-list'),
    path('boards/create/', views.create_board, name='board-create'),
    path('lists/', views.list_list, name='list-list'),
    path('cards/', views.card_list, name='card-list'),
    path('labels/', views.label_list, name='label-list'),
]

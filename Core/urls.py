from django.urls import path, include
from rest_framework.routers import DefaultRouter
from Core.viewset.taskviewset import *
from Core.viewset.userviewset  import *
from . import views


router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')  # 🚀 Endpoint CRUD des tâches
router.register(r'invitations', InvitedUserOnTaskViewSet, basename='invitation')  # 🔄 Gestion des invitations


urlpatterns = [
    path('', views.Home, name='home'),
    path('register/', views.RegisterView, name='register'),
    path('login/', views.LoginView, name='login'),
    path('logout/', views.LogoutView, name='logout'),
    path('forgot-password/', views.ForgotPassword, name='forgot-password'),
    path('password-reset-sent/<str:reset_id>/', views.PasswordResetSent, name='password-reset-sent'),
    path('reset-password/<str:reset_id>/', views.ResetPassword, name='reset-password'),
    path('api/task/create/', views.create_task, name='create_task'),  # Créer une tâche
    path('api/task/delete/<int:task_id>/', views.delete_task, name='delete_task'),  # Supprimer une tâche




    path("auth/register/", RegisterAPIView.as_view(), name="register"),  # ✅ Inscription utilisateur
    path("auth/login/", LoginAPIView.as_view(), name="login"),  # ✅ Connexion utilisateur
    path("auth/logout/", LogoutAPIView.as_view(), name="logout"),  # ✅ Déconnexion utilisateur
    path("auth/forgot-password/", ForgotPasswordAPIView.as_view(), name="forgot-password"),  # 🔄 Demande de reset password
    path("auth/reset-password/<str:reset_id>/", ResetPasswordAPIView.as_view(), name="reset-password"),  # 🚀 Réinitialisation du mot de passe
    path("", include(router.urls)),  # ✅ Inclusion des ViewSets (Tasks & Invitations)


]


from django.urls import path,include
from . import views
from rest_framework.routers import DefaultRouter
from Core.ViewSet.CategoryViewSet import CategoryViewSet
from Core.ViewSet.TaskViewSet import TaskViewSet
from Core.ViewSet.UserViewSet import UserViewSet,RegisterAPIView, LoginAPIView, LogoutAPIView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tasks', TaskViewSet, basename='task')

urlpatterns = [
    path('api/', include(router.urls)),
    path('', views.Home, name='home'),
    path('api/register/', RegisterAPIView.as_view(), name='api-register'),
    path('api/login/', LoginAPIView.as_view(), name='api-login'),
    path('api/logout/', LogoutAPIView.as_view(), name='api-logout'),

# test frontend
    path('login/', views.LoginView, name='login'),
    path('logout/', views.logout, name='logout'),
    path('register/', views.RegisterView, name='register'),
    path('forgot-password/', views.ForgotPassword, name='forgot-password'),
    path('password-reset-sent/<str:reset_id>/', views.PasswordResetSent, name='password-reset-sent'),
    path('reset-password/<str:reset_id>/', views.ResetPassword, name='reset-password'),

    # front end tsks
    path('tasks-list/', views.task_list, name='tasks-list'),
    path('tasks-create/', views.create_task, name='tasks-create'),
]
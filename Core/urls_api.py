from django.urls import path, include
from rest_framework.routers import DefaultRouter

from Core.ViewSet.CategoryViewSet import CategoryViewSet
from Core.ViewSet.TaskViewSet import TaskViewSet
from Core.ViewSet.UserViewSet import UserViewSet, RegisterAPIView, LoginAPIView, LogoutAPIView
from Core.ViewSet.InvitedUserOnTaskViewSet import InvitedUserOnTaskViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'invitations', InvitedUserOnTaskViewSet, basename='invitation')

urlpatterns = [
    path('', include(router.urls)),

    # Auth API
    path('register/', RegisterAPIView.as_view(), name='api-register'),
    path('login/', LoginAPIView.as_view(), name='api-login'),
    path('logout/', LogoutAPIView.as_view(), name='api-logout'),
]

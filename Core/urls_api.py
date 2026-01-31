from django.urls import path, include
from rest_framework.routers import DefaultRouter

from Core.ViewSet.UserViewSet import UserViewSet, RegisterAPIView, LoginAPIView, LogoutAPIView
from Core.ViewSet.BoardViewSet import BoardViewSet
from Core.ViewSet.ListViewSet import ListViewSet
from Core.ViewSet.CardViewSet import CardViewSet
from Core.ViewSet.LabelViewSet import LabelViewSet
from Core.ViewSet.BoardMemberViewSet import BoardMemberViewSet
from Core.ViewSet.CardMemberViewSet import CardMemberViewSet
from Core.ViewSet.CardLabelViewSet import CardLabelViewSet
from Core.ViewSet.ChecklistViewSet import ChecklistViewSet
from Core.ViewSet.ChecklistItemViewSet import ChecklistItemViewSet
from Core.ViewSet.CommentViewSet import CommentViewSet
from Core.ViewSet.AttachmentViewSet import AttachmentViewSet
from Core.ViewSet.ActivityViewSet import ActivityViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

router.register(r'boards', BoardViewSet, basename='board')
router.register(r'lists', ListViewSet, basename='list')
router.register(r'cards', CardViewSet, basename='card')
router.register(r'labels', LabelViewSet, basename='label')
router.register(r'board-members', BoardMemberViewSet, basename='boardmember')
router.register(r'card-members', CardMemberViewSet, basename='cardmember')
router.register(r'card-labels', CardLabelViewSet, basename='cardlabel')
router.register(r'checklists', ChecklistViewSet, basename='checklist')
router.register(r'checklist-items', ChecklistItemViewSet, basename='checklistitem')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'attachments', AttachmentViewSet, basename='attachment')
router.register(r'activities', ActivityViewSet, basename='activity')

urlpatterns = [
    path('', include(router.urls)),
    
    # Auth API
    path('register/', RegisterAPIView.as_view(), name='api-register'),
    path('login/', LoginAPIView.as_view(), name='api-login'),
    path('logout/', LogoutAPIView.as_view(), name='api-logout'),
]

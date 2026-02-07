from rest_framework import permissions
from .models import BoardMember

class IsBoardMember(permissions.BasePermission):
    """
    Custom permission to only allow members of a board to view/edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        # But wait, public boards should be readable by anyone? Let's say yes.
        if obj.visibility == 'public':
            return True

        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user is a member of the board
        return BoardMember.objects.filter(board=obj, user=request.user).exists() or obj.creator == request.user

class IsBoardAdmin(permissions.BasePermission):
    """
    Custom permission to only allow admins of a board to edit it.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
            
        return BoardMember.objects.filter(board=obj, user=request.user, role='admin').exists() or obj.creator == request.user

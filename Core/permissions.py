from rest_framework import permissions
from .models import BoardMember


def _is_board_member_or_creator(board, user):
    return board.creator == user or BoardMember.objects.filter(board=board, user=user).exists()


def _is_board_admin_or_creator(board, user):
    return board.creator == user or BoardMember.objects.filter(
        board=board, user=user, role=BoardMember.Role.ADMIN
    ).exists()


class IsBoardMember(permissions.BasePermission):
    """
    Object-level permission for Board objects.
    Public boards are readable by anyone authenticated.
    Private/workspace boards require membership.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if obj.visibility == 'public' and request.method in permissions.SAFE_METHODS:
            return True
        return _is_board_member_or_creator(obj, request.user)


class IsBoardAdmin(permissions.BasePermission):
    """
    Object-level permission: only board admins or creator can perform the action.
    Applied on Board objects.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        board = getattr(obj, 'board', obj)
        return _is_board_admin_or_creator(board, request.user)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Generic permission: safe methods allowed for authenticated users,
    unsafe methods only for the resource owner.
    Expects object to have a `user` attribute pointing to its owner.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


class IsOwner(permissions.BasePermission):
    """Strict owner-only permission (for profile updates, password resets)."""
    def has_object_permission(self, request, view, obj):
        return obj == request.user

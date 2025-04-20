from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from Core.models import Task
from Core.serializers import TaskSerializer

class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les tâches de l'utilisateur connecté :
    - Liste, création, mise à jour et suppression (CRUD complet).
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retourne uniquement les tâches de l'utilisateur connecté.
        """
        return Task.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Lors de la création, associe automatiquement la tâche à l'utilisateur connecté.
        """
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """
        Lors de la mise à jour, vérifie que l'utilisateur est bien le créateur.
        """
        if serializer.instance.user != self.request.user:
            raise PermissionDenied("Vous ne pouvez modifier que vos propres tâches.")
        serializer.save()

    def perform_destroy(self, instance):
        """
        Lors de la suppression, vérifie que l'utilisateur est bien le créateur.
        """
        if instance.user != self.request.user:
            raise PermissionDenied("Vous ne pouvez supprimer que vos propres tâches.")
        instance.delete()

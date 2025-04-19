from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from Core import serializers
from Core.models import Task
from Core.serializers import TaskSerializer

class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les tâches de l'utilisateur connecté :
    - Liste, création, mise à jour et suppression.
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]  # L'utilisateur doit être authentifié pour accéder aux tâches

    def get_queryset(self):
        """
        Retourne uniquement les tâches de l'utilisateur connecté.
        """
        user = self.request.user
        if user.is_anonymous:
            # Si l'utilisateur n'est pas connecté, on ne retourne rien
            return Task.objects.none()
        return Task.objects.filter(user=user)

    def perform_create(self, serializer):
        """
        Lors de la création, associe automatiquement la tâche à l'utilisateur connecté.
        """
        serializer.save(user=self.request.user)
    def validate(self, data):
        if data['end_date'] < data['start_date']:
            raise serializers.ValidationError("La date de fin doit être après la date de début.")
        return data

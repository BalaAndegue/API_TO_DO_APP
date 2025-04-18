
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from Core.models import Task
from Core.serializers import TaskSerializer

class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les tâches."""
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Ne renvoyer que les tâches de l'utilisateur connecté
        return Task.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Associer la tâche à l'utilisateur connecté automatiquement
        serializer.save(user=self.request.user)

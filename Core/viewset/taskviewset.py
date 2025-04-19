
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, viewsets
from ..models import User, Task, InvitedUserOnTask
from ..serializers import  TaskSerializer,  InvitedUserOnTaskSerializer



# ✅ Gestion des tâches avec `ViewSet`
class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        task = self.get_object()
        if task.user != request.user:
            return Response({"error": "Vous n'avez pas la permission de supprimer cette tâche."}, status=status.HTTP_403_FORBIDDEN)
        task.delete()
        return Response({"message": "Tâche supprimée"}, status=status.HTTP_204_NO_CONTENT)

# ✅ Invitations aux tâches avec `ViewSet`
class InvitedUserOnTaskViewSet(viewsets.ModelViewSet):
    queryset = InvitedUserOnTask.objects.all()
    serializer_class = InvitedUserOnTaskSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()

    def update(self, request, *args, **kwargs):
        invitation = self.get_object()
        if invitation.invited_user != request.user:
            return Response({"error": "Vous ne pouvez pas accepter cette invitation."}, status=status.HTTP_403_FORBIDDEN)
        invitation.accepted = True
        invitation.save()
        return Response({"message": "Invitation acceptée"}, status=status.HTTP_200_OK)

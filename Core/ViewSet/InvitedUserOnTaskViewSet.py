from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from Core.models import InvitedUserOnTask,User
from Core.serializers import InvitedUserOnTaskSerializer
from django.db.models import Q


class InvitedUserOnTaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les invitations liées aux tâches :
    - L'utilisateur voit les invitations qu’il a envoyées ou reçues.
    - Il peut en créer, modifier ou supprimer selon le rôle.
    """
    
    serializer_class = InvitedUserOnTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Affiche les invitations envoyées ou reçues par l'utilisateur.
        """
        # recuperation de l'iutilisateur
        user = self.request.user
        if not user or user.is_anonymous:
            return InvitedUserOnTask.objects.none()
        return InvitedUserOnTask.objects.filter(inviter=user)

    def perform_create(self, serializer):
        """
        Lors de la création, l'utilisateur est automatiquement mis comme l'inviteur.
        """
        #recherche l'utilisateur invité
        invited_user = User.objects.filter(self.invited_user)
        serializer.save(inviter=self.request.user)

    def perform_update(self, serializer):
        """
        Seul l'invité peut accepter/refuser, et seul l'inviteur peut modifier les autres infos.
        """
        invitation = serializer.instance
        user = self.request.user

        # L'invité peut seulement changer le statut `accepted`
        if user == invitation.invited_user:
            if 'accepted' in serializer.validated_data:
                invitation.accepted = serializer.validated_data['accepted']
                invitation.save()
            else:
                raise PermissionDenied("Vous pouvez seulement accepter ou refuser une invitation.")
        elif user == invitation.inviter:
            serializer.save()
        else:
            raise PermissionDenied("Vous n'avez pas le droit de modifier cette invitation.")

    def perform_destroy(self, instance):
        """
        Seul l'inviteur ou l'invité peut supprimer l'invitation.
        """
        user = self.request.user
        if user != instance.inviter and user != instance.invited_user:
            raise PermissionDenied("Vous ne pouvez pas supprimer cette invitation.")
        instance.delete()

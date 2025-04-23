from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from Core.models import InvitedUserOnTask,User
from Core.serializers import InvitedUserOnTaskSerializer
from django.db.models import Q
from django.core.mail import EmailMessage, send_mail
from django.conf import settings
from django.urls import reverse

class InvitedUserOnTaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les invitations liées aux tâches :
    - L'utilisateur voit les invitations qu’il a envoyées ou reçues.
    - Il peut en créer, modifier ou supprimer selon le rôle.
    """
    
    serializer_class = InvitedUserOnTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args , **kwargs):
        """
        Affiche les invitations envoyées ou reçues par l'utilisateur.
        """
        # recuperation de l'iutilisateur
        user = self.request.user
        queryset = InvitedUserOnTask.objects.all() 
        serializer_class = InvitedUserOnTaskSerializer
        if not user or user.is_anonymous:
            return InvitedUserOnTask.objects.none()
        return Response({"success ": True,"message": "objet retournee","data ":InvitedUserOnTask.objects.filter(inviter=user)})

    def create(self, request, *args, **kwargs):
        """
        Lors de la création, l'utilisateur est automatiquement mis comme l'inviteur.
        """
        
        email_invited = request.data.get("email_invited_user")
        invited_user = User.objects.filter(email=email_invited).first()  # ✅ Utiliser `.first()` pour éviter une liste

        if not invited_user:
            return Response({"success": True, "message": "utilisateur introuvable", "data": serializer.data}, status=status.HTTP_400_BAD_REQUEST)

        #password_reset_url = reverse('reset-password', kwargs={'reset_id': new_password_reset.reset_id})

        #full_password_reset_url = f'{request.scheme}://{request.get_host()}{password_reset_url}'
        full_password_reset_url = f'vous avez ete invite par {self.request.user}'

        email_body = f'Reset your password using the link below:\n\n\n{full_password_reset_url}'
        
        email_message = EmailMessage(
                'Reset your password', # email subject
                email_body,
                settings.EMAIL_HOST_USER, # email sender
                [email_invited] # email  receiver 
            )
        email_message.send()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(inviter=request.user, invited_user=invited_user)  # ✅ Enregistre inviter et invited_user

        return Response({"success": True, "message": "Invitation envoyée avec succès", "data": serializer.data}, status=status.HTTP_201_CREATED)

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

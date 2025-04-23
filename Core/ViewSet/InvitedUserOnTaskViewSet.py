from rest_framework.exceptions import ValidationError,PermissionDenied
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from Core.models import InvitedUserOnTask,User
from Core.serializers import InvitedUserOnTaskSerializer
from django.core.mail import EmailMessage
from django.conf import settings

class InvitedUserOnTaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les invitations liées aux tâches :
    - L'utilisateur voit les invitations qu’il a envoyées ou reçues.
    - Il peut en créer, modifier ou supprimer selon le rôle.
    """
    
    serializer_class = InvitedUserOnTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return InvitedUserOnTask.objects.none() 
        
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

    def create(self, request, *args, **kwargs):
        """
        Lors de la création, l'utilisateur est automatiquement mis comme l'inviteur.
        """

        try:
            email_invited = request.data.get("email_invited_user")

            if not email_invited:
                return Response({
                    "success": False,
                    "message": "L'e-mail de l'utilisateur invité est requis."
                }, status=status.HTTP_400_BAD_REQUEST)

            invited_user = User.objects.filter(email=email_invited).first()

            if not invited_user:
                return Response({
                    "success": False,
                    "message": "Utilisateur invité introuvable.",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)

            # Message d'invitation
            full_message = f"Vous avez été invité à collaborer par {request.user.email}."

            email_message = EmailMessage(
                subject='Invitation à collaborer sur une tâche',
                body=full_message,
                from_email=settings.EMAIL_HOST_USER,
                to=[email_invited]
            )
            email_message.send(fail_silently=False)

            # Création de l'invitation
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(inviter=request.user, invited_user=invited_user)

            return Response({
                "success": True,
                "message": "Invitation envoyée avec succès.",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        except ValidationError as ve:
            return Response({
                "success": False,
                "message": "Erreur de validation.",
                "errors": ve.detail
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "success": False,
                "message": "Une erreur est survenue lors de l'envoi de l'invitation.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        
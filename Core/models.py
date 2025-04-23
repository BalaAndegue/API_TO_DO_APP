from django.db import models
from django.contrib.auth.models import AbstractUser,User
import uuid
from django.conf import settings
from django.forms import ValidationError

class PasswordReset(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) # supprime la demande si l'utilisateur est supprime
    reset_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False) # Génère un UUID unique pour identifier chaque demande
    created_when = models.DateTimeField(auto_now_add=True) #Stocke la date de création pour gérer l’expiration du lien. 

    def __str__(self):
        return f"Password reset for {self.user.username} at {self.created_when}"
    
class User(AbstractUser):
    # LES AUTRES CHAMPS SONT DÉJÀ ^RESENTS DANS ABSTRACTSUSER
    phone_number = models.CharField(max_length=20, blank=True, null=True) # Numéro de téléphone de l'utilisateur
    avatar = models.ImageField(verbose_name="avatar", blank=True, null=True) # Avatar de l'utilisateur

class Task(models.Model):
    class Priority(models.IntegerChoices):
        LOW = 1, 'Faible'
        MEDIUM = 2, 'Moyenne'
        HIGH = 3, 'Élevée'

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tasks")
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=False, related_name="tasks")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.BooleanField(default=False)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    time_reminder = models.IntegerField(default=0)
    reminder = models.BooleanField(default=False)
    priority = models.IntegerField(choices=Priority.choices, default=Priority.MEDIUM)

   
    
class Category(models.Model):
    id = models.AutoField(primary_key=True) # Utilise un champ AutoField pour l'identifiant unique de la catégorie
    name = models.CharField(max_length=255) # Nom de la catégorie
    description = models.CharField(max_length=255,default="Description")
    icon = models.CharField(max_length=255,default="") # Nom de l'icoone
    created_at = models.DateTimeField(auto_now_add=True) # Date de création de la catégorie
    updated_at = models.DateTimeField(auto_now=True) # Date de mise à jour de la catégorie


class InvitedUserOnTask(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)  # 🔗 La tâche concernée
    inviter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="task_invitations")  # 🔗 Celui qui invite
    invited_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="task_invited")  # 🔗 Celui qui est invité
    accepted = models.BooleanField(default=False)  # ✅ Statut d'acceptation
    invited_at = models.DateTimeField(auto_now_add=True)  # 📅 Date d’invitation

    
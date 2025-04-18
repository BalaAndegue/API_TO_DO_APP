from django.db import models
from django.contrib.auth.models import User
import uuid

class PasswordReset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE) # supprime la demande si l'utilisateur est supprime
    reset_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False) # Génère un UUID unique pour identifier chaque demande
    created_when = models.DateTimeField(auto_now_add=True) #Stocke la date de création pour gérer l’expiration du lien. 

    def __str__(self):
        return f"Password reset for {self.user.username} at {self.created_when}"
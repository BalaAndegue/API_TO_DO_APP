from rest_framework import serializers
from .models import InvitedUserOnTask, Task, Category, PasswordReset, User
from django.contrib.auth import authenticate


# Serializer pour l'enregistrement et la représentation des utilisateurs
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'avatar', 'password']
        extra_kwargs = {
            'password': {'write_only': True}  # Le mot de passe ne sera jamais renvoyé côté client
        }

    # Vérifie que le nom d'utilisateur est unique
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà utilisé.")
        return value

    # Vérifie que l'adresse email est unique
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value

    # Méthode appelée lors de la création de l'utilisateur
    def create(self, validated_data):
        password = validated_data.pop('password')  # On retire le mot de passe pour le hacher
        user = User(**validated_data)
        user.set_password(password)  # Hash du mot de passe
        user.save()
        return user


# Serializer pour la connexion (login)
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    # Méthode de validation pour vérifier que les identifiants sont corrects
    def validate(self, data):
        user = authenticate(**data)  # Authentification avec Django
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Identifiants invalides")


# Serializer pour les tâches
class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'  # Tous les champs du modèle
        read_only_fields = ['user', 'created_at', 'updated_at']  # Champs gérés automatiquement

    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError("La date de fin doit être après la date de début.")
        return data

    
# Serializer pour les catégories
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']


# Serializer pour les objets de réinitialisation de mot de passe
class PasswordResetSerializer(serializers.ModelSerializer):
    class Meta:
        model = PasswordReset
        fields = '__all__'
        read_only_fields = ['reset_id', 'created_when']

class InvitedUserOnTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvitedUserOnTask
        fields = '__all__'
        read_only_fields = ['inviter', 'invited_at']  # ✅ L’utilisateur qui invite est ajouté automatiquement

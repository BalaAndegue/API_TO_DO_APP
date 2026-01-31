from rest_framework import serializers
from .models import InvitedUserOnTask, Task, Category, PasswordReset, User, Board, List, Card, Label, BoardMember, CardMember, CardLabel, Checklist, ChecklistItem, Comment, Attachment, Activity


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
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    # Méthode de validation pour vérifier que les identifiants sont corrects
    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Email ou mot de passe invalide")

        if not user.check_password(password):
            raise serializers.ValidationError("Email ou mot de passe invalide")

        if not user.is_active:
            raise serializers.ValidationError("Informations invalide.")

        return user


 

# Serializer pour les objets de réinitialisation de mot de passe
class PasswordResetSerializer(serializers.ModelSerializer):
    class Meta:
        model = PasswordReset
        fields = '__all__'
        read_only_fields = ['reset_id', 'created_when']

class InvitedUserOnTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvitedUserOnTask
        fields = ['id_task', "email_invited_user"]
        read_only_fields = ['inviter', 'invited_at']  # L’utilisateur qui invite est ajouté automatiquement

class BoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = '__all__'
        read_only_fields = ['creator', 'created_at', 'updated_at']

class ListSerializer(serializers.ModelSerializer):
    class Meta:
        model = List
        fields = '__all__'
        read_only_fields = ['created_at']

class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = '__all__'

class BoardMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoardMember
        fields = '__all__'
        read_only_fields = []

class CardMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardMember
        fields = '__all__'
        read_only_fields = []

class CardLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardLabel
        fields = '__all__'
        read_only_fields = []

class ChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Checklist
        fields = '__all__'
        read_only_fields = []

class ChecklistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistItem
        fields = '__all__'
        read_only_fields = []

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ['created_at']

class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = '__all__'
        read_only_fields = []

class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = '__all__'
        read_only_fields = ['created_at']

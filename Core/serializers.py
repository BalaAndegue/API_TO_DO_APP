from rest_framework import serializers
from .models import PasswordReset, User, Board, List, Card, Label, BoardMember, CardMember, CardLabel, Checklist, ChecklistItem, Comment, Attachment, Activity, BoardInvitation

# Serializer pour l'enregistrement et la représentation des utilisateurs
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['user_id', 'username', 'email', 'first_name', 'last_name', 'bio', 'avatar_url', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà utilisé.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

# Serializer pour la connexion (login)
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

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
            raise serializers.ValidationError("Compte désactivé.")

        return user

class PasswordResetSerializer(serializers.ModelSerializer):
    class Meta:
        model = PasswordReset
        fields = '__all__'
        read_only_fields = ['reset_id', 'created_when']

class BoardMemberSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = BoardMember
        fields = ['id', 'board', 'user', 'user_details', 'role', 'joined_at']
        read_only_fields = ['joined_at']

class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = '__all__'

class CardLabelSerializer(serializers.ModelSerializer):
    label_details = LabelSerializer(source='label', read_only=True)

    class Meta:
        model = CardLabel
        fields = ['id', 'card', 'label', 'label_details']

class CardMemberSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)

    class Meta:
        model = CardMember
        fields = ['id', 'card', 'user', 'user_details', 'added_at']

class ChecklistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistItem
        fields = '__all__'

class ChecklistSerializer(serializers.ModelSerializer):
    items = ChecklistItemSerializer(many=True, read_only=True)

    class Meta:
        model = Checklist
        fields = ['checklist_id', 'card', 'name', 'position', 'created_at', 'items']

class AttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_details = UserSerializer(source='uploaded_by', read_only=True)

    class Meta:
        model = Attachment
        fields = ['attach_id', 'card', 'filename', 'url', 'mime_type', 'size', 'uploaded_by', 'uploaded_by_details', 'uploaded_at']
        read_only_fields = ['uploaded_at']

class CommentSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)

    class Meta:
        model = Comment
        fields = ['comment_id', 'card', 'user', 'user_details', 'content', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class CardSerializer(serializers.ModelSerializer):
    labels = CardLabelSerializer(source='card_labels', many=True, read_only=True)
    members = CardMemberSerializer(source='card_members', many=True, read_only=True)
    checklists = ChecklistSerializer(many=True, read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    comments_count = serializers.IntegerField(source='comments.count', read_only=True)

    class Meta:
        model = Card
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class ListSerializer(serializers.ModelSerializer):
    cards = CardSerializer(many=True, read_only=True)

    class Meta:
        model = List
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class BoardSerializer(serializers.ModelSerializer):
    lists = ListSerializer(many=True, read_only=True)
    members = BoardMemberSerializer(source='board_members', many=True, read_only=True)
    creator_details = UserSerializer(source='creator', read_only=True)

    class Meta:
        model = Board
        fields = ['board_id', 'name', 'description', 'visibility', 'background_type', 'background_value', 'creator', 'creator_details', 'position', 'is_closed', 'created_at', 'updated_at', 'lists', 'members']
        read_only_fields = ['creator', 'created_at', 'updated_at']

class BoardInvitationSerializer(serializers.ModelSerializer):
    inviter_details = UserSerializer(source='inviter', read_only=True)
    board_name = serializers.CharField(source='board.name', read_only=True)

    class Meta:
        model = BoardInvitation
        fields = ['id', 'board', 'board_name', 'inviter', 'inviter_details', 'email', 'token', 'accepted', 'created_at']
        read_only_fields = ['token', 'created_at', 'accepted']

class ActivitySerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)

    class Meta:
        model = Activity
        fields = '__all__'
        read_only_fields = ['created_at']

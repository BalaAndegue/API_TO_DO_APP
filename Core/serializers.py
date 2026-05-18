from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import (
    PasswordReset, User, Board, List, Card, Label,
    BoardMember, CardMember, CardLabel, Checklist,
    ChecklistItem, Comment, Attachment, Activity, BoardInvitation,
)


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class UserPublicSerializer(serializers.ModelSerializer):
    """Minimal user representation embedded in other resources."""
    class Meta:
        model = User
        fields = ['user_id', 'username', 'first_name', 'last_name', 'avatar_url']
        read_only_fields = fields


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'user_id', 'username', 'email',
            'first_name', 'last_name', 'bio', 'avatar_url',
            'created_at', 'password',
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'user_id': {'read_only': True},
            'created_at': {'read_only': True},
        }

    def validate_username(self, value):
        qs = User.objects.filter(username=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà utilisé.")
        return value

    def validate_email(self, value):
        qs = User.objects.filter(email=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError("Email ou mot de passe invalide.")
        if not user.check_password(data['password']):
            raise serializers.ValidationError("Email ou mot de passe invalide.")
        if not user.is_active:
            raise serializers.ValidationError("Compte désactivé.")
        return user


class PasswordResetSerializer(serializers.ModelSerializer):
    class Meta:
        model = PasswordReset
        fields = '__all__'
        read_only_fields = ['reset_id', 'created_when']


# ---------------------------------------------------------------------------
# Label
# ---------------------------------------------------------------------------

class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ['label_id', 'board', 'name', 'color', 'archived']


# ---------------------------------------------------------------------------
# Checklist
# ---------------------------------------------------------------------------

class ChecklistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistItem
        fields = ['item_id', 'checklist', 'name', 'checked', 'position', 'created_at']
        read_only_fields = ['item_id', 'created_at']


class ChecklistSerializer(serializers.ModelSerializer):
    items = ChecklistItemSerializer(many=True, read_only=True)
    items_total = serializers.IntegerField(source='items.count', read_only=True)
    items_checked = serializers.SerializerMethodField()

    class Meta:
        model = Checklist
        fields = ['checklist_id', 'card', 'name', 'position', 'created_at', 'items_total', 'items_checked', 'items']
        read_only_fields = ['checklist_id', 'created_at']

    def get_items_checked(self, obj):
        return obj.items.filter(checked=True).count()


# ---------------------------------------------------------------------------
# Attachment
# ---------------------------------------------------------------------------

class AttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_details = UserPublicSerializer(source='uploaded_by', read_only=True)

    class Meta:
        model = Attachment
        fields = [
            'attach_id', 'card', 'filename', 'url',
            'mime_type', 'size', 'uploaded_by', 'uploaded_by_details', 'uploaded_at',
        ]
        read_only_fields = ['attach_id', 'uploaded_at', 'uploaded_by']


# ---------------------------------------------------------------------------
# Comment
# ---------------------------------------------------------------------------

class CommentSerializer(serializers.ModelSerializer):
    user_details = UserPublicSerializer(source='user', read_only=True)
    is_edited = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'comment_id', 'card', 'user', 'user_details',
            'content', 'created_at', 'updated_at', 'is_edited',
        ]
        read_only_fields = ['comment_id', 'user', 'created_at', 'updated_at']

    def get_is_edited(self, obj):
        delta = obj.updated_at - obj.created_at
        return delta.total_seconds() > 2


# ---------------------------------------------------------------------------
# Card
# ---------------------------------------------------------------------------

class CardLabelSerializer(serializers.ModelSerializer):
    label_details = LabelSerializer(source='label', read_only=True)

    class Meta:
        model = CardLabel
        fields = ['id', 'card', 'label', 'label_details']


class CardMemberSerializer(serializers.ModelSerializer):
    user_details = UserPublicSerializer(source='user', read_only=True)

    class Meta:
        model = CardMember
        fields = ['id', 'card', 'user', 'user_details', 'added_at']
        read_only_fields = ['added_at']


class CardSerializer(serializers.ModelSerializer):
    """Full card detail — used on retrieve."""
    labels = CardLabelSerializer(source='card_labels', many=True, read_only=True)
    members = CardMemberSerializer(source='card_members', many=True, read_only=True)
    checklists = ChecklistSerializer(many=True, read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    comments_count = serializers.IntegerField(source='comments.count', read_only=True)

    class Meta:
        model = Card
        fields = [
            'card_id', 'list', 'board', 'title', 'description',
            'start_date', 'due_date', 'due_date_complete',
            'cover_image_url', 'position', 'archived',
            'created_at', 'updated_at',
            'labels', 'members', 'checklists', 'attachments', 'comments_count',
        ]
        read_only_fields = ['card_id', 'board', 'created_at', 'updated_at']


class CardListSerializer(serializers.ModelSerializer):
    """Lightweight card — used when embedded inside a list."""
    labels = CardLabelSerializer(source='card_labels', many=True, read_only=True)
    members = CardMemberSerializer(source='card_members', many=True, read_only=True)
    comments_count = serializers.IntegerField(source='comments.count', read_only=True)

    class Meta:
        model = Card
        fields = [
            'card_id', 'title', 'description', 'position',
            'due_date', 'due_date_complete', 'cover_image_url',
            'archived', 'labels', 'members', 'comments_count',
        ]


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

class ListSerializer(serializers.ModelSerializer):
    cards = CardListSerializer(many=True, read_only=True)
    cards_count = serializers.IntegerField(source='cards.count', read_only=True)

    class Meta:
        model = List
        fields = [
            'list_id', 'board', 'name', 'position', 'archived',
            'created_at', 'updated_at', 'cards_count', 'cards',
        ]
        read_only_fields = ['list_id', 'created_at', 'updated_at']


class ListLightSerializer(serializers.ModelSerializer):
    """Minimal list — used when embedded inside board detail."""
    cards_count = serializers.IntegerField(source='cards.count', read_only=True)

    class Meta:
        model = List
        fields = ['list_id', 'name', 'position', 'archived', 'cards_count']


# ---------------------------------------------------------------------------
# Board
# ---------------------------------------------------------------------------

class BoardMemberSerializer(serializers.ModelSerializer):
    user_details = UserPublicSerializer(source='user', read_only=True)

    class Meta:
        model = BoardMember
        fields = ['id', 'board', 'user', 'user_details', 'role', 'joined_at']
        read_only_fields = ['joined_at']


class BoardSerializer(serializers.ModelSerializer):
    """Full board detail — includes lists summary and members."""
    lists = ListLightSerializer(many=True, read_only=True)
    members = BoardMemberSerializer(source='board_members', many=True, read_only=True)
    creator_details = UserPublicSerializer(source='creator', read_only=True)
    lists_count = serializers.IntegerField(source='lists.count', read_only=True)

    class Meta:
        model = Board
        fields = [
            'board_id', 'name', 'description', 'visibility',
            'background_type', 'background_value',
            'creator', 'creator_details', 'position', 'is_closed',
            'created_at', 'updated_at',
            'lists_count', 'lists', 'members',
        ]
        read_only_fields = ['board_id', 'creator', 'created_at', 'updated_at']


class BoardListSerializer(serializers.ModelSerializer):
    """Minimal board — used when listing all boards."""
    creator_details = UserPublicSerializer(source='creator', read_only=True)
    members_count = serializers.IntegerField(source='board_members.count', read_only=True)
    lists_count = serializers.IntegerField(source='lists.count', read_only=True)

    class Meta:
        model = Board
        fields = [
            'board_id', 'name', 'description', 'visibility',
            'background_type', 'background_value',
            'creator_details', 'position', 'is_closed',
            'members_count', 'lists_count', 'created_at',
        ]


# ---------------------------------------------------------------------------
# Invitation & Activity
# ---------------------------------------------------------------------------

class BoardInvitationSerializer(serializers.ModelSerializer):
    inviter_details = UserPublicSerializer(source='inviter', read_only=True)
    board_name = serializers.CharField(source='board.name', read_only=True)

    class Meta:
        model = BoardInvitation
        fields = [
            'id', 'board', 'board_name', 'inviter', 'inviter_details',
            'email', 'token', 'accepted', 'created_at',
        ]
        read_only_fields = ['token', 'created_at', 'accepted', 'inviter']


class ActivitySerializer(serializers.ModelSerializer):
    user_details = UserPublicSerializer(source='user', read_only=True)

    class Meta:
        model = Activity
        fields = [
            'activity_id', 'board', 'card', 'list',
            'user', 'user_details', 'action_type', 'content', 'created_at',
        ]
        read_only_fields = ['activity_id', 'created_at']

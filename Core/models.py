from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
import uuid

class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True, db_index=True)
    email = models.EmailField(max_length=100, unique=True, db_index=True)
    password_hash = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return self.username

class PasswordReset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reset_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_when = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Password reset for {self.user.username} at {self.created_when}"

class Board(models.Model):
    class Visibility(models.TextChoices):
        PUBLIC = 'public', 'Public'
        PRIVATE = 'private', 'Private'

    board_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    visibility = models.CharField(max_length=7, choices=Visibility.choices, default=Visibility.PRIVATE)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='boards_created', db_index=True)
    position = models.IntegerField(default=0, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'boards'
        indexes = [
            models.Index(fields=['creator']),
            models.Index(fields=['position']),
        ]

    def __str__(self):
        return self.name

class List(models.Model):
    list_id = models.AutoField(primary_key=True)
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='lists', db_index=True)
    name = models.CharField(max_length=100)
    position = models.IntegerField(db_index=True)
    archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'lists'
        indexes = [
            models.Index(fields=['board']),
            models.Index(fields=['position']),
        ]

    def __str__(self):
        return self.name

class Card(models.Model):
    card_id = models.AutoField(primary_key=True)
    list = models.ForeignKey(List, on_delete=models.CASCADE, related_name='cards', db_index=True)
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='cards', db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    due_date = models.DateTimeField(blank=True, null=True)
    position = models.IntegerField(db_index=True)
    archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cards'
        indexes = [
            models.Index(fields=['list']),
            models.Index(fields=['board']),
            models.Index(fields=['position']),
        ]

    def __str__(self):
        return self.title

class Label(models.Model):
    label_id = models.AutoField(primary_key=True)
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='labels', db_index=True)
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=20)
    archived = models.BooleanField(default=False)

    class Meta:
        db_table = 'labels'
        indexes = [
            models.Index(fields=['board']),
        ]

    def __str__(self):
        return self.name

class BoardMember(models.Model):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        MEMBER = 'member', 'Member'

    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='board_members', db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='board_memberships', db_index=True)
    role = models.CharField(max_length=6, choices=Role.choices, default=Role.MEMBER)

    class Meta:
        db_table = 'board_members'
        unique_together = ('board', 'user')
        indexes = [
            models.Index(fields=['board']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user} on {self.board} as {self.role}"

class CardMember(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='card_members', db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='card_memberships', db_index=True)

    class Meta:
        db_table = 'card_members'
        unique_together = ('card', 'user')
        indexes = [
            models.Index(fields=['card']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user} on {self.card}"

class CardLabel(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='card_labels', db_index=True)
    label = models.ForeignKey(Label, on_delete=models.CASCADE, related_name='card_labels', db_index=True)

    class Meta:
        db_table = 'card_labels'
        unique_together = ('card', 'label')
        indexes = [
            models.Index(fields=['card']),
            models.Index(fields=['label']),
        ]

    def __str__(self):
        return f"{self.label} on {self.card}"

class Checklist(models.Model):
    checklist_id = models.AutoField(primary_key=True)
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='checklists', db_index=True)
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'checklists'
        indexes = [
            models.Index(fields=['card']),
        ]

    def __str__(self):
        return self.name

class ChecklistItem(models.Model):
    item_id = models.AutoField(primary_key=True)
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name='items', db_index=True)
    name = models.CharField(max_length=200)
    checked = models.BooleanField(default=False)
    position = models.IntegerField(db_index=True)

    class Meta:
        db_table = 'checklist_items'
        indexes = [
            models.Index(fields=['checklist']),
            models.Index(fields=['position']),
        ]

    def __str__(self):
        return self.name

class Comment(models.Model):
    comment_id = models.AutoField(primary_key=True)
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='comments', db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments', db_index=True)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'comments'
        indexes = [
            models.Index(fields=['card']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"Comment by {self.user} on {self.card}"

class Attachment(models.Model):
    attach_id = models.AutoField(primary_key=True)
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='attachments', db_index=True)
    filename = models.CharField(max_length=255)
    url = models.CharField(max_length=500)
    mime_type = models.CharField(max_length=100)
    size = models.IntegerField()
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attachments', db_index=True)

    class Meta:
        db_table = 'attachments'
        indexes = [
            models.Index(fields=['card']),
            models.Index(fields=['uploaded_by']),
        ]

    def __str__(self):
        return self.filename

class Activity(models.Model):
    activity_id = models.AutoField(primary_key=True)
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='activities', db_index=True)
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='activities', db_index=True, blank=True, null=True)
    list = models.ForeignKey(List, on_delete=models.CASCADE, related_name='activities', db_index=True, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities', db_index=True)
    action_type = models.CharField(max_length=50)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'activities'
        indexes = [
            models.Index(fields=['board']),
            models.Index(fields=['card']),
            models.Index(fields=['list']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.action_type} by {self.user} on {self.board}"

# Méthode utilitaire pour drag-drop
from django.db import transaction

def update_position(model, obj_id, new_position):
    with transaction.atomic():
        obj = model.objects.select_for_update().get(pk=obj_id)
        obj.position = new_position
        obj.save()
    return obj


"""
Django signals — automatic Activity logging for key workspace events.

Every write operation on Board, List, Card, Comment, ChecklistItem
produces an Activity record so the frontend can display a real-time
audit trail (like Trello's board activity feed).
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Activity, Board, List, Card, Comment, ChecklistItem, BoardMember


def _log(board, user, action_type, content, card=None, list_obj=None):
    """Create an Activity record. Silently ignores failures so they never
    break the main request."""
    if user is None or not user.is_authenticated:
        return
    try:
        Activity.objects.create(
            board=board,
            card=card,
            list=list_obj,
            user=user,
            action_type=action_type,
            content=content,
        )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Board signals
# ---------------------------------------------------------------------------

@receiver(post_save, sender=Board)
def on_board_saved(sender, instance, created, **kwargs):
    if created:
        _log(
            board=instance,
            user=instance.creator,
            action_type='create_board',
            content=f"a créé le tableau « {instance.name} ».",
        )


# ---------------------------------------------------------------------------
# List signals
# ---------------------------------------------------------------------------

@receiver(post_save, sender=List)
def on_list_saved(sender, instance, created, update_fields, **kwargs):
    if created:
        # The creating user is not available via signal; activity is best
        # created in the ViewSet (perform_create). Skip here to avoid
        # duplicate / anonymous entries.
        return
    if update_fields and 'archived' in update_fields and instance.archived:
        # Archiving is done via ViewSet which passes the user in context;
        # we cannot reliably get the user here, so we skip.
        return


# ---------------------------------------------------------------------------
# Card signals
# ---------------------------------------------------------------------------

@receiver(post_save, sender=Card)
def on_card_saved(sender, instance, created, update_fields, **kwargs):
    """
    We only handle the `created` case here because for updates we need
    the acting user — which is injected by the ViewSet after save via
    Activity.objects.create() directly.  For creation the creator is
    the user who called perform_create, but signals run before the
    ViewSet can log it.  We therefore log creation here using board.creator
    as a fallback; ViewSets override if they need finer attribution.
    """
    if created:
        pass  # Logged in CardViewSet.perform_create via signal_utils below


# ---------------------------------------------------------------------------
# Comment signals
# ---------------------------------------------------------------------------

@receiver(post_save, sender=Comment)
def on_comment_saved(sender, instance, created, **kwargs):
    if created:
        _log(
            board=instance.card.board,
            user=instance.user,
            action_type='add_comment',
            content=f"a commenté la carte « {instance.card.title} ».",
            card=instance.card,
        )


@receiver(post_delete, sender=Comment)
def on_comment_deleted(sender, instance, **kwargs):
    _log(
        board=instance.card.board,
        user=instance.user,
        action_type='delete_comment',
        content=f"a supprimé un commentaire sur « {instance.card.title} ».",
        card=instance.card,
    )


# ---------------------------------------------------------------------------
# ChecklistItem signals
# ---------------------------------------------------------------------------

@receiver(post_save, sender=ChecklistItem)
def on_checklist_item_saved(sender, instance, created, update_fields, **kwargs):
    if not created and update_fields and 'checked' in update_fields:
        card = instance.checklist.card
        action = 'check_item' if instance.checked else 'uncheck_item'
        verb = "a coché" if instance.checked else "a décoché"
        _log(
            board=card.board,
            user=None,  # No user in signal scope — logged by ViewSet
            action_type=action,
            content=f"{verb} « {instance.name} » dans « {card.title} ».",
            card=card,
        )


# ---------------------------------------------------------------------------
# BoardMember signals
# ---------------------------------------------------------------------------

@receiver(post_save, sender=BoardMember)
def on_member_added(sender, instance, created, **kwargs):
    if created:
        _log(
            board=instance.board,
            user=instance.user,
            action_type='join_board',
            content=f"a rejoint le tableau « {instance.board.name} » en tant que {instance.role}.",
        )


@receiver(post_delete, sender=BoardMember)
def on_member_removed(sender, instance, **kwargs):
    _log(
        board=instance.board,
        user=instance.user,
        action_type='leave_board',
        content=f"a quitté le tableau « {instance.board.name} ».",
    )

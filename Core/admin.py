from django.contrib import admin
from .models import (
    User, Board, List, Card, Label, BoardMember, CardMember, CardLabel,
    Checklist, ChecklistItem, Comment, Attachment, Activity
)

admin.site.register(User)
admin.site.register(Board)
admin.site.register(List)
admin.site.register(Card)
admin.site.register(Label)
admin.site.register(BoardMember)
admin.site.register(CardMember)
admin.site.register(CardLabel)
admin.site.register(Checklist)
admin.site.register(ChecklistItem)
admin.site.register(Comment)
admin.site.register(Attachment)
admin.site.register(Activity)

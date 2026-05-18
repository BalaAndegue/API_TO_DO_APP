"""
Shared fixtures for the entire test suite.

Fixture tree:
  alice  (admin of board)
  bob    (member  of board)
  carol  (no access — outsider)
  board  (private, created by alice, bob is member)
  lst    (list on board, pos 0)
  lst2   (second list on board, pos 1)
  card   (card in lst, pos 0)
  label  (label on board)
  checklist  (checklist on card)
  item       (item in checklist)
"""
import pytest
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from Core.models import (
    User, Board, BoardMember, List, Card,
    Label, Checklist, ChecklistItem, Comment, Attachment,
)

BASE = '/api'


# ── User helpers ──────────────────────────────────────────────────────────────

def _make_user(username, email, password='StrongPass123!'):
    u = User.objects.create_user(username=username, email=email, password=password)
    return u


def _client(user):
    token = Token.objects.create(user=user)
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    c._user = user
    return c


# ── User fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def alice(db):
    return _make_user('alice', 'alice@test.com')


@pytest.fixture
def bob(db):
    return _make_user('bob', 'bob@test.com')


@pytest.fixture
def carol(db):
    return _make_user('carol', 'carol@test.com')


@pytest.fixture
def alice_client(alice):
    return _client(alice)


@pytest.fixture
def bob_client(bob):
    return _client(bob)


@pytest.fixture
def carol_client(carol):
    return _client(carol)


# ── Board + membership ────────────────────────────────────────────────────────

@pytest.fixture
def board(alice, bob):
    b = Board.objects.create(
        name='Test Board', visibility='private', creator=alice,
    )
    BoardMember.objects.create(board=b, user=alice, role=BoardMember.Role.ADMIN)
    BoardMember.objects.create(board=b, user=bob,   role=BoardMember.Role.MEMBER)
    return b


@pytest.fixture
def public_board(alice):
    b = Board.objects.create(name='Public Board', visibility='public', creator=alice)
    BoardMember.objects.create(board=b, user=alice, role=BoardMember.Role.ADMIN)
    return b


# ── List / Card ───────────────────────────────────────────────────────────────

@pytest.fixture
def lst(board):
    return List.objects.create(board=board, name='To Do', position=0)


@pytest.fixture
def lst2(board):
    return List.objects.create(board=board, name='Done', position=1)


@pytest.fixture
def card(board, lst):
    return Card.objects.create(
        board=board, list=lst, title='Test Card', position=0,
    )


@pytest.fixture
def card2(board, lst):
    return Card.objects.create(
        board=board, list=lst, title='Second Card', position=1,
    )


# ── Label ─────────────────────────────────────────────────────────────────────

@pytest.fixture
def label(board):
    return Label.objects.create(board=board, name='Bug', color='#ff0000')


# ── Checklist + Item ──────────────────────────────────────────────────────────

@pytest.fixture
def checklist(card):
    return Checklist.objects.create(card=card, name='Tasks', position=0)


@pytest.fixture
def item(checklist):
    return ChecklistItem.objects.create(
        checklist=checklist, name='Step 1', position=0,
    )


# ── Comment ───────────────────────────────────────────────────────────────────

@pytest.fixture
def comment(card, alice):
    return Comment.objects.create(card=card, user=alice, content='Hello world')


# ── Attachment ────────────────────────────────────────────────────────────────

@pytest.fixture
def attachment(card, alice):
    return Attachment.objects.create(
        card=card, uploaded_by=alice,
        filename='doc.pdf', url='https://s3.example.com/doc.pdf',
        mime_type='application/pdf', size=12345,
    )

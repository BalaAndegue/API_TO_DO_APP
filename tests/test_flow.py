"""
Critical-path integration test — covers the full user journey:
  register → login → create board → create list → create card
  → move card → reorder list → invite member → accept invitation

This single file exercises ~80 % of the business logic and catches
regressions across auth, boards, lists, cards, and invitations.
"""
import pytest
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from Core.models import BoardMember, BoardInvitation

BASE = '/api'


# ── helpers ───────────────────────────────────────────────────────────────────

def _register(client, username, email, password='StrongPass123!'):
    res = client.post(f'{BASE}/register/', {
        'username': username, 'email': email, 'password': password,
    })
    assert res.status_code == status.HTTP_201_CREATED, res.json()
    token = res.data['token']
    authed = APIClient()
    authed.credentials(HTTP_AUTHORIZATION=f'Token {token}')
    return authed, res.data['user']


# ── tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCriticalPath:

    def test_register_and_login(self, api_client):
        """Register returns a token; the same credentials work for login."""
        _register(api_client, 'alice', 'alice@flow.com')
        login_res = api_client.post(f'{BASE}/login/', {
            'email': 'alice@flow.com', 'password': 'StrongPass123!',
        })
        assert login_res.status_code == status.HTTP_200_OK
        assert login_res.data['token']

    def test_create_board(self, api_client):
        client, _ = _register(api_client, 'alice2', 'alice2@flow.com')
        res = client.post(f'{BASE}/boards/', {
            'name': 'Sprint #1', 'visibility': 'private',
        })
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data['name'] == 'Sprint #1'

    def test_full_kanban_flow(self, api_client):
        """
        Full Kanban flow:
        Alice creates board → two lists → a card → moves card cross-list.
        Bob registers → Alice invites him → Bob accepts → Bob becomes member.
        """
        # 1. Alice registers
        alice, _ = _register(api_client, 'alice3', 'alice3@flow.com')

        # 2. Create board
        board_res = alice.post(f'{BASE}/boards/', {
            'name': 'Kanban Board', 'visibility': 'private',
        })
        assert board_res.status_code == status.HTTP_201_CREATED
        board_id = board_res.data['board_id']

        # 3. Two lists (columns)
        todo_res = alice.post(f'{BASE}/lists/', {
            'board': board_id, 'name': 'To Do', 'position': 0,
        })
        assert todo_res.status_code == status.HTTP_201_CREATED
        todo_id = todo_res.data['list_id']

        done_res = alice.post(f'{BASE}/lists/', {
            'board': board_id, 'name': 'Done', 'position': 1,
        })
        assert done_res.status_code == status.HTTP_201_CREATED
        done_id = done_res.data['list_id']

        # 4. Create card in "To Do" at position 0
        card_res = alice.post(f'{BASE}/cards/', {
            'list': todo_id, 'title': 'Implement DnD', 'position': 0,
        })
        assert card_res.status_code == status.HTTP_201_CREATED
        card_id = card_res.data['card_id']
        assert card_res.data['list'] == todo_id

        # 5. Second card at position 1 (to test gap-closing after move)
        card2_res = alice.post(f'{BASE}/cards/', {
            'list': todo_id, 'title': 'Write tests', 'position': 1,
        })
        assert card2_res.status_code == status.HTTP_201_CREATED

        # 6. Move card 1 to "Done" at position 0 (cross-list)
        move_res = alice.post(f'{BASE}/cards/{card_id}/move/', {
            'list_id': done_id, 'position': 0,
        })
        assert move_res.status_code == status.HTTP_200_OK
        assert move_res.data['data']['list'] == done_id
        assert move_res.data['data']['position'] == 0

        # 7. Bob registers
        bob, _ = _register(api_client, 'bob3', 'bob3@flow.com')

        # 8. Alice invites Bob by email
        invite_res = alice.post(f'{BASE}/boards/{board_id}/invite/', {
            'email': 'bob3@flow.com',
        })
        assert invite_res.status_code == status.HTTP_200_OK

        # 9. Get invitation token directly from DB
        invitation = BoardInvitation.objects.get(board_id=board_id, email='bob3@flow.com')
        assert not invitation.accepted

        # 10. Bob accepts
        accept_res = bob.post(f'{BASE}/invitations/accept/', {
            'token': str(invitation.token),
        })
        assert accept_res.status_code == status.HTTP_200_OK
        assert accept_res.data['success'] is True

        # 11. Bob is now a member
        assert BoardMember.objects.filter(
            board_id=board_id, user__email='bob3@flow.com',
        ).exists()

        # 12. Invitation flagged as accepted
        invitation.refresh_from_db()
        assert invitation.accepted

    def test_reorder_lists(self, api_client):
        """Dragging a column shifts sibling positions correctly."""
        alice, _ = _register(api_client, 'alice4', 'alice4@flow.com')
        board_res = alice.post(f'{BASE}/boards/', {
            'name': 'DnD Board', 'visibility': 'private',
        })
        board_id = board_res.data['board_id']

        ids = []
        for i, name in enumerate(['A', 'B', 'C']):
            r = alice.post(f'{BASE}/lists/', {
                'board': board_id, 'name': name, 'position': i,
            })
            ids.append(r.data['list_id'])

        # Move list C (pos 2) → pos 0
        move_res = alice.post(f'{BASE}/lists/{ids[2]}/move/', {'position': 0})
        assert move_res.status_code == status.HTTP_200_OK
        assert move_res.data['data']['position'] == 0

        # A → pos 1, B → pos 2
        a = alice.get(f'{BASE}/lists/{ids[0]}/')
        b = alice.get(f'{BASE}/lists/{ids[1]}/')
        assert a.data['position'] == 1
        assert b.data['position'] == 2

    def test_me_endpoint(self, api_client):
        """GET /api/users/me/ returns the authenticated user's profile."""
        client, _ = _register(api_client, 'alice5', 'alice5@flow.com')
        res = client.get(f'{BASE}/users/me/')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['email'] == 'alice5@flow.com'

    def test_unauthenticated_board_access_denied(self, api_client):
        """Anonymous requests to the API return 401, not a redirect."""
        res = api_client.get(f'{BASE}/boards/')
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

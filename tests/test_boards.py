"""
Board endpoints: CRUD, invite, members, close/reopen.
Role enforcement: only admin can update/delete/invite/close.
"""
import pytest
from rest_framework import status
from Core.models import Board, BoardMember, BoardInvitation

BASE = '/api'


@pytest.mark.django_db
class TestBoardCRUD:
    def test_list_returns_own_boards(self, alice_client, board):
        res = alice_client.get(f'{BASE}/boards/')
        assert res.status_code == status.HTTP_200_OK
        ids = [b['board_id'] for b in res.data['results']]
        assert board.board_id in ids

    def test_member_can_list_board(self, bob_client, board):
        res = bob_client.get(f'{BASE}/boards/')
        assert res.status_code == status.HTTP_200_OK
        ids = [b['board_id'] for b in res.data['results']]
        assert board.board_id in ids

    def test_outsider_cannot_see_private_board(self, carol_client, board):
        res = carol_client.get(f'{BASE}/boards/')
        ids = [b['board_id'] for b in res.data['results']]
        assert board.board_id not in ids

    def test_anyone_can_see_public_board(self, carol_client, public_board):
        res = carol_client.get(f'{BASE}/boards/')
        ids = [b['board_id'] for b in res.data['results']]
        assert public_board.board_id in ids

    def test_create_board_auto_adds_admin(self, alice_client, alice):
        res = alice_client.post(f'{BASE}/boards/', {
            'name': 'New Board', 'visibility': 'private',
        })
        assert res.status_code == status.HTTP_201_CREATED
        board_id = res.data['board_id']
        assert BoardMember.objects.filter(
            board_id=board_id, user=alice, role=BoardMember.Role.ADMIN,
        ).exists()

    def test_retrieve_board(self, alice_client, board):
        res = alice_client.get(f'{BASE}/boards/{board.pk}/')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['name'] == board.name

    def test_outsider_cannot_retrieve_private_board(self, carol_client, board):
        res = carol_client.get(f'{BASE}/boards/{board.pk}/')
        assert res.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_can_update_board(self, alice_client, board):
        res = alice_client.patch(f'{BASE}/boards/{board.pk}/', {'name': 'Renamed'})
        assert res.status_code == status.HTTP_200_OK
        board.refresh_from_db()
        assert board.name == 'Renamed'

    def test_member_cannot_update_board(self, bob_client, board):
        res = bob_client.patch(f'{BASE}/boards/{board.pk}/', {'name': 'Hacked'})
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_outsider_cannot_update_board(self, carol_client, board):
        res = carol_client.patch(f'{BASE}/boards/{board.pk}/', {'name': 'Hacked'})
        assert res.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)

    def test_admin_can_delete_board(self, alice_client, board):
        res = alice_client.delete(f'{BASE}/boards/{board.pk}/')
        assert res.status_code == status.HTTP_204_NO_CONTENT
        assert not Board.objects.filter(pk=board.pk).exists()

    def test_member_cannot_delete_board(self, bob_client, board):
        res = bob_client.delete(f'{BASE}/boards/{board.pk}/')
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_filter_by_visibility(self, alice_client, board, public_board):
        res = alice_client.get(f'{BASE}/boards/?visibility=public')
        names = [b['name'] for b in res.data['results']]
        assert public_board.name in names
        assert board.name not in names

    def test_filter_is_closed(self, alice_client, board):
        board.is_closed = True
        board.save()
        res = alice_client.get(f'{BASE}/boards/?is_closed=true')
        ids = [b['board_id'] for b in res.data['results']]
        assert board.board_id in ids

    def test_requires_auth(self, api_client):
        res = api_client.get(f'{BASE}/boards/')
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestBoardInvite:
    def test_admin_can_invite(self, alice_client, board, carol):
        res = alice_client.post(f'{BASE}/boards/{board.pk}/invite/', {
            'email': carol.email,
        })
        assert res.status_code == status.HTTP_200_OK
        assert BoardInvitation.objects.filter(board=board, email=carol.email).exists()

    def test_member_cannot_invite(self, bob_client, board, carol):
        res = bob_client.post(f'{BASE}/boards/{board.pk}/invite/', {
            'email': carol.email,
        })
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_cannot_invite_existing_member(self, alice_client, board, bob):
        res = alice_client.post(f'{BASE}/boards/{board.pk}/invite/', {
            'email': bob.email,
        })
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_duplicate_pending_invitation_rejected(self, alice_client, board, carol):
        alice_client.post(f'{BASE}/boards/{board.pk}/invite/', {'email': carol.email})
        res = alice_client.post(f'{BASE}/boards/{board.pk}/invite/', {'email': carol.email})
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_email(self, alice_client, board):
        res = alice_client.post(f'{BASE}/boards/{board.pk}/invite/', {})
        assert res.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestBoardMembers:
    def test_list_members(self, alice_client, board, alice, bob):
        res = alice_client.get(f'{BASE}/boards/{board.pk}/members/')
        assert res.status_code == status.HTTP_200_OK
        usernames = [m['user_details']['username'] for m in res.data]
        assert alice.username in usernames
        assert bob.username in usernames

    def test_member_can_list_members(self, bob_client, board):
        res = bob_client.get(f'{BASE}/boards/{board.pk}/members/')
        assert res.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestBoardCloseReopen:
    def test_admin_can_close(self, alice_client, board):
        res = alice_client.post(f'{BASE}/boards/{board.pk}/close/')
        assert res.status_code == status.HTTP_200_OK
        board.refresh_from_db()
        assert board.is_closed is True

    def test_member_cannot_close(self, bob_client, board):
        res = bob_client.post(f'{BASE}/boards/{board.pk}/close/')
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_reopen(self, alice_client, board):
        board.is_closed = True
        board.save()
        res = alice_client.post(f'{BASE}/boards/{board.pk}/reopen/')
        assert res.status_code == status.HTTP_200_OK
        board.refresh_from_db()
        assert board.is_closed is False

    def test_member_cannot_reopen(self, bob_client, board):
        board.is_closed = True
        board.save()
        res = bob_client.post(f'{BASE}/boards/{board.pk}/reopen/')
        assert res.status_code == status.HTTP_403_FORBIDDEN

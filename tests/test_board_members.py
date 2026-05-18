"""
BoardMember endpoints: list, create, update role, delete.
Only admins can add/change/remove members; members can read.
"""
import pytest
from rest_framework import status
from Core.models import BoardMember

BASE = '/api'


@pytest.mark.django_db
class TestBoardMemberRead:
    def test_member_can_list(self, bob_client, board, alice, bob):
        res = bob_client.get(f'{BASE}/board-members/')
        assert res.status_code == status.HTTP_200_OK
        user_ids = [m['user_details']['user_id'] for m in res.data['results']]
        assert alice.pk in user_ids
        assert bob.pk in user_ids

    def test_outsider_cannot_see_board_members(self, carol_client, board):
        res = carol_client.get(f'{BASE}/board-members/')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['results'] == []

    def test_filter_by_board(self, alice_client, board, public_board, alice):
        res = alice_client.get(f'{BASE}/board-members/?board={board.pk}')
        assert res.status_code == status.HTTP_200_OK

    def test_requires_auth(self, api_client):
        res = api_client.get(f'{BASE}/board-members/')
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestBoardMemberCreate:
    def test_admin_can_add_member(self, alice_client, board, carol):
        res = alice_client.post(f'{BASE}/board-members/', {
            'board': board.pk, 'user': carol.pk, 'role': 'member',
        })
        assert res.status_code == status.HTTP_201_CREATED
        assert BoardMember.objects.filter(board=board, user=carol).exists()

    def test_member_cannot_add_member(self, bob_client, board, carol):
        res = bob_client.post(f'{BASE}/board-members/', {
            'board': board.pk, 'user': carol.pk, 'role': 'member',
        })
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_outsider_cannot_add_member(self, carol_client, board, carol):
        res = carol_client.post(f'{BASE}/board-members/', {
            'board': board.pk, 'user': carol.pk, 'role': 'member',
        })
        assert res.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestBoardMemberUpdateRole:
    def test_admin_can_change_role(self, alice_client, board, bob):
        membership = BoardMember.objects.get(board=board, user=bob)
        res = alice_client.patch(f'{BASE}/board-members/{membership.pk}/', {
            'role': 'admin',
        })
        assert res.status_code == status.HTTP_200_OK
        membership.refresh_from_db()
        assert membership.role == 'admin'

    def test_member_cannot_change_role(self, bob_client, board, alice):
        membership = BoardMember.objects.get(board=board, user=alice)
        res = bob_client.patch(f'{BASE}/board-members/{membership.pk}/', {
            'role': 'observer',
        })
        assert res.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestBoardMemberDelete:
    def test_admin_can_remove_member(self, alice_client, board, bob):
        membership = BoardMember.objects.get(board=board, user=bob)
        res = alice_client.delete(f'{BASE}/board-members/{membership.pk}/')
        assert res.status_code == status.HTTP_204_NO_CONTENT
        assert not BoardMember.objects.filter(pk=membership.pk).exists()

    def test_member_cannot_remove_member(self, bob_client, board, alice):
        membership = BoardMember.objects.get(board=board, user=alice)
        res = bob_client.delete(f'{BASE}/board-members/{membership.pk}/')
        assert res.status_code == status.HTTP_403_FORBIDDEN

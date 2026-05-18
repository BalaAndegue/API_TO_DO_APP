"""
List endpoints: CRUD + move (column reorder).
Only board members can read; only admin can delete.
"""
import pytest
from rest_framework import status
from Core.models import List

BASE = '/api'


@pytest.mark.django_db
class TestListCRUD:
    def test_member_can_list(self, bob_client, lst):
        res = bob_client.get(f'{BASE}/lists/')
        assert res.status_code == status.HTTP_200_OK
        ids = [l['list_id'] for l in res.data['results']]
        assert lst.list_id in ids

    def test_outsider_cannot_see_private_list(self, carol_client, lst):
        res = carol_client.get(f'{BASE}/lists/')
        ids = [l['list_id'] for l in res.data['results']]
        assert lst.list_id not in ids

    def test_filter_by_board(self, alice_client, board, lst, lst2):
        res = alice_client.get(f'{BASE}/lists/?board={board.pk}')
        ids = [l['list_id'] for l in res.data['results']]
        assert lst.list_id in ids
        assert lst2.list_id in ids

    def test_member_can_create_list(self, bob_client, board):
        res = bob_client.post(f'{BASE}/lists/', {
            'board': board.pk, 'name': 'In Progress', 'position': 2,
        })
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data['name'] == 'In Progress'

    def test_outsider_cannot_create_list(self, carol_client, board):
        res = carol_client.post(f'{BASE}/lists/', {
            'board': board.pk, 'name': 'Hack', 'position': 99,
        })
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_list(self, alice_client, lst):
        res = alice_client.get(f'{BASE}/lists/{lst.pk}/')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['name'] == lst.name

    def test_member_can_rename_list(self, bob_client, lst):
        res = bob_client.patch(f'{BASE}/lists/{lst.pk}/', {'name': 'Renamed'})
        assert res.status_code == status.HTTP_200_OK
        lst.refresh_from_db()
        assert lst.name == 'Renamed'

    def test_only_admin_can_delete_list(self, bob_client, alice_client, lst):
        res = bob_client.delete(f'{BASE}/lists/{lst.pk}/')
        assert res.status_code == status.HTTP_403_FORBIDDEN
        res2 = alice_client.delete(f'{BASE}/lists/{lst.pk}/')
        assert res2.status_code == status.HTTP_204_NO_CONTENT

    def test_requires_auth(self, api_client):
        res = api_client.get(f'{BASE}/lists/')
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestListMove:
    def test_move_shifts_siblings(self, alice_client, board, lst, lst2):
        # lst=pos0, lst2=pos1 → move lst2 to pos0
        res = alice_client.post(f'{BASE}/lists/{lst2.pk}/move/', {'position': 0})
        assert res.status_code == status.HTTP_200_OK
        assert res.data['data']['position'] == 0
        lst.refresh_from_db()
        assert lst.position == 1

    def test_noop_same_position(self, alice_client, lst):
        res = alice_client.post(f'{BASE}/lists/{lst.pk}/move/', {'position': lst.position})
        assert res.status_code == status.HTTP_200_OK

    def test_missing_position(self, alice_client, lst):
        res = alice_client.post(f'{BASE}/lists/{lst.pk}/move/', {})
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_outsider_cannot_move(self, carol_client, lst):
        res = carol_client.post(f'{BASE}/lists/{lst.pk}/move/', {'position': 0})
        assert res.status_code == status.HTTP_404_NOT_FOUND

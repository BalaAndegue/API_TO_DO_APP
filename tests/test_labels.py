"""
Label endpoints: CRUD.
Only admins can create/update/delete; members can read.
"""
import pytest
from rest_framework import status
from Core.models import Label

BASE = '/api'


@pytest.mark.django_db
class TestLabelCRUD:
    def test_member_can_list_labels(self, bob_client, label):
        res = bob_client.get(f'{BASE}/labels/')
        assert res.status_code == status.HTTP_200_OK
        ids = [l['label_id'] for l in res.data['results']]
        assert label.label_id in ids

    def test_outsider_cannot_see_labels(self, carol_client, label):
        res = carol_client.get(f'{BASE}/labels/')
        ids = [l['label_id'] for l in res.data['results']]
        assert label.label_id not in ids

    def test_filter_by_board(self, alice_client, board, label):
        res = alice_client.get(f'{BASE}/labels/?board={board.pk}')
        ids = [l['label_id'] for l in res.data['results']]
        assert label.label_id in ids

    def test_admin_can_create_label(self, alice_client, board):
        res = alice_client.post(f'{BASE}/labels/', {
            'board': board.pk, 'name': 'Feature', 'color': '#00ff00',
        })
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data['name'] == 'Feature'

    def test_member_cannot_create_label(self, bob_client, board):
        res = bob_client.post(f'{BASE}/labels/', {
            'board': board.pk, 'name': 'Hack', 'color': '#000',
        })
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_outsider_cannot_create_label(self, carol_client, board):
        res = carol_client.post(f'{BASE}/labels/', {
            'board': board.pk, 'name': 'Hack', 'color': '#000',
        })
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_label(self, alice_client, label):
        res = alice_client.get(f'{BASE}/labels/{label.pk}/')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['name'] == label.name

    def test_admin_can_update_label(self, alice_client, label):
        res = alice_client.patch(f'{BASE}/labels/{label.pk}/', {'name': 'Urgent'})
        assert res.status_code == status.HTTP_200_OK
        label.refresh_from_db()
        assert label.name == 'Urgent'

    def test_member_cannot_update_label(self, bob_client, label):
        res = bob_client.patch(f'{BASE}/labels/{label.pk}/', {'name': 'Hacked'})
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_delete_label(self, alice_client, label):
        res = alice_client.delete(f'{BASE}/labels/{label.pk}/')
        assert res.status_code == status.HTTP_204_NO_CONTENT
        assert not Label.objects.filter(pk=label.pk).exists()

    def test_member_cannot_delete_label(self, bob_client, label):
        res = bob_client.delete(f'{BASE}/labels/{label.pk}/')
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_requires_auth(self, api_client):
        res = api_client.get(f'{BASE}/labels/')
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

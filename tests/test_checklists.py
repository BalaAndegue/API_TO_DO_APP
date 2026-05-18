"""
Checklist + ChecklistItem endpoints: CRUD.
Board members can read/write; outsiders cannot.
"""
import pytest
from rest_framework import status
from Core.models import Checklist, ChecklistItem

BASE = '/api'


@pytest.mark.django_db
class TestChecklistCRUD:
    def test_member_can_list_checklists(self, bob_client, checklist):
        res = bob_client.get(f'{BASE}/checklists/')
        assert res.status_code == status.HTTP_200_OK
        ids = [c['checklist_id'] for c in res.data['results']]
        assert checklist.checklist_id in ids

    def test_outsider_cannot_see_checklists(self, carol_client, checklist):
        res = carol_client.get(f'{BASE}/checklists/')
        ids = [c['checklist_id'] for c in res.data['results']]
        assert checklist.checklist_id not in ids

    def test_filter_by_card(self, alice_client, card, checklist):
        res = alice_client.get(f'{BASE}/checklists/?card={card.pk}')
        assert res.status_code == status.HTTP_200_OK
        ids = [c['checklist_id'] for c in res.data['results']]
        assert checklist.checklist_id in ids

    def test_retrieve_checklist(self, alice_client, checklist):
        res = alice_client.get(f'{BASE}/checklists/{checklist.pk}/')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['name'] == checklist.name

    def test_member_can_create_checklist(self, bob_client, card):
        res = bob_client.post(f'{BASE}/checklists/', {
            'card': card.pk, 'name': 'Sprint Tasks', 'position': 1,
        })
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data['name'] == 'Sprint Tasks'

    def test_outsider_cannot_create_checklist(self, carol_client, card):
        res = carol_client.post(f'{BASE}/checklists/', {
            'card': card.pk, 'name': 'Hack', 'position': 0,
        })
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_member_can_rename_checklist(self, bob_client, checklist):
        res = bob_client.patch(f'{BASE}/checklists/{checklist.pk}/', {
            'name': 'Renamed',
        })
        assert res.status_code == status.HTTP_200_OK
        checklist.refresh_from_db()
        assert checklist.name == 'Renamed'

    def test_member_can_delete_checklist(self, alice_client, checklist):
        res = alice_client.delete(f'{BASE}/checklists/{checklist.pk}/')
        assert res.status_code == status.HTTP_204_NO_CONTENT
        assert not Checklist.objects.filter(pk=checklist.pk).exists()

    def test_requires_auth(self, api_client):
        res = api_client.get(f'{BASE}/checklists/')
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestChecklistItemCRUD:
    def test_member_can_list_items(self, bob_client, item):
        res = bob_client.get(f'{BASE}/checklist-items/')
        assert res.status_code == status.HTTP_200_OK
        ids = [i['item_id'] for i in res.data['results']]
        assert item.item_id in ids

    def test_outsider_cannot_see_items(self, carol_client, item):
        res = carol_client.get(f'{BASE}/checklist-items/')
        ids = [i['item_id'] for i in res.data['results']]
        assert item.item_id not in ids

    def test_filter_by_checklist(self, alice_client, checklist, item):
        res = alice_client.get(f'{BASE}/checklist-items/?checklist={checklist.pk}')
        assert res.status_code == status.HTTP_200_OK
        ids = [i['item_id'] for i in res.data['results']]
        assert item.item_id in ids

    def test_retrieve_item(self, alice_client, item):
        res = alice_client.get(f'{BASE}/checklist-items/{item.pk}/')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['name'] == item.name

    def test_member_can_create_item(self, bob_client, checklist):
        res = bob_client.post(f'{BASE}/checklist-items/', {
            'checklist': checklist.pk, 'name': 'New Step', 'position': 1,
        })
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data['name'] == 'New Step'

    def test_outsider_cannot_create_item(self, carol_client, checklist):
        res = carol_client.post(f'{BASE}/checklist-items/', {
            'checklist': checklist.pk, 'name': 'Hack', 'position': 0,
        })
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_member_can_check_item(self, bob_client, item):
        res = bob_client.patch(f'{BASE}/checklist-items/{item.pk}/', {
            'checked': True,
        })
        assert res.status_code == status.HTTP_200_OK
        item.refresh_from_db()
        assert item.checked is True

    def test_member_can_uncheck_item(self, bob_client, item):
        item.checked = True
        item.save()
        res = bob_client.patch(f'{BASE}/checklist-items/{item.pk}/', {
            'checked': False,
        })
        assert res.status_code == status.HTTP_200_OK
        item.refresh_from_db()
        assert item.checked is False

    def test_member_can_delete_item(self, alice_client, item):
        res = alice_client.delete(f'{BASE}/checklist-items/{item.pk}/')
        assert res.status_code == status.HTTP_204_NO_CONTENT
        assert not ChecklistItem.objects.filter(pk=item.pk).exists()

    def test_requires_auth(self, api_client):
        res = api_client.get(f'{BASE}/checklist-items/')
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

"""
Card endpoints: CRUD, move (DnD), archive/unarchive.
Access scoped to board members; outsiders get 404.
"""
import pytest
from rest_framework import status
from Core.models import Card

BASE = '/api'


@pytest.mark.django_db
class TestCardCRUD:
    def test_member_can_list_cards(self, bob_client, card):
        res = bob_client.get(f'{BASE}/cards/')
        assert res.status_code == status.HTTP_200_OK
        ids = [c['card_id'] for c in res.data['results']]
        assert card.card_id in ids

    def test_outsider_cannot_see_private_cards(self, carol_client, card):
        res = carol_client.get(f'{BASE}/cards/')
        ids = [c['card_id'] for c in res.data['results']]
        assert card.card_id not in ids

    def test_filter_by_list(self, alice_client, lst, card, card2):
        res = alice_client.get(f'{BASE}/cards/?list={lst.pk}')
        ids = [c['card_id'] for c in res.data['results']]
        assert card.card_id in ids
        assert card2.card_id in ids

    def test_filter_by_board(self, alice_client, board, card):
        res = alice_client.get(f'{BASE}/cards/?board={board.pk}')
        ids = [c['card_id'] for c in res.data['results']]
        assert card.card_id in ids

    def test_search_filter(self, alice_client, card):
        res = alice_client.get(f'{BASE}/cards/?search=Test')
        ids = [c['card_id'] for c in res.data['results']]
        assert card.card_id in ids

    def test_member_can_create_card(self, bob_client, lst):
        res = bob_client.post(f'{BASE}/cards/', {
            'list': lst.pk, 'title': 'New Task', 'position': 99,
        })
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data['title'] == 'New Task'
        assert res.data['list'] == lst.pk

    def test_outsider_cannot_create_card(self, carol_client, lst):
        res = carol_client.post(f'{BASE}/cards/', {
            'list': lst.pk, 'title': 'Hack', 'position': 0,
        })
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_card(self, alice_client, card):
        res = alice_client.get(f'{BASE}/cards/{card.pk}/')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['title'] == card.title

    def test_outsider_cannot_retrieve_card(self, carol_client, card):
        res = carol_client.get(f'{BASE}/cards/{card.pk}/')
        assert res.status_code == status.HTTP_404_NOT_FOUND

    def test_member_can_update_card(self, bob_client, card):
        res = bob_client.patch(f'{BASE}/cards/{card.pk}/', {'title': 'Updated'})
        assert res.status_code == status.HTTP_200_OK
        card.refresh_from_db()
        assert card.title == 'Updated'

    def test_outsider_cannot_update_card(self, carol_client, card):
        res = carol_client.patch(f'{BASE}/cards/{card.pk}/', {'title': 'Hacked'})
        assert res.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)

    def test_member_can_delete_card(self, bob_client, card):
        res = bob_client.delete(f'{BASE}/cards/{card.pk}/')
        assert res.status_code == status.HTTP_204_NO_CONTENT

    def test_outsider_cannot_delete_card(self, carol_client, card):
        res = carol_client.delete(f'{BASE}/cards/{card.pk}/')
        assert res.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)

    def test_requires_auth(self, api_client):
        res = api_client.get(f'{BASE}/cards/')
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestCardMove:
    def test_same_list_move_down(self, alice_client, board, lst, card, card2):
        # card=pos0, card2=pos1 → move card to pos1
        res = alice_client.post(f'{BASE}/cards/{card.pk}/move/', {'position': 1})
        assert res.status_code == status.HTTP_200_OK
        assert res.data['data']['position'] == 1
        card2.refresh_from_db()
        assert card2.position == 0

    def test_same_list_move_up(self, alice_client, board, lst, card, card2):
        # card2=pos1 → move to pos0, card should shift to pos1
        res = alice_client.post(f'{BASE}/cards/{card2.pk}/move/', {'position': 0})
        assert res.status_code == status.HTTP_200_OK
        card.refresh_from_db()
        assert card.position == 1

    def test_cross_list_move(self, alice_client, card, lst2):
        res = alice_client.post(f'{BASE}/cards/{card.pk}/move/', {
            'list_id': lst2.pk, 'position': 0,
        })
        assert res.status_code == status.HTTP_200_OK
        assert res.data['data']['list'] == lst2.pk
        assert res.data['data']['position'] == 0

    def test_cannot_move_to_different_board(self, alice_client, card, alice):
        other_board = __import__('Core.models', fromlist=['Board']).Board.objects.create(
            name='Other', visibility='private', creator=alice,
        )
        other_list = __import__('Core.models', fromlist=['List']).List.objects.create(
            board=other_board, name='Other List', position=0,
        )
        res = alice_client.post(f'{BASE}/cards/{card.pk}/move/', {
            'list_id': other_list.pk, 'position': 0,
        })
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_position(self, alice_client, card):
        res = alice_client.post(f'{BASE}/cards/{card.pk}/move/', {})
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_list(self, alice_client, card):
        res = alice_client.post(f'{BASE}/cards/{card.pk}/move/', {
            'list_id': 99999, 'position': 0,
        })
        assert res.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestCardArchive:
    def test_archive(self, alice_client, card):
        res = alice_client.post(f'{BASE}/cards/{card.pk}/archive/')
        assert res.status_code == status.HTTP_200_OK
        card.refresh_from_db()
        assert card.archived is True

    def test_unarchive(self, alice_client, card):
        card.archived = True
        card.save()
        res = alice_client.post(f'{BASE}/cards/{card.pk}/unarchive/')
        assert res.status_code == status.HTTP_200_OK
        card.refresh_from_db()
        assert card.archived is False

    def test_filter_archived(self, alice_client, card):
        card.archived = True
        card.save()
        res = alice_client.get(f'{BASE}/cards/?archived=true')
        ids = [c['card_id'] for c in res.data['results']]
        assert card.card_id in ids

    def test_filter_active(self, alice_client, card):
        res = alice_client.get(f'{BASE}/cards/?archived=false')
        ids = [c['card_id'] for c in res.data['results']]
        assert card.card_id in ids

    def test_outsider_cannot_archive(self, carol_client, card):
        res = carol_client.post(f'{BASE}/cards/{card.pk}/archive/')
        assert res.status_code == status.HTTP_404_NOT_FOUND

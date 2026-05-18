"""
Extra endpoints: CardMember, CardLabel, Attachment, Activity.
All scoped to board membership; outsiders see nothing.
"""
import pytest
from rest_framework import status
from Core.models import CardMember, CardLabel, Attachment, Activity

BASE = '/api'


# ── CardMember ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCardMember:
    def test_member_can_list(self, bob_client, card, bob):
        CardMember.objects.create(card=card, user=bob)
        res = bob_client.get(f'{BASE}/card-members/')
        assert res.status_code == status.HTTP_200_OK

    def test_outsider_cannot_see(self, carol_client, card, bob):
        CardMember.objects.create(card=card, user=bob)
        res = carol_client.get(f'{BASE}/card-members/')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['results'] == []

    def test_member_can_assign(self, bob_client, card, bob):
        res = bob_client.post(f'{BASE}/card-members/', {
            'card': card.pk, 'user': bob.pk,
        })
        assert res.status_code == status.HTTP_201_CREATED

    def test_outsider_cannot_assign(self, carol_client, card, carol):
        res = carol_client.post(f'{BASE}/card-members/', {
            'card': card.pk, 'user': carol.pk,
        })
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_cannot_assign_non_board_member(self, alice_client, card, carol):
        res = alice_client.post(f'{BASE}/card-members/', {
            'card': card.pk, 'user': carol.pk,
        })
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_member_can_unassign(self, alice_client, card, bob):
        assignment = CardMember.objects.create(card=card, user=bob)
        res = alice_client.delete(f'{BASE}/card-members/{assignment.pk}/')
        assert res.status_code == status.HTTP_204_NO_CONTENT

    def test_filter_by_card(self, alice_client, card, bob):
        CardMember.objects.create(card=card, user=bob)
        res = alice_client.get(f'{BASE}/card-members/?card={card.pk}')
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data['results']) >= 1

    def test_requires_auth(self, api_client):
        res = api_client.get(f'{BASE}/card-members/')
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


# ── CardLabel ─────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCardLabel:
    def test_member_can_list(self, bob_client, card, label):
        CardLabel.objects.create(card=card, label=label)
        res = bob_client.get(f'{BASE}/card-labels/')
        assert res.status_code == status.HTTP_200_OK

    def test_outsider_cannot_see(self, carol_client, card, label):
        CardLabel.objects.create(card=card, label=label)
        res = carol_client.get(f'{BASE}/card-labels/')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['results'] == []

    def test_member_can_apply_label(self, bob_client, card, label):
        res = bob_client.post(f'{BASE}/card-labels/', {
            'card': card.pk, 'label': label.pk,
        })
        assert res.status_code == status.HTTP_201_CREATED

    def test_outsider_cannot_apply_label(self, carol_client, card, label):
        res = carol_client.post(f'{BASE}/card-labels/', {
            'card': card.pk, 'label': label.pk,
        })
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_member_can_remove_label(self, alice_client, card, label):
        cl = CardLabel.objects.create(card=card, label=label)
        res = alice_client.delete(f'{BASE}/card-labels/{cl.pk}/')
        assert res.status_code == status.HTTP_204_NO_CONTENT

    def test_filter_by_card(self, alice_client, card, label):
        CardLabel.objects.create(card=card, label=label)
        res = alice_client.get(f'{BASE}/card-labels/?card={card.pk}')
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data['results']) >= 1

    def test_requires_auth(self, api_client):
        res = api_client.get(f'{BASE}/card-labels/')
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


# ── Attachment ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAttachment:
    def test_member_can_list(self, bob_client, attachment):
        res = bob_client.get(f'{BASE}/attachments/')
        assert res.status_code == status.HTTP_200_OK
        ids = [a['attach_id'] for a in res.data['results']]
        assert attachment.attach_id in ids

    def test_outsider_cannot_see(self, carol_client, attachment):
        res = carol_client.get(f'{BASE}/attachments/')
        ids = [a['attach_id'] for a in res.data['results']]
        assert attachment.attach_id not in ids

    def test_member_can_create(self, bob_client, card):
        res = bob_client.post(f'{BASE}/attachments/', {
            'card': card.pk,
            'filename': 'report.pdf',
            'url': 'https://s3.example.com/report.pdf',
            'mime_type': 'application/pdf',
            'size': 99999,
        })
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data['filename'] == 'report.pdf'

    def test_outsider_cannot_create(self, carol_client, card):
        res = carol_client.post(f'{BASE}/attachments/', {
            'card': card.pk,
            'filename': 'hack.pdf',
            'url': 'https://evil.com/hack.pdf',
            'mime_type': 'application/pdf',
            'size': 1,
        })
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_uploader_set_automatically(self, bob_client, bob, card):
        res = bob_client.post(f'{BASE}/attachments/', {
            'card': card.pk,
            'filename': 'auto.pdf',
            'url': 'https://s3.example.com/auto.pdf',
            'mime_type': 'application/pdf',
            'size': 100,
        })
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data['uploaded_by'] == bob.pk

    def test_uploader_can_delete(self, alice_client, attachment):
        res = alice_client.delete(f'{BASE}/attachments/{attachment.pk}/')
        assert res.status_code == status.HTTP_204_NO_CONTENT

    def test_non_uploader_member_cannot_delete(self, bob_client, attachment):
        res = bob_client.delete(f'{BASE}/attachments/{attachment.pk}/')
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_delete_any(self, alice_client, card, bob):
        att = Attachment.objects.create(
            card=card, uploaded_by=bob,
            filename='bob.pdf', url='https://s3.example.com/bob.pdf',
            mime_type='application/pdf', size=5000,
        )
        res = alice_client.delete(f'{BASE}/attachments/{att.pk}/')
        assert res.status_code == status.HTTP_204_NO_CONTENT

    def test_filter_by_card(self, alice_client, card, attachment):
        res = alice_client.get(f'{BASE}/attachments/?card={card.pk}')
        assert res.status_code == status.HTTP_200_OK
        ids = [a['attach_id'] for a in res.data['results']]
        assert attachment.attach_id in ids

    def test_requires_auth(self, api_client):
        res = api_client.get(f'{BASE}/attachments/')
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


# ── Activity ──────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestActivity:
    def test_member_can_list_activity(self, alice_client, board):
        res = alice_client.get(f'{BASE}/activities/')
        assert res.status_code == status.HTTP_200_OK

    def test_outsider_cannot_see_private_activity(self, carol_client, board):
        res = carol_client.get(f'{BASE}/activities/')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['results'] == []

    def test_filter_by_board(self, alice_client, board):
        res = alice_client.get(f'{BASE}/activities/?board={board.pk}')
        assert res.status_code == status.HTTP_200_OK

    def test_filter_by_card(self, alice_client, card):
        res = alice_client.get(f'{BASE}/activities/?card={card.pk}')
        assert res.status_code == status.HTTP_200_OK

    def test_activity_is_read_only(self, alice_client, board):
        res = alice_client.post(f'{BASE}/activities/', {
            'board': board.pk, 'action': 'create_board',
        })
        assert res.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_requires_auth(self, api_client):
        res = api_client.get(f'{BASE}/activities/')
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

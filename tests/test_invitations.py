"""
Invitation endpoints: list (admin-only), retrieve, destroy, accept.
Only board admins can see/cancel invitations; any authenticated user can accept with a valid token.
"""
import pytest
from rest_framework import status
from Core.models import BoardInvitation, BoardMember

BASE = '/api'


@pytest.fixture
def invitation(board, alice, carol):
    return BoardInvitation.objects.create(
        board=board,
        inviter=alice,
        email=carol.email,
    )


@pytest.mark.django_db
class TestInvitationList:
    def test_admin_can_list_invitations(self, alice_client, invitation):
        res = alice_client.get(f'{BASE}/invitations/')
        assert res.status_code == status.HTTP_200_OK
        ids = [i['id'] for i in res.data['results']]
        assert invitation.pk in ids

    def test_member_cannot_list_invitations(self, bob_client, invitation):
        res = bob_client.get(f'{BASE}/invitations/')
        assert res.status_code == status.HTTP_200_OK
        # Bob is a member, not admin — should see empty list
        ids = [i['id'] for i in res.data['results']]
        assert invitation.pk not in ids

    def test_outsider_cannot_list_invitations(self, carol_client, invitation):
        res = carol_client.get(f'{BASE}/invitations/')
        assert res.status_code == status.HTTP_200_OK
        ids = [i['id'] for i in res.data['results']]
        assert invitation.pk not in ids

    def test_requires_auth(self, api_client, invitation):
        res = api_client.get(f'{BASE}/invitations/')
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestInvitationRetrieve:
    def test_admin_can_retrieve(self, alice_client, invitation):
        res = alice_client.get(f'{BASE}/invitations/{invitation.pk}/')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['email'] == invitation.email

    def test_non_admin_gets_404(self, bob_client, invitation):
        res = bob_client.get(f'{BASE}/invitations/{invitation.pk}/')
        assert res.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestInvitationCancel:
    def test_admin_can_cancel_invitation(self, alice_client, invitation):
        res = alice_client.delete(f'{BASE}/invitations/{invitation.pk}/')
        assert res.status_code == status.HTTP_204_NO_CONTENT
        assert not BoardInvitation.objects.filter(pk=invitation.pk).exists()

    def test_member_cannot_cancel_invitation(self, bob_client, invitation):
        res = bob_client.delete(f'{BASE}/invitations/{invitation.pk}/')
        assert res.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)


@pytest.mark.django_db
class TestInvitationAccept:
    def test_carol_can_accept_invitation(self, carol_client, board, invitation):
        res = carol_client.post(f'{BASE}/invitations/accept/', {
            'token': str(invitation.token),
        })
        assert res.status_code == status.HTTP_200_OK
        assert res.data['success'] is True
        assert BoardMember.objects.filter(board=board, user__email=invitation.email).exists()

    def test_accept_marks_invitation_as_used(self, carol_client, invitation):
        carol_client.post(f'{BASE}/invitations/accept/', {
            'token': str(invitation.token),
        })
        invitation.refresh_from_db()
        assert invitation.accepted is True

    def test_cannot_accept_same_token_twice(self, carol_client, invitation):
        carol_client.post(f'{BASE}/invitations/accept/', {
            'token': str(invitation.token),
        })
        res = carol_client.post(f'{BASE}/invitations/accept/', {
            'token': str(invitation.token),
        })
        assert res.status_code == status.HTTP_404_NOT_FOUND

    def test_invalid_token_returns_404(self, carol_client):
        res = carol_client.post(f'{BASE}/invitations/accept/', {
            'token': '00000000-0000-0000-0000-000000000000',
        })
        assert res.status_code == status.HTTP_404_NOT_FOUND

    def test_missing_token_returns_400(self, carol_client):
        res = carol_client.post(f'{BASE}/invitations/accept/', {})
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_already_member_accepts_gracefully(self, bob_client, board, invitation):
        # bob is already a member — accept should still return 200
        invitation.email = 'bob@test.com'
        invitation.save()
        res = bob_client.post(f'{BASE}/invitations/accept/', {
            'token': str(invitation.token),
        })
        assert res.status_code == status.HTTP_200_OK
        assert res.data['success'] is True

    def test_requires_auth(self, api_client, invitation):
        res = api_client.post(f'{BASE}/invitations/accept/', {
            'token': str(invitation.token),
        })
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

"""
Auth endpoints: register, login, logout, /users/me/, change_password.
"""
import pytest
from rest_framework import status
from rest_framework.authtoken.models import Token

BASE = '/api'


@pytest.mark.django_db
class TestRegister:
    def test_success_returns_token(self, api_client):
        res = api_client.post(f'{BASE}/register/', {
            'username': 'newuser', 'email': 'new@test.com', 'password': 'StrongPass123!',
        })
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data['success'] is True
        assert 'token' in res.data['data']
        assert res.data['data']['user']['email'] == 'new@test.com'

    def test_duplicate_email_rejected(self, api_client, alice):
        res = api_client.post(f'{BASE}/register/', {
            'username': 'other', 'email': alice.email, 'password': 'StrongPass123!',
        })
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_duplicate_username_rejected(self, api_client, alice):
        res = api_client.post(f'{BASE}/register/', {
            'username': alice.username, 'email': 'unique@test.com', 'password': 'StrongPass123!',
        })
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_weak_password_rejected(self, api_client):
        res = api_client.post(f'{BASE}/register/', {
            'username': 'weakuser', 'email': 'weak@test.com', 'password': '123',
        })
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_fields_rejected(self, api_client):
        res = api_client.post(f'{BASE}/register/', {'username': 'incomplete'})
        assert res.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLogin:
    def test_success_returns_token(self, api_client, alice):
        res = api_client.post(f'{BASE}/login/', {
            'email': alice.email, 'password': 'StrongPass123!',
        })
        assert res.status_code == status.HTTP_200_OK
        assert 'token' in res.data['data']

    def test_wrong_password(self, api_client, alice):
        res = api_client.post(f'{BASE}/login/', {
            'email': alice.email, 'password': 'WrongPass!',
        })
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_unknown_email(self, api_client):
        res = api_client.post(f'{BASE}/login/', {
            'email': 'nobody@test.com', 'password': 'any',
        })
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_fields(self, api_client):
        res = api_client.post(f'{BASE}/login/', {})
        assert res.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLogout:
    def test_success(self, alice_client):
        res = alice_client.post(f'{BASE}/logout/')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['success'] is True
        # Token must be deleted
        assert not Token.objects.filter(user=alice_client._user).exists()

    def test_requires_auth(self, api_client):
        res = api_client.post(f'{BASE}/logout/')
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestMe:
    def test_returns_own_profile(self, alice_client, alice):
        res = alice_client.get(f'{BASE}/users/me/')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['data']['email'] == alice.email

    def test_requires_auth(self, api_client):
        res = api_client.get(f'{BASE}/users/me/')
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestChangePassword:
    def test_returns_new_token(self, alice_client):
        old_token = Token.objects.get(user=alice_client._user).key
        res = alice_client.post(f'{BASE}/users/change_password/', {
            'new_password': 'NewStrongPass456!',
        })
        assert res.status_code == status.HTTP_200_OK
        new_token = res.data['data']['token']
        assert new_token != old_token
        assert not Token.objects.filter(key=old_token).exists()

    def test_missing_field(self, alice_client):
        res = alice_client.post(f'{BASE}/users/change_password/', {})
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_weak_new_password_rejected(self, alice_client):
        res = alice_client.post(f'{BASE}/users/change_password/', {
            'new_password': '123',
        })
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_requires_auth(self, api_client):
        res = api_client.post(f'{BASE}/users/change_password/', {
            'new_password': 'NewStrongPass456!',
        })
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestUserCRUD:
    def test_list_users(self, alice_client):
        res = alice_client.get(f'{BASE}/users/')
        assert res.status_code == status.HTTP_200_OK

    def test_retrieve_user(self, alice_client, bob):
        res = alice_client.get(f'{BASE}/users/{bob.pk}/')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['username'] == bob.username

    def test_update_own_profile(self, alice_client, alice):
        res = alice_client.patch(f'{BASE}/users/{alice.pk}/', {'bio': 'Updated bio'})
        assert res.status_code == status.HTTP_200_OK
        assert res.data['data']['bio'] == 'Updated bio'

    def test_cannot_update_other_user(self, alice_client, bob):
        res = alice_client.patch(f'{BASE}/users/{bob.pk}/', {'bio': 'Hacked!'})
        assert res.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)

    def test_delete_own_account(self, alice_client, alice):
        res = alice_client.delete(f'{BASE}/users/{alice.pk}/')
        assert res.status_code == status.HTTP_204_NO_CONTENT

    def test_cannot_delete_other_account(self, alice_client, bob):
        res = alice_client.delete(f'{BASE}/users/{bob.pk}/')
        assert res.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)

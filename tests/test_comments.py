"""
Comment endpoints: CRUD.
Author can edit/delete their own comment; admin can also edit/delete any.
Outsiders cannot see or post comments on private boards.
"""
import pytest
from rest_framework import status
from Core.models import Comment

BASE = '/api'


@pytest.mark.django_db
class TestCommentRead:
    def test_member_can_list_comments(self, bob_client, comment):
        res = bob_client.get(f'{BASE}/comments/')
        assert res.status_code == status.HTTP_200_OK
        ids = [c['comment_id'] for c in res.data['results']]
        assert comment.comment_id in ids

    def test_outsider_cannot_see_private_comments(self, carol_client, comment):
        res = carol_client.get(f'{BASE}/comments/')
        ids = [c['comment_id'] for c in res.data['results']]
        assert comment.comment_id not in ids

    def test_filter_by_card(self, alice_client, card, comment):
        res = alice_client.get(f'{BASE}/comments/?card={card.pk}')
        assert res.status_code == status.HTTP_200_OK
        ids = [c['comment_id'] for c in res.data['results']]
        assert comment.comment_id in ids

    def test_retrieve_comment(self, alice_client, comment):
        res = alice_client.get(f'{BASE}/comments/{comment.pk}/')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['content'] == comment.content

    def test_requires_auth(self, api_client):
        res = api_client.get(f'{BASE}/comments/')
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestCommentCreate:
    def test_member_can_post_comment(self, bob_client, card):
        res = bob_client.post(f'{BASE}/comments/', {
            'card': card.pk, 'content': 'Looking good!',
        })
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data['content'] == 'Looking good!'

    def test_outsider_cannot_post_comment(self, carol_client, card):
        res = carol_client.post(f'{BASE}/comments/', {
            'card': card.pk, 'content': 'Hack',
        })
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_author_set_automatically(self, bob_client, bob, card):
        res = bob_client.post(f'{BASE}/comments/', {
            'card': card.pk, 'content': 'Auto-author test',
        })
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data['user'] == bob.pk


@pytest.mark.django_db
class TestCommentUpdate:
    def test_author_can_update_own_comment(self, alice_client, comment):
        res = alice_client.patch(f'{BASE}/comments/{comment.pk}/', {
            'content': 'Edited text',
        })
        assert res.status_code == status.HTTP_200_OK
        comment.refresh_from_db()
        assert comment.content == 'Edited text'

    def test_admin_can_update_any_comment(self, alice_client, bob, card):
        bob_comment = Comment.objects.create(card=card, user=bob, content='Bob said')
        res = alice_client.patch(f'{BASE}/comments/{bob_comment.pk}/', {
            'content': 'Admin edited',
        })
        assert res.status_code == status.HTTP_200_OK

    def test_member_cannot_update_others_comment(self, bob_client, comment):
        res = bob_client.patch(f'{BASE}/comments/{comment.pk}/', {
            'content': 'Hacked',
        })
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_outsider_cannot_update_comment(self, carol_client, comment):
        res = carol_client.patch(f'{BASE}/comments/{comment.pk}/', {
            'content': 'Hacked',
        })
        assert res.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)


@pytest.mark.django_db
class TestCommentDelete:
    def test_author_can_delete_own_comment(self, alice_client, comment):
        res = alice_client.delete(f'{BASE}/comments/{comment.pk}/')
        assert res.status_code == status.HTTP_204_NO_CONTENT
        assert not Comment.objects.filter(pk=comment.pk).exists()

    def test_admin_can_delete_any_comment(self, alice_client, bob, card):
        bob_comment = Comment.objects.create(card=card, user=bob, content='Bob said')
        res = alice_client.delete(f'{BASE}/comments/{bob_comment.pk}/')
        assert res.status_code == status.HTTP_204_NO_CONTENT

    def test_member_cannot_delete_others_comment(self, bob_client, comment):
        res = bob_client.delete(f'{BASE}/comments/{comment.pk}/')
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_outsider_cannot_delete_comment(self, carol_client, comment):
        res = carol_client.delete(f'{BASE}/comments/{comment.pk}/')
        assert res.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)

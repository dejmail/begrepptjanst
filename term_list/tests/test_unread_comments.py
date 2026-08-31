"""A logged-in staff member checking how many term comments are waiting for review."""

import pytest
from django.contrib.auth.models import User

from term_list.tests.factories import ConceptCommentFactory, ConceptFactory, DictionaryFactory

pytestmark = pytest.mark.django_db


class TestUnreadCommentsAccess:
    def test_anonymous_request_is_denied(self, client):
        """An unauthenticated request to the unread-comments endpoint is redirected to login, not served."""
        response = client.get("/unread-comments/")
        assert response.status_code == 302


class TestUnreadCommentsCounting:
    def test_counts_are_scoped_to_the_logged_in_users_groups(self, client, group):
        """Comment counts only include concepts in dictionaries belonging to the logged-in user's own groups."""
        user = User.objects.create_user(username="staff", password="password123")
        user.groups.add(group)
        client.force_login(user)

        own_dictionary = DictionaryFactory()
        own_dictionary.groups.add(group)
        own_concept = ConceptFactory()
        own_concept.dictionaries.add(own_dictionary)
        ConceptCommentFactory(concept=own_concept)  # default status: unread

        other_dictionary = DictionaryFactory()  # belongs to no group the user is in
        other_concept = ConceptFactory()
        other_concept.dictionaries.add(other_dictionary)
        ConceptCommentFactory(concept=other_concept)

        response = client.get("/unread-comments/")
        data = response.json()

        assert data["totalcomments"] == 1
        assert data["unreadcomments"] == 1

    def test_comments_marked_beslutad_are_not_counted_as_unread(self, client, group):
        """A comment whose status has been changed to 'Beslutad' still counts toward the total, but not toward unread."""
        user = User.objects.create_user(username="staff2", password="password123")
        user.groups.add(group)
        client.force_login(user)

        dictionary = DictionaryFactory()
        dictionary.groups.add(group)
        concept = ConceptFactory()
        concept.dictionaries.add(dictionary)
        ConceptCommentFactory(concept=concept, status="Beslutad")

        response = client.get("/unread-comments/")
        data = response.json()

        assert data["totalcomments"] == 1
        assert data["unreadcomments"] == 0

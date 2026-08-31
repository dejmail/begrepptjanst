"""A staff member bulk-deleting selected concepts from the admin changelist.

Note: `admin_actions.change_dictionaries` exists but is never registered as
an admin action anywhere (`ConceptAdmin.actions` only lists
`export_chosen_concepts_action` and `delete_concepts`) — it's unreachable
dead code, so it isn't tested here.
"""

import pytest
from django.contrib import admin as django_admin
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware

from term_list.models import Concept
from term_list.tests.factories import ConceptFactory, DictionaryFactory

pytestmark = pytest.mark.django_db


def admin_delete_request(rf, user, queryset):
    request = rf.post("/admin/term_list/concept/", {"post": "yes"})
    request.user = user
    SessionMiddleware(lambda r: None).process_request(request)
    request._messages = FallbackStorage(request)
    concept_admin = django_admin.site._registry[Concept]
    concept_admin.delete_concepts(request, queryset)
    return request


class TestBulkDeleteAsSuperuser:
    def test_superuser_can_delete_any_selected_concept(self, rf, dictionary):
        """A superuser bulk-deleting selected concepts deletes all of them, regardless of dictionary."""
        superuser = User.objects.create_superuser(
            username="root", email="root@example.com", password="password123"
        )
        concept = ConceptFactory()
        concept.dictionaries.add(dictionary)
        queryset = Concept.objects.filter(pk=concept.pk)

        admin_delete_request(rf, superuser, queryset)

        assert not Concept.objects.filter(pk=concept.pk).exists()


class TestBulkDeleteAsScopedStaff:
    def test_staff_can_only_delete_concepts_in_their_own_groups_dictionaries(
        self, rf, group
    ):
        """A non-superuser bulk-deleting concepts only has the ones in their group's dictionaries actually deleted."""
        staff = User.objects.create_user(
            username="staff", password="password123", is_staff=True
        )
        staff.groups.add(group)

        own_dictionary = DictionaryFactory()
        own_dictionary.groups.add(group)
        own_concept = ConceptFactory()
        own_concept.dictionaries.add(own_dictionary)

        foreign_dictionary = DictionaryFactory()  # no group access for `staff`
        foreign_concept = ConceptFactory()
        foreign_concept.dictionaries.add(foreign_dictionary)

        queryset = Concept.objects.filter(pk__in=[own_concept.pk, foreign_concept.pk])

        admin_delete_request(rf, staff, queryset)

        assert not Concept.objects.filter(pk=own_concept.pk).exists()
        assert Concept.objects.filter(pk=foreign_concept.pk).exists()

    def test_staff_with_no_access_to_any_selected_concept_deletes_nothing(
        self, rf, group
    ):
        """If none of the selected concepts are in the staff member's accessible dictionaries, nothing is deleted."""
        staff = User.objects.create_user(
            username="staff2", password="password123", is_staff=True
        )
        staff.groups.add(group)

        foreign_dictionary = DictionaryFactory()
        foreign_concept = ConceptFactory()
        foreign_concept.dictionaries.add(foreign_dictionary)

        queryset = Concept.objects.filter(pk=foreign_concept.pk)

        admin_delete_request(rf, staff, queryset)

        assert Concept.objects.filter(pk=foreign_concept.pk).exists()

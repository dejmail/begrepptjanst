"""A staff member confirming an Excel import of concepts in the admin.

Only the final "confirm" step is exercised here — it takes the already
column-mapped data as JSON and doesn't need a real uploaded file, so it's
reachable directly without driving the earlier upload/column-mapping steps
of the wizard.
"""

import json

import pytest
from django.urls import reverse

from term_list.models import Concept

pytestmark = pytest.mark.django_db


def confirm_import(client, concept_data_list):
    return client.post(
        reverse("admin:import_excel_view"),
        {
            "confirm_import": "1",
            "concept_data_list": json.dumps(concept_data_list),
        },
    )


class TestImportWithNoDictionaryChosen:
    def test_a_row_with_no_dictionary_creates_a_concept_without_one(
        self, admin_user_authenticated_client
    ):
        """A row with no dictionary mapped creates the Concept anyway, without a dictionary attached, instead of crashing."""
        confirm_import(
            admin_user_authenticated_client,
            [{"term": "Importerad utan ordbok", "definition": "En definition"}],
        )
        new_concept = Concept.objects.get(term="Importerad utan ordbok")
        assert new_concept.dictionaries.count() == 0

    def test_a_row_with_a_valid_dictionary_attaches_it(
        self, admin_user_authenticated_client, dictionary
    ):
        """A row whose dictionary column matches a real Dictionary's long name attaches the new concept to it."""
        confirm_import(
            admin_user_authenticated_client,
            [
                {
                    "term": "Importerad med ordbok",
                    "definition": "En definition",
                    "Ordböcker": dictionary.dictionary_long_name,
                }
            ],
        )
        new_concept = Concept.objects.get(term="Importerad med ordbok")
        assert dictionary in new_concept.dictionaries.all()

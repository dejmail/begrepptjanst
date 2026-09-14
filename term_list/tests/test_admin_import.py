"""A staff member confirming an Excel import of concepts in the admin.

Only the final "confirm" step is exercised here — it takes the already
column-mapped data as JSON and doesn't need a real uploaded file, so it's
reachable directly without driving the earlier upload/column-mapping steps
of the wizard.
"""

import base64
import io
import json

import openpyxl
import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
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


def build_excel_base64(headers, rows):
    """Build an in-memory .xlsx (as base64 text) the way the hidden 'excel_file'
    field carries the upload between the wizard's steps."""
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(headers)
    for row in rows:
        sheet.append([row.get(header) for header in headers])
    buffer = io.BytesIO()
    workbook.save(buffer)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def apply_mapping(client, *, excel_file_b64, column_mapping, dictionary_field, dictionary_value):
    return client.post(
        reverse("admin:import_excel_view"),
        {
            "apply_mapping": "1",
            "column_mapping_json": json.dumps(column_mapping),
            "excel_file": excel_file_b64,
            dictionary_field: dictionary_value,
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


class TestApplyMappingDictionaryResolution:
    """The column-mapping step ('apply_mapping') must resolve the dictionary
    the user chose, however it was chosen, before showing the confirm preview.
    """

    def _build_sheet(self):
        return build_excel_base64(
            headers=["Term", "Definition"],
            rows=[{"Term": "Mappat begrepp", "Definition": "En definition"}],
        )

    def test_manually_selected_dictionary_resolves_without_error(
        self, admin_user_authenticated_client, dictionary
    ):
        """The dropdown posts the dictionary's id, not its name — the lookup
        must match on id, or every manual selection raises DoesNotExist."""
        response = apply_mapping(
            admin_user_authenticated_client,
            excel_file_b64=self._build_sheet(),
            column_mapping={"Term": "term", "Definition": "definition"},
            dictionary_field="dictionary",
            dictionary_value=str(dictionary.dictionary_id),
        )
        assert response.status_code == 200
        assert (
            response.context["concept_data_list"][0]["Ordböcker"]
            == dictionary.dictionary_long_name
        )

    def test_dictionary_detected_in_file_resolves_by_long_name(
        self, admin_user_authenticated_client, dictionary
    ):
        """The hidden 'dictionary-in-file' field carries the dictionary's long
        name (set from the earlier upload step), so it must be looked up by
        long name rather than by its short name."""
        response = apply_mapping(
            admin_user_authenticated_client,
            excel_file_b64=self._build_sheet(),
            column_mapping={"Term": "term", "Definition": "definition"},
            dictionary_field="dictionary-in-file",
            dictionary_value=dictionary.dictionary_long_name,
        )
        assert response.status_code == 200
        assert (
            response.context["concept_data_list"][0]["Ordböcker"]
            == dictionary.dictionary_long_name
        )

    def test_preview_headers_do_not_include_a_spurious_dictionary_column(
        self, admin_user_authenticated_client, dictionary
    ):
        """The dictionary selector must not leak into column_headers as an
        extra column with no matching row data (previously rendered as the
        literal text "None" in the preview table)."""
        response = apply_mapping(
            admin_user_authenticated_client,
            excel_file_b64=self._build_sheet(),
            column_mapping={"Term": "term", "Definition": "definition"},
            dictionary_field="dictionary",
            dictionary_value=str(dictionary.dictionary_id),
        )
        header_keys = {header["key"] for header in response.context["column_headers"]}
        assert header_keys == {"term", "definition"}


class TestConfirmImportUpdatesExistingConcepts:
    """When a term already exists, only the fields that actually differ are
    updated; a blank cell or an unchanged value leaves the existing data as-is.
    """

    def test_blank_cell_in_mapped_column_keeps_existing_value(
        self, admin_user_authenticated_client, concept, dictionary
    ):
        concept.definition = "Ursprunglig definition"
        concept.save()

        confirm_import(
            admin_user_authenticated_client,
            [
                {
                    "term": concept.term,
                    "definition": None,
                    "Ordböcker": dictionary.dictionary_long_name,
                }
            ],
        )

        concept.refresh_from_db()
        assert concept.definition == "Ursprunglig definition"

    def test_differing_value_in_mapped_column_updates_it(
        self, admin_user_authenticated_client, concept, dictionary
    ):
        concept.definition = "Ursprunglig definition"
        concept.save()

        confirm_import(
            admin_user_authenticated_client,
            [
                {
                    "term": concept.term,
                    "definition": "Ny definition",
                    "Ordböcker": dictionary.dictionary_long_name,
                }
            ],
        )

        concept.refresh_from_db()
        assert concept.definition == "Ny definition"

    def test_same_value_in_mapped_column_leaves_it_unchanged(
        self, admin_user_authenticated_client, concept, dictionary
    ):
        concept.definition = "Oförändrad definition"
        concept.save()

        confirm_import(
            admin_user_authenticated_client,
            [
                {
                    "term": concept.term,
                    "definition": "Oförändrad definition",
                    "Ordböcker": dictionary.dictionary_long_name,
                }
            ],
        )

        concept.refresh_from_db()
        assert concept.definition == "Oförändrad definition"


def _join_table_inserts(queries):
    """How many INSERTs were attempted against the concept<->dictionary
    through table, out of a CaptureQueriesContext's captured query log."""
    return sum(
        1
        for q in queries
        if q["sql"].lstrip().upper().startswith("INSERT")
        and "term_list_concept_dictionaries" in q["sql"]
    )


class TestConfirmImportDictionaryLinking:
    """Linking a concept to its dictionary must not attempt a redundant insert
    for a pair that's already linked. On MySQL locally, that redundant insert
    is what raised a DatabaseError (see mysql.connector.django's DEBUG-only
    raise_on_warnings) — but the test DB is SQLite, which just no-ops it
    silently, so "the request doesn't crash" can't tell the fix apart from the
    bug here. What can: whether the insert is attempted at all, since the fix
    checks for an existing link before ever calling `.add()`."""

    def test_reimporting_a_term_already_in_its_dictionary_attempts_no_insert(
        self, admin_user_authenticated_client, concept, dictionary
    ):
        with CaptureQueriesContext(connection) as queries:
            response = confirm_import(
                admin_user_authenticated_client,
                [
                    {
                        "term": concept.term,
                        "definition": concept.definition,
                        "Ordböcker": dictionary.dictionary_long_name,
                    }
                ],
            )
        assert response.status_code == 302
        assert concept.dictionaries.count() == 1
        assert _join_table_inserts(queries.captured_queries) == 0

    def test_duplicate_rows_for_same_term_and_dictionary_insert_the_link_once(
        self, admin_user_authenticated_client, dictionary
    ):
        """Two rows for the same new term/dictionary pair in a single import:
        the first creates and links the concept (one insert), the second must
        find it already linked and skip the redundant add instead of trying
        to insert it again."""
        row = {
            "term": "Dubblettbegrepp",
            "definition": "En definition",
            "Ordböcker": dictionary.dictionary_long_name,
        }
        with CaptureQueriesContext(connection) as queries:
            response = confirm_import(admin_user_authenticated_client, [row, row])
        assert response.status_code == 302
        new_concept = Concept.objects.get(term="Dubblettbegrepp")
        assert new_concept.dictionaries.count() == 1
        assert _join_table_inserts(queries.captured_queries) == 1

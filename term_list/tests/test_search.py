"""A visitor searching for a term on the front page.

`main_search_view` only returns real results on an AJAX request (it checks
a custom `X-Custom-Requested-With` header) — a plain GET renders an empty
results page. Tests that exercise search results go through the AJAX path.
"""

import pytest

from term_list.models import SearchTrack
from term_list.tests.factories import (
    AttributeFactory,
    AttributeValueFactory,
    ConceptFactory,
    DictionaryFactory,
    SynonymFactory,
)
from term_list.views import search_concepts_with_attributes

pytestmark = pytest.mark.django_db

AJAX_HEADERS = {"X-Custom-Requested-With": "XMLHttpRequest"}


def search(client, q, dictionary=None):
    params = {"q": q}
    if dictionary:
        params["dictionary"] = dictionary
    response = client.get("/", params, headers=AJAX_HEADERS)
    return response.json()


class TestSearchMatching:
    def test_finds_concept_by_term(self, client, dictionary):
        """Searching for a concept's term text finds that concept."""
        concept = ConceptFactory(term="Diagnos")
        concept.dictionaries.add(dictionary)
        html = search(client, "Diagnos")
        assert "Diagnos" in html

    def test_finds_concept_by_definition(self, client, dictionary):
        """Searching for text that only appears in the definition still finds the concept."""
        concept = ConceptFactory(term="Xyz", definition="Ovanlig sjukdomsbild")
        concept.dictionaries.add(dictionary)
        html = search(client, "Ovanlig sjukdomsbild")
        assert "Xyz" in html

    def test_finds_concept_by_synonym(self, client, dictionary):
        """Searching for a synonym's text finds the concept it belongs to."""
        concept = ConceptFactory(term="Huvudterm")
        concept.dictionaries.add(dictionary)
        SynonymFactory(concept=concept, synonym="Smeknamn")
        html = search(client, "Smeknamn")
        assert "Huvudterm" in html

    @pytest.mark.xfail(
        reason=(
            "BUG (term_list/views.py::search_concepts_with_attributes): "
            "`matched_concepts` correctly includes concepts found only via an "
            "AttributeValue match, but the function then reassigns `queryset` "
            "from the original term/definition/synonym-only queryset instead "
            "of from `matched_concepts`, so attribute-only matches never make "
            "it into the returned results. TODO: fix the bug, then remove this "
            "xfail marker."
        ),
        strict=True,
    )
    def test_finds_concept_by_custom_attribute_value(self, client, dictionary):
        """Searching for text stored in a custom Attribute's value finds the concept."""
        concept = ConceptFactory(term="Attributterm")
        concept.dictionaries.add(dictionary)
        attribute = AttributeFactory(data_type="string")
        AttributeValueFactory(
            term=concept, attribute=attribute, value_string="ovanlig sökbar text"
        )
        html = search(client, "ovanlig sökbar text")
        assert "Attributterm" in html

    def test_excluded_status_never_appears_in_results(self, dictionary):
        """A concept whose status is configured as excluded is never returned, even on an exact term match.

        Asserts against `search_concepts_with_attributes()` directly rather
        than the rendered "no results" HTML: that template echoes the search
        term back into a `no_search_result(...)` script call, so a plain
        "term not in html" check would pass even when zero-results was a
        coincidence, not proof the exclusion actually filtered anything.
        """
        concept = ConceptFactory(term="Dold", status="Avställd")
        concept.dictionaries.add(dictionary)
        results = search_concepts_with_attributes("Dold")
        assert all(r["id"] != concept.id for r in results)

    def test_search_by_single_uppercase_letter_filters_by_first_letter(
        self, client, dictionary
    ):
        """A single uppercase letter search matches concepts whose term starts with that letter."""
        matching = ConceptFactory(term="Ärende")
        matching.dictionaries.add(dictionary)
        non_matching = ConceptFactory(term="Övrigt")
        non_matching.dictionaries.add(dictionary)
        html = search(client, "Ä")
        assert "Ärende" in html
        assert "Övrigt" not in html


class TestSearchDictionaryFiltering:
    def test_filtering_by_dictionary_excludes_concepts_in_other_dictionaries(
        self, client, dictionary
    ):
        """Filtering search to one dictionary hides concepts that only belong to a different dictionary."""
        other_dictionary = DictionaryFactory()
        in_chosen = ConceptFactory(term="Inom")
        in_chosen.dictionaries.add(dictionary)
        in_other = ConceptFactory(term="Utanför")
        in_other.dictionaries.add(other_dictionary)

        html = search(client, "n", dictionary=dictionary.dictionary_name)

        assert "Inom" in html
        assert "Utanför" not in html

    def test_no_dictionary_filter_searches_across_all_dictionaries(
        self, client, dictionary
    ):
        """Searching without a dictionary filter ("show all") returns matches from every dictionary."""
        other_dictionary = DictionaryFactory()
        first = ConceptFactory(term="Alfa")
        first.dictionaries.add(dictionary)
        second = ConceptFactory(term="Alfabet")
        second.dictionaries.add(other_dictionary)

        html = search(client, "Alfa")

        assert "Alfa" in html
        assert "Alfabet" in html


class TestSearchTracking:
    def test_search_records_a_search_track_entry(self, client, dictionary):
        """Performing a search creates a SearchTrack row recording what was searched for."""
        concept = ConceptFactory(term="Spårat")
        concept.dictionaries.add(dictionary)
        search(client, "Spårat")
        assert SearchTrack.objects.filter(sök_term="Spårat").exists()

    def test_search_track_prefers_x_forwarded_for_header(self, client, dictionary):
        """The IP recorded for a search comes from X-Forwarded-For when present, not REMOTE_ADDR."""
        concept = ConceptFactory(term="Ip")
        concept.dictionaries.add(dictionary)
        client.get(
            "/",
            {"q": "Ip"},
            headers={**AJAX_HEADERS, "X-Forwarded-For": "203.0.113.9, 10.0.0.1"},
        )
        track = SearchTrack.objects.get(sök_term="Ip")
        assert track.ip_adress == "203.0.113.9"

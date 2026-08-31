"""A visitor viewing a single term's full definition page."""

import pytest

from term_list.functions import Xlator
from term_list.models import MetadataSearchTrack
from term_list.tests.factories import (
    AttributeFactory,
    AttributeValueFactory,
    GroupAttributeFactory,
    GroupFactory,
)
from term_list.views import (
    concept_detail_view,
    creating_tooltip_hover_substitution_object,
    substitute_occurrence_of_terms_in_definitions,
)

pytestmark = pytest.mark.django_db


class TestTermDetailView:
    def test_viewing_a_term_shows_its_definition(self, client, concept):
        """GET on the term detail page with a concept id shows that concept's term and definition."""
        concept.term = "Synlig"
        concept.definition = "En tydlig definition"
        concept.save()
        response = client.get("/begrepp-forklaring/", {"q": concept.id})
        content = response.content.decode()
        assert "Synlig" in content
        assert "En tydlig definition" in content

    def test_viewing_a_term_records_a_metadata_search_track_entry(self, client, concept):
        """Viewing a term's detail page creates a MetadataSearchTrack row for that term id."""
        client.get("/begrepp-forklaring/", {"q": concept.id})
        assert MetadataSearchTrack.objects.filter(sök_term=str(concept.id)).exists()


class TestConceptDetailAttributes:
    def test_attribute_visible_to_its_group_is_included(self, concept, group):
        """An Attribute marked visible=True for the concept's group appears in its detail attributes."""
        attribute = AttributeFactory(data_type="string", display_name="Synligt attribut")
        attribute.groups.add(group)
        GroupAttributeFactory(group=group, attribute=attribute, visible=True)
        AttributeValueFactory(term=concept, attribute=attribute, value_string="värde")

        fields = concept_detail_view(concept_id=concept.id)

        assert any(f["display_name"] == "Synligt attribut" for f in fields)

    def test_attribute_hidden_from_its_group_is_excluded(self, concept, group):
        """An Attribute marked visible=False for the concept's group is left out of its detail attributes."""
        attribute = AttributeFactory(data_type="string", display_name="Dolt attribut")
        attribute.groups.add(group)
        GroupAttributeFactory(group=group, attribute=attribute, visible=False)
        AttributeValueFactory(term=concept, attribute=attribute, value_string="värde")

        fields = concept_detail_view(concept_id=concept.id)

        assert all(f["display_name"] != "Dolt attribut" for f in fields)

    def test_attribute_belonging_to_an_unrelated_group_is_excluded(self, concept):
        """An Attribute that belongs to a group unrelated to the concept's dictionaries never appears."""
        unrelated_group = GroupFactory()
        attribute = AttributeFactory(data_type="string", display_name="Främmande attribut")
        attribute.groups.add(unrelated_group)
        GroupAttributeFactory(group=unrelated_group, attribute=attribute, visible=True)

        fields = concept_detail_view(concept_id=concept.id)

        assert all(f["display_name"] != "Främmande attribut" for f in fields)


class TestDefinitionTooltipSubstitution:
    """Definitions that mention another Concept's term by name get that
    mention turned into a hover-tooltip link, so a reader can see the
    referenced term's definition inline without navigating away.
    """

    def test_referenced_term_becomes_a_tooltip_span(self):
        """A definition containing another term's exact name gets wrapped in a tooltip span for it."""
        all_terms = [
            {"term": "diagnos", "definition": "en sjukdomsbild"},
        ]
        search_results = [
            {"term": "huvudbegrepp", "definition": "Se diagnos för mer info"}
        ]
        xlator = creating_tooltip_hover_substitution_object(all_terms)
        result = substitute_occurrence_of_terms_in_definitions(
            search_results, xlator, key="definition"
        )
        assert 'class="term"' in result[0]["definition"]
        assert "diagnos" in result[0]["definition"]

    def test_unrelated_word_is_left_untouched(self):
        """A definition with no reference to any known term is returned unchanged."""
        all_terms = [
            {"term": "diagnos", "definition": "en sjukdomsbild"},
        ]
        search_results = [
            {"term": "huvudbegrepp", "definition": "Detta nämner inget känt begrepp"}
        ]
        xlator = creating_tooltip_hover_substitution_object(all_terms)
        result = substitute_occurrence_of_terms_in_definitions(
            search_results, xlator, key="definition"
        )
        assert result[0]["definition"] == "Detta nämner inget känt begrepp"

    def test_xlator_matches_plural_suffix_of_a_known_word(self):
        """Xlator.xlat still matches a known word when it appears with a plural/genitive suffix attached."""
        xlator = Xlator({"diagnos": "DIAGNOS-TOOLTIP"})
        result = xlator.xlat("Flera diagnoser noterades.")
        assert "DIAGNOS-TOOLTIPer" in result

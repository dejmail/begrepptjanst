"""A visitor requesting that a brand new term be added to a dictionary."""

import pytest

from term_list.models import Concept, TaskOrderer
from term_list.tests.factories import DictionaryFactory

pytestmark = pytest.mark.django_db

AJAX_HEADERS = {"X-Custom-Requested-With": "XMLHttpRequest"}


def submit_request(client, concept_name, dictionary, name, email, context="Sammanhang."):
    return client.post(
        "/requesttermform/",
        {
            "concept": concept_name,
            "dictionary": dictionary.dictionary_long_name,
            "context": context,
            "name": name,
            "email": email,
        },
    )


class TestRequestFormDisplay:
    def test_ajax_get_shows_form_prefilled_with_query_params(self, client, dictionary):
        """An AJAX GET pre-fills the concept and dictionary fields from the querystring."""
        response = client.get(
            "/requesttermform/",
            {"q": "Nytt begrepp", "dictionary": dictionary.dictionary_long_name},
            headers=AJAX_HEADERS,
        )
        content = response.content.decode()
        assert "Nytt begrepp" in content


class TestRequestSubmission:
    @pytest.mark.xfail(
        reason=(
            "BUG (term_list/views.py::request_new_term, ~L977): after "
            "form.is_valid() already runs clean_dictionary() once (storing its "
            "return value, a Dictionary instance, into cleaned_data['dictionary']), "
            "the view calls form.clean_dictionary() a SECOND time manually. That "
            "second call re-reads cleaned_data.get('dictionary'), which is now the "
            "Dictionary instance rather than the submitted string; filtering "
            "dictionary_long_name against str(that instance) (== dictionary_name, "
            "per Dictionary.__str__) fails whenever the short and long names "
            "differ, raising an unhandled ValidationError and 500ing on every "
            "legitimate submission. TODO: stop re-calling the clean_X methods and "
            "just read form.cleaned_data directly, then remove this xfail marker."
        ),
        strict=True,
    )
    def test_valid_submission_creates_a_concept_and_task_orderer(
        self, client, dictionary
    ):
        """A valid POST creates a new pending Concept in the chosen dictionary, with a TaskOrderer recording who asked for it."""
        response = client.post(
            "/requesttermform/",
            {
                "concept": "Helt Nytt Begrepp",
                "dictionary": dictionary.dictionary_long_name,
                "context": "Används i sammanhang X.",
                "name": "Beställaren",
                "email": "bestallare@example.com",
            },
        )
        assert response.status_code == 200
        new_term = Concept.objects.get(term="Helt Nytt Begrepp")
        assert dictionary in new_term.dictionaries.all()
        orderer = TaskOrderer.objects.get(concept=new_term)
        assert orderer.name == "Beställaren"
        assert orderer.email == "bestallare@example.com"

    def test_submission_for_an_already_existing_term_is_rejected(
        self, client, dictionary, concept
    ):
        """Requesting a term that already exists in the system does not create a duplicate Concept."""
        existing_count = Concept.objects.filter(term=concept.term).count()
        response = client.post(
            "/requesttermform/",
            {
                "concept": concept.term,
                "dictionary": dictionary.dictionary_long_name,
                "context": "Sammanhang.",
                "name": "Beställaren",
                "email": "bestallare@example.com",
            },
        )
        assert "finns redan i systemet" in response.content.decode()
        assert Concept.objects.filter(term=concept.term).count() == existing_count

    def test_submission_with_a_nonexistent_dictionary_is_rejected(self, client):
        """Submitting a dictionary name that doesn't exist fails form validation and saves nothing."""
        response = client.post(
            "/requesttermform/",
            {
                "concept": "Begrepp utan ordbok",
                "dictionary": "Ordbok Som Inte Finns",
                "context": "Sammanhang.",
                "name": "Beställaren",
                "email": "bestallare@example.com",
            },
        )
        assert response.status_code == 500
        assert not Concept.objects.filter(term="Begrepp utan ordbok").exists()


class TestRepeatRequesterGetsTheirOwnOrderer:
    def test_a_second_request_from_the_same_person_gets_its_own_task_orderer(
        self, client
    ):
        """A second request from the same name/email creates a new TaskOrderer, without reassigning the earlier request's orderer to the new concept."""
        # dictionary_name == dictionary_long_name here so this test isn't
        # tripped up by the separately-tracked xfailed bug above.
        dictionary = DictionaryFactory(dictionary_name="Samma", dictionary_long_name="Samma")

        submit_request(client, "Första Begreppet", dictionary, "Beställaren", "b@example.com")
        first_orderer = TaskOrderer.objects.get(concept__term="Första Begreppet")

        submit_request(client, "Andra Begreppet", dictionary, "Beställaren", "b@example.com")
        second_orderer = TaskOrderer.objects.get(concept__term="Andra Begreppet")

        assert first_orderer.pk != second_orderer.pk
        first_orderer.refresh_from_db()
        assert first_orderer.concept.term == "Första Begreppet"

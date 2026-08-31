"""Smoke tests: every named URL in term_list/urls.py resolves, and pages
that don't require special params/auth load without a server error.
"""

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db

NAMED_URLS_WITH_KWARGS = {
    "concept": {},
    "comment_term": {},
    "term_metadata": {},
    "request_new_term": {},
    "unread_comments": {},
    "no_search_result": {},
    "autocomplete_suggestions": {"attribute": "term", "search_term": "x"},
    "get_dictionary_details": {"dictionary": "Ordbok"},
    "get_json_terms": {},
    "get_terms": {"id": 1},
    "get_all_accepted_terms_as_json": {},
    "all_synonyms": {},
    "export_chosen_attrs": {},
    "fetch_attributes": {},
}


@pytest.mark.parametrize("url_name,kwargs", NAMED_URLS_WITH_KWARGS.items())
def test_every_named_url_resolves(url_name, kwargs):
    """Every URL name declared in term_list/urls.py can still be reversed."""
    assert reverse(url_name, kwargs=kwargs)


class TestUrlsLoadWithoutServerError:
    def test_search_page_loads(self, client):
        """The main search page loads for an anonymous visitor."""
        assert client.get(reverse("concept")).status_code == 200

    def test_no_search_result_page_loads(self, client):
        """The 'no results' page loads without needing a prior search."""
        assert client.get(reverse("no_search_result")).status_code == 200

    def test_unread_comments_redirects_anonymous_users_to_login(self, client):
        """The unread-comments endpoint redirects an anonymous visitor rather than erroring."""
        assert client.get(reverse("unread_comments")).status_code == 302

    def test_all_approved_terms_redirect_loads(self, client):
        """The base JSON terms URL responds with a redirect, not a server error."""
        response = client.get(reverse("get_json_terms"))
        assert response.status_code in (301, 302)

    def test_all_accepted_terms_json_loads(self, client):
        """The all-accepted-terms JSON endpoint loads for an anonymous visitor."""
        assert client.get(reverse("get_all_accepted_terms_as_json")).status_code == 200

    def test_all_synonyms_json_loads(self, client):
        """The all-synonyms JSON endpoint loads for an anonymous visitor."""
        assert client.get(reverse("all_synonyms")).status_code == 200

    def test_get_single_term_json_loads_for_a_real_concept(self, client, concept):
        """Fetching a single term's JSON by a real id loads successfully."""
        response = client.get(reverse("get_terms", kwargs={"id": concept.id}))
        assert response.status_code == 200

    def test_fetch_attributes_without_a_dictionary_id_responds_400_not_500(self, client):
        """Calling fetch-attributes with no dictionary_id fails gracefully, not with a server error."""
        response = client.get(reverse("fetch_attributes"))
        assert response.status_code == 400

"""A visitor submitting a comment on an existing term."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from term_list.models import ConceptComment, ConceptExternalFiles, DEFAULT_STATUS

pytestmark = pytest.mark.django_db


class TestCommentFormDisplay:
    def test_get_shows_form_prefilled_with_the_concept_id(self, client, concept):
        """GET on the comment page pre-fills the hidden term field with the concept's id."""
        response = client.get("/kommentera/", {"q": concept.id})
        content = response.content.decode()
        assert f'value="{concept.id}"' in content


class TestCommentSubmission:
    def test_valid_submission_saves_a_comment_against_the_concept(self, client, concept):
        """A valid POST saves a ConceptComment linked to the concept, with the default status."""
        response = client.post(
            "/kommentera/",
            {
                "name": "Anna",
                "epost": "anna@example.com",
                "comment": "Detta är en kommentar.",
                "term": concept.id,
            },
        )
        assert response.status_code == 200
        comment = ConceptComment.objects.get(concept=concept)
        assert comment.name == "Anna"
        assert comment.email == "anna@example.com"
        assert comment.status == DEFAULT_STATUS

    def test_valid_submission_with_a_file_attaches_it_to_the_comment(
        self, client, concept
    ):
        """A comment submitted with a file attachment creates a ConceptExternalFiles row linked to both the concept and the new comment."""
        upload = SimpleUploadedFile(
            "bevis.png", b"filinnehall", content_type="image/png"
        )
        client.post(
            "/kommentera/",
            {
                "name": "Anna",
                "epost": "anna@example.com",
                "comment": "Se bifogad fil.",
                "term": concept.id,
                "file_field": upload,
            },
        )
        comment = ConceptComment.objects.get(concept=concept)
        external_file = ConceptExternalFiles.objects.get(comment=comment)
        assert external_file.concept_id == concept.id

    def test_invalid_submission_does_not_save_a_comment(self, client, concept):
        """Submitting without a required field (e.g. name) re-renders the form and saves nothing."""
        response = client.post(
            "/kommentera/",
            {
                "name": "",
                "epost": "anna@example.com",
                "comment": "Detta är en kommentar.",
                "term": concept.id,
            },
        )
        assert response.status_code == 200
        assert not ConceptComment.objects.filter(concept=concept).exists()

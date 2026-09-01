"""A visitor submitting a comment on an existing term."""

import re

import pytest
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile

from term_list.models import ConceptComment, ConceptExternalFiles, DEFAULT_STATUS
from term_list.tests.factories import ConceptFactory

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

    def test_comment_on_one_of_two_duplicate_named_concepts_attaches_to_that_exact_one(
        self, client, dictionary
    ):
        """Commenting on a concept looks it up by id, so it still works when another concept shares the same term text."""
        first = ConceptFactory(term="Samma namn")
        first.dictionaries.add(dictionary)
        second = ConceptFactory(term="Samma namn")
        second.dictionaries.add(dictionary)

        client.post(
            "/kommentera/",
            {
                "name": "Anna",
                "epost": "anna@example.com",
                "comment": "Gäller den andra.",
                "term": second.id,
            },
        )

        assert ConceptComment.objects.filter(concept=second).exists()
        assert not ConceptComment.objects.filter(concept=first).exists()


class TestCommentFileUploadSafety:
    def test_swedish_characters_in_a_filename_are_made_safe(self, client, concept):
        """A filename with å/ä/ö is transliterated to a plain-ASCII name before being saved."""
        upload = SimpleUploadedFile(
            "bilaga med åäö.png", b"innehall", content_type="image/png"
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
        base_name = str(external_file.support_file).rsplit(".", 1)[0]
        assert re.fullmatch(r"[A-Za-z0-9_/-]+", base_name)

    def test_extension_is_preserved_and_not_mangled(self, client, concept):
        """The uploaded file's extension survives unchanged, including its case."""
        upload = SimpleUploadedFile(
            "Skärmklipp.PNG", b"innehall", content_type="image/png"
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
        assert str(external_file.support_file).endswith(".PNG")

    def test_saved_file_matches_the_name_recorded_against_the_comment(
        self, client, concept
    ):
        """The filename recorded on ConceptExternalFiles is the exact name the file was saved under."""
        upload = SimpleUploadedFile(
            "bevis för ärendet.txt", b"innehall", content_type="text/plain"
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
        assert FileSystemStorage().exists(str(external_file.support_file))

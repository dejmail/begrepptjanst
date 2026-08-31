"""Model-level data-integrity rules that aren't cleanly reachable through a
single specific view (unlike most behavior in this suite, which is tested
through the workflow that depends on it).
"""

import pytest
from django.core.exceptions import ValidationError

from term_list.tests.factories import AttributeFactory, AttributeValueFactory

pytestmark = pytest.mark.django_db


class TestAttributeValueSingleFieldRule:
    def test_clean_allows_exactly_one_populated_value_field(self):
        """clean() does not raise when exactly one value_* field is set."""
        attribute = AttributeFactory(data_type="string")
        value = AttributeValueFactory(attribute=attribute, value_string="hej")
        value.clean()

    def test_clean_rejects_more_than_one_populated_value_field(self):
        """clean() raises ValidationError when more than one value_* field is set on the same row."""
        attribute = AttributeFactory(data_type="string")
        value = AttributeValueFactory(
            attribute=attribute, value_string="hej", value_integer=1
        )
        with pytest.raises(ValidationError):
            value.clean()

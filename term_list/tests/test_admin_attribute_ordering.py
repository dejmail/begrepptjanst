"""A staff member viewing a Concept's custom attributes in the admin edit page."""

import pytest
from django.contrib import admin as django_admin
from django.test import RequestFactory

from term_list.admin import AttributeValueInline
from term_list.models import Concept
from term_list.tests.factories import (
    AttributeFactory,
    AttributeValueFactory,
    GroupAttributeFactory,
    GroupFactory,
)

pytestmark = pytest.mark.django_db


def inline_for(concept):
    inline = AttributeValueInline(Concept, django_admin.site)
    inline._parent_obj = concept
    return inline


class TestAttributeInlineRowOrder:
    def test_rows_are_ordered_by_group_attribute_position(self, concept, group):
        """AttributeValue rows in the admin inline are ordered by their GroupAttribute.position, not creation order."""
        attr_last = AttributeFactory(data_type="string")
        attr_last.groups.add(group)
        GroupAttributeFactory(group=group, attribute=attr_last, position=2)
        AttributeValueFactory(term=concept, attribute=attr_last, value_string="last")

        attr_first = AttributeFactory(data_type="string")
        attr_first.groups.add(group)
        GroupAttributeFactory(group=group, attribute=attr_first, position=1)
        AttributeValueFactory(term=concept, attribute=attr_first, value_string="first")

        inline = inline_for(concept)
        request = RequestFactory().get("/admin/")
        ordered = list(inline.get_queryset(request))

        assert [row.attribute_id for row in ordered] == [attr_first.id, attr_last.id]

    def test_attributes_with_no_configured_position_sort_last(self, concept, group):
        """An AttributeValue whose Attribute has no GroupAttribute position for this concept's groups sorts after positioned ones."""
        positioned = AttributeFactory(data_type="string")
        positioned.groups.add(group)
        GroupAttributeFactory(group=group, attribute=positioned, position=0)
        AttributeValueFactory(term=concept, attribute=positioned, value_string="x")

        unpositioned_group = GroupFactory()
        unpositioned = AttributeFactory(data_type="string")
        unpositioned.groups.add(unpositioned_group)
        AttributeValueFactory(term=concept, attribute=unpositioned, value_string="y")

        inline = inline_for(concept)
        request = RequestFactory().get("/admin/")
        ordered = list(inline.get_queryset(request))

        assert [row.attribute_id for row in ordered] == [positioned.id, unpositioned.id]


class TestAttributeInlineFieldDeduplication:
    def test_an_attribute_shared_by_two_relevant_groups_is_not_duplicated(
        self, concept, group
    ):
        """An Attribute assigned to more than one of the concept's relevant groups appears once in get_fields, not once per group."""
        second_group = GroupFactory()
        concept.dictionaries.first().groups.add(second_group)

        shared_attribute = AttributeFactory(data_type="string")
        shared_attribute.groups.add(group, second_group)
        GroupAttributeFactory(group=group, attribute=shared_attribute, position=0)
        GroupAttributeFactory(
            group=second_group, attribute=shared_attribute, position=0
        )

        inline = inline_for(concept)
        request = RequestFactory().get("/admin/")
        fields = inline.get_fields(request, obj=concept)

        assert fields.count("value_string") == 1

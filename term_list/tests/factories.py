"""factory_boy factories for term_list models, used across the test suite."""

import factory
from django.contrib.auth.models import Group

from term_list.models import (
    Attribute,
    AttributeValue,
    Concept,
    ConceptComment,
    ConceptExternalFiles,
    ConfigurationOptions,
    Dictionary,
    GroupAttribute,
    Synonym,
    TaskOrderer,
)


class GroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Group
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Grupp {n}")


class DictionaryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Dictionary

    dictionary_name = factory.Sequence(lambda n: f"Ordbok {n}")
    dictionary_long_name = factory.Sequence(lambda n: f"Ordbok långt namn {n}")
    order = factory.Sequence(lambda n: n)


class ConceptFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Concept

    term = factory.Sequence(lambda n: f"Begrepp {n}")
    definition = "En testdefinition."
    status = "Beslutad"


class AttributeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Attribute

    name = factory.Sequence(lambda n: f"attribut_{n}")
    display_name = factory.Sequence(lambda n: f"Attribut {n}")
    data_type = "string"


class GroupAttributeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GroupAttribute

    position = 0
    visible = True


class AttributeValueFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AttributeValue

    term = factory.SubFactory(ConceptFactory)
    attribute = factory.SubFactory(AttributeFactory)


class SynonymFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Synonym

    concept = factory.SubFactory(ConceptFactory)
    synonym = factory.Sequence(lambda n: f"Synonym {n}")
    synonym_status = "Tillåten"


class ConceptCommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ConceptComment

    concept = factory.SubFactory(ConceptFactory)
    usage_context = "Testkontext"
    email = "kommentator@example.com"
    name = "Kommentator"


class ConceptExternalFilesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ConceptExternalFiles

    concept = factory.SubFactory(ConceptFactory)


class TaskOrdererFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TaskOrderer

    name = "Beställare Testsson"
    email = "bestallare@example.com"
    concept = factory.SubFactory(ConceptFactory)


class ConfigurationOptionsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ConfigurationOptions

    name = "status-and-colour"
    description = "Test config"
    visible = True
    config = factory.LazyFunction(
        lambda: {
            "statuses": [
                {"label": "Beslutad"},
                {"label": "Pågår"},
                {"label": "Avråds"},
                {"label": "Publicera ej"},
                {"label": "Avställd"},
                {"label": "Ej Påbörjad"},
            ]
        }
    )

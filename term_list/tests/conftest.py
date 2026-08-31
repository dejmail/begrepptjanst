import pytest
from django.contrib.auth.models import User

from term_list.tests.factories import (
    ConceptFactory,
    ConfigurationOptionsFactory,
    DictionaryFactory,
    GroupFactory,
)


@pytest.fixture(autouse=True)
def status_config(db):
    """`term_list.context_processors.global_status_config` does an
    unguarded `ConfigurationOptions.objects.get(name="status-and-colour")`
    on every template render, and `ConceptForm`/search views rely on
    `get_status_choices` / `get_excluded_statuses`. Seed both rows for every
    test so that behavior doesn't have to be repeated per-test.
    """
    status_and_colour = ConfigurationOptionsFactory()
    status_exclude = ConfigurationOptionsFactory(
        name="status-exclude",
        config={
            "statuses": [
                {"label": "Avställd", "exclude": True},
                {"label": "Publicera ej", "exclude": True},
            ]
        },
    )
    return {"status-and-colour": status_and_colour, "status-exclude": status_exclude}


@pytest.fixture
def group(db):
    return GroupFactory()


@pytest.fixture
def dictionary(db, group):
    dictionary = DictionaryFactory()
    dictionary.groups.add(group)
    return dictionary


@pytest.fixture
def concept(db, dictionary):
    concept = ConceptFactory()
    concept.dictionaries.add(dictionary)
    return concept


@pytest.fixture
def admin_user_authenticated_client(db, client):
    user = User.objects.create_superuser(
        username="admin", email="admin@example.com", password="password123"
    )
    client.force_login(user)
    return client

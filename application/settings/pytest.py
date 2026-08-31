"""Settings used exclusively for running the automated test suite (pytest).

Uses an in-memory SQLite database instead of MySQL so tests run fast and
without any external dependency (e.g. the docker-compose MySQL container).
"""

import tempfile

from application.settings.base import *  # noqa: F401,F403
from application.settings.base import INSTALLED_APPS, MIDDLEWARE  # noqa: F401

DEBUG = False

SECRET_KEY = "pytest-test-suite-secret-key-not-for-production"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

MEDIA_URL = "/media/"
MEDIA_ROOT = str(pathlib.Path(tempfile.gettempdir()) / "olli-begreppstjanst-test-media")

STATICFILES_DIRS = [
    "static",
]
STATIC_URL = "/static/"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

import locale
import os
import pathlib
import signal

from application.settings.base import *  # noqa: F401,F403

# Ignore SIGPIPE to prevent BrokenPipeError during logging in Passenger
# This is a known issue with Passenger and logging during startup
if hasattr(signal, 'SIGPIPE'):
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

# sys.stdout.reconfigure(encoding='utf-8')  # Ensure stdout is UTF-8
locale.setlocale(locale.LC_ALL, "sv_SE.UTF-8")  # Set Swedish locale

DEBUG=False

SUBDOMAIN = 'begreppstjanst'

DB_NAME = os.getenv('DB_NAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_USER = os.getenv('DB_USER')

DATABASES = {
    'default': {
        'ENGINE': 'mysql.connector.django',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': 'localhost',   # Or an IP Address that your DB is hosted on
        'PORT': '3306',
        'OPTIONS': {
            'sql_mode' : 'traditional',
            'charset': 'utf8mb4',
            'init_command': "SET NAMES 'utf8mb4' COLLATE 'utf8mb4_swedish_ci'"

        },
         'TEST': {
            'NAME': 'vgrinfor_concept_test',
        },
    }
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/
STATIC_ROOT = '/home/vgrinfor/public_html/begreppstjanst/static'
STATICFILES_DIRS = ['/home/vgrinfor/begreppstjanst/static',]
STATIC_URL = '/begreppstjanst/static/'

# media files
MEDIA_URL = '/begreppstjanst/media/'
MEDIA_ROOT = '/home/vgrinfor/public_html/begreppstjanst/media'


# Email settings
MEDIA_URL = '/begreppstjanst/media/'
MEDIA_ROOT = '/home/vgrinfor/public_html/begreppstjanst/media'

BASE_DIR = pathlib.Path(__file__).resolve().parents[2]
LOG_FILE = os.getenv("LOG_FILE", str(BASE_DIR / "logs.log"))

# Ensure directory exists BEFORE logging config runs
pathlib.Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "simple": {
            "format": "%(asctime)s %(levelname)s %(message)s",
        },
    },

    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_FILE,
            "formatter": "simple",
            "level": "INFO",
            "maxBytes": 500000,
            "backupCount": 3,
        }
    },

    "root": {
        "handlers": ["file"],
        "level": "INFO",
    },

    "loggers": {
        "django.server": {
            "handlers": [],
            "level": "CRITICAL",
            "propagate": False,
        },
        "django.request": {
            "handlers": [],
            "level": "CRITICAL",
            "propagate": False,
        },
    },
}

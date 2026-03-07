import logging
import os

from application.settings.base import *  # noqa: F401,F403
from application.settings.base import INSTALLED_APPS, MIDDLEWARE

logger = logging.getLogger(__name__)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

INTERNAL_IPS = ['127.0.0.1',]

DATABASES = {
    'default': {
        'ENGINE': 'mysql.connector.django',
        'NAME': 'vgrinfor_olli_eav_prod',
        'USER': 'vgrinfor_admin',
        'PASSWORD': 'YqvyYGm5cJMLmzt',
        'HOST': '127.0.0.1',   # Or an IP Address that your DB is hosted on
        'PORT': '3306',

        'OPTIONS': {
            # Tell MySQLdb to connect with 'utf8mb4' character set
            'sql_mode' : 'traditional',
        },
         'TEST': {
            'NAME': 'vgrinfor_begrepp_test',
        },
    },
    'target' : {
        'ENGINE': 'mysql.connector.django',
        'NAME': 'vgrinfor_begrepp_prod',
        'USER': 'vgrinfor_admin',
        'PASSWORD': 'YqvyYGm5cJMLmzt',
        'HOST': 'localhost',   # Or an IP Address that your DB is hosted on
        'PORT': '3306',
        'OPTIONS': {
            'sql_mode' : 'traditional',
        },
         'TEST': {
            'NAME': 'vgrinfor_begrepp_test',
        },
    }
}

GRAPH_MODELS = {
  'all_applications': True,
  'group_models': True,
}

SECRET_KEY = "j4kf!tlx#w%=0+t(u38(1jqno8x)b$-^gb@$@%5s2q$wki*mx^"
INSTALLED_APPS.append('debug_toolbar')

MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')

DJANGO_DEBUG=True
DEBUG_TOOLBAR_PANELS = ['debug_toolbar.panels.headers.HeadersPanel',
                        'debug_toolbar.panels.request.RequestPanel',
                        'debug_toolbar.panels.templates.TemplatesPanel']

PROJECT_PATH = os.path.realpath(os.path.dirname(__file__))
logger.info(f'PROJECT_PATH --> {PROJECT_PATH}')

MEDIA_URL = '/application/media/'
MEDIA_ROOT = 'media'


STATICFILES_DIRS = [
    "static",
]

STATIC_URL = '/static/'

# Email settings
# Use this backend if you want the system to print out emails to the console
#EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

EMAIL_HOST = 'mail.vgrinformatik.se'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'info@vgrinformatik.se'
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = True

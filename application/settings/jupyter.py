import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from application.settings.base import MIDDLEWARE

logger = logging.getLogger(__name__)

#load the config parameters
dotenv_path = Path('./docker/env.dev')
load_dotenv(dotenv_path=dotenv_path)


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(os.environ.get("DEBUG", default=0))
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS").split(" ")
SECRET_KEY = os.environ.get("SECRET_KEY")

# If the website sits at a URL other than /, such as 127.0.0.1/subdomain/
SUBDOMAIN=''

INTERNAL_IPS = ['127.0.0.1',]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'vgrinfor_olli_test',
        'USER': 'vgrinfor_admin',
        'PASSWORD': 'YqvyYGm5cJMLmzt',
        'HOST': 'suijin.oderland.com',   # Or an IP Address that your DB is hosted on
        'PORT': '3306',

        'OPTIONS': {
            # Tell MySQLdb to connect with 'utf8mb4' character set
            'sql_mode' : 'traditional',
        },
         'TEST': {
            'NAME': 'vgrinfor_begrepp_test',
        },
    },
    'old' : {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'vgrinfor_begrepp_prod',
        'USER': 'vgrinfor_admin',
        'PASSWORD': 'YqvyYGm5cJMLmzt',
        'HOST': 'suijin.oderland.com',   # Or an IP Address that your DB is hosted on
        'PORT': '3306',

        'OPTIONS': {
            # Tell MySQLdb to connect with 'utf8mb4' character set
            'sql_mode' : 'traditional',
        },
         'TEST': {
            'NAME': 'vgrinfor_begrepp_test',
        },
    }
}


# DATABASES = {
#     "default": {
#         "ENGINE": os.environ.get("SQL_ENGINE"),
#         "NAME": os.environ.get("SQL_DATABASE"),
#         "USER": os.environ.get("SQL_USER"),
#         "PASSWORD": os.environ.get("SQL_PASSWORD"),
#         "HOST": os.environ.get("SQL_HOST"),
#         "PORT": os.environ.get("SQL_PORT"),
#         'OPTIONS': {
#             'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
#         },
#     }
# }

MIDDLEWARE.append("django_cprofile_middleware.middleware.ProfilerMiddleware")

PROJECT_PATH = os.path.realpath(os.path.dirname(__file__))
logger.info(f'PROJECT_PATH --> {PROJECT_PATH}')
TEMPLATE_DIRS = ['/templates/','/templates/term_list/']

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

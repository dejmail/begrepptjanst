from begrepptjanst.settings.base import *
from django.conf import settings
from django.urls import include, path
import os 
import ordbok
import logging

logger = logging.getLogger(__name__)

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME' : 'ordlist_databas.sqlite3'

    }
}

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

INTERNAL_IPS = ['127.0.0.1',]

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql', 
#         'NAME': 'vgrinfor_begrepp',
#         'USER': 'vgrinfor_admin',
#         'PASSWORD': 'YqvyYGm5cJMLmzt',
#         'HOST': 'vgrinformatik.se',   # Or an IP Address that your DB is hosted on
#         'PORT': '3306',
#         'DEFAULT-CHARACTER-SET' : 'utf8',
        
#     }
# }

#INSTALLED_APPS.append('debug_toolbar')

#MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')

PROJECT_PATH = os.path.realpath(os.path.dirname(__file__))
logger.info(f'PROJECT_PATH --> {PROJECT_PATH}')
TEMPLATE_DIRS = ['/templates/',]

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
from begrepptjanst.settings.base import *
from django.urls import include, path  # For django versions from 2.0 and up
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

SUBDOMAIN = 'begreppstjanst-dev'
DEBUG=True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', 
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': 'localhost',   # Or an IP Address that your DB is hosted on
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

INSTALLED_APPS.append('debug_toolbar')

MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/
STATIC_ROOT = '/home/vgrinfor/public_html/begreppstjanst-dev/static'
STATICFILES_DIRS = ['/home/vgrinfor/begreppstjanst-dev/static',]
STATIC_URL = '/begreppstjanst-dev/static/'

# media files 
MEDIA_URL = '/begreppstjanst/media/'
MEDIA_ROOT = '/home/vgrinfor/public_html/begreppstjanst/media'
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = 587
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = True


import logging
import os

from application.settings.base import INSTALLED_APPS, MIDDLEWARE

logger = logging.getLogger(__name__)

SUBDOMAIN = 'begreppstjanst-eav'
DEBUG=True

DB_NAME = os.getenv('DB_NAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_USER = os.getenv('DB_USER')

logger.debug(f'DB login credentials - {DB_NAME}, {DB_USER}, {DB_PASSWORD}')

DATABASES = {
    'default': {
        'ENGINE': 'mysql.connector.django',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
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
STATIC_ROOT = '/home/vgrinfor/public_html/begreppstjanst-eav/static'
STATICFILES_DIRS = ['/home/vgrinfor/begreppstjanst-eav/static',]
STATIC_URL = '/begreppstjanst-eav/static/'

# media files
MEDIA_URL = '/begreppstjanst/media/'
MEDIA_ROOT = '/home/vgrinfor/public_html/begreppstjanst-eav/media'

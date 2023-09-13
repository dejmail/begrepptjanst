from begrepptjanst.settings.base import *
from django.conf import settings
from django.urls import include, path
import os 
import ordbok
import logging

logger = logging.getLogger(__name__)

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

SUBDOMAIN=''

INTERNAL_IPS = ['127.0.0.1',]

SECRET_KEY = "j4kf!tlx#w%=0+t(u38(1jqno8x)b$-^gb@$@%5s2q$wki*mx^"

SUBDOMAIN = ''

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', 
        'NAME': 'vgrinfor_olli',
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
    }
}

MIDDLEWARE.append("django_cprofile_middleware.middleware.ProfilerMiddleware")

PROJECT_PATH = os.path.realpath(os.path.dirname(__file__))
logger.info(f'PROJECT_PATH --> {PROJECT_PATH}')
TEMPLATE_DIRS = ['/templates/','/templates/ordbok/']

MEDIA_URL = '/begrepptjanst/media/'
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
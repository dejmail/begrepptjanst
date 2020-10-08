from begrepptjanst.settings.base import *
from django.urls import include, path  # For django versions from 2.0 and up
from django.conf import settings


DEBUG=True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', 
        'NAME': 'vgrinfor_begrepp_prod',
        'USER': 'vgrinfor_admin',
        'PASSWORD': 'YqvyYGm5cJMLmzt',
        'HOST': 'localhost',   # Or an IP Address that your DB is hosted on
        'PORT': '3306',
        'DEFAULT-CHARACTER-SET' : 'utf8',
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
MEDIA_URL = '/begrepptjanst/media/'
MEDIA_ROOT = '/home/vgrinfor/public_html/begrepptjanst/media'
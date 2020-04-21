from begrepptjanst.settings.base import *

DEBUG=False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', 
        'NAME': 'vgrinfor_backup',
        'USER': 'vgrinfor_admin',
        'PASSWORD': 'YqvyYGm5cJMLmzt',
        'HOST': 'localhost',   # Or an IP Address that your DB is hosted on
        'PORT': '3306',
        'DEFAULT-CHARACTER-SET' : 'utf8',
    }
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/
STATIC_ROOT = '/home/vgrinfor/public_html/begreppstjanst-dev/static'
STATICFILES_DIRS = ['/home/vgrinfor/begreppstjanst-dev/static',]
STATIC_URL = '/begreppstjanst-dev/static/'

# Email settings

EMAIL_HOST = 'mail.vgrinformatik.se'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'info@vgrinformatik.se'
EMAIL_HOST_PASSWORD = 'XrT5bsRq@[ks'
EMAIL_USE_TLS = True

from begrepptjanst.settings.base import *

DEBUG=False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', 
        'NAME': 'vgrinfor_begrepp_prod',
        'USER': 'vgrinfor_admin',
        'PASSWORD': 'YqvyYGm5cJMLmzt',
        'HOST': 'localhost',   # Or an IP Address that your DB is hosted on
        'PORT': '3306',
        'OPTIONS': {
            # Tell MySQLdb to connect with 'utf8mb4' character set
            # 'charset': 'utf8mb4',
            'sql_mode' : 'traditional',
        },
         'TEST': {
            'NAME': 'vgrinfor_begrepp_test',
        },
    }
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/
STATIC_ROOT = '/home/vgrinfor/public_html/begrepptjanst/static'
STATICFILES_DIRS = ['/home/vgrinfor/begrepptjanst/static',]
STATIC_URL = '/begrepptjanst/static/'

# media files 
MEDIA_URL = '/begreppstjanst/media/'
MEDIA_ROOT = '/home/vgrinfor/public_html/begreppstjanst/media'


# Email settings
MEDIA_URL = '/begreppstjanst/media/'
MEDIA_ROOT = '/home/vgrinfor/public_html/begreppstjanst/media'
EMAIL_HOST = 'mail.vgrinformatik.se'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'info@vgrinformatik.se'
EMAIL_HOST_PASSWORD = os.getenv('OLLI_EMAIL_PASSWORD')
EMAIL_USE_TLS = True
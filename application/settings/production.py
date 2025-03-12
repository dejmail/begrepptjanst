from application.settings.base import *
import locale
import sys

sys.stdout.reconfigure(encoding='utf-8')  # Ensure stdout is UTF-8
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
STATIC_ROOT = '/home/vgrinfor/public_html/begrepptjanst/static'
STATICFILES_DIRS = ['/home/vgrinfor/begrepptjanst/static',]
STATIC_URL = '/begrepptjanst/static/'

# media files 
MEDIA_URL = '/begreppstjanst/media/'
MEDIA_ROOT = '/home/vgrinfor/public_html/begreppstjanst/media'


# Email settings
MEDIA_URL = '/begreppstjanst/media/'
MEDIA_ROOT = '/home/vgrinfor/public_html/begreppstjanst/media'
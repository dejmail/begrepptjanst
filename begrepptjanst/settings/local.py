from begrepptjanst.settings.base import *
import os 
import ordbok


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME' : 'ordlist_databas.sqlite3'

    }
}

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

PROJECT_PATH = os.path.realpath(os.path.dirname(__file__))
TEMPLATE_DIRS = ['/templates/',]

STATICFILES_DIRS = [
    "static",
]

STATIC_URL = '/static/'

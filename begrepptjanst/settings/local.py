from begrepptjanst.settings.base import *
import os 
import ordbok


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME' : 'H:\Mina dokument\coding\db.sqlite3'

#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', 
        'NAME': 'vgrinfor_begrepp',
        'USER': 'vgrinfor_admin',
        'PASSWORD': 'YqvyYGm5cJMLmzt',
        'HOST': 'vgrinformatik.se',   # Or an IP Address that your DB is hosted on
        'PORT': '3306',
        'DEFAULT-CHARACTER-SET' : 'utf8',
    }
}

PROJECT_PATH = os.path.realpath(os.path.dirname(__file__))
TEMPLATE_DIRS = [PROJECT_PATH + '/templates/',]

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"), 'django-ajax-search/static/',
    os.path.join(os.path.dirname(ordbok.__file__), 'django-ajax-search','static'),
]

STATIC_URL = '/static/'

from begrepptjanst.settings.base import *

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME' : 'H:\Mina dokument\coding\db.sqlite3'

    }
}


STATIC_URL = '/static/'

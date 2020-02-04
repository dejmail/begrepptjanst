from begrepptjanst.settings.base import *
import os 


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME' : 'H:\Mina dokument\coding\db.sqlite3'

    }
}

PROJECT_PATH = os.path.realpath(os.path.dirname(__file__))
TEMPLATE_DIRS = [PROJECT_PATH + '/templates/',]

STATIC_URL = '/static/'

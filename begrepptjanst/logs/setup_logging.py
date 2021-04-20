import socket
import os
import logging

if socket.gethostname() == 'suijin.oderland.com':
    FILENAME = '/home/vgrinfor/begrepptjanst/logging/debug.log'
elif socket.gethostname() == 'W363207':
    if os.path.isdir('/mnt/c'):
        FILENAME = '/mnt/c/Users/liath1/coding/begrepptjanst/settings/logging/logs.log'
    else:
        FILENAME = '/Users/liath1/coding/begrepptjanst/settings/logging/logs.log'

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '%(name)-12s %(levelname)-8s %(message)s'
        },
        'file': {
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'file',
            'filename': 'logs.log'
        }
    },
    'loggers': {
        'asyncio': {
            'level': 'WARNING',
        },
        'django.utils.autoreload': {
           'level': 'INFO',
        },
        '': {
            'level': 'DEBUG',
            'handlers': ['file']
        },

    }
})
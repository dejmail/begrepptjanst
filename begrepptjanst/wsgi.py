"""
WSGI config for begrepptjanst project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os
import socket

from django.core.wsgi import get_wsgi_application

if socket.gethostname() == 'suijin.oderland.com':
    dir_path = os.path.dirname(os.path.realpath(__file__))
    if 'dev' in dir_path:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'begrepptjanst.settings.dev')
    if 'test' in dir_path:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'begrepptjanst.settings.test')
    else:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'begrepptjanst.settings.production')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'begrepptjanst.settings.local')

#os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'begrepptjanst.settings.base')

application = get_wsgi_application()

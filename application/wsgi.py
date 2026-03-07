"""
WSGI config for application project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os
import socket

from django.core.wsgi import get_wsgi_application

# Ensure logging is configured during WSGI startup
import application.logs.setup_logging  # noqa: F401

if socket.gethostname() == 'suijin.oderland.com':
    dir_path = os.path.dirname(os.path.realpath(__file__))
    if 'dev' in dir_path:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'application.settings.dev')
    if 'test' in dir_path:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'application.settings.test')
    if 'eav' in dir_path:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'application.settings.eav')
    else:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'application.settings.production')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'application.settings.local')

application = get_wsgi_application()  # type: ignore[assignment]

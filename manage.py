#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import socket

def main():
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
        
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()

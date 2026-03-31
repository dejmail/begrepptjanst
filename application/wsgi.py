import os
import socket

from django.core.wsgi import get_wsgi_application

hostname = socket.gethostname()
dir_path = os.path.dirname(os.path.realpath(__file__))

if hostname == "suijin.oderland.com":
    if "eav" in dir_path:
        settings_module = "application.settings.eav"
    elif "test" in dir_path:
        settings_module = "application.settings.test"
    elif "dev" in dir_path:
        settings_module = "application.settings.dev"
    else:
        settings_module = "application.settings.production"
else:
    settings_module = "application.settings.local"

os.environ["DJANGO_SETTINGS_MODULE"] = settings_module


application = get_wsgi_application()

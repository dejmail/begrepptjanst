Configuration
=============

Django Configuration
--------------------

SECRET_KEY
&&&&&&&&&&

Set the secret key as a parameter on the system hosting the app.

SUB DOMAIN
&&&&&&&&&&

Set the subdomain of the website. For example if your app is hosted att http://www.yourapp.com/terminology then the subdomain is *terminology*.


Database Configuration
----------------------

There are 3 database parameters that are supplied from settings stored on the system that need to be changed. In the ``settings/dev.py`` or ``settings/production.py``. The parameters should not be stored in the files if they are going to be publically viewable. ::

    'NAME': DB_NAME,
    'USER': DB_USER,
    'PASSWORD': DB_PASSWORD,


Once the database settings are in place, the database migration file need to be executed to generate the relevant tables within the database. ::

    python manage.py migrate


Configuration of Email
----------------------

There are certain email setting parameters that should be obtained in a similar way to the DB settings, and they should not be publically viewable. ::

    EMAIL_HOST = os.getenv('EMAIL_HOST')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')



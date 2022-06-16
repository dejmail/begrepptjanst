Installation
============

Clone the repository
--------------------

The repo can be cloned from the Github repo `Begreppstjänst <https://github.com/dejmail/begrepptjanst/>`_ into a suitable local directory.

Certain Python dependencies are required for the app to function.

.. literalinclude:: requirements.txt

Install package requirements
----------------------------

If your hosting solution offers the possibility of Python virtual environments, you need to activate that environment on the server and install the required packages using the following command:: 

    pip install -r requirements.txt

Setup the database
------------------

Set up your hosted database. This app was originally configured to run on MySQL / MariaDB, but there is no reason why it cannot be used on Postgresql as well, though this has not been tested.


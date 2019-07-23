Developer Notes
===============

Setup
-----

``requirements-dev.txt`` contains the packages required for development,
it will be a superset of the packages required to run ``usepa_omega2``.

User-required packages will be called out in ``setup.py``.

Set up your environment, virtual or otherwise (such that the desired ``python.exe`` and the Python ``Scripts``
folder are in your ``PATH``) and run the following commands to get the latest version of ``pip``
and the required development packages:

::

    $ python -m pip install --upgrade pip setuptools
    $ pip install -r requirements-dev.txt

You can test your install with the following:

::

    $ bumpversion --help
    $ twine --help


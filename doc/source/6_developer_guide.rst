.. image:: _static/epa_logo_1.jpg

.. _developer_guide_label:

Developer Guide
===============

Developer Notes
^^^^^^^^^^^^^^^

Setup
-----

``requirements-dev.txt`` contains the packages required for development,
it will be a superset of the packages required to run ``usepa_omega2``.

User-required packages will be called out in ``setup.py``.

Set up your environment, virtual or otherwise (such that the desired ``python.exe`` and the Python ``Scripts``
folder are in your ``PATH``) and run the following commands to get the latest version of ``pip``
and the required development packages:

::

    python -m pip install --upgrade pip setuptools
    pip install -r requirements-dev.txt

You can test your install with the following:

::

    bumpversion --help
    twine --help

Versioning and Distribution Tools
---------------------------------

The ``versioning`` folder contains batch files for updating code version numbers and
creating distributions that can be uploaded to PyPi, for example.

Versioning
++++++++++

``bump_version.bat`` can be used to increment the code version number.  There are three components to the version #.
The format is major.minor.patch.  So version 1.2.3 would be major version 1, minor version 2, patch version 3.

``bump_version`` can be used as follows to increment the patch, minor and major version numbers respectively::

    bump_version patch
    bump_version minor
    bump_version major

``bump_version`` uses the ``bump2version`` Python package to update version numbers
in ``setup.py`` and ``__init__.py``.

.. note::
    Once a particular version number has been uploaded (to PyPi, for example) it cannot ever be reused.  So if you
    accidentally bump the major version and upload it, you have to live with the new version number forever, as far as
    I can tell!

Distribution
++++++++++++

``build_dist.bat`` can be used to create source or binary distributions for upload to PyPi, for exmaple.

``build_dist`` takes no arguments and places the latest build in a ``dist`` folder, prior versions are moved to a
``dist_old`` folder.

.. note::

    Should distributions be put out on the network?  Right now they are only whatever machine runs ``build_dist``.

``build_dist`` uses the ``setuptools`` and ``twine`` Python packages to build the distributable files and upload
them to the internet.

``twine`` will ask for a username and password in order to upload the files to the appropriate destination site.

Documentation
-------------

Project documentation primarily takes the form of reStructuredText (``.rst``) files.  Here are some helpful references:

http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html

https://devguide.python.org/documenting/

https://github.com/ralsina/rst-cheatsheet/blob/master/rst-cheatsheet.rst

FAQ
^^^

Multiprocessor Mode
-------------------

Dispy and Pycos Versions
++++++++++++++++++++++++

Some versions of dispy and pycos have proved to be incompatible with each other.  The following versions have been tested together successfully:

* dispy v4.12.2 and pycos v4.18.15
* dispy v4.12.4 and pycos v4.11.0



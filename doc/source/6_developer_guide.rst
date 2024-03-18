.. image:: _static/epa_logo_1.jpg

.. _developer_guide_label:

Developer Guide
===============

This Developer Guide will assist those interested in the latest (pre-release) version of OMEGA available from source code.  This guide assumes some familiarity with Python programming and development, but also attempts to point newcomers in the right direction where possible.

Github Repository
-----------------

The development version of OMEGA is available in the ``developer`` branch of the EPA_OMEGA_Model GitHub repository:

https://github.com/USEPA/EPA_OMEGA_Model

The ``developer`` branch contains in-development, pre-release code, subject to change without notice and no guarantees as to stability at any given point in time.  Features may be added or removed and may or may not be used for future rulemakings.

Releases will be available on separate branches that contain only the particular release in question.

The ``developer`` branch can be accessed via ``.zip`` file directly (https://github.com/USEPA/EPA_OMEGA_Model/archive/refs/heads/developer.zip), via GitHub-integrated development environments or via GitHub command-line calls (e.g. ``gh repo clone USEPA/EPA_OMEGA_Model``).

The OMEGA development team uses PyCharm Community Edition to write and debug code, but any Python development environment may be used.

Setup
-----

After downloading the source code (via ``.zip`` file or cloning the repository), it is necessary to install Python and various required Python packages.

.. sidebar:: Which Python Version Should I Use?

    OMEGA will work with versions at or above 3.7.1, however, some packages may not be readily available for some Python versions and platforms and might require downloading a compiler (Visual Studio, for example) or disabling certain features.

    **The currently recommended Python version is** `Python 3.11.6 <https://python.org/downloads/release/python-3116/>`_ **.**

    Earlier versions will work, but 3.11+ has a faster Cython engine for all platforms, and runs natively on Mx ARM macs as well.  Newer versions may also work but have not been tested at the time of this writing.

    To use parallel processing via dispy (4.15.2) with 3.11+ a `patch <https://github.com/pgiri/dispy/commit/5e136eec3fc1625b7239cc15f67f6a642f906a1f>`_ is required in the dispy ``__init__.py``, otherwise stick with Python 3.10.

Python
++++++

The latest versions of Python are available at https://www.python.org/downloads/

OMEGA has been developed with Python versions 3.7.1 (the minimum required version) thru 3.11.6 and has not been tested with version 3.12 or higher.  If you already have Python installed, there is probably no reason to update to a newer version unless one of the required packages is not compatible with your Python version and hardware platform.

The recommended practice is to run the source code in a virtual environment, which may be set up manually or via the IDE.  The virtual environment isolates the installation of OMEGA-required Python packages from whatever packages may have already been installed at the system level.  This allows a 'clean' installation that can guarantee no known conflicts between packages.

Required Packages
+++++++++++++++++

In addition to Python, OMEGA requires several publicly available Python packages in order to run.  These are detailed in the ``requirements.txt`` file.

Simple Install
^^^^^^^^^^^^^^

The simplest way to install the packages is to use ``pip``, the package installer for Python.  Sometimes there is an updated version of ``pip`` available.  The command-line code below updates ``pip`` and installs the packages detailed in ``requirements.txt``.

::

    python -m pip install --upgrade pip setuptools
    pip install -r requirements.txt


Running From Source Code
++++++++++++++++++++++++

There are at least four common ways to run OMEGA:

    1) from the executable GUI (see :any:`2_getting_started` and :any:`3_running_and_understanding_the_demo`)
    2) from source at the command line as a single (default) session via :any:`omega_model.omega`
    3) from source at the command line as a GUI via :any:`omega_gui.omega_gui`
    4) from source at the command line as a batch via :any:`omega_model.omega_batch` (See also `Omega Batch Command Line Interface <5_user_guide.html#omega-batch-cli>`__)

----

**To run the default session directly from source at the command line from the project top-level folder:**

.. highlight:: none

::

    python omega_model/omega.py

Will produce output such as:

::

    loading omega version X.Y.Z
    importing XXX.py

    ...

    Initializing OMEGA Quick Test:
    importing XYZ.py

    ...

    Running OMEGA Quick Test:

    Running OMEGA Quick Test Pass 0: Manufacturer=consolidated_OEM
    Running OMEGA Quick Test:  Year=2020  Iteration=0 consolidated_OEM
    Running OMEGA Quick Test:  Year=2020  Iteration=1 consolidated_OEM
    Running OMEGA Quick Test:  Year=2020  Iteration=2 consolidated_OEM
    Running OMEGA Quick Test:  Year=2021  Iteration=0 consolidated_OEM
    Running OMEGA Quick Test:  Year=2021  Iteration=1 consolidated_OEM
    Running OMEGA Quick Test:  Year=2021  Iteration=2 consolidated_OEM

    Session ended at 2023-04-05 11:38:00
    Session elapsed time 120.56 seconds

The primary use case for running ``omega.py`` directly is just to confirm the installation or perhaps when it's simpler to debug code without the overhead of the batch process.

----

**To run the gui directly from source at the command line from the project top-level folder:**

.. highlight:: none

::

    python omega_gui/omega_gui.py

----

**For all other development use cases it is recommended to run** ``omega_batch.py`` **as shown in the** :any:`User Guide <5_user_guide>` **under** `Omega Batch Command Line Interface <5_user_guide.html#omega-batch-cli>`__

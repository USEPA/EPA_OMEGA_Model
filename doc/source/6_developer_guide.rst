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

    OMEGA will work with versions at or above 3.7.1, however, some packages may not be readily available for versions at or above 3.9 and might require downloading a compiler (Visual Studio, for example) or disabling certain features.

    For example, at the time of this writing, the ``netifaces`` package used with ``dispy`` requires building from source on Windows when used with Python >= 3.9.  The ``pip`` install process may not complete if it finds a package it cannot download and cannot build from source, in which case other packages may fail to install even though they are readily available.  The workarounds would be to disable the requirement (comment it out in the requirements file), switch to a compatible version of Python, or download the compiler and attempt to compile from source.

    **The currently recommended Python version is** `Python 3.8.10 <https://python.org/downloads/release/python-3810/>`_ **.**

    M1 Mac users should install `the Intel version of Python 3.8.10 <https://www.python.org/ftp/python/3.8.10/python-3.8.10-macosx10.9.pkg>`_ which runs under Rosetta, it prevents compatiblity issues with packages that haven't been updated to run natively, then follow the Simple Install directions.

Python
++++++

The latest versions of Python are available at https://www.python.org/downloads/

OMEGA has been developed with Python versions 3.7.1 (the minimum required version) thru 3.9.6 and has not been tested with version 3.10 or higher.  If you already have Python installed, there is probably no reason to update to a newer version unless one of the required packages is not compatible with your Python version and hardware platform.

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

``conda`` / ``pip`` Install
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Many of the most popular Python packages include pre-compiled versions that are intended for specific hardware.  However, depending on your development environment (ARM-based Mac, for example) it may be useful (or necessary) to get some of the pre-compiled packages from other sources, such as `Anaconda <https://anaconda.org>`_ / `Conda <https://docs.conda.io/en/latest/>`_.  A lightweight ``conda`` install is available via `miniforge <https://github.com/conda-forge/miniforge>`_.  The full `Anaconda <https://anaconda.org>`_ installation is quite large, so if it is not already installed then it is recommended to use something like `miniforge <https://github.com/conda-forge/miniforge>`_ instead.

This more advanced installation method has two steps

    * install available pre-compiled packages via ``conda``
    * install any remaining packages via ``pip``

::

    conda install --file requirements-conda.txt
    pip install -r requirements.txt

``requirements-conda.txt`` may need to be tailored to the developer's specific operating system and hardware but should serve as a good starting point.

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

    Initializing OMEGA Demo:
    importing XYZ.py

    ...

    Running OMEGA Demo:

    Running OMEGA Demo: Manufacturer=OEM_B
    Running OMEGA Demo:  Year=2020  Iteration=0
    Running OMEGA Demo:  Year=2020  Iteration=1
    Running OMEGA Demo:  Year=2021  Iteration=0
    Running OMEGA Demo:  Year=2021  Iteration=1

    Running OMEGA Demo: Manufacturer=OEM_A
    Running OMEGA Demo:  Year=2020  Iteration=0
    Running OMEGA Demo:  Year=2020  Iteration=1
    Running OMEGA Demo:  Year=2021  Iteration=0
    Running OMEGA Demo:  Year=2021  Iteration=1

    Calculating tech volumes and shares
    Saving out/OMEGA Demo_tech_tracking.csv

    Calculating physical effects

    Calculating cost effects

    Discounting costs
    Saving out/OMEGA Demo_cost_effects.csv
    Saving out/OMEGA Demo_physical_effects.csv

    Session ended at 2021-10-18 16:27:10
    Session elapsed time 17.47 seconds

The primary use case for running ``omega.py`` directly is just to confirm the installation or perhaps when it's simpler to debug code without the overhead of the batch process.

----

**To run the gui directly from source at the command line from the project top-level folder:**

.. highlight:: none

::

    python omega_gui/omega_gui.py

----

**For all other development use cases it is recommended to run** ``omega_batch.py`` **as shown in the** :any:`User Guide <5_user_guide>` **under** `Omega Batch Command Line Interface <5_user_guide.html#omega-batch-cli>`__

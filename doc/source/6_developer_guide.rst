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

Python
++++++

The latest versions of Python are available at https://www.python.org/downloads/

OMEGA has been developed with Python versions 3.7.1 (the minimum required version) thru 3.9.6 and has not been tested with version 3.10 or higher.  If you already have Python installed, there is probably no reason to update to a newer version unless one of the required packges is not compatible with earlier versions of Python.

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

``conda`` / ``pip`` install
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

There are at least three common ways to run OMEGA:

    #. from the GUI (see :any:`2_getting_started` and :any:`3_running_and_understanding_the_demo`)
    #. as a batch via ``omega_model/omega_batch.py`` (See `Omega Batch Command Line Interface <5_user_guide.html#omega-batch-cli>`__)
    #. as a single (default) session via ``omega_model/omega.py`` directly

To run the default session directly from source at the command line:

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

For all other development use cases it is recommended to run ``omega_batch.py`` as shown in the :any:`User Guide <5_user_guide>`
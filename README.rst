EPA_OMEGA_Model
===============

The OMEGA2 model determines compliance pathways for light-duty vehicle GHG standards.

Installation
------------

**Typical Install**

Install required packages:

    ``pip install -r requirements.txt``


Install optional developer packages:

    ``pip install -r requirements-dev.txt``

----

**Conda Install**

    ``conda install --file requirements-conda.txt``

    ``pip install -r requirements.txt``

Install optional developer packages:

    ``pip install -r requirements-dev.txt``

Usage
-----

To run from the command line::

    python -m usepa_omega2

To use from within Python::

    >>> import usepa_omega2 as o2
    >>> print('OMEGA2 version %s' % o2.__version__)



Documentation
-------------

https://omega2.readthedocs.io/en/latest/index.html

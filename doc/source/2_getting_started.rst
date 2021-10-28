.. image:: _static/epa_logo_1.jpg

Getting Started
===================
The OMEGA model is written in the open source Python programming language. The model is available in two different packages to suit the particular requirements of the end user:

*  For users intending to run the OMEGA model with input modifications only, an executable version is available along with a directory structure and a complete set of sample inputs. This Getting Started chapter is focused on this executable version.

*  For users intending to run the OMEGA model with user-definable submodules or other code modifications, a developer version is available in a GitHub repository. For more information on the developer version, please refer to the :ref:`developer_guide_label`.

Downloading OMEGA
^^^^^^^^^^^^^^^^^
Releases of the OMEGA model executable will be available as single ``.zip`` files at:

  *  https://www.epa.gov/regulations-emissions-vehicles-and-engines/optimization-model-reducing-emissions-greenhouse-gases

Installing OMEGA
^^^^^^^^^^^^^^^^
Create a directory that will be used as the installation directory for the OMEGA model and copy the downloaded ``.zip`` file into this directory.  Unzip the file into this directory to create the entire OMEGA model file structure.

The folder will contain a ``readme.txt``, the executable, a ``code`` folder which contains a copy of the source code, a ``.pdf`` of the model documentation, an ``inputs`` folder which contains demo batch file(s) and model inputs, and an ``outputs`` folder that contains pre-run demo simulations.

Running OMEGA
^^^^^^^^^^^^^

The newly created run directory will contain the OMEGA model executable file ``OMEGA-X.Y.Z-win.exe``, where X, Y and Z represent the version number.  Opening this file will bring up the OMEGA graphical user interface.  The executable takes a few moments to start up, (or it may take longer, depending on the speed of the user’s computer), as it contains compressed data which must be extracted to a temporary folder.  A self-contained Python installation is included in the executable and Python does not need to be installed by the user in order to run OMEGA. A console window will also be displayed in addition to the GUI window which shows additional runtime information and any diagnostic messages that may be generated.

The GUI has two file system selection boxes in the ``Run Model`` tab; one for choosing the batch file (e.g. 'test_batch.csv') and one for choosing the folder where the batch will execute and produce outputs.  The output folder for the batch will contain the model source code, the batch file, a log file, a requirements file describing the Python installation details, and subfolders for each simulation session.  These session folders will contain an ``in`` and an ``out`` folder.  The ``in`` folder contains the complete set of inputs to the session, and the ``out`` folder contains the simulation outputs and log file.

Step by Step Example Model Run
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Please refer to the :ref:`graphical_user_interface_label` documentation for a step by step execution of the demo example model run.

Viewing the Results
^^^^^^^^^^^^^^^^^^^
After OMEGA model runs have completed, the results generated for each session are available in the associated ``out`` folder in .csv and .png file formats.


.. image:: _static/epa_logo_1.jpg

User Guide
==========

Default Inputs and Assumptions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Inputs/Assumptions body text

Tips for preparing inputs
^^^^^^^^^^^^^^^^^^^^^^^^^
Tips body text

Using The Graphical User Interface
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The EPA OMEGA Model by nature is highly modular and can be run using several methods including but not limited to the command line, the Python environment, and the Graphical User Interface (GUI).  The GUI is the best option for new users of OMEGA to reproduce existing model runs and become familiar with the model's input and output structure.

Running the GUI
----------------
After launching the GUI, the 'Run Model' page will appear as shown in :numref:`ug_label1`.

.. _ug_label1:
.. figure:: _static/ug_figures/gui_run_model_page.jpg
    :align: center

    GUI 'Run Model' Page

The elements of the GUI 'Run Model' page are shown in :numref:`ug_label2`.

.. _ug_label2:
.. figure:: _static/ug_figures/gui_run_model_page_elements.jpg
    :align: center

    GUI 'Run Model' Page Elements

Description of the 'Run Model' page elements:

::

    Note: Context help is always available by hovering the cursor over an element.

* Element 1 - Page Selection
    Tabs to select the various pages of the GUI.

* Element 2 - Configuration File
    Allows the user to open or save a Configuration File.  The Configuration File saves all of the GUI selections to easily recreate a particular OMEGA model run.  When a Configuration File is selected, the base file name will be displayed.  If the complete path to the Configuration File is needed, hover the cursor over the base filename and the entire file path will be displayed.  The red X will be replaced with a green checkmark when a valid Configuration File is selected.

* Element 3 - Input Batch File
    Allows the user to select an Input Batch File.  The Input Batch File is a standard OMEGA input file that describes the complete parameters for a model run.  When an Input Batch File is selected, the base file name will be displayed.  If the complete path to the Input Batch File is needed, hover the cursor over the base filename and the entire path will be displayed.  The red X will be replaced with a green checkmark when a valid Input Batch File is selected.

* Element 4 - Output Batch Directory
    Allows the user to select an Output Batch Directory.  The Output Batch Directory instructs OMEGA where to put the results of a model run.  When an Output Batch Directory is selected, the base directory name will be displayed.  If the complete path to the Output Batch Directory is needed, hover the cursor over the base filename and the entire path will be displayed.  The red X will be replaced with a green checkmark when a valid Output Batch Directory is selected.

* Element 5 - Project Description
    Allows the user to enter any useful text that will be saved in the Configuration File for future reference.  This element is free format text to allow standard functions (such as copy and paste) to be used.  The saved text will be displayed whenever the Configuration File is opened.

* Element 6 - Event Monitor
    The Event Monitor prompts the user during model run setup (file selection, etc.) and keeps a running record of OMEGA model execution in real time.  This is a standard text field to allow simple copying of text as needed for further study or debugging purposes.

* Element 7 - Multiprocessor
    The OMEGA model can be configured to utilize multiple system processors for true multitasking that significantly reduces model completion time.  For example, a typical Intel Core I7(R) has 8 processors total and typically 7 available for OMEGA to utilize.  Checking this box instructs OMEGA to use multiprocessor mode.

* Element 8 - Model Run
    When everything is properly configured, this button will be enabled for initiation of the OMEGA model run.









Text2
^^^^^

Text3
^^^^^

Text4
^^^^^

Text5
^^^^^

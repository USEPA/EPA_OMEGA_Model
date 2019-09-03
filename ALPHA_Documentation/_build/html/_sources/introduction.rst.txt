
Introduction
============

What is ALPHA?
^^^^^^^^^^^^^^

The Advanced Light-Duty Powertrain and Hybrid Analysis (ALPHA) tool was created by EPA to evaluate the Greenhouse Gas (GHG) emissions of Light-Duty (LD) vehicles.  ALPHA is a physics-based, forward-looking, full vehicle computer simulation capable of analyzing various vehicle types combined with different powertrain technologies. The software tool is a MATLAB/Simulink based application.

EPA has developed the ALPHA model to enable the simulation of current and future vehicles, and as a tool for understanding vehicle behavior, greenhouse gas emissions and the effectiveness of various powertrain technologies.  For GHG, ALPHA calculates CO2 emissions based on test fuel properties and vehicle fuel consumption.  No other emissions are calculated at the present time but future work on other emissions is not precluded.

EPA engineers utilize ALPHA as an in-house research tool to explore in detail current and future advanced vehicle technologies.  ALPHA is continually refined and updated to more accurately model light-duty vehicle behavior and to include new technologies.

ALPHA a (and EPA’s Heavy-Duty compliance model, GEM) are built on a common platform known as “REVS” – Regulated Emissions Vehicle Simulation.  REVS forms the foundation of ALPHA.  This document refers to the third revision of REVS, known as REVS3.  ALPHA can be considered a tool as well as a modeling process, the components of which are defined in REVS.

    For more information, visit:

    https://www.epa.gov/regulations-emissions-vehicles-and-engines/advanced-light-duty-powertrain-and-hybrid-analysis-alpha

What is this Document?
^^^^^^^^^^^^^^^^^^^^^^
This documentation should provide the reader a good overview of the ALPHA modeling process and serve as a starting point for understanding some of the ALPHA implementation details.  Common use cases are covered as a way to jump start ALPHA use and techniques commonly used to control and modify the modeling process are presented.

Target Audience
^^^^^^^^^^^^^^^
The target audience for this document is anyone who is interested in learning more about how to run EPA’s ALPHA model.  Prior modeling experience or a good understanding of vehicle powertrains and some Matlab familiarity is assumed.  There are plentiful resources available to learn the basics of Matlab and Simulink in print and online from MathWorks and other third parties.

System Requirements for Installation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

System Requirements
-------------------
ALPHA REVS3 requires Matlab/Simulink with StateFlow 2016b, but should also work with later releases after library/model up-conversions.  Also required is a compiler, for compiling the StateFlow code, see http://www.mathworks.com/support/compilers/R2016b/index.html

Installation
------------
Install Matlab/Simulink and the Simulink StateFlow toolbox following MathWork's instructions.  Copy the REVS_Common folder (and Matlab Common if provided) to a suitable directory on your modeling machine.  Matlab Common is a directory of helpful Matlab scripts and functions which are commonly used for data analysis and visualization, etc.  If Matlab Common is provided, add it to your Matlab path in the same manner as REVS_Common.

Launch Matlab and add REVS_Common and its subfolders to your Matlab path (from the Matlab console, select "Set Path" from the "HOME" tab of the Matlab window, then select "Add with Subfolders..." and browse to REVS_Common).  The path may be saved for future sessions or it is also possible to write a simple script to add the required folders to your path on an as-needed basis.  For example:

::

    addpath(genpath('C:\dev\REVS3 localdev\REVS_Common'));
    addpath(genpath('C:\dev\Matlab Common'));

Directory Structure
^^^^^^^^^^^^^^^^^^^
A high-level description of the REVS_Common directory structure follows.  Use it as a rough guide to exploring the file system.  Not all releases of ALPHA may contain all subfolders (for example, the HIL-related files) but this should still give a good idea of where common items are located.

* REVS_Common  top level
    * Contains REVS_VM.mdl, the top-level ALPHA model and the ALPHA logo
* datatypes
    * Contains Matlab class definitions for the Matlab objects that compose REVS and various enumerated datatypes.  Also contains REVS_fuel_table.csv that holds the fuel properties for known fuel types
* drive_cycles
    * Contains .mat files that represent various compliance or custom drive cycles in the form of class_REVS_drive_cycle objects with the name drive_cycle. The "sim_xxx.m" Matlab scripts are basically deprecated at this point and have been replaced by the use of tags in config strings within the batch process (more on that below)
* executable_tools
    * Contains tools for generating executable (binary) versions of the model.  Primarily used for developing the GEM compliance model
* functions
    * Contains various Matlab functions used during the modeling process.   Also contains functionSignatures.json which Matlab can use to provide auto-completion assistance in the Editor
* helper_scripts
    * Primarily contains scripts related to pre- and post-processing simulation runs
* HIL_tools
    * Tools related to building executable ALPHA models for Hardware-in-the-Loop (HIL) testing
* libraries
    * Contains the REVS Simulink component block models, separated into various libraries by component type
* log_packages
    * Contains scripts that are used in conjunction with the batch modeling process in order to control the datalogging and post-processing of datalogs into a standardized data object
* param_files
    * Contains data for common model components such as engines or batteries which can be used across multiple modeling projects.  In particular, the engine files are part of the NCAT “data packet” publishing process
* plots
    * Can be used to store plots of common interest to REVS3 development
* publish_tools
    * Contains tools related to publishing NCAT data packets, particularly for publishing engine data
* python
    * Contains Python scripts related to the implementation of multi-core and/or multi-machine parallel modeling processes on a local network using Python packages.

Design Principles
^^^^^^^^^^^^^^^^^
This section will lay out of the some high-level design principles that guide ALPHA development.

Object Oriented Design
----------------------
REVS3 makes significant use of Matlab classes and objects in order to provide a well-defined, maintainable and re-usable set of data structures and model functionality.  Class definitions start with \class_ and enumerated types start with \enum_.  With a few exceptions, most of the classes start with class_REVS so that Matlab auto-completion provides a useful list of the available classes.

Component Reuse
---------------
The use of Matlab classes and objects aids in the maintenance of the code base by allowing easier addition of new elements and behaviors to existing data structures.  Using classes (instead of structures) also ensures that data structures have known and reusable definitions.

Generally speaking, model components have class definitions that correspond to the required parameters and data necessary for their intended function.  There are rare exceptions for a few legacy components that came over from REVS2 (which did not generally used Matlab classes and objects).  New components should be added to the model following the object-oriented paradigm whenever possible.

Datalogging and Auditing
------------------------
Datalogging enables post-simulation data analysis and debugging.  Significant effort was applied to the creation of a datalogging framework that is both flexible and fast.  For that reason there are controls available to limit the amount of data logged by the model (excess datalogging significantly slows the model down and is therefore to be avoided).  For example, datalogging may be limited to the bare minimum required to calculate fuel economy, or datalogging may be limited to the bare minimum plus everything related to the engine or transmission.  It is also possible to log every available signal in the model, if desired and the associated performance slowdown is acceptable.  Datalogging should generally be limited to the signals or components required for the investigation at hand.  Datalogs are found in a workspace object named result at the end of simulation.

The model is also set up to audit the energy flows throughout the model.  If auditing is enabled then a text file (or console output) is created that shows the energy sources and sinks that were simulated.  The total energy provided and absorbed should be equal if the model conserves energy.  Since the model runs at discrete time steps and since modeling is an exercise in approximation there is commonly some slight discrepancy which is noted as the Simulation Error in the audit report.  The Energy Conservation is reported as a percentage ratio between the Net Energy Provided and the Total Loss Energy.

If new components are added to the model then new audit blocks need also to be added and the corresponding audit scripts will require updating in order to capture the new energy source or sink in the audit report.  Adding audits to the model is somewhat of an advanced topic, primarily because the block layout of the model and the mathematical structure of the model are not the same – except that sometimes they are!  The primary principle is to remember that the purpose of the audit is to monitor the physical energy flows and not the energy flow through the Simulink blocks which may be distinct from the physics.

Auditing the energy flow in the model is a key factor in ensuring the plausibility and function of the model.

Conventions and Guidelines
--------------------------
There are several conventions and guidelines that enhance the consistency and usability of the model, see :ref:`ad-crossref-1` under ALPHA Development.







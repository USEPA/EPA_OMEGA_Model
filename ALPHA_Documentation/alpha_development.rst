
ALPHA Development
=================

.. _ad-crossref-1:

Conventions and Guidelines
^^^^^^^^^^^^^^^^^^^^^^^^^^
There are a few guidelines that cover the use of variable names within the modeling environment and other conventions.  Understanding and following the guidelines facilitates collaboration, ease of use and understanding of the modeling environment.

* Class definitions start with \class_.
* Enumerated datatype definitions start with \enum_.
* Physical unit conversions should be accomplished using the convert class.  For example engine_max_torque_ftlbs = engine_max_torque_Nm * convert.Nm2ftlbs.  Avoid hard-coded conversion constants.
* Any variable that has corresponding units should take the form variable_units, such as vehicle_speed_kmh or shaft_torque_Nm.  SI units are preferred whenever possible unless superseded by convention (such as roadload ABCs).  Units commonly use lowercase 'p' for 'per'.  For example mps = meters per second, radps = radians per second.  Readability outweighs consistency if convention and context allows, for example vehicle_speed_mph is understood to be vehicle speed in miles per hour, not meters per hour.
* If English units are used by a class, that class should also provide SI equivalents.  REVS provides some frameworks for and examples of automatic unit conversions that may be used.
* Variable names should be concise but abbreviations or acronyms are generally to be avoided unless superseded by convention.  For example, datalog.transmission.gearbox, not dl.trns.gbx.  Exceptions are bus signal names and the port names on Simulink blocks (long names reduce readability rather than enhancing it) - for example torque may be trq and speed may be spd. Simulink block names may also receive abbreviated names if it enhances readability.
* The use of underscores is preferred for workspace and data structure variable names, for example selected_gear_num.  Camelcase is preferred for variables defined in Simulink masks and local block workspaces so they may be distinguished from ordinary workspace variables.
* Most functions that are specific to the REVS modeling platform start with \REVS_.
* The use of 'goto' and 'from' flags is to be avoided in Simulink blocks as they significantly decrease the readability and understanding of block connections.  Exceptions to this rule are the REVS_VM top-level system_bus component sub-buses, the global_stop_flag and the REVS_audit_phase_flag which must be made available throughout the model.
* Trivial Simulink blocks (such as multiplication, addition, etc) may have their block names hidden to enhance readability, non-trivial blocks should have names which concisely and accurately describe their function.
* Simulink blocks should have a white background and a black foreground.  Exceptions are red foreground for blocks that are deprecated or orange foreground for blocks that may be unproven or experimental.
* Useful Simulink blocks should be added to the appropriate REVS_Common model library if they are likely to be reused.
* Simulink block names are lowercase unless superseded by convention and words are separated by spaces (as opposed to underscores).
* Simulink blocks that take in the system bus should have system_bus as input port 1.
* Simulink blocks that produce a signal bus should have bus_out as output port 1.

Customizing the Batch Process
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Custom Pre- and Post-Processing
-------------------------------

Creating and Using Config String Tags
-------------------------------------

Custom Output Summary File Formats
----------------------------------

REVS_VM
^^^^^^^

Overview
--------
Powertrain Variants
-------------------


Understanding the Simulink Libraries
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
accessory_lib
-------------
ambient_lib
-----------
controls_lib
------------
driver_lib
----------
electric_lib
------------
engine_lib
----------
general_lib
-----------
HIL_lib
-------
logging_lib
-----------
powertrain_lib
--------------
transmission_lib
----------------
vehicle_lib
-----------

Understanding Datalogging
^^^^^^^^^^^^^^^^^^^^^^^^^

Understanding Auditing
^^^^^^^^^^^^^^^^^^^^^^

Component Development
^^^^^^^^^^^^^^^^^^^^^

Data Structures and Classes
^^^^^^^^^^^^^^^^^^^^^^^^^^^





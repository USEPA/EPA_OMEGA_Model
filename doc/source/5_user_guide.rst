.. image:: _static/epa_logo_1.jpg

User Guide
==========

The primary input to OMEGA is the batch definition file which contains rows for each user input required to define a simulation session or group of sessions.

The line-by-line documentation of the batch definition file is available at :any:`omega_model/omega_batch.py<omega_model.omega_batch>` and won't be repeated here.

Batch definition inputs can be scalar values or input file paths (relative to the location of the batch file and/or absolute).

Several of the input files may dynamically load user-definable modules at runtime.  These files are indicated as ``user_definable`` in the table below.  User-definable inputs and modules are loaded by interpreting the input file ``input_template_name:`` field. For example, if the input template name of a user-definable input is ``consumer.market_classes`` then the Python module ``omega_model/consumer/market_classes.py`` will be used to load the rest of the input file, which may contain an arbitrary format known to the module. The process of creating user-definable modules is a topic for developers.

Below is a table with links to the modules that load the files and their documentation of the input file formats.

Batch Input Files and Loaders
    .. csv-table::
        :header-rows: 1
        :stub-columns: 1

        Parameter,Loaded By
        Context Fuel Prices File, :any:`omega_model/context/fuel_prices.py<omega_model.context.fuel_prices>`
        Context New Vehicle Market File, :any:`omega_model/context/new_vehicle_market.py<omega_model.context.new_vehicle_market>`
        Manufacturers File, :any:`omega_model/producer/manufacturers.py<omega_model.producer.manufacturers>`
        Market Classes File, ``user_definable`` e.g. :any:`omega_model/consumer/market_classes_unibody.py<omega_model.consumer.market_classes_unibody>`
        Onroad Fuels File, :any:`omega_model/context/onroad_fuels.py<omega_model.context.onroad_fuels>`
        Onroad Vehicle Calculations File, :any:`omega_model/producer/vehicles.py<omega_model.producer.vehicles>`
        Onroad VMT File, ``user_definable`` e.g. :any:`omega_model/consumer/annual_vmt_fixed_by_age.py<omega_model.consumer.annual_vmt_fixed_by_age>`
        Producer Generalized Cost File, ``user_definable`` e.g. :any:`omega_model/producer/producer_generalized_cost.py<omega_model.producer.producer_generalized_cost>`
        Production Constraints File, :any:`omega_model/context/production_constraints.py<omega_model.context.production_constraints>`
        Sales Share File, ``user_definable`` e.g. :any:`omega_model/consumer/sales_share_ice_bev.py<omega_model.consumer.sales_share_ice_bev>`
        Vehicle Price Modifications File, :any:`omega_model/context/price_modifications.py<omega_model.context.price_modifications>`
        Vehicle Reregistration File, ``user_definable`` e.g. :any:`omega_model/consumer/reregistration_fixed_by_age.py<omega_model.consumer.reregistration_fixed_by_age>`
        ICE Vehicle Simulation Results File, ``user_definable`` e.g. :any:`omega_model/context/rse_cost_clouds.py<omega_model.context.rse_cost_clouds>`
        BEV Vehicle Simulation Results File, ``user_definable`` e.g. :any:`omega_model/context/rse_cost_clouds.py<omega_model.context.rse_cost_clouds>`
        PHEV Vehicle Simulation Results File, ``user_definable`` e.g. :any:`omega_model/context/rse_cost_clouds.py<omega_model.context.rse_cost_clouds>`
        Vehicles File, :any:`omega_model/producer/vehicle_aggregation.py<omega_model.producer.vehicle_aggregation>`
        Powertrain Cost File, :any:`omega_model/context/powertrain_cost.py<omega_model.context.powertrain_cost>`
        Glider Cost File, :any:`omega_model/context/glider_cost.py<omega_model.context.glider_cost>`
        Body Styles File, :any:`omega_model/context/body_styles.py<omega_model.context.body_styles>`
        Mass Scaling File, :any:`omega_model/context/mass_scaling.py<omega_model.context.mass_scaling>`
        Workfactor Definition File, :any:`omega_model/policy/workfactor_definition.py<omega_model.policy.workfactor_definition>`
        ,
        Session Policy Alternatives Settings,
        Drive Cycle Weights File, :any:`omega_model/policy/drive_cycle_weights.py<omega_model.policy.drive_cycle_weights>`
        Drive Cycle Ballast File, :any:`omega_model/policy/drive_cycle_ballast.py<omega_model.policy.drive_cycle_ballast>`
        Drive Cycles File, :any:`omega_model/policy/drive_cycles.py<omega_model.policy.drive_cycles>`
        GHG Credit Params File, :any:`omega_model/policy/credit_banking.py<omega_model.policy.credit_banking>`
        GHG Credits File, :any:`omega_model/policy/credit_banking.py<omega_model.policy.credit_banking>`
        GHG Standards File, ``user_definable`` e.g. :any:`omega_model/policy/targets_footprint.py<omega_model.policy.targets_footprint>`
        Off-Cycle Credits File, ``user_definable`` e.g. :any:`omega_model/policy/offcycle_credits.py<omega_model.policy.offcycle_credits>`
        Policy Fuel Upstream Methods File, :any:`omega_model/policy/upstream_methods.py<omega_model.policy.upstream_methods>`
        Policy Fuels File, :any:`omega_model/policy/policy_fuels.py<omega_model.policy.policy_fuels>`
        Production Multipliers File, :any:`omega_model/policy/incentives.py<omega_model.policy.incentives>`
        Regulatory Classes File, ``user_definable`` e.g. :any:`omega_model/policy/regulatory_classes.py<omega_model.policy.regulatory_classes>`
        Required Sales Share File, :any:`omega_model/policy/required_sales_share.py<omega_model.policy.required_sales_share>`
        ,
        Session Postproc Settings,
        Context Implicit Price Deflators File, :any:`omega_model/context/ip_deflators.py<omega_model.context.ip_deflators>`

Simulation Context
    The context inputs apply to all sessions within a batch.  Multiple batch files must be defined to run multiple contexts.

Simulation Sessions
    The Reference Session
        The batch file must define at least one simulation session, known as the reference session, which is the left-most session in the batch definition file.  The reference session should align with the provided context inputs.  For example, if the context fuel price and new vehicle market data are from AEO, then the policy inputs of the reference session must be consistent with the assumptions used by AEO to generate the projections.  For example, the sales projections take into account ghg and fuel economy policies in force or projected at the time and the policy inputs used for the reference session should be consistent with those.  It would be inconsistent to assume the same sales for a different ghg/fuel economy policy.
    Policy Alternative Sessions
        Optionally, one or more alternative policy sessions may be defined in subsequent columns. Typically these would be various policies under evaluation via OMEGA or perhaps a single policy with various alternative inputs or assumptions.

.. _omega_batch_cli:

OMEGA Batch Command Line Interface
    The batch process can be initiated from the OMEGA GUI or from the command line by running ``omega_batch.py`` directly, as in:

::

    >>python omega_model/omega_batch.py --bundle_path path/to/my/bundle_folder --batch_file path/to/my/batch_file.csv

    or

    >>python omega_model/omega_batch.py --bundle_path path/to/my/bundle_folder --ui_batch_file


In fact, the GUI can be thought of as a wrapper to a command line call to ``omega_batch.py``.  The paths supplied to the GUI fill in the ``--bundle_path`` and ``--batch_file`` arguments.

Typical Command Line Usage (not all available command-line options shown)

.. highlight:: none

::

    usage: omega_batch.py
            [-h] [--bundle_path BUNDLE_PATH] [--batch_file BATCH_FILE]  [--ui_batch_file]
            [--session_num SESSION_NUM] [--analysis_final_year ANALYSIS_FINAL_YEAR]
            [--verbose] [--show_figures]

    Run OMEGA batch simulation

    optional arguments:
      -h, --help            show this help message and exit

      --bundle_path BUNDLE_PATH
                            Path to bundle folder

      --batch_file BATCH_FILE
                            Path to batch definition file

      --ui_batch_file
                            Select batch file from dialog box

      --session_num SESSION_NUM
                            ID # of session to run from batch

      --analysis_final_year ANALYSIS_FINAL_YEAR
                            Override analysis final year

      --verbose             Enable verbose omega_batch messages

Other command line arguments are available, mostly associated with parallel processing options and implementation or code development.  The full list of arguments can be viewed as follows:

::

    >>python omega_model/omega_batch.py

    or

    >>python omega_model/omega_batch.py -h

    or

    >>python omega_model/omega_batch.py --help

Selecting Sessions to Run
    Sessions can be enabled or disabled within the batch file by setting the ``Enable Session`` field to ``TRUE`` or ``FALSE``, respectively.  Alternatively, the ``--session_num`` argument can be passed to ``omega_batch``.  The reference session is session number ``0``.  The reference session cannot be disabled, regardless of the ``Enable Session`` field value, as it generates reference vehicle prices that the other sessions require in order to calculate overall vehicle sales.

Understanding the Batch Process
    The first step in the batch process is to copy the complete source code to the ``bundle`` folder (in the ``omega_model`` directory, or as specified by the user via the ``--bundle_path`` argument) and to create subfolders for each active session.  Within each session folder will be an ``in`` folder (and an ``out`` folder will be created when the session runs).  The bundle folder contains the original batch definition file as well as a timestamped batch definition file that is actually run.  The timestamped file has the original batch settings with new session input file paths relative to the bundle.  The bundle folder contains a ``requirements.txt`` file for reference.  When running from source code the requirements file indicates the version of Python used to run the batch and contains the list of installed Python packages and their versions at the time, e.g. ``python_3_8_10_requirements.txt``.  When running from the executable the contents of the ``GUI_requirements.txt`` file indicates the version number of the GUI.

    The batch itself and each session will have a log file indicating the progress and success or failure of the process.  The batch log file is named ``batch_logfile.txt`` and exists at the top of the bundle folder.  Session logs have the prefix ``o2log_`` and are located in each session's ``out`` folder.

    If a session completes successfully, the session folder is renamed and prepended with an underscore, ``_``.  Failed session folders are prepended with ``#FAIL_``.  In this way the session status can be monitored by observing the folder names as the batch runs.

    Since the bundle folder contains the source code and all inputs for every session it is possible to re-run a batch, or part of a batch, at a later time and reproduce the results if desired.  To do so, remove any session folder prefixes and use ``omega_batch.py`` to re-run the timestamped batch file, while supplying the ``--no_bundle`` and ``--no_validate`` arguments, since the batch has already been bundled.  As in:

::

    >>python path/to/my/bundle_folder/omega_model/omega_batch.py --batch_file path/to/my/bundle_folder/YYYY_MM_DD_hh_mm_ss_batch.csv --no_bundle --no_validate


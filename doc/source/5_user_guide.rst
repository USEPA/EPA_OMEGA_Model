.. image:: _static/epa_logo_1.jpg

User Guide
==========

OMEGA Model
^^^^^^^^^^^
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
        Context Electricity Prices File, ``user_definable`` e.g. :any:`omega_model/context/fuel_prices.py<omega_model.context.electricity_prices_aeo>`
        Context New Vehicle Market File, :any:`omega_model/context/new_vehicle_market.py<omega_model.context.new_vehicle_market>`
        Manufacturers File, :any:`omega_model/producer/manufacturers.py<omega_model.producer.manufacturers>`
        Market Classes File, ``user_definable`` e.g. :any:`omega_model/consumer/market_classes_ice_bev_phev_body_style.py<omega_model.consumer.market_classes_ice_bev_phev_body_style>`
        Onroad Fuels File, :any:`omega_model/context/onroad_fuels.py<omega_model.context.onroad_fuels>`
        Onroad Vehicle Calculations File, :any:`omega_model/producer/vehicles.py<omega_model.producer.vehicles>`
        Onroad VMT File, ``user_definable`` e.g. :any:`omega_model/consumer/annual_vmt_fixed_by_age.py<omega_model.consumer.annual_vmt_fixed_by_age>`
        Producer Generalized Cost File, ``user_definable`` e.g. :any:`omega_model/producer/producer_generalized_cost.py<omega_model.producer.producer_generalized_cost>`
        Production Constraints File, :any:`omega_model/context/production_constraints.py<omega_model.context.production_constraints>`
        Sales Share File, ``user_definable`` e.g. :any:`omega_model/consumer/sales_share_ice_bev_phev_body_style.py<omega_model.consumer.sales_share_ice_bev_phev_body_style>`
        Vehicle Price Modifications File, :any:`omega_model/context/price_modifications.py<omega_model.context.price_modifications>`
        Vehicle Reregistration File, ``user_definable`` e.g. :any:`omega_model/consumer/reregistration_fixed_by_age.py<omega_model.consumer.reregistration_fixed_by_age>`
        ICE Vehicle Simulation Results File, ``user_definable`` e.g. :any:`omega_model/context/rse_cost_clouds.py<omega_model.context.rse_cost_clouds>`
        BEV Vehicle Simulation Results File, ``user_definable`` e.g. :any:`omega_model/context/rse_cost_clouds.py<omega_model.context.rse_cost_clouds>`
        PHEV Vehicle Simulation Results File, ``user_definable`` e.g. :any:`omega_model/context/rse_cost_clouds.py<omega_model.context.rse_cost_clouds>`
        Vehicles File, :any:`omega_model/producer/vehicle_aggregation.py<omega_model.producer.vehicle_aggregation>`
        Powertrain Cost File, ``user_definable`` e.g. :any:`omega_model/context/powertrain_cost_frm.py<omega_model.context.powertrain_cost_frm>`
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
        Policy Utility Factor Methods File, :any:`omega_model/policy/utility_factors.py<omega_model.policy.utility_factors>`

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

OMEGA Effects
^^^^^^^^^^^^^
The primary inputs to the OMEGA effects calculator are the OMEGA Model's vehicles and vehicle annual data output files for
sessions of interest. For the Effects calculator to find these necessary OMEGA Model output files, the user must provide to the
Effects calculator the path where they can be found. This is done via the "batch_settings_effects" input file. Assuming the user has run the OMEGA
Model and has the bundled results saved to an accessible directory, then the batch_settings_effects file should provide the full system
path to that directory.

Importantly, the batch_settings_effects file must also provide a session name associated with each session for which effects
are to be calculated. The session name must be consistent with the session name used in the OMEGA Model run. These session names
also need to include a context session name, a no action session name and at least one action session name. These are needed
to calculate the effects properly since the context session serves to calculate fleet vehicle miles traveled (VMT) and fleet fuel costs per
mile from which any VMT rebound effects in subsequent sessions can be calculated.

The OMEGA effects calculator will look for several necessary files within "in" folder of the context session folder contained within the
bundled OMEGA Model results (i.e., the user need not specify these files in the batch_settings_effects file). In particular, the OMEGA
effects calculator will look for and find the context fuel prices, price deflator files used to adjust all monetized values into a common
valuation, an onroad fuels file, an onroad vehicle calculations file, an annual VMT file, and a reregistration file.

In addition to the context session, a no action and action session are required because some of the effects calculations are meant
to calculate impacts of a policy action relative to a no action, or business as usual, policy. In particular, the benefits
calculations can only be done by first calculating physical effects of the action policy relative to the no action
policy since benefits do not exist, within OMEGA, absent a policy change.

The other inputs to the OMEGA effects calculator are those associated with: vehicle, EGU and refinery emission rates; cost factors, or $/ton, factors
associated with criteria air pollutants, GHG emissions, energy security impacts, crashes, congestion, noise, vehicle repair, vehicle
maintenance, fuel prices, etc. All of these input files must be provided by the user via the batch_settings_effects file.

Below is a table describing the entries needed in the batch_settings_effects file. User entries are to be made in the
``value`` or ``full_path`` columns of the batch_settings_effects file.

Batch Input Files and Loaders
    .. csv-table::
        :header-rows: 1
        :stub-columns: 1

        parameter,session_policy,description
        RUNTIME OPTIONS,,
        Run ID,all,enter ``value`` for the run identifier for your output folder name or blank for default (default is omega_effects)
        Save Path,all,enter ``full path`` of the *folder* to which to save results but do not include unique run identifiers
        Save Input Files,all,enter ``value`` as True to save input files to your results folder or False to save space and not do so
        Save Context Fuel Cost per Mile File,all,enter ``value`` as True or False and note that these files can be large especially in CSV format
        Save Vehicle-Level Safety Effects Files,all,enter ``value`` as True or False and note that these files can be large especially in CSV format
        Save Vehicle-Level Physical Effects Files,all,enter ``value`` as True or False and note that these files can be large especially in CSV format
        Save Vehicle-Level Cost Effects Files,all,enter ``value`` as True or False and note that these files can be large especially in CSV format
        Format for Vehicle-Level Output Files,all,enter ``value`` as 'csv' for large Excel-readable files or 'parquet' for compressed files usable in Pandas
        BATCH SETTINGS,,
        batch_folder,all,enter ``full_path`` of the *folder* containing OMEGA Model run results
        Vehicles File Base Year,all,enter ``value`` consistent with the OMEGA Model run
        Analysis Final Year,all,enter ``value`` <= the value used in the OMEGA Model run
        Cost Accrual,all,enter ``value`` as start-of-year or end-of-year - this entry impacts the discounting of costs and benefits
        Discount Values to Year,all,enter ``value`` to which costs and benefits will be discounted
        Analysis Dollar Basis,all,enter ``value`` consistent with the OMEGA Model run
        Batch Analysis Context Settings,,
        Context Name,all,enter ``value`` of the AEO report (e.g. AEO2021) used in the OMEGA Model run
        Context Case,all,enter ``value`` of the AEO case (e.g. Reference case) used in the OMEGA Model run
        VMT Rebound Rate ICE,all,enter ``value`` for ICE rebound (e.g. -0.1)
        VMT Rebound Rate BEV,all,enter ``value`` for BEV rebound
        SC-GHG in Net Benefits,all,enter ``value`` as 'global' or 'domestic' or 'both' (note that both global and domestic benefits are calculated, this only impacts net benefits)"
        Maintenance Costs File,all,enter ``full_path`` of maintenance costs file in CSV format
        Repair Costs File,all,enter ``full_path`` of repair costs file in CSV format
        Refueling Costs File,all,enter ``full_path`` of refueling costs file in CSV format (i.e. the cost of time spent refueling)
        General Inputs for Effects File,all,enter ``full_path`` of general inputs for effects file in CSV format
        Context Criteria Cost Factors File,all,enter ``full_path`` of criteria air pollutant $/ton factors file in CSV format
        Context SCC Cost Factors File,all,enter ``full_path`` of social cost of GHG $/ton factors file in CSV format
        Context Energy Security Cost Factors File,all,enter ``full_path`` of energy security $/barrel file in CSV format
        Context Congestion-Noise Cost Factors File,all,enter ``full_path`` of crashes & congestion & noise costs file in CSV format
        Context Legacy Fleet File,all,enter ``full_path`` of legacy fleet file in CSV format
        ,,
        Session Name,context,enter ``value`` of the context session name (e.g. SAFE or HDP2_noIRA)
        Context Stock and VMT File,context,enter ``full_path`` of stock and VMT file file in CSV format
        ,,
        Session Name,no_action,enter ``value`` of the no action session name (e.g. NTR or HDP2)
        Context Powersector Emission Rates File,no_action,enter ``full_path`` of EGU emission rates file in CSV format
        Context Refinery Emission Rates File,no_action,enter ``full_path`` of refinery emission rates file in CSV format
        Context Refinery Emission Factors File,no_action,leave blank - use is not recommended
        Context Vehicle Emission Rates File,no_action,enter ``full_path`` of vehicle emission rates file in CSV format
        Context Safety Values File,no_action,enter ``full_path`` of safety values file in CSV format
        Context Fatality Rates File,no_action,enter ``full_path`` of fatality rates file in CSV format
        ,,
        Session Name,action_1,enter ``value`` of the first action or policy session name (e.g. Proposal)
        Context Powersector Emission Rates File,action_1,enter ``full_path`` which may be the same as used for the no action session
        Context Refinery Emission Rates File,action_1,enter ``full_path`` which may be the same as used for the no action session
        Context Refinery Emission Factors File,action_1,enter ``full_path`` which may be the same as used for the no action session
        Context Vehicle Emission Rates File,action_1,enter ``full_path`` which may be the same as used for the no action session
        Context Safety Values File,action_1,enter ``full_path`` which may be the same as used for the no action session
        Context Fatality Rates File,action_1,enter ``full_path`` which may be the same as used for the no action session

Runtime Options
---------------
The effects results will be saved to a folder specified in the save_path ``full_path`` entry (e.g. "c:/omega/effects"). In that save_path folder,
a folder will be auto generated and will have the same name as the OMEGA Model batch for which effects are being calculated.
Within that batch folder, a run results folder will be auto generated whose name will consist of a date and timestamp associated with
the time of the OMEGA effects calculator run along with the run ID to assist in keeping track of different runs and ensuring that nothing is
overwritten by future runs. As a result, you might find your results saved to a folder named something like
"c:/omega/effects/ld_omega_model_batch/20230504_090000_omega_effects" for a run done on May 4, 2023, at 9:00AM.

Note that some effects output files may or may not be desired. The effects are calculated for every vehicle in the fleet in every
year up to and including the Analysis Final Year ``value``. If you run through 2055, this becomes a large number of vehicles and
the vehicle-level output files can become very large (0.5 GB to 1 GB per file). Depending on your machine, you may have trouble
viewing those files let alone conducting analyses of the results (e.g., in Excel or OpenOffice). Saving of these large output files
can be avoided by setting the "Save Vehicle-Level" file ``value`` to False. Alternatively, the use can generate those files in
parquet format, which is a compressed file format, to save space. Parquet files are readable by Python's Pandas library but cannot
be opened directly in a spreadsheet application. Instructions for reading saved parquet files in Pandas are included in the save_file function
of :any:`/omega_effects/general/file_id_and_save.py<omega_effects.general.file_id_and_save>`.

Batch Analysis Context Settings
-------------------------------
The files specified in the Batch Analysis Context Settings section of the batch_settings_effects file are meant to apply to all
sessions in the batch.

Session Settings
----------------
Any session can be run in the OMEGA Effects calculator provided those sessions exist in the batch_folder. A ``value`` for
the session name must be provided. A session can be ignored by setting the Session Name ``value`` to None. A Context Session Name
must be provided and no session meant to be included can have a session name of None.

Emission Rates Files
--------------------
Note that an action session may require a different emission rate input file than that used for the no action session for, say,
vehicle emission rates in the event that the policy impacts vehicle emission rates.

Running the OMEGA Effects Executable
------------------------------------
1)	The OMEGA Effects code, input files and output files can be found on the OMEGA webpage at this link https://www.epa.gov/regulations-emissions-vehicles-and-engines/optimization-model-reducing-emissions-greenhouse-gases

2)	The OMEGA Effects are not part of the OMEGA Model executable file. The OMEGA Effects can be run using the Python code included in the OMEGA repository at https://github.com/USEPA/EPA_OMEGA_Model or the Python code included in the zip file linked above.

3)	Alternatively, the OMEGA Effects can be run using a separate executable file (recommended).

4)	These instructions assume that the executable file is being used to generate the OMEGA Effects.

5)	Place the executable file in your preferred location on your local machine.

6)	Place the associated “effects_inputs” folder and its contents in your preferred location on your local machine. This folder is available on request to omega_support@epa.gov.

7)	In the effects_inputs folder, find 2 batch settings files: one for light-duty (batch_settings_effects_ld.csv) and one for medium-duty (batch_settings_effects_md.csv).

8)	In cell C3 of the batch settings file, enter a run ID if desired (e.g., NPRM, test, etc.). This run ID will be included as part of the output folder name. The default value is omega_effects.

9)	In cell D5, enter the path of the save folder (e.g., "C:/omega/effects"). The output folder will be saved to this folder. The output folder will be named using other entries in the batch file and the run ID set in step 8.

10)	Other options in Column C can be set to TRUE or FALSE, but please read the notes associated with each.

11)	In cell D14 of the batch settings file, enter the full path to the folder that contains your OMEGA compliance run results. This is important since the OMEGA Effects will look to this folder to find the needed vehicles.csv and vehicle_annual_data.csv files generated for each session in your OMEGA compliance run.

12)	Most values in column C can be left as is. There must be a context session name in cell C42. If your context session name is different, then set cell C42 accordingly. The same is true of subsequent session names in column C. If you do not want your effects outputs to include a session that exists in your OMEGA compliance run folder, simply set the session name to None.

13)	Remaining entries in Column D should then point to the “effects_inputs” folder on your local machine. Filenames can probably be left as is unless you are using files with different names.

14)	After setting up the batch settings file, be sure to save it as a CSV file (not Excel).

15)	Double click the executable file.

16)	The executable should launch. Be patient. After several seconds, a file dialog window should open asking for the batch settings file. Navigate to the batch settings file you saved in step 14, select it, and click open. The executable should now run using the settings in your batch settings file.


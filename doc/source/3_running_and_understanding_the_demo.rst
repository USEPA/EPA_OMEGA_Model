.. image:: _static/epa_logo_1.jpg

.. _running_and_understanding_the_demo_label:

Running the Demo Example using the Graphical User Interface (GUI)
=================================================================

.. _graphical_user_interface_label:

GUI Basics
^^^^^^^^^^
The EPA OMEGA Model is highly modular and can be run using several methods including but not limited to the command line, the Python environment, and the Graphical User Interface (GUI).  The GUI is the best option for new users of OMEGA to reproduce existing model runs and become familiar with the model's input and output structure.  This introduction will guide the user through running the demo example.

After launching the GUI, the 'Intro' tab will appear as shown in :numref:`ug_label1`.

.. _ug_label1:
.. figure:: _static/gui_figures/gui_intro_page.jpg
    :align: center

    GUI 'Intro' Tab

Selecting the 'Run Model' tab allows the user to set up an OMEGA model run. The elements of the 'Run Model' tab are shown in :numref:`ug_label2`.

.. _ug_label2:
.. figure:: _static/gui_figures/gui_run_model_page_elements.jpg
    :align: center

    GUI 'Run Model' Tab Elements

Description of the 'Run Model' tab elements:

.. highlight:: none

::

    Note: Context help is always available by hovering the cursor over an element.

*  Element 1 - Tab Selection
    Tabs to select areas of the GUI.

::

    Note: The 'Results' tab is not currently active.

*  Element 2 - Input Batch File
    Allows the user to select the Input Batch File.  The Input Batch File is a standard OMEGA input file that describes the complete parameters for a model run.  The Input Batch File may be selected from the file menu or the "..." button within the element field.  When the Input Batch File is selected, the complete path will be displayed.  Hovering the cursor over the complete path will display just the base file name.

*  Element 3 - Output Batch Directory
    Allows the user to select the Output Batch Directory.  The Output Batch Directory instructs OMEGA where to store the results of a model run.  The Output Batch Directory may be selected from the file menu or the folder button within the element field.  When the Output Batch Directory is selected, the complete path be displayed.  Hovering the cursor over the complete path will display just the base file name.

*  Element 4 - Project Description
    Allows the user to enter any useful text that will be saved in an optional Configuration File for future reference.  This element is free format text to allow standard functions (such as copy and paste) to be used.  The saved text will be displayed whenever the Configuration File is opened.

*  Element 5 - Event Monitor
    The Event Monitor prompts the user during model run setup (file selection, etc.) and keeps a running record of OMEGA model execution in real time.  This is a standard text field to allow simple copying of text as needed for further study or debugging purposes. Log files are also produced in the batch and session output folders as the model runs, in fact the Event Monitor echoes these files as the model runs.

*  Element 6 - Run Model
    When everything is properly configured, this button will be enabled for initiation of the OMEGA model run.

Running the Demo Example
^^^^^^^^^^^^^^^^^^^^^^^^
The elements required to run the model are loaded by creating a new model run, or by using an existing Configuration File.  As this is the first time the Demo Example will be run, a new model run will be created.

::

    Note: The Event Monitor will provide additional guidance through the model loading process.

Creating a New Model Run From The Demo Example
----------------------------------------------
* Select the 'Run Model' tab.
* Load an existing OMEGA Input Batch File using the file menu or button within the field.  (Required)
* Select a new or existing OMEGA Output Batch Directory using the file menu or button within the field.  (Required)
* Add a Project Description.  (Optional)
* Use the file menu to save the new Configuration File.  (Optional)

The 'Run Model' tab will look similar to :numref:`ug_label3` below.  The displayed values represent one of the supplied demonstration model configurations.

Existing Configuration File
---------------------------
If a model run configuration was previously saved, the configuration may be reloaded to simplify repeating runs.  From the file menu, select 'Open Configuration File' to launch a standard File Explorer window to load an existing Configuration File.  When properly loaded, the 'Run Model' tab will look similar to :numref:`ug_label3` below.  The displayed values represent one of the supplied demonstration model configurations.

.. _ug_label3:
.. figure:: _static/gui_figures/gui_model_loaded.jpg
    :align: center

    Configuration File Loaded

Set Model Run Options
+++++++++++++++++++++
Selecting the 'Options' tab will show a display similar to :numref:`ug_label11` below.

.. _ug_label11:
.. figure:: _static/gui_figures/gui_options_page.jpg
    :align: center

    GUI Options Tab Display

The OMEGA model can be optionally configured to utilize multiple system processors for true multitasking that significantly reduces model completion time. Checking the 'Enable Multiprocessor' box instructs OMEGA to use multiprocessor mode. The 'Multiprocessor Help' button provides additional information.

The Event Monitor will indicate multiprocessor availability during GUI launch as shown in :numref:`ug_label1` above.

To use the Multiprocessor mode, a batch file customized to the configuration
of this computer must be executed before the GUI is launched.

Example Multiprocessor Batch File:

::

    ECHO OFF

    REM set BASEPATH to the python install on your machine that has dispy installed
    set BASEPATH=C:\dev\GitHub\EPA_OMEGA_Model\venv\

    REM location of python.exe (in Scripts path for venvs, else in basepath for straight install):
    set PYTHONPATH=%BASEPATH%Scripts\

    REM location of dispy package:
    set DISPYPATH=%BASEPATH%Lib\site-packages\dispy\

    REM how many cpus to serve (e.g. number of cores minus one)
    set NUM_CPUS=7

    ECHO ON
    "%PYTHONPATH%python" "%DISPYPATH%dispynode.py" --clean --cpus=%NUM_CPUS% --client_shutdown --ping_interval=15 --daemon --zombie_interval=1

.. _ug_run_the_model:

Running the Model
-----------------
With all of the model requirements loaded, select the 'Run Model' tab and the 'Model Run' button will be enabled.  Press the 'Model Run' button to start the model run.

As the model is running, the 'Run Model' tab will look similar to :numref:`ug_label4` below.

.. _ug_label4:
.. figure:: _static/gui_figures/gui_model_running.jpg
    :align: center

    Model Running

The GUI provides real time information during the model run:

* The model starting information is detailed in the event monitor.  This includes the time and Input Batch File used.
* The model status, error count, and elapsed time from model start are continuously updated adjacent to the 'Run Model' button.
* The load on the system CPU and system Memory is monitored in the Windows Status Bar at the bottom of the GUI window.
* The Event Monitor provides a continuous stream of information gathered from the simultaneous OMEGA processes.

When the model run is completed, the 'Run Model' tab will look similar to :numref:`ug_label5` below.

.. _ug_label5:
.. figure:: _static/gui_figures/gui_model_complete.jpg
    :align: center

    Model Completed

Final GUI Data:

* The model ending information is detailed in the event monitor.  This includes the time and the Output Batch Directory used.
* The model status and final model run time are displayed adjacent to the 'Run Model' button.

Interpreting the Demo Example Results
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Each session folder has an ``out`` folder which contains a number of default outputs.  The outputs fall into three categories described in this section: image file outputs, detailed outputs in csv-formatted text files, and a run log text file.

.. _gui_label_graphical_output:

Auto-generated image file outputs
---------------------------------

While the detailed modeling results are primarily recorded in csv-formatted text files (described in :numref:`gui_label_csv_output_files`), OMEGA also produces a number of standard graphical image outputs. This lets the user quickly and easily review the results, without requiring any further post-processing analyses. The various types of auto-generated images are listed in :numref:`gui_label_table_default_image_outputs`.

.. _gui_label_table_default_image_outputs:
.. csv-table:: Image File Outputs (``.png``)
    :widths: auto
    :header-rows: 1

    Abbreviated File Name, File Description
    ...Cert Mg v Year...png,"compliance including credit transfers, initial and final compliance state"
    ...Shares.png,"absolute market share by market category, market class, regulatory class and context size class"
    ...V Cert CO2e gpmi...png,"sales-weighted average vehicle certification CO2e g/mi by market category / class"
    ...V Tgt CO2e gpmi...png,"sales-weighted average vehicle target CO2e g/mi by market category / class"
    ...V kWh pmi...png,"sales-weighted average vehicle cert direct kWh/mi by market category / class"
    ...V GenCost...png,"sales-weighted average vehicle producer generalized cost by market category / class"
    ...V Mg...png,"sales-weighted average vehicle cert CO2e Mg by market category / class"
    ...Stock CO2 Mg.png,"vehicle stock CO2 emissions aggregated by calendar year"
    ...Stock Count.png,"vehicle stock registered count aggregated by calendar year"
    ...Stock Gas Gallons.png,"vehicle stock fuel consumed (gasoline gallons) aggregated by calendar year"
    ...Stock kWh.png,"vehicle stock fuel consumed (kWh) aggregated by calendar year"
    ...Stock VMT.png,"vehicle stock distance travelled (miles) aggregated by calendar year"

.. admonition:: Demo example: Reading the manufacturer compliance plot

    The manufacturer compliance plot provides several visual details on how the manufacturers are achieving compliance (or not) for each model year, and is a good starting point to inform the user of the model results.  An example run with the demo inputs is shown in :numref:`gui_label_figure_reading_compliance_plot`.

    .. _gui_label_figure_reading_compliance_plot:
    .. figure:: _static/gui_figures/comp_plot.png
        :align: center

        Typical manufacturer compliance plot

    The following describes the key features of this plot:

    * The Y-axis represents the total CO2e emissions, in metric tons (or Mg) for each model year.
    * The blue line and dots represent the required industry standard for each year, in metric tons (Mg).
    * The orange line represents the industry-achieved net standard after credits have been applied or carried to other model years. The orange dots represent the existence of credits banked prior to the analysis start year (they are placed on the chart to be visible, but the Mg level of the dots has no meaning.)
    * Green arrows indicate the source model year (arrow origin) and the model year in which credits have been applied (arrow end.)
    * Vertical down arrows, in red, indicate that some or all of the credits generated by that model year expired unused.
    * Red circle-x symbols indicate years that compliance was not achieved, after considering the carry-forward and carry-back of credits.

.. admonition:: Demo example: Using image files to compare policy alternative results for Context A

    In this demo example, the action alternative (Alt 1) is generally more stringent than the no-action alternative (Alt 0), so we should expect to see this difference in policy reflected in the results. :numref:`gui_label_figure_context_a_mktclass_gpmi_targets_cert` highlights some of the main differences between these two alternatives. The upper panels show the GHG targets (grams CO2e per mile), which decrease in each model year through 2030 in Alt 0, while in Alt 1 the targets are decreasing through 2050 with an accelerated rate after 2041. While the GHG targets are determined at the vehicle level, the plots shown here are weighted average values for each market class. The underlying individual vehicle targets are available in the '...vehicles.csv' output file (see :numref:`gui_label_csv_output_files`) and are a function of the respective policy definitions and the attributes of the vehicles that are used in the assignment of targets. See :numref:`Policy Module` and :numref:`al_label_table_policy_alternative_inputs` for more detail on the policy definitions. For both policy alternatives, the targets are lower for vehicles in the non-hauling market category compared to hauling. Note that there is no difference in the targets between BEV and ICE vehicles within the hauling and non-hauling market categories.

    The lower panels show the :any:`certification emissions<gl_label_certification_co2e>`, which like the targets, are also expressed here in CO2e grams per mile. These values are the result of producer, consumer, and policy elements in the model run. For the less stringent Alt 0, the ICE market classes show some modest reduction in certification emissions in the earlier years, which then level off and begin increasing after 2035. For BEVs, certification levels actually begin with negative values due to the policy application of off-cycle credits; specifically, 'ac leakage' technology, as defined in the 'offcycle_credits...csv' input files. In Alt 0, upstream emissions are applied to BEV certification values beginning in 2035. The no-action policy upstream emissions rates (defined in 'policy_fuels-alt0.csv') decline from 2035 to 2040, as reflected in the declining BEV certification emissions over that timeframe. For the more stringent Alt 1, ICE certification values decrease nearly through 2050. In 2045, the available ICE technologies have been exhausted, and certification values level off at the minimum possible levels. BEV certification levels remain constant throughout for Alt 1, and reflect only off-cycle credits since there is no accounting for upstream emissions in this policy alternative.

    .. |fig_gui_mktclass_targetco2_a| image:: _static/gui_figures/demo_results_mktclass_targetco2_context-a_alt-0.png
        :scale: 50%
    .. |fig_gui_mktclass_targetco2_b| image:: _static/gui_figures/demo_results_mktclass_targetco2_context-a_alt-1.png
        :scale: 50%
    .. |fig_gui_mktclass_certco2_c| image:: _static/gui_figures/demo_results_mktclass_certco2_context-a_alt-0.png
        :scale: 50%
    .. |fig_gui_mktclass_certco2_d| image:: _static/gui_figures/demo_results_mktclass_certco2_context-a_alt-1.png
        :scale: 50%

    .. csv-table::
        :widths: auto

        |fig_gui_mktclass_targetco2_a|,|fig_gui_mktclass_targetco2_b|
        |fig_gui_mktclass_certco2_c|,|fig_gui_mktclass_certco2_d|

    .. _gui_label_figure_context_a_mktclass_gpmi_targets_cert:
    .. figure:: _static/1x1.png
        :align: center

        Target CO2 (upper) and certification CO2 (lower) for no-action (left, Alt 0) and action (right, Alt 1) policy alternatives

    :numref:`gui_label_figure_context_a_compliance` shows the compliance results for the two policy alternatives used in this demo example. The year-to-year changes in targets (blue points) reflect the CO2e grams per mile targets shown in :numref:`gui_label_figure_context_a_mktclass_gpmi_targets_cert`, as well as changes in sales and other policy elements used to calculate and scale the absolute Mg CO2e values, such as multipliers and VMT. Certification emissions (red points) generally overlay the targets in each year. Similarly, :any:`compliance emissions <gl_label_compliance_co2e>` (orange line) are aligned with certification emissions, since the strategic use of existing credits has not been implemented in the model for this demo. Minor corrections for year-over-year credit transfers are shown with the green arrows, although the magnitude of transfers is small for this demo; larger transfers would be discernible as a difference between the red points and orange line. For Alt 1, the certification emissions begin to depart from the targets in 2045. With insufficient credits to carry-forward (or carry-back) to 2045 and 2046, those two years are non-compliant (red circle-x symbols.) The remaining years, 2047-2050, have an indeterminate compliance status since the demo example was only run out to 2050, and there is still a possible opportunity to carry-back credits from future years.

    .. |fig_gui_compliance_a| image:: _static/gui_figures/demo_results_compliance_context-a_alt-0.png
        :scale: 50%
    .. |fig_gui_compliance_b| image:: _static/gui_figures/demo_results_compliance_context-a_alt-1.png
        :scale: 50%

    .. csv-table::
        :widths: auto

        |fig_gui_compliance_a|,|fig_gui_compliance_b|

    .. _gui_label_figure_context_a_compliance:
    .. figure:: _static/1x1.png
        :align: center

        Compliance results for no-action (left, Alt 0) and action (right, Alt 1) policy alternatives

    :numref:`gui_label_figure_context_a_shares` shows new vehicle shares by market class. The more stringent Alt 1 has higher BEV shares for both hauling and non-hauling market classes compared to the less stringent Alt 0. The significant increase in BEV shares in 2048 coincides with the producer’s state of non-compliance; the producer’s attempts to maximize BEV share at this time is limited by the consumer share response (defined in ‘sales_share_params-cntxt_a.csv’), and the specified limits on producer price cross-subsidization (defined in ‘demo_batch-context_a.csv’.)  BEV shares also increase in the less stringent Alt 0, although at a slower rate than the action alternative. This increase occurs smoothly as BEVs become relatively less expensive due to cost learning over time. A step-up and plateau in BEV shares from 2040 to 2044 is due to the no-action policy’s minimum production requirement values, specified in ‘required_sales_share-alt0.csv’.

    .. |fig_gui_shares_a| image:: _static/gui_figures/demo_results_mktclass_share_context-a_alt-0.png
        :scale: 50%
    .. |fig_gui_shares_b| image:: _static/gui_figures/demo_results_mktclass_share_context-a_alt-1.png
        :scale: 50%

    .. csv-table::
        :widths: auto

        |fig_gui_shares_a|,|fig_gui_shares_b|

    .. _gui_label_figure_context_a_shares:
    .. figure:: _static/1x1.png
        :align: center

        Market class shares for no-action (left, Alt 0) and action (right, Alt 1) policy alternatives

    :numref:`gui_label_figure_context_a_vehstockkeyfigures` shows some of the key results for the overall vehicle stock. For this example, the base year vehicle inputs (specified in ‘vehicles.csv’) do not contain any information about any vehicles older than age 0 (i.e. MY 2019) in the base year. Therefore, the growth trend that is exhibited in all the panels of :numref:`gui_label_figure_context_a_vehstockkeyfigures` is a function of the increasing stock of vehicles that are accounted for as the model progresses over the analysis years. If the model were run with additional data for older vehicles in the base year inputs, the curves shown in these results would appear flatter. When comparing policy alternatives, it is the incremental changes that will likely be of most interest to the user. That information can be gathered from the csv-formatted output files, as described in :numref:`gui_label_csv_output_files`. These auto-generated image files are mainly intended to provide a high-level view of the key results.

    In the first row of :numref:`gui_label_figure_context_a_vehstockkeyfigures`, the CO2e emissions results from the Effects Module are shown for the two policy alternatives. While the order of magnitude is similar to the Mg CO2e shown in the compliance plot in :numref:`gui_label_figure_context_a_compliance`, there are some important differences. First, :numref:`gui_label_figure_context_a_vehstockkeyfigures` shows the combined effects for the entire on-road stock, rather than the effects of only new vehicles. Second, the VMT assumptions used for :numref:`gui_label_figure_context_a_vehstockkeyfigures` are meant to represent the on-road usage, as a function of vehicle age, while the Mg CO2e values for the compliance plot are based on policy-defined *lifetime* VMT. Finally, the Mg CO2e values in :numref:`gui_label_figure_context_a_vehstockkeyfigures` include all CO2e emissions, direct (tailpipe) and indirect (upstream), while the interpretation of Mg CO2e in the compliance plot may vary year-to-year depending on whether the policy includes consideration of upstream emissions or not.

    The second row of :numref:`gui_label_figure_context_a_vehstockkeyfigures` shows the kWh consumed for the no-action policy (Alt 0) and the action alternative (Alt 1.) Note the difference in scale; Alt 1 electricity consumption in 2050 is more than two times Alt 0 due to the higher penetration of BEVs in the vehicle stock. Partly because of this increase in BEVs (in addition to technology added to ICE vehicles), the third row of :numref:`gui_label_figure_context_a_vehstockkeyfigures` shows gasoline consumption tapering off more dramatically for Alt 1 by 2050.

    The fourth row of :numref:`gui_label_figure_context_a_vehstockkeyfigures` shows total vehicle miles traveled (VMT) for the vehicle stock. There is no endogenous response for per-vehicle VMT included in this demo example (e.g. the VMT rebound effect), so the curves here show only minor VMT differences between policy alternatives due to the differences in overall sales.

    The final row of :numref:`gui_label_figure_context_a_vehstockkeyfigures` shows the total registered count of vehicles for each year which indicates the effect of adding new vehicles (the rate of increase in the early years) and the effect of de-registering vehicles (the rate of increase slows in later years as the de-registration rate approaches the re-registration rate).

    .. |fig_gui_vehstock_a| image:: _static/gui_figures/demo_results_mgco2e_context-a_alt-0.png
        :scale: 50%
    .. |fig_gui_vehstock_b| image:: _static/gui_figures/demo_results_mgco2e_context-a_alt-1.png
        :scale: 50%
    .. |fig_gui_vehstock_c| image:: _static/gui_figures/demo_results_kwhfuelconsumption_context-a_alt-0.png
        :scale: 50%
    .. |fig_gui_vehstock_d| image:: _static/gui_figures/demo_results_kwhfuelconsumption_context-a_alt-1.png
        :scale: 50%
    .. |fig_gui_vehstock_e| image:: _static/gui_figures/demo_results_gallonsfuelconsumption_context-a_alt-0.png
        :scale: 50%
    .. |fig_gui_vehstock_f| image:: _static/gui_figures/demo_results_gallonsfuelconsumption_context-a_alt-1.png
        :scale: 50%
    .. |fig_gui_vehstock_g| image:: _static/gui_figures/demo_results_vmt_context-a_alt-0.png
        :scale: 50%
    .. |fig_gui_vehstock_h| image:: _static/gui_figures/demo_results_vmt_context-a_alt-1.png
        :scale: 50%
    .. |fig_gui_vehstock_i| image:: _static/gui_figures/demo_results_registered_count_context-a_alt-0.png
        :scale: 50%
    .. |fig_gui_vehstock_j| image:: _static/gui_figures/demo_results_registered_count_context-a_alt-1.png
        :scale: 50%

    .. csv-table::
        :widths: auto

        |fig_gui_vehstock_a|,|fig_gui_vehstock_b|
        |fig_gui_vehstock_c|,|fig_gui_vehstock_d|
        |fig_gui_vehstock_e|,|fig_gui_vehstock_f|
        |fig_gui_vehstock_g|,|fig_gui_vehstock_h|
        |fig_gui_vehstock_i|,|fig_gui_vehstock_j|

    .. _gui_label_figure_context_a_vehstockkeyfigures:
    .. figure:: _static/1x1.png
        :align: center

        MY2020+ vehicle stock GHG emissions (1st row), kWh consumption (2nd row), gasoline consumption (3rd row), VMT (4th row) and registered count (5th row) for no-action (left, Alt 0) and action (right, Alt 1) policy alternatives

    :numref:`gui_label_figure_context_a_productionandgeneralizedcost` shows the vehicle production costs (upper panels) and producer generalized costs (lower panels) for the two policy alternatives. BEV production costs decrease at a faster rate than ICE vehicles due to cost learning (as defined in the ‘simulated_vehicles.csv’ inputs.) Still, in the less stringent no-action policy (Alt 0) BEV production costs remain higher than ICE costs throughout the analysis timeframe. That’s not true for the more stringent action alternative (Alt 1), where production cost parity is reached in 2045 as additional technology added causes ICE costs to converge with BEV costs. The lower panels of :numref:`gui_label_figure_context_a_productionandgeneralizedcost` show that producer generalized costs follow the same trends as vehicle production costs. However, there are a few important differences; First, the generalized costs in this example include the portion of fuel cost that producers assume is valued by consumers in the purchase decision (defined in ‘producer_generalized_cost.csv’), making generalized costs higher than production costs. Note that the increase in Alt 0 ICE production costs in 2035 actually corresponds to a decrease in generalized costs, as the addition of ICE technology changes the fuel consumption rates, and therefore the fuel operating costs per mile. Second, because of the difference in fuel operating costs for BEV and ICE vehicles, cost parity occurs earlier for generalized costs than for production costs.

    .. |fig_gui_vehcost_a| image:: _static/gui_figures/demo_results_mktclass_vehcost_context-a_alt-0.png
        :scale: 50%
    .. |fig_gui_vehcost_b| image:: _static/gui_figures/demo_results_mktclass_vehcost_context-a_alt-1.png
        :scale: 50%
    .. |fig_gui_vehcost_c| image:: _static/gui_figures/demo_results_mktclass_generalizedvehcost_context-a_alt-0.png
        :scale: 50%
    .. |fig_gui_vehcost_d| image:: _static/gui_figures/demo_results_mktclass_generalizedvehcost_context-a_alt-1.png
        :scale: 50%

    .. csv-table::
        :widths: auto

        |fig_gui_vehcost_a|,|fig_gui_vehcost_b|
        |fig_gui_vehcost_c|,|fig_gui_vehcost_d|

    .. _gui_label_figure_context_a_productionandgeneralizedcost:
    .. figure:: _static/1x1.png
        :align: center

        Vehicle Production Cost (upper) and Generalized Cost (lower) for no-action (left, Alt 0) and action (right, Alt 1) policy alternatives

    In this demo example, overall new vehicle sales are determined by the assumed price elasticity of demand (``-1``, as defined in ‘demo_batch-context_a’.csv’), and the change in generalized cost for vehicles relative to the analysis context. :numref:`gui_label_figure_context_a_sales` shows the sales results for the two policy alternatives. Because the no-action alternative (left panel) is the same as the context policy, the model automatically calibrates the aggregate generalized cost in each year so that overall sales volumes match the analysis context sales projections. See :numref:`Consumer Module` for more details. The right panel shows sales for the action alternative, Alt 1. Deviations from the projected sales, above and below, are the result of differences in generalized costs between the two alternatives. Prior to 2035, Alt 1 has lower generalized costs then Alt 0, so sales are higher than the context projections. After 2035, Alt 1 has higher generalized costs, so sales are lower than the context projections. :numref:`gui_label_figure_context_a_generalized_costs` shows the incremental generalized costs as derived from the ‘…summary_results.csv’ output file.

    .. |fig_gui_sales_a| image:: _static/gui_figures/demo_results_sales_context-a_alt-0.png
        :scale: 50%
    .. |fig_gui_sales_b| image:: _static/gui_figures/demo_results_sales_context-a_alt-1.png
        :scale: 50%

    .. csv-table::
        :widths: auto

        |fig_gui_sales_a|,|fig_gui_sales_b|

    .. _gui_label_figure_context_a_sales:
    .. figure:: _static/1x1.png
        :align: center

        Total new vehicle sales for no-action (left, Alt 0) and action (right, Alt 1) policy alternatives

Detailed csv-formatted text output files
----------------------------------------

While the auto-generated image files are convenient for quickly looking at high-level results, the csv-formatted output files provide a full accounting of detailed results. This includes the full range of modeled effects, both physical and monetary, as well as credit logs to provide a better understanding of producer compliance decisions, and intermediate iteration steps to help illuminate the producer-consumer modeling. The resolution of the majority of these output files is at the same level defined by the user in the run inputs; namely by producer, vehicle, and analysis year. :numref:`gui_label_csv_output_files` summarizes the complete set of csv-formatted output files.

.. _gui_label_csv_output_files:
.. csv-table:: Text File Outputs (``.csv``)
    :widths: auto
    :header-rows: 1

    Abbreviated File Name, File Description
    ...summary_results.csv,"contains the data from the image files"
    ...GHG_credit_balances.csv,"beginning and ending model year GHG credit balances by calendar year"
    ...GHG_credit_transactions.csv,"model year GHG credit transactions by calendar year"
    ...manufacturer_annual_data.csv,"manufacturer compliance and cost data by model year"
    ...vehicle_annual_data.csv,"registered count and VMT data by model year and age"
    ...vehicles.csv,"detailed base year and compliance (produced) vehicle data"
    ...new_vehicle_prices.csv,"new vehicle sales-weighted average manufacturer generalized cost data by model year"
    ...producer_consumer_iteration_log.csv,"detailed producer-consumer cross-subsidy iteration data by model year"
    ...cost_effects.csv,"vehicle-level cost effects data by model year and age"
    ...physical_effects.csv,"vehicle-level physical effects data by model year and age"
    ...tech_tracking.csv,"vehicle-level technology tracking data by model year and age"

Four of these output files, in particular, may be helpful for the user to better understand the details of the model results; ‘summary_results.csv’, ‘physical_effects.csv’, ‘cost_effects.csv’, and ‘tech_tracking.csv.’ The examples given here are meant to illustrate how these outputs can be used to quantify specific effects of the policies. A full description of the fields contained the csv output files is provided in :any:`Chapter 7<7_code_details>`.

**Summary results output file**

The ‘summary_results.csv’ output file is unique among the csv-formatted output files in that it combines results for all sessions in a batch into a single file. While some of the other output files contain significantly more detail and vehicle-level resolution, the summary file is a convenient source for some of the important key outputs, and is aggregated to a single row for each session + analysis year.

.. admonition:: Demo example: Using the 'summary_results.csv' file to compare policy alternative results for Context A

    :numref:`gui_label_figure_context_a_costs` shows vehicle production costs for the action (Alt 1) and no-action (Alt 0) policy alternatives. These values are the same as those shown in the auto-generated images in :numref:`gui_label_figure_context_a_productionandgeneralizedcost`, combined into a single plot. In the right panel, the incremental costs have been calculated from the ‘summary_results.csv’ file. The most impactful effects of the policy definitions can be seen here: in 2035, the incremental cost of Alt 1 is reduced as upstream emissions accounting is introduced in the no-action case; in 2042, the incremental cost begins to increase as the Alt 1 year-over-year stringency increases.

    .. |fig_gui_avgcost_a| image:: _static/gui_figures/demo_results_avgcost_context-a_alt-1_and_alt-0.png
        :scale: 50%
    .. |fig_gui_avgcost_b| image:: _static/gui_figures/demo_results_avgcostdelta_context-a_alt-1_minus_alt-0.png
        :scale: 50%

    .. csv-table::
        :widths: auto

        |fig_gui_avgcost_a|,|fig_gui_avgcost_b|

    .. _gui_label_figure_context_a_costs:
    .. figure:: _static/1x1.png
        :align: center

        Average per vehicle production cost: absolute costs (left), and change in costs due to the action alternative policy (right)

    :numref:`gui_label_figure_context_a_generalized_costs` shows the producer generalized costs for the action and no-action policy alternatives. As with the auto-generated image files showing generalized costs, the costs here are higher than vehicle production costs because of the example's inclusion of 5 years of fuel operating costs. The incremental generalized costs shown in the right panel are helpful for understanding the sales effects shown in Figure :numref:`gui_label_figure_context_a_sales`. In the years when the action alternative has higher generalized costs, new vehicles sales decrease relative to the analysis context projections; and when costs are lower, new vehicle sales are higher.

    .. |fig_gui_generalizedcost_a| image:: _static/gui_figures/demo_results_genralizedcost_context-a_alt-1_and_alt-0.png
        :scale: 50%
    .. |fig_gui_generalizedcost_b| image:: _static/gui_figures/demo_results_generalizedcostdelta_context-a_alt-1_minus_alt-0.png
        :scale: 50%

    .. csv-table::
        :widths: auto

        |fig_gui_generalizedcost_a|,|fig_gui_generalizedcost_b|

    .. _gui_label_figure_context_a_generalized_costs:
    .. figure:: _static/1x1.png
        :align: center

        Vehicle generalized cost: absolute costs (left), and change in costs due to the action alternative policy (right)

**Physical effects output file**

The 'physical_effects.csv' file provides details such as the quantity of GHG and criteria pollutants, fuel consumption, number of registered vehicles, and vehicle miles traveled. These data are presented at the vehicle level for all model years and ages included in the model run. For any given calendar year, the associated rows in the file represent the effects associated with the stock of registered vehicles at that time, considering new vehicles that have been sold and existing vehicles that have been re-registered. The units of each data field in the file are included in the header (i.e., the field name) for each column of data. With this file, the user can explore physical effects by vehicle ID, model year, age, calendar year, manufacturer, regulatory class, in-use fuel, or market class.

.. admonition:: Demo example: Using the 'physical_effects.csv' file to compare policy alternative results for Context A

    :numref:`gui_label_figure_context_a_co2_effects_tailpipe_upstream` shows the CO2e emissions of the action alternative (Alt 1) and the no-action policy alternative (Alt 0.) The total values are the same as in the auto-generated image outputs shown in :numref:`gui_label_figure_context_a_vehstockkeyfigures`. The csv-formatted outputs shown here allow both alternatives to be shown with a breakdown by direct (tailpipe) and indirect (upstream) emissions. The contribution of BEV upstream emissions is lower in the left panel because of the lower BEV shares for Alt 0, compared to the more stringent Alt 1 policy in the right panel. In contrast, ICE emissions (both tailpipe and upstream) taper off more in the latter years for Alt 1 due to the combination of fewer ICE vehicles in use, and greater application of technologies which reduce fuel consumption and emissions.

    .. |fig_gui_co2_effects_a| image:: _static/gui_figures/demo_results_co2_effects_context-a_alt-0.png
        :scale: 50%
    .. |fig_gui_co2_effects_b| image:: _static/gui_figures/demo_results_co2_effects_context-a_alt-1.png
        :scale: 50%

    .. csv-table::
        :widths: auto

        |fig_gui_co2_effects_a|,|fig_gui_co2_effects_b|

    .. _gui_label_figure_context_a_co2_effects_tailpipe_upstream:
    .. figure:: _static/1x1.png
        :align: center

        GHG emissions with upstream and tailpipe breakdown for no-action (left, Alt 0) and action (right, Alt 1) policy alternatives

**Technology tracking output file**

.. admonition:: Demo example: Using the 'tech_tracking.csv' file to compare policy alternative results for Context A

    :numref:`gui_label_figure_context_a_techshares` shows the shares of applied technologies at the level of resolution specified by the tech package details in the ‘simulated_vehicles.csv’ input file. While the particular details of the technology package definitions are not relevant for the purpose of this example, the differences between policy alternatives is illustrative. With the more stringent action alternative (Alt 1), BEV shares are clearly higher than in Alt 0, especially in the years approaching 2050. The technology packages with ‘turb12’ and ‘atk2’ have lower certification emissions than the packages with ‘turb11’ and ‘gdi-only’, so the transition to the more advanced packages occurs earlier in the analysis timeframe under the more stringent Alt 1, accordingly.

    .. |fig_gui_co2_techshares_a| image:: _static/gui_figures/demo_results_techshares_context-a_alt-0.png
        :scale: 50%
    .. |fig_gui_co2_techshares_b| image:: _static/gui_figures/demo_results_techshares_context-a_alt-1.png
        :scale: 50%

    .. csv-table::
        :widths: auto

        |fig_gui_co2_techshares_a|,|fig_gui_co2_techshares_b|

    .. _gui_label_figure_context_a_techshares:
    .. figure:: _static/1x1.png
        :align: center

        Technology shares for no-action (left, Alt 0) and action (right, Alt 1) policy alternatives

**Cost effects output file**

The 'cost_effects.csv' file provides all of the monetized effects associated with the physical effects described above. Like the physical effects, the monetized costs are reported on an absolute basis. However, since the user will likely be most interested in the difference in costs between two policy alternatives, it is left up to the user to take advantage of the csv-formatted outputs to calculate the values that are most useful.

.. admonition:: Demo example: Using the 'cost_effects.csv' file to compare policy alternative results for Context A

    :numref:`gui_label_figure_context_a_netcost` shows the cost elements that would be used in a societal benefits-cost analysis. The dark orange curve represents the net costs as the sum of costs for technology, GHG pollution, fuel, noise, energy security, criteria pollutants, and congestion. In the earlier years, the net costs are positive, and then changing to negative (i.e. benefits) after 2031. This tendency is due to the accounting convention used within the Effects Module, where the costs for technologies are counted at the time a new vehicle is produced, while the fuel consumption and emissions (and associated costs) accrue over the lifetime of a vehicle. This delayed response due to the turnover and use of the vehicle stock is especially evident in 2035; at this point, the incremental technology costs are dramatically reduced as the no-action alternative becomes effectively more stringent with the introduction of upstream accounting. However, the impacts on other costs (fuel, emissions, etc.) show up more gradually as the vehicle stock continually turns over with new vehicles.

    .. _gui_label_figure_context_a_netcost:
    .. figure:: _static/gui_figures/demo_results_netcosts_context-a.png
        :align: center

        Net cost, with breakdown of contributing costs, for the action alternative relative to the no-action policy

.. _gui_label_runllog_output_files:

Run log output file
----------------------------------------

.. csv-table:: Text File Outputs (``.txt``)
    :widths: auto
    :header-rows: 1

    Abbreviated File Name, File Description
    o2log...txt,"session console output"

The session log file contains console output and may provide useful information in the event of a runtime error.

.. admonition:: Post-processing Notes

    Post-compliance-modeling image files and other outputs are generated by :any:`omega_model.postproc_session`, which runs effects calculations via :any:`omega_model.effects.omega_effects`.

    The producer-consumer iteration log and new vehicle price files as well as the log file are generated and/or saved during compliance modeling rather than post-processing.


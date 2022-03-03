.. image:: _static/epa_logo_1.jpg


Model Architecture and Algorithms
=================================
OMEGA is structured around four main modules which represent the distinct and interrelated decision-making agents and system elements that are most important for modeling how policy influences the environmental and other effects of the light duty sector. This chapter begins with a description of the simulation process, including the overall flow of an OMEGA run, and fundamental data structures and model inputs. That section is followed by descriptions of the algorithms and internal logic of the `Policy Module`_, `Producer Module`_, and `Consumer Module`_, and then by a section on the approach for `Iteration and Convergence Algorithms`_ between these three modules. Finally, the accounting method is described for the physical and monetary effects in the `Effects Module`_.

Throughout this chapter, references to a demo analysis are included to provide additional specificity to the explanations in the main text. These examples, highlighted in shaded boxes, are also included with the model code. Please refer to  :numref:`ug_run_the_model` for more information on how to view and rerun the demo analysis.

Overall Simulation Process
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _simulation_scope_and_resolution:

Simulation Scope and Resolution
--------------------------------------
The model boundary of OMEGA as illustrated in :numref:`al_label_modelboundary` defines the system elements which are modeled internally, and the elements which are specified as user inputs and assumptions. The timeframe of a given analysis spans the years between analysis start and end years defined by the user. Together, the boundary and analysis timeframe define the scope of an analysis.

.. _al_label_modelboundary:

.. figure:: _static/al_figures/model_boundary.png
    :align: center

    OMEGA model boundary

.. admonition:: Demo example: Analysis timeframe

    For the demo analysis, the base year is defined as calendar year 2019. The year immediately following the base year is automatically used as the analysis start year. The analysis final year in this example is set to 2050 in the ‘demo_batch-context-X.csv’ input file. Therefore, the analysis timeframe is a 31-year span, inclusive of 2020 and 2050. The selection of 2019 as the base year is automatically derived from the last year of historical data contained in the ‘vehicles.csv’ and ‘ghg_credits.csv’ input files. These inputs describe the key attributes and counts for registered vehicles, and producers’ banked Mg CO2e credits as they actually existed. Note that for this example, base year vehicle inputs are limited to MY2019 new vehicles and their attributes. For an analysis which is intended to project the impacts of various policy alternatives on the reregistration and use of earlier model years, the base year inputs would describe the entire stock of registered vehicles, including MY2018, MY2017, etc.

.. sidebar:: Analysis start year and the base year

   The analysis start year is the first year in which modeling is performed, and is one year after a *base year* representing actual observations of key elements of the light duty sector, such as descriptions of the vehicle stock and new vehicle attributes. Due to the timing of when this base year input data becomes available (typically, 2 or more years after vehicle production and registration data is available), it is often necessary for the first analysis year to be earlier than the actual year in which the model is run.

Typically, the analysis start year will already be in the past at the time the model is run. Having the most up-to-date base year data can reduce the number of historical years that need to be modeled, although as noted in the sidebar, there are usually limits to data availability. Some overlap between the modeled and historical years may be beneficial, as it gives the user an opportunity to validate key model outputs against actual data and adjust modeling assumptions if needed.

Model inputs for the policy alternatives and analysis context projections must be available for every year throughout the analysis timeframe. Many of the input files for OMEGA, utilize a ‘start_year’ field, which allows the user to skip years with repetitive inputs if desired. In general, OMEGA will carry over input assumptions from the most recent prior value whenever the user has not specified a unique value for the given analysis year. Similarly, in cases where the user-provided input projections do not extend to the analysis end year, the value in the last specified year is assumed to hold constant in subsequent years. For example, in the demo analysis, 2045 is the last year for which input values are specified in ‘cost_factors-criteria.csv’, so OMEGA will apply the same 2045 values for 2046 through 2050.

An OMEGA analysis can be conducted at various levels of resolution depending on the user’s choice of inputs and run settings. The key modeling elements where resolution is an important consideration include vehicles, technologies, market classes, producers, and consumers.

.. sidebar:: Vehicles and Candidate Vehicles

    A modeled ‘vehicle’ in OMEGA is one that has been produced and registered for use in the analysis timeframe. This simulated vehicle production is the outcome of the model’s consideration of a large number of ‘candidate vehicle’ choices. Many of these candidates are not chosen for production, but nevertheless must be considered along with their attributes.

**Vehicle resolution:** The definition of a ‘vehicle’ in an OMEGA analysis is an important user decision that determines one of the fundamental units of analysis around which the model operates. In reality, the vehicle stock is made up of hundreds of millions of vehicles, owned and operated by a similarly large number of individuals and companies. Theoretically, a user could define the vehicle resolution down to the individual options and features applied, or even VIN-level of detail. But given limitations in computational resources, the OMEGA user will more likely define vehicles at the class or nameplate level (e.g. ‘crossover utility vehicle’, or ‘AMC Gremlin’.)  Regardless of how vehicles are represented, OMEGA will retain the details of each vehicle throughout the model (including in the outputs) at the level of resolution that the user has chosen. For example, if a user defines vehicle inputs at the nameplate level, the outputs will report nameplate level vehicle counts, key attributes, emissions rates, and physical and cost effects.

**Technology package resolution:** In OMEGA, producer decisions are made using complete packages of technologies which are integral to, and inseparable from, the definition of a candidate vehicle. In other words, a change to any of the individual technology components would result in a different candidate vehicle. The 'simulated_vehicles.csv' file contains the information for each candidate vehicle that is needed for modeling producer decisions, including the costs and emissions rates that are associated with the technology package.

**Technology component resolution:** Though the model operates using full technology packages (mentioned above), it may sometimes be helpful to track the application of particular sub-components of a package. The user can choose to add flags to the 'simulated_vehicles.csv' file to identify which types of components are present on the candidate vehicles. These flags are then used by the model to tabulate the penetration of components in the vehicle stock over time.

**Market class resolution:** The level of detail, and type of information used within the Producer and Consumer modules is different. For example, we assume that consumers are not aware of the compliance implications and detailed design choices made by the producer, unless those factors are evident in the price, availability, or key attributes of a vehicle. Therefore, consumer decisions regarding the demanded shares of vehicles are modeled based on vehicle characteristics aggregated at the market class level. The user's determination of the appropriate resolution for the market classes will depend on the chosen specification for share response modeling within the Consumer Module. Note that within the Consumer Module, while share response is modeled at the market class level, other consumer decisions (like reregistration and use) can be based on more detailed vehicle-level information.

**Producer resolution:** The producers in OMEGA are the regulated entities subject to the policy alternatives being analyzed and are responsible (together with the consumers and policy) for the decisions about the quantities and characteristics of the vehicles produced. The user can choose to model the producers either as an aggregate entity with the assumption that compliance credits are available in an unrestricted market (i.e. 'perfect trading'), or as individual entities with no trading between firms.

**Consumer resolution:** The approach to account for heterogeneity in consumers is an important consideration when modeling the interaction between producer decisions and the demand for vehicles. By taking advantage of user-definable submodules, a developer can set-up the Consumer Module to account for different responses between consumer segments.

Whatever the level of resolution, the detail provided in the inputs 1) must meet the requirements of the various modeling subtasks, and 2) will determine the level of detail of the outputs. When preparing analysis inputs, it is therefore necessary to consider the appropriate resolution for each module. For example:

* Within the Policy Module, vehicle details are needed to calculate the target and achieved compliance emissions. This might include information about regulatory classification and any vehicle attributes that are used to define a GHG standard.

* Within the Producer Module, the modeling of producer decisions requires sufficient detail to choose between compliance options based the GHG credits and generalized producer cost associated with each option.

* Within the Consumer Module, the modeling of consumer decisions requires sufficient detail to distinguish between market classes for representing both the purchase choices among different classes, and the reregistration and use of vehicles within a given class.

.. admonition:: Demo example: Modeling resolution

    .. csv-table:: How modeling resolution is defined in an OMEGA run
        :widths: auto
        :header-rows: 1

        Modeling element,Where is the resolution defined?,Description of resolution in the demo
        Vehicle resolution,vehicles.csv,51 2019 base year vehicles differentiated by context size class ('Small Crossover' 'Large Pickup' etc) manufacturer_id and electrification_class ('N' 'HEV' 'EV')
        Technology package resolution:,simulated_vehicles.csv,578088 candidate vehicles for the analysis timeframe 2020 through 2050 with technology packages for ICE and BEV powertrains
        Technology component resolution:,simulated_vehicles.csv,detailed flags for identifying technology package contents of ac_leakage ac_efficiency high_eff_alternator start_stop hev phev bev weight_reduction  deac_pd deac_fc cegr atk2 gdi turb12 turb11
        Market class resolution,consumer.market_classes.py user-definable submodule and market_classes.csv,4 classes in 2 nested levels with BEV and ICE categories within first tier hauling and non-hauling categories
        Consumer resolution,consumer.sales_share_gcam.py user-definable submodule,consumer heterogeneity is inherent in share weights used to estimate market class shares
        Producer resolution,`demo_batch-context-X.csv` and manufacturers.csv,2 producers ('OEM_A' and 'OEM_B') and 'Consolidate Manufacturers' run setting set to FALSE

Process Flow Summary
--------------------
In an OMEGA session, the model runs by looping over analysis years and  producers. Within each successive loop, the simulation of producer and consumer decisions results in new vehicles entering the stock of registered vehicles, and the reregistration and use of existing vehicles from the prior year’s stock.

As shown in :numref:`al_label_overallprocessflow` , this simulation process involves two iterative loops. In one loop, the Policy Module determines whether or not the producer’s strategic compliance target is met by the candidate production options under consideration. In the other iterative loop, the Consumer Module determines whether or not the market will accept the quantities of vehicles offered at the prices set by the producer. Both the Producer-Policy and the Producer-Consumer iterative loops must achieve convergence for the simulation to proceed. Once all the analysis years and producers have been completed, the effects calculations are performed and results are written to the output files.

.. _al_label_overallprocessflow:
.. figure:: _static/al_figures/overall_process_flow.png
    :align: center

    OMEGA process flow



Model Inputs
------------

As described in the :numref:`inputs_and_outputs_label` overview, OMEGA model inputs are grouped into two categories; *policy alternative* inputs and *analysis context* inputs. The policy alternatives define the GHG standards that are being evaluated by the model run, while the analysis context refers collectively to the external assumptions that apply to all policies under analysis.

**Policy Alternatives Inputs**

An OMEGA run requires a full description of the GHG standards themselves so that the modeled producer compliance considerations are consistent with how an EPA rule would be defined in the Federal Register and Code of Federal Regulations. As described in :numref:`Policy Module`, OMEGA is intended primarily for the analysis of fleet averaging standards, and the demo example has been set up to illustrate how accounting rules for GHG credits in a fleet averaging program can be defined. This includes the coefficients for calculating emissions rate targets (gram CO2e per mile) based on vehicle attributes, the methods for determining emissions rate certification values (e.g. drive cycle and fuel definitions, off-cycle credits), and the rules for calculating and accounting for Mg CO2e credits over time (e.g. banking and trading rules, and lifetime VMT assumptions.) See :numref:`al_label_table_policy_alternative_inputs` for a complete list of the policy alternative inputs used in the demo example.

**Analysis Context Inputs**

The analysis context defines the inputs and assumptions that the user assumes are independent of the policy alternatives. This clear delineation of exogenous factors is what enables the apples-to-apples comparison of policy alternatives within a given analysis context. This is the primary purpose for which OMEGA was designed – to quantify the incremental effects of a policy for informing policy decisions. At the same time, considering how the incremental effects of a policy might vary depending on the analysis context assumptions is a useful approach for understanding the sensitivity of the projected results to differences in assumptions.

.. admonition:: Demo example: Analysis Context inputs for 'Context A'

    The demo example includes two policy alternatives ('alt0' and 'alt1') and two sets of analysis context assumptions ('A' and 'B'.) :numref:`al_label_table_policy_context_a_inputs` shows the complete set of input files and settings for Context A as defined in the 'demo_batch-context_a.csv' file.

    .. _al_label_table_policy_context_a_inputs:
    .. csv-table:: Input files and settings for 'Context A'
        :widths: auto
        :header-rows: 1

        Analysis context element,Input file name/ Input setting value,Description
        Context Name,AEO2021,"Together with 'Context Case' setting, selects which set of input values to use from the fuel price and new vehicle market files."
        Context Case,Reference case,"Together with 'Context Name' setting, selects which set of input values to use from the fuel price and new vehicle market files."
        Context Fuel Prices File,context_fuel_prices.csv,"Retail and pre-tax price projections for any fuels considered in the analysis (e.g. gasoline, electricity.)"
        Context New Vehicle Market File,context_new_vehicle_market.csv,"Projections for new vehicle key attributes, sales, and mix under the analysis context conditions, including whatever policies are assumed."
        GHG Credits File,ghg_credits.csv,"Balance of existing banked credits, by model year earned."
        Manufacturers File,manufacturers.csv,"List of producers considered as distinct entities for GHG compliance. When 'Consolidate Manufacturers' is set to TRUE, in the batch input file, 'consolidated_OEM' value is used for all producers."
        Market Classes File,market_classes.csv,Market class ID's for distinguishing vehicle classes in the Consumer Module.
        New Vehicle Price Elasticity of Demand,-1,Scalar value of the price elasticity of demand for overall new vehicle sales.
        Onroad Fuels File,onroad_fuels.csv,Parameters inherent to fuels and independent of policy or technology (e.g. carbon intensity.)
        Onroad Vehicle Calculations File,onroad_vehicle_calculations.csv,Multiplicative factors to convert from certification energy and emissions rates to onroad values.
        Onroad VMT File,annual_vmt_fixed_by_age.csv,Annual mileage accumulation assumptions for estimating vehicle use in Consumer and Effects modules
        Producer Cross Subsidy Multiplier Max,1.05,Upper limit price multiplier value considered by producers to increase vehicle prices though cross subsidies.
        Producer Cross Subsidy Multiplier Min,0.95,Lower limit price multiplier value considered by producers to decrease vehicle prices though cross subsidies.
        Producer Generalized Cost File,producer_generalized_cost.csv,Parameter values for the producers generalized costs for compliance decisions (e.g. the producers view of consumers consideration of fuel costs in purchase decisions.)
        Production Constraints File,production_constraints-cntxt_a.csv,Upper limits on market class shares due to constraints on production capacity.
        Sales Share File,sales_share_params-cntxt_a.csv,Parameter values required to specify the demand share estimation in the Consumer Module.
        Vehicle Price Modifications File,vehicle_price_modifications-cntxt_a.csv,Purchase incentives or taxes/fees which are external to the producer pricing decisions.
        Vehicle Reregistration File,reregistration_fixed_by_age.csv,"Proportion of vehicles reregistered at each age, by market class."
        Vehicle Simulation Results and Costs File,simulated_vehicles.csv,Vehicle production costs and emissions rates by technology package and cost curve class.
        Vehicles File,vehicles.csv,The base year vehicle stock and key attributes. Note that the demo example contains MY2019 vehicles. Prior model years could also be included if needed for stock and use modeling.
        Context Criteria Cost Factors File,cost_factors-criteria.csv,The marginal pollution damages per unit mass from criteria pollutant emissions.
        Context SCC Cost Factors File,cost_factors-scc.csv,The marginal costs per unit mass from GHG emissions (i.e. Social Cost of Carbon.)
        Context Energy Security Cost Factors File,cost_factors-energysecurity.csv,The marginal energy security cost per unit of fuel consumption.
        Context Congestion-Noise Cost Factors File,cost_factors-congestion-noise.csv,The marginal cost per mile of noise and congestion from changes in VMT.
        Context Powersector Emission Factors File,emission_factors-powersector.csv,The marginal cost per kWh of upstream emissions from electricity generation.
        Context Refinery Emission Factors File,emission_factors-refinery.csv,The marginal cost per gallon upstream emissions from fuel refining.
        Context Vehicle Emission Factors File,emission_factors-vehicles.csv,The marginal cost per mile of direct emissions (i.e. tailpipe emissions) from changes in VMT.
        Context Implicit Price Deflators File,implicit_price_deflators.csv,Factors for converting costs to a common dollar basis.
        Context Consumer Price Index File,cpi_price_deflators.csv,Factors for converting costs to a common dollar basis.

.. admonition:: Demo example: Unique Analysis Context inputs for 'Context B'

    While most of the example input files are common for contexts ‘A’ and ‘B’, in cases where context assumptions vary, input files are differentiated using ‘context_a’ and ‘context_b’ in the file names. :numref:`al_label_table_policy_context_b_unique_inputs` shows the input files and settings that are unique for Context B as defined in the in the ‘demo_batch-context_b.csv’ file.

    .. _al_label_table_policy_context_b_unique_inputs:
    .. csv-table:: Input files and setting differences between contexts 'A' and 'B'
        :widths: auto
        :header-rows: 1

        Analysis context element,Input file name/ Input setting value,Difference between contexts 'A' and 'B'
        Context Case,High oil price,"Taken from AEO2021, Context A uses the Reference Case fuel prices and Context B uses the 'High oil price' case fuel prices."
        Producer Cross Subsidy Multiplier Max,1.4,Context B uses a higher upper limit price multiplier value compared to the 1.05 value for Context A.
        Producer Cross Subsidy Multiplier Min,0.6,Context B uses a reduced lower limit price multiplier value compared to the 0.95 value for Context A.
        Production Constraints File,production_constraints-cntxt_b.csv,"Context B has a linearly increasing maximum production constraint for BEVs from 2020 to 2030, compared to Context A which has no production limits specified in that timeframe."
        Sales Share File,sales_share_params-cntxt_b.csv,"Context B has BEV share weight parameters for the Consumer Module which represent a logistic function that increases earlier, reaching a value of 0.5 in 2025 instead of 2030 in Context A. In other words, Context B represents greater consumer demand for BEVs, all else equal."
        Vehicle Price Modifications File,vehicle_price_modifications-cntxt_b.csv,"Context B introduces an external BEV purchase incentive of $10,000 in 2025, which decreases to $5,000 in 2027, and then linearly to zero in 2036 compared to Context A which has no purchase incentives in this timeframe."

Projections and the Analysis Context
------------------------------------
The output of an OMEGA run is a modeled projection of the future. While this projection should not be interpreted as a single point prediction of what will happen, it does represent a forecast that is the result of the modeling algorithms, inputs, and assumptions used for the run. Normally, these modeled projections of the future will vary from year-to-year over the analysis timeframe due to year-to-year changes in the policy, as well changes in producer decisions due to considerations of compliance strategy, credit utilization, and production constraints. Another reason that results in future are not constant from one year to the next is because the exogenous factors in the analysis context are themselves projections of the future, and any year-to-year changes in those factors will influence the model results.

It is important that we consider the relationship between these exogenous projections and the factors being modeled internally within OMEGA to avoid inconsistencies. Three situations are described here, along with an explanation for how the model integrates external projections in a consistent manner.

**Projections that are purely exogenous**

Input projections for items that are assumed to be not influenced at all by the policy response modeled within OMEGA are left as specified in the inputs. Examples might include projections of fuel prices, the state of available technology, or upstream emissions factors. While in reality these things might be influenced by the policy alternatives, we are assuming complete independence for modeling purposes, and no additional special treatment is needed for consistency.

.. sidebar:: Context policy

    Among the range of assumptions that define the analysis context is an assumption about the light-duty vehicle emissions policy. This is defined as the *context policy*, and is necessarily the first policy alternative session that must be run in order to ensure that the modeled results are consistent with the analysis context.

**Calibrating to projected elements that are also modeled with policy influences**

Both the consumer and producer decisions will influence the modeled new vehicle sales and attributes; for example, new vehicle prices, overall sales, sales mix, technology applications, emissions rates and fuel consumption rates. While some of these elements might not be within the scope of the input projections, when a projected element is also modeled as being responsive to policy, OMEGA uses a calibration approach to maintain consistency. Specifically, after calibration, the results of a model run using the context policy will produce results that match the projections in the analysis context. If that were not the case, results for any other policy alternatives could deviate in unrealistic ways from the underlying projections.

.. admonition:: Demo example: Overall sales projections and the context policy

    The overall sales level is an item that is both specified as a projection in the context inputs, and is also modeled internally as responsive to changes in vehicle prices, fuel operating costs, etc. In each batch run (each batch contains two or more policy alternatives), OMEGA automatically calibrates the overall average new vehicle prices in the first session, which represents the context policy. This calibration process ensures that overall sales match the context projected sales by generating calibrated new vehicle prices (P) which are associated with the context. In subsequent sessions of the batch run for the other policy alternatives, these calibrated prices are used as the basis to which any price changes are applied (the P in equation :eq:`al_label_eqn_demand_elasticity`.)

**Elements not explicitly projected in new vehicle market inputs**

Some elements related to vehicle attributes and sales mix may be neither part of the projection inputs nor modeled internally, yet still be important to consider in the future projections. In these cases, base year vehicle fleet attributes and relative mix characteristics are assumed to hold constant into the future.

.. admonition:: Demo example: Projections for new vehicle size class mix

    In the demo example, overall new vehicle sales projections are taken as purely exogenous. The ‘context_new_vehicle_market.csv’ file specifies the sales mix projections from AEO though 2050 by size class. As shown in :numref:`al_label_fig_context_projections_size_class_share`, the projected sales mix of size classes varies by year, and between Context A and Context B.

    .. _al_label_fig_context_projections_size_class_share:
    .. figure:: _static/al_figures/context_projections_size_class_share_by_context_a_b.png
        :align: center

        Exogenous projections of size class from ‘context_new_vehicle_market.csv’

    All vehicle attributes which are not explicitly projected exogenously and not modeled internally are held constant from the base year fleet. For example, while size class projections are provided for overall new sales in each year, the projections are not defined at the individual producer level. Therefore, MY2019 base year relative shares of size classes for each producer are assumed to hold constant in the future. As shown in the left bar chart of :numref:`al_label_fig_context_projections_applied_to_base_year_oem_a_b`, in MY2019 OEM A was more heavily focused on the Large Pickup, Small Utility, and Small Crossover classes, while OEM B was more heavily focused on the Large Utility and Midsize car classes. These relative differences between producers are maintained in the model during the process of applying the size class projections for new sales overall to the individual vehicle projections, and their associated producers, in the base year. The result is shown on the right of Figure :numref:`al_label_fig_context_projections_applied_to_base_year_oem_a_b`. The combined sales of OEM A and OEM B will match the overall new sales size class shares from :numref:`al_label_fig_context_projections_size_class_share`, while retaining the relative tendency for OEM A and OEM B to produce different size class mixes.

    .. _al_label_fig_context_projections_applied_to_base_year_oem_a_b:
    .. figure:: _static/al_figures/context_projections_applied_to_base_year_oem_a_b.png
        :align: center

        Context size class projections applied to MY2019 base year vehicles

.. _Policy Module:

Policy Module
^^^^^^^^^^^^^
OMEGA's primary function is to help evaluate and compare policy alternatives which may vary in terms of regulatory program structure and stringency. Because we cannot anticipate all possible policy elements in advance, the code within the Policy Module is generic, to the greatest extent possible. This leaves most of the policy definition to be defined by the user as inputs to the model. Where regulatory program elements cannot be easily provided as inputs, for example the equations used to calculate GHG target values, the code has been organized into user-definable submodules. Much like the definitions recorded in the Code of Federal Regulations (CFR), the combination of inputs and user-definable submodules must unambiguously describe the methodologies for determining vehicle-level emissions targets and certification values, as well as the accounting rules for determining how individual vehicles contribute to a manufacturer's overall compliance determination.


:numref:`al_label_plcym_ov` shows the flow of inputs and outputs for the Policy Module. As shown in this simple representation, the vehicle GHG targets and achieved certification values are output from the module, as a function of the attributes of candidate vehicles presented by the Producer Module.

.. _al_label_plcym_ov:
.. figure:: _static/al_figures/policymod_ov.png
    :align: center

    Overview of the Policy Module

Throughout OMEGA, *policy alternatives* refer only to the regulatory options that are being evaluated in a particular model run. There will also be relevant inputs and assumptions which are technically policies but are assumed to be fixed (i.e. exogenous) for a given comparison of alternatives. Such assumptions are defined by the user in the *analysis context*, and may reflect a combination of local, state, and federal programs that influence the transportation sector through regulatory and market-based mechanisms. For example, these exogenous context policies might include some combination of state-level mandates for zero-emissions vehicles, local restrictions or fees on ICE vehicle use, state or Federal vehicle purchase incentives, fuel taxes, or a carbon tax. A comparison of policy alternatives requires that the user specify a no-action policy (aka context policy) and one or more action alternatives.

Policy alternatives that can be defined within OMEGA fall into two categories: those that involve fleet average emissions standards with compliance based on the accounting of credits, and those that specify a required share of a specific technology. OMEGA can model either policy type as an independent alternative, or model both types together; for example, in the case of a policy which requires a minimum share of a technology while still satisfying fleet averaging requirements.

**Policy alternatives involving fleet average emissions standards:**
In this type of policy, the key principle is that the compliance determination for a manufacturer is the result of the combined performance of all vehicles, and does not require that every vehicle achieves compliance individually. Fleet averaging in the Policy Module is based on CO2 *credits* as the fungible accounting currency. Each vehicle has an emissions target and an achieved certification emissions value. The difference between the target and certification emissions in absolute terms (Mg CO2) is referred to as a *credit*, and might be a positive or negative value that can be transferred across years, depending on the credit accounting rules defined in the policy alternative. The user-specified policy inputs can be used to define restrictions on credit averaging and banking, including limits on credit lifetime or the ability to carry a negative balance into the future. The analogy of a financial bank is useful here, and OMEGA has adopted data structures and names that mirror the familiar bank account balance and transaction logs.

OMEGA is designed so that within an analysis year, under an unrestricted *fleet averaging* policy, credits from all the producer’s vehicles are counted without limitations towards the producer’s credit balance. Vehicles with positive credits may contribute to offset other vehicles with negative credits. The OMEGA model calculates overall credits earned in an analysis year as the difference between the aggregate certification emissions minus the aggregate target emissions. An alternative approach of calculating overall credits as the sum of individual vehicle credits is unnecessary and in some cases may not be possible. To give one example, if a policy applies any constraints on the averaging or transfer of credits, it would not be possible to determine compliance status simply by counting each vehicle’s credit contribution fully towards the overall credits.

The transfer of credits between producers can be simulated in OMEGA by representing multiple regulated entities as a hypothetical 'consolidated' producer, under an assumption that there is no cost or limitation to the transfer of compliance credits among entities. OMEGA is not currently designed to explicitly model any strategic considerations involved with the transfer of credits between producers.

Emissions standards are defined in OMEGA using a range of policy elements, including:

* rules for the accounting of upstream emissions
* definition of compliance incentives, like multipliers
* definition of regulatory classes
* definition of attribute-based target function
* definition of the vehicles’ assumed lifetime miles

.. admonition:: Demo example: Input files for no-action and action policy definitions

    .. _al_label_table_policy_alternative_inputs:
    .. csv-table:: Description of Policy Alternative input files
        :widths: auto
        :header-rows: 1

        Policy element, No-action policy [Action policy] input files, Description
        Drive cycles, drive_cycles-alt0[alt1].csv; drive_cycle_weights-alt0[alt1].csv, Drive cycle ID's and weights for calculating weighted average emissions from certification tests.
        Fuels, policy_fuels-alt0[alt1].csv, Direct and indirect CO2 values used in certification calculations for each fuel.
        GHG credit rules, ghg_credit_params-alt0[alt1].csv, Credit carry-forward and carry-back rules.
        GHG targets, ghg_standards-alt0[alt1].csv, Formula definitions for calculating g CO2/mi targets from vehicle attributes and regulatory classes. Also includes lifetime VMT assumptions.
        Offcycle credits, offcycle_credits-alt0[alt1].csv, Offcycle credit values for specific technologies.
        Upstream emissions accounting, policy_fuel_upstream_methods-alt0[alt1].csv, Selection of which methods to use for the calculation of indirect emissions certification values.
        Advanced technology multipliers, production_multipliers-alt0[alt1].csv, Values for multipliers used in credit calculations to incentivize the introduction of specific technologies.
        Reg classes, regulatory_classes-alt0[alt1].csv, Regulatory class ID's and descriptions.
        Technology mandates, required_sales_share-alt0[alt1].csv, Minimum required production shares as required by the policy.

**Policy alternatives requiring specific technologies:**
This type of policy requires all, or a portion, of a producer’s vehicles to have particular technologies. OMEGA treats these policy requirements as constraints on the producer’s design options. This type of policy alternative input can be defined either separately, or together with a fleet averaging emissions standard; for example, a minimum Zero Emission Vehicle (ZEV) share requirement could be combined with an emissions standard where the certification emissions associated with ZEVs are counted towards the producer’s achieved compliance value.

**Policy representation in the analysis context:**
Some policies are not modeled in OMEGA as policy alternatives, either because the policy is not aimed directly at the producer as a regulated entity, or because the particular OMEGA analysis is not attempting to evaluate the impact of that policy relative to other alternatives. However, even when a policy is not reflected in any of the analyzed policy alternatives, it may still be appropriate to represent that policy in the Analysis Context inputs. This is especially true when that external policy (or policies) might significantly influence the producer or consumer decisions. Some examples include:

* Fuel tax policy
* State and local ZEV policies
* Vehicle purchase incentives
* Investment in refueling and charging infrastructure
* Accelerated vehicle retirement incentives

.. _Producer Module:

Producer Module
^^^^^^^^^^^^^^^
Producer Module Overview
------------------------
The modeling of producer decisions is central to the optimization problem that OMEGA has been developed to solve. In short, the objective is to minimize the producers' generalized costs subject to the constraints of regulatory compliance and consumer demand. The ‘producer’ is defined in OMEGA as a regulated entity that is subject to the policy alternatives being modeled, and responsible for making decisions about the attributes and pricing of new vehicles offered to consumers. A user might choose to model producers as an individual manufacturer of light duty vehicles, as a division of a single manufacturer, or as a collection of manufacturers. This choice will depend on the goals of the particular analysis, and what assumptions the user is making about the transfer of compliance credits within and between manufacturers.

:numref:`al_label_pm_ov` shows the flow of inputs and outputs for the Producer Module. Analysis context inputs are not influenced by the modeling within the Consumer, Producer, and Policy Modules, and are therefore considered as exogenous to OMEGA.

.. _al_label_pm_ov:
.. figure:: _static/al_figures/producermod_ov.png
    :align: center

    Overview of the Producer Module

**Inputs to the Producer Module:** Policy Alternative inputs are used to calculate a compliance target for the producer (in Mg CO2) for a given analysis year using the provided attribute-based vehicle GHG targets, vehicle regulatory class definitions, and assumed lifetime VMT for compliance. Other policy inputs may define, for example, the credit lifetime for carry-forward and carry-back, or a floor on the minimum share of ZEV vehicles produced.

Analysis context inputs and assumptions that the Producer Module uses define all factors, apart from the policies under evaluation, that influence the modeled producer decisions. Key factors include the vehicle costs and emissions for the technologies and vehicle attributes considered, and the producer constraints on pricing strategy and cross-subsidization.

During the iteration process, shares of new vehicles demanded are generated by the Consumer Module as inputs to the Producer Module. These shares are at the market class-level, and based on the prices and attributes of the candidate vehicles offered by the producer in that iteration. See :numref:`Iteration and Convergence Algorithms` for a description of the iteration and convergence algorithms.

**Outputs of the Producer Module:** During the iteration process, the outputs of the Producer Module describe the candidate vehicles -- prices, quantities, and key attributes -- which forms the basis for determining compliance status (by iterating with the Policy Module) and demanded sales shares (by iterating with the Consumer Module.) Once model convergence is achieved, the Producer Module outputs the details of the produced vehicles.

.. _producer_compliance_strategy_section:

Producer Compliance Strategy
----------------------------
The Producer Module simulates decisions about vehicle design, pricing, and production quantities that minimize compliance costs while satisfying other considerations imposed by the policy, consumers, and production constraints. With a fleet averaging policy that allows credit banking and trading, the producer is making these product decisions within an overall strategy of managing compliance credits from year-to-year.

**Vehicle design strategy**


.. sidebar:: The producer's view of consumers

    The producer, as an independent decision-making agent, will not have perfect information about the internal consumer decision process. Within the Producer Module, OMEGA allows the user to define the consumer decisions from the producer’s perspective, which may be different from (or the same as) the representation within the Consumer Module.

While the producer’s modeled objective function is cost minimization, the term ‘cost’ is used generically here, as it is not necessarily the case that the lowest production cost option is the best option for the producer. Consumer willingness to pay for a particular vehicle attribute can result in another choice if the producer expects that the additional production costs can be more than offset by a higher price. Here, the term *producer generalized costs* is defined as the net of vehicle production costs and the producer’s view of consumer’s willingness to pay for that vehicle.

The Producer Module will first attempt to select the available vehicle design options (i.e. tech package applications) and sales mix that minimizes generalized costs while meeting the strategic compliance target (Mg CO2e.) This is the starting point of an iterative process, since in many cases the demand estimated by the Consumer Module will not match this first set of vehicle attributes, prices, and quantities within the desired convergence tolerance.

**Vehicle pricing and sales mix strategy**

In addition to influencing key vehicle attributes by the design decisions, the producer also has some flexibility in how vehicle prices are set. Using cross-subsidization strategies to spur greater sales of some vehicles at the expense of others, producers can incentivize market class sales mix changes in order to reduce generalized costs. This assumption that producers will attempt to minimize their generalized costs is consistent with a producer goal of profit maximization.

In reality, there are limits to the ability of producers to adjust vehicle prices. The user can define upper and lower limits to how much price cross-subsidization can be applied. Also, the model automatically only searches for solutions that maintain the overall average vehicle price, thus forcing any cross-subsidization strategies to be revenue neutral.

**Credit management strategy**

With a policy that allows credit banking, the efficient management of compliance credits from year-to-year involves a degree of look-ahead, both in terms of expected changes in regulatory stringency and other policies, and expected changes in generalized costs over time. At this time, OMEGA assumes that producers aim to meet the GHG target in each year, with any banked credits used only to make up differences between the certification and target values. The producer logic associated with the process box labeled “Determine Strategic Target Offset” in the process flow diagram (:numref:`al_label_overallprocessflow`) therefore simply applies the offset, if any, to the policy GHG target. In a future revision, we plan to consider incorporating producer decisions that are intentionally under- or over-target based on the assumption that producers make strategic decisions looking beyond the immediate present to minimize generalized costs over a longer time horizon.

Vehicle Definitions
-------------------
The vehicle is the fundamental unit of analysis within the Producer Module, and the decisions made by producers determine the vehicle attributes and sales in the modeled results. The vehicle resolution is determined by the user (see :numref:`simulation_scope_and_resolution`) consistent with the resolution defined in the base year vehicles input file.  Depending on the focus of a particular run, vehicles might be defined at a market class level using an aggregate representation over multiple producers, or at the nameplate or even subconfiguration level.

Along with a definition of resolution, the base year vehicles inputs also define the key exogenous attributes that are necessary for 1) generating future projections, 2) assigning the policy emissions targets, 3) estimating consumer demanded quantities, 4) determining appropriate emissions rates and costs from the applied technology packages.

.. admonition:: Demo example: Vehicle definitions in base year fleet

    .. _al_label_table_key_base_year_attributes_and_uses:
    .. csv-table:: Key base year vehicle attributes and their uses from 'vehicles.csv'
        :widths: auto
        :header-rows: 1

        Field Name,Attribute Required For:,Example 1,Example 2,Example 3,Example 4
        vehicle_name,tracking of producer decisions in modeled results,ICE Large car,ICE Large Crossover truck,ICE-HEV Large Pickup truck 4WD,ICE Large Van truck minivan 4WD
        manufacturer_id,grouping for producer modeling,OEM_B,OEM_A,OEM_A,OEM_A
        model_year,determination of analysis start year,2019,2019,2019,2019
        reg_class_id,reference (assigned by policy in analysis timeframe),car,truck,truck,truck
        epa_size_class,reference,Large Cars,Standard SUV 2WD,Standard Pick-up Trucks 4WD,"Special Purpose Vehicle, minivan 4WD"
        context_size_class,sales mix projections,Large,Large Crossover,Large Pickup,Large Van
        electrification_class,reference (modeled element in analysis timeframe),N,N,HEV,N
        cost_curve_class,cost and emissions rates for tech packages,ice_MPW_LRL,ice_MPW_HRL,ice_Truck,ice_MPW_HRL
        in_use_fuel_id,reference (modeled element in analysis timeframe),{'pump gasoline':1.0},{'pump gasoline':1.0},{'pump gasoline':1.0},{'pump gasoline':1.0}
        cert_fuel_id,reference (modeled element in analysis timeframe),{'gasoline':1.0},{'gasoline':1.0},{'gasoline':1.0},{'gasoline':1.0}
        sales,sales mix projections,536531,496834,78297,13795
        cert_direct_oncycle_co2e_grams_per_mile,reference (modeled element in analysis timeframe),345.3,418.6,405.8,403.0
        cert_direct_oncycle_kwh_per_mile,reference (modeled element in analysis timeframe),0,0,0,0
        footprint_ft2,policy targets ('Alternative 0' only),50.5,54.7,68.5,56.0
        eng_rated_hp,reference (modeled element in analysis timeframe),268,318,364,296
        tot_road_load_hp,reference (modeled element in analysis timeframe),12.5,16.1,19.3,17.3
        etw_lbs,reference (modeled element in analysis timeframe),4035,5095,5518,5000
        length_in,reference,195.3,201.6,231.6,200.6
        width_in,reference,73.8,78.0,80.6,78.1
        height_in,reference,58.2,71.1,77.0,70.4
        ground_clearance_in,reference,5.2,8.3,,6.5
        wheelbase_in,reference,114.0,118.4,143.1,119.3
        interior_volume_cuft,reference,,148.3,,
        msrp_dollars,reference (modeled element in analysis timeframe),42554,46592,40740,39962
        passenger_capacity,policy targets ('Alternative 1' only),5.0,6.6,5.5,7.0
        payload_capacity_lbs,reference,1030,1438,1748,
        towing_capacity_lbs,reference,1000,5598,10509,3500
        unibody_structure,reference,1,1,0,1


Vehicle Simulation and Cost Inputs
------------------------------------------
One of the most important sets of inputs to the Producer Module is the simulated vehicles file. It contains the vehicle parameters used by OMEGA to generate all possible vehicle technology (and cost) options available to the producers – these production options represent distinct points in what might be considered a point 'cloud'. The use of these vehicle clouds by OMEGA is described in :numref:`veh clouds section`.

The simulated vehicle file contains the various vehicles of different core attributes (such as vehicle size, weight, powertrain, etc), the CO2-reducing technologies that are applied to each, and their predicted energy consumption, CO2 performance, and cost. While not required by all users, EPA uses its own simulation tool (ALPHA) to predict the energy consumption and CO2 emissions for each vehicle and technology combination. For the demo, these vehicle and technology options (and associated CO2 performance) are consolidated into the 'simulated_vehicles.csv' file. The simulated vehicles file contains the following fields for use in the Producer Module:

* the associated **cost curve class** (defined by powertrain family and described below)
* vehicle properties such as curb weight, type of base powertrain (ICE/HEV/PHEV/BEV, etc)
* other included technologies (e.g., A/C credits, high efficiency alternator, etc)
* test cycle performance (energy consumption (for plug-in vehicles) and/or CO2 emissions)
* vehicle attributes, such as included technologies, costs

**Significance of the cost curve class:**
Each cost curve class includes multiple vehicles and represents the design space for all vehicle options in each class. In the demo, multiple vehicles are grouped within a single cost curve class to reduce the number of simulations required to represent the design space. OMEGA producer decisions are made based on discrete vehicle options within each vehicle cost curve class. For possible future consideration, EPA recommends the generation of RSEs (response surface equations) to derive particular cost clouds unique to each vehicle. This would allow for more unique cost and vehicle clouds without excessive simulation calculation burden.

.. _veh clouds section:

Vehicle Cost Clouds, Cost Curves, and Aggregation
-------------------------------------------------

The technology packages and their application to candidate vehicles are described in the model inputs as a discrete set of options that were generated using tools and approaches external to OMEGA (e.g. vehicle simulation, benchmarking, cost teardowns, etc.) Because the product design problem being solved is multi-dimensional (i.e. an intersection of technology package applications and market share decisions for multiple vehicles), the choice set must be built up from various combinations of vehicle-level decisions that cannot be readily predicted in advance.

The Producer Module uses an approach of aggregating the discrete, vehicle-level decisions at several levels, while retaining the vehicle-specific information that can be accessed later in other stages of the modeling and presented in the results. These processes of vehicle aggregation (also referred to as composition or the creation of “composite vehicles”) and decomposition are critical for the solution search process. First, aggregation allows the model to efficiently search for a solution without a complete enumeration of all possible choice combinations. Second, decomposition allows the model to draw upon the key vehicle attribute details that have been retained and are required for calculating the compliance emissions values and estimating the consumer response.

**Vehicle-level technology application options**

In oder to minimize cost, a producer would need to select the minimum cost package available at a given compliance emissions rate (i.e. g CO2/mi.) This subset of cost-minimizing vehicle technology packages is referred to as the *cost curve*, while the broader set of points is the *cost cloud*. Note that ‘cost’ here is referring to the producer generalized cost, as explained in :numref:`producer_compliance_strategy_section`.

.. admonition:: Demo example: Vehicle cost clouds

    An example cost cloud for a single vehicle in MY2025 (vehicle #62, a 4WD minivan) for the no-action policy in Context A is shown in :numref:`al_label_pm_vehicle_cloud`. The costs for the blue points are production costs. The orange point costs are producer generalized costs, and include 5 years of fuel costs at 15,000 miles per year that the producer assumes are valued by consumers at the time of purchase (as defined in the analysis context input file ‘producer_generalized_costs.csv’.) Note that the producer generalized costs are higher than the production costs, and also form a cloud with a different shape than the blue production cost cloud. Essentially, the orange cloud is shifted up and rotated counterclockwise relative to the blue cloud because the technology packages with higher emissions rates also have relatively higher fuel costs that are assumed to factor into consumer purchases.

    :numref:`al_label_pm_vehicle_cloud` also contains the resultant cost curve (black line) that represents the cost-minimizing frontier of the cost cloud. The Producer Module automatically generates this piece-wise linear approximation of the frontier using points in the cloud.

    .. _al_label_pm_vehicle_cloud:
    .. figure:: _static/al_figures/2025_ICE_Large_Van_truck_minivan_4WD_cost_curve.png
        :align: center

        Example vehicle cloud

**Compliance options based on design decisions across multiple vehicles**

Because a producer can offer a range of different vehicles, each with distinct costs associated with applying technology packages, it is not likely that the lowest cost compliance solution will be a uniform application of technology to all vehicles. Nor will selecting the lowest cost option for each vehicle likely result in producer compliance, except in cases where a policy is non-binding. In order to consider design options for multiple vehicles simultaneously, the Producer Module aggregates individual vehicles into composites, with one composite vehicle for each market class and reg class combination. It is important that the resultant cost curves (producer generalized cost vs. g CO2/mi emissions rates) are not aggregated further since 1) aggregating emissions rates across market classes would no longer be valid after iteration when the Consumer Module changes the relative shares of market classes, and 2) aggregating emissions rates across regulatory classes would, under some policy definitions, make it impossible to calculate the Mg CO2 compliance credits (e.g. in policy cases where there are limits to the transfer of credits between regulatory classes.)

.. admonition:: Demo example: Vehicle aggregation into market class - reg class cost curves

    :numref:`al_label_pm_composite_vehicle` shows the black cost curve of veh #62 as presented in :numref:`al_label_pm_vehicle_cloud`, along with the other vehicles that are in the same combination of market class (ICE non-hauling) and reg class (‘a’.) Note that the simulated_vehicles.csv file for this demo example does not contain distinct costs and emissions rates for every vehicle. As a result, even though there are 12 vehicles are represented here, they overlay into only three distinct cost curves. If a user provided simulated_vehicles.csv inputs defined with greater resolution, every vehicle could be associated with its own distinct cost curve.

    The bold orange line in :numref:`al_label_pm_composite_vehicle` is the MY2025 cost minimizing frontier for a composite vehicle made by aggregating the individual vehicle cost curves in the same market class and reg class combination. The relative shares of vehicles within a market class and reg class remain fixed in the Producer-Consumer iteration process. Therefore the composite vehicle cost curve does not change as a result of the consumer response. This curve, along with the composite vehicle cost curves from the other market class and reg class combinations, is used to generate the producer compliance options.

    .. _al_label_pm_composite_vehicle:
    .. figure:: _static/al_figures/2025_composite_vehicle_non_hauling_ICE_a_reg_class_cost_curve_composition.png
        :align: center

        Example aggregation of vehicles into a composite vehicle

Once composite vehicle cost curves are generated for each market class and reg class combination, the Producer Module creates compliance options from a combination of design choices for the relative shares of composite vehicles and the emissions rate of each composite vehicle. The resulting compliance options are defined in terms of cost vs. Mg CO2 credits rather than g CO2/mi.  See :numref:`Iteration and Convergence Algorithms` (iteration and convergence) for more discussion of how the model converges on a solution by searching among these compliance options, and generating interpolated compliance options that are successively more refined with each iteration.

**Extracting key vehicle attributes from the composite vehicles through decomposition**

Once a compliance option is selected through the iteration and convergence process, a user will likely want to know how specific vehicle design decisions contributed to that solution.

.. admonition:: Demo example: Decomposition of composite vehicle

    Because the composite vehicle is made up of individual vehicles of fixed sales shares (at least relative to the other vehicles in the same market class, reg class combination), there is one-and-only-one solution for individual vehicle costs and emissions rates that will result in the selected option for the composite vehicle’s cost and emissions rate.  :numref:`al_label_pm_composite_vehicle_decomposition` shows the same orange composite vehicle curve from :numref:`al_label_pm_composite_vehicle`, along with star symbols to indicate the selected option for the composite vehicle and associated points for the individual vehicles.

    .. _al_label_pm_composite_vehicle_decomposition:
    .. figure:: _static/al_figures/2025_composite_vehicle_non_hauling_ICE_a_reg_class_cost_curve_decomposition.png
        :align: center

        Example decomposition of composite vehicle back to individual vehicles

.. _Consumer Module:

Consumer Module
^^^^^^^^^^^^^^^
The Consumer Module is a significant addition to OMEGA. With the ongoing evolutions in the light-duty vehicle market, including major growth in technologies and services, the need for an endogenous consumer response is clear. The Consumer Module is structured to project how consumers of light-duty vehicles would respond to policy-driven changes in new vehicle prices, fuel operating costs, trip fees for ride hailing services, and other consumer-facing elements. The module is set up to allow the inputs to affect total new vehicle sales (both in number and proportion of sales attributes to different market classes), total vehicle stock (including how the used vehicle market responds), and total vehicle use (the VMT of the stock of vehicles).

An important consideration with the addition of the Consumer Module is ensuring consistency between the set of vehicles and their attributes that the Producer Module supplies and the set of vehicles and their attributes that the Consumer Module demands. In order to estimate the set of new vehicles that provide this equilibrium, the Consumer and Producer modules iterate until convergence is achieved - where the set of vehicles, including their prices and attributes, that satisfy producers is the same set of vehicles that satisfy consumers.

Consumer Module Overview
------------------------
As explained in the Overview chapter, and shown in :numref:`mo_label_compare`, OMEGA is structured in a modular format. This means that each primary module --- the Policy Module, Producer Module, Consumer Module and Effects Module --- can be changed without requiring code changes in other modules. This ensures users can update model assumptions and methods while preserving the consistency and functionality of OMEGA.

An overview of the Consumer Module can be seen in :numref:`al_label_cm_ov`. This overview shows the connections between the Consumer Module, the analysis context, and other OMEGA modules. The Consumer Module receives inputs from the analysis context and the Producer Module, and computes outputs used in iteration with the Producer Module and for use in the Effects Module.

.. _al_label_cm_ov:
.. figure:: _static/al_figures/consmod_ov.png
    :align: center

    Overview of the Consumer Module

.. sidebar:: Reregistration

    Reregistration measures the vehicles that have been kept in the fleet for onroad use, or reregistered, each year; that is, it measures the used vehicle stock. Reregistration can be thought of as those vehicles that survive (the inverse of scrappage). Scrappage measures the vehicles that are taken out of use each year. The term is used throughout OMEGA for precision in describing the vehicle stock of interest in an analysis of policy effects, which is made up of registered and in-use vehicles, as opposed to vehicles which have not been physically scrapped.

The Consumer Module’s purpose is to estimate how light duty vehicle ownership and use respond to key vehicle characteristics within a given analysis context. There are five main user-definable elements estimated within the Consumer Module, as seen in :numref:`al_label_inside_cm`. These estimates are: market class definitions, new sales volumes, new vehicle sales shares by market class (where market classes depend on the requirements of the specific consumer decision approach used in the analysis), used vehicle market responses (including reregistration), and new and used vehicle use measured using vehicle miles traveled (VMT). Further explanations of each of these elements are described in the following sections.

.. _al_label_inside_cm:
.. figure:: _static/al_figures/inside_cm.png
    :align: center

    Inside the Consumer Module

.. sidebar:: Market shares of new vehicles

    Throughout this chapter, 'shares' refers to the portion of all new vehicle sales that are classified into each of the different user-definable vehicle market classes.

Each of these five elements represents a user-definable submodule within the Consumer Module code. The code within each submodule may be updated by a user, or the submodule may be replaced with an alternative submodule. When a modifies a submodule, they must ensure that the submodule retains consistency with the other submodules within the Consumer Module, as well as with the rest of OMEGA. For example, if the market class submodule is changed from the demo analysis version, the sales share submodule must be updated as well since sales shares are determined by market class.

.. admonition:: Demo example: Consumer Module user-definable submodules

    The user-definable submodules in the demo analysis version of the Consumer Module are listed in the table below.

    .. csv-table::
        :widths: auto
        :header-rows: 1

        Element,Submodule
        Market class definitions, market_classes.py
        New vehicle sales volume, sales_volume.py
        New vehicle sales shares, sales_share.py
        Used vehicle reregistration, reregistration_fixed_by_age.py
        New and used vehicle use, annual_vmt_fixed_by_age.py

The Consumer Module works in two phases: first, an iterative new vehicle phase, followed by a non-iterative stock and use phase. During the first phase, the Consumer Module and Producer Module iterate to achieve convergence on the estimates of new vehicles produced and demanded that meet the standards set in the Policy Module. The Producer Module sends a set of candidate vehicles, including their prices and attributes, to the Consumer Module to consider. The Consumer Module uses that set of candidate vehicles to estimate total new vehicles demanded and the shares of those new vehicles in the specified market classes, which are passed back to the Producer Module. If the estimates do not converge within a tolerance, a new set of candidate vehicles is sent to the Consumer Module for consideration. See :numref:`Iteration and Convergence Algorithms` for more information on the Consumer-Producer iteration process. Once convergence between the Producer and Consumer modules is achieved, the set of candidate vehicles are no longer considered candidates for consideration, but are the estimated new vehicle fleet, and the Consumer Module enters the second phase. In this phase, total vehicle stock (new and used vehicles and their attributes) and use (VMT) are estimated.

**Inputs to the Consumer Module**
In general, the Consumer Module uses exogenous inputs from the analysis context, and endogenous inputs from the Producer Module. The exogenous inputs may include data such as fuel prices, existing vehicle stock, and specific modeling parameters, for example, the parameters used in estimations of vehicle ownership and use decisions. The analysis context must also contain the inputs required to define projections of vehicle ownership and use in the absence of any policy alternatives being analyzed. These projections might be provided directly as inputs to the Consumer Module, such as projections of vehicle ownership from the Annual Energy Outlook (AEO), or generated within the Consumer Module based on exogenous inputs, including future demographic or macroeconomic trends. Endogenous inputs are factors determined within the model and passed to the Consumer Module from the Producer Module. They may include vehicle prices and other relevant vehicle attributes, such as fuel consumption rate. Because the Consumer Module’s internal representation of consumer decisions can be defined by the user, the specific exogenous and endogenous inputs required will depend on the models, methods, and assumptions specified by the user. The vehicle attributes needed as inputs to the Consumer Module are determined by the methods used to estimate new vehicle sales, the market shares of vehicles demanded, used vehicle reregistration, and new and used vehicle use. For example, vehicle attributes used to define market classes must be included as inputs from the Producer Module. As an additional example, if the user defines vehicle sales responses to differ based on consumer income, the user must ensure that income is included in the analysis context inputs.

**Outputs of the Consumer Module**
The Consumer Module produces two categories of outputs: sales estimates during the iterative Phase 1, and stock and use estimates during the non-iterative Phase 2. During the iterative phase, outputs of the Consumer Module, including new vehicle sales and responsive market shares (explained in the following section), are fed back to the Producer Module for iteration and convergence. See :numref:`phase1` for more information on what happens during Phase 1, and :numref:`Iteration and Convergence Algorithms` for more detailed information on how OMEGA estimates iteration and convergence between the Producer and Consumer modules. Once that convergence is achieved, the Consumer Module estimates the outputs of the stock of vehicles, including both new and reregistered used vehicles, and VMT, which are used by the Effects Module.

Market Class Definitions
------------------------
During the iterative first phase, the Consumer Module considers vehicle prices and attributes at an aggregate level by grouping vehicles into market classes. These market classes are the fundamental unit of analysis for which the Consumer Module estimates new vehicle sales and shares. The choice of market classes is tied to the specification used to estimate the shares of new vehicles sold, and is dependent on the attributes available in the input data files. For example, vehicles might be identified by attributes such as fuel type (electric, gas, diesel, etc.), expected use (primarily for goods or passenger transport), or size.

Users can define market classes in the market class definitions submodule (as shown in :numref:`al_label_inside_cm`.) In doing so, the user must ensure that all other inputs and user-definable submodules (for example, with respect to stock and use estimation) within the Consumer Module are defined consistently. For example, if the sales share submodule is defined as estimating shares of vehicles in a set of fuel type categories, those fuel type categories must be defined within the market class submodule.

The designation of market classes can be used to reflect market heterogeneity in purchasing behavior or vehicle use based on specific vehicle attributes. Accordingly, market classes are defined using vehicle attributes and inputs from the analysis context (i.e. the base year vehicle inputs.) In addition, the user can categorize market classes as ‘responsive,’ where the shares of total vehicles attributed to those market classes change due to endogenously modeled elements that change in response to policy (like relative costs), or ‘nonresponsive,’ where the shares of total vehicles attributed to those market classes do not change with the policy being analyzed.

.. sidebar:: Independent market share assumption

    The assumptions of independence in parent market class categories is consistent with the assumption of independence of irrelevant alternatives (IIA) commonly used in nested choice models.

Before the Consumer Module can estimate new vehicle sales or market shares responses, all vehicles must be categorized into their market classes. This categorization is defined as a series of nested market category levels. The user can define any number of market classes, or levels, as well as the hierarchy of the levels. In defining the hierarchy, it is important to note that OMEGA assumes that the sales share estimates within a parent category are independent of sales share estimates outside the parent category. This means that changing the available market classes outside the parent category will not change the sales share estimates within the parent category.

.. admonition:: Demo example: Market class structure

    :numref:`mo_label_mktree` below illustrates an example of a nested market class hierarchy using the demo analysis market classes as an example. Hauling/non-hauling market classes are the highest, parent, level. Vehicles are separated into the appropriate hauling and non-hauling class using their attributes. Nested within the hauling and non-hauling categories, there are BEV/ICE market classes. The candidate vehicle inputs from the Producer Module, for example, vehicle prices, fuel cost and VMT, are used to determine the share of vehicles in the BEV/ICE market classes, as described in the examples below. During the iterative first phase, if the share of BEVs that consumers will accept given the candidate vehicle attributes does not converge within a tolerance with the share that the Producer Module estimates, the iterative process continues. The demanded BEV share is passed back to the Producer Module, which will return a new set of candidate vehicles and their attributes, including prices. Given the updated candidate vehicle inputs, the Consumer Module will redistribute vehicles into the BEV and ICE classes, with the BEV/ICE share estimates in the hauling category being independent from those in the non-hauling category. This possible redistribution between market class categories is represented by the dashed lines between each set of BEV/ICE classes. Note that the dashed lines travel within the hauling class and within the non-hauling class, but do not travel across them.

        .. _mo_label_mktree:
        .. figure:: _static/al_figures/market_class_tree.png
            :align: center

            Illustration of the Market Class Structure in the Demo Analysis

Within a given analysis context, the shares of vehicles allocated to nonresponsive market class categories do not shift between those nonresponsive market categories, even under different policy alternatives or during iteration with the Producer Module. Shares of vehicles allocated to responsive market class categories may shift between the responsive market categories.

.. admonition:: Demo example: Nonresponsive and responsive market classes

    Within the demo analysis, vehicles are separated into four market classes depending on whether they are categorized as hauling (primarily meant for transporting goods or towing, as a body-on-frame vehicle would be expected to do) or non-hauling (primarily meant for passenger transportation, as a unibody vehicle might do), and their fuel type (battery electric vehicle (BEV) or internal combustion engine vehicles (ICE)). The hauling/non-hauling market classes are defined as nonresponsive market class categories. The share of vehicles defined as hauling or non-hauling, regardless of the fuel type, depends on analysis context inputs, and is unaffected by model results. The BEV/ICE market classes are defined as responsive market class categories, the share of vehicles in that market class is estimated within the Consumer Module and is responsive to vehicle cost and fuel consumption rate of the set of candidate vehicles input from the Producer Module.

.. _phase1:

Phase 1: Producer-Consumer Iteration
------------------------------------
During the iterative first phase of the Consumer Module, the Producer Module and Consumer Module iterate to estimate total new vehicle sales, market shares, and prices at the market class level, based on the candidate vehicle options being offered by the producer. The iteration process is described more fully in the `Iteration and Convergence Algorithms`_ section. It begins with the Producer Module providing a set of candidate vehicles that meet the policy targets as defined within the Policy Module while minimizing the producer's generalized costs. At this initial step, overall volumes are taken directly from the analysis context projections, along with sales shares projection of nonresponsive market class categories. If the sales and market shares result estimated within the Consumer Module is not within a given threshold of the estimates from the Producer Module, iteration between the modules occurs. The process entails the Producer Module offering successive sets of candidate vehicles and their attributes, including prices, which still achieve the policy targets until a there is set of candidate vehicles which results in agreement between the Producer Module and Consumer Module estimates of sales and market shares, or until an iteration limit is reached. On the Producer Module side, the process also includes determining the level of cross-subsidization between vehicle classes, which is covered more fully in the `Iteration and Convergence Algorithms`_ section. Within this iterative first phase of the Consumer Module, there are two main determinations being made: the total sales volume consumers will accept, and the share of vehicles they demand from each market class. Much of the method and assumptions used to estimate sales and shares impacts can be defined by the user in the New Vehicle Sales Volumes and New Vehicle Sales Shares submodule as seen in :numref:`al_label_inside_cm`, including the method of estimating a change in sales volumes or responsive market shares, consumer responsiveness to price, and what is included in the price consumers take into account.


**Sales volumes**

The Consumer Module estimates the total new vehicles sold at the aggregated market class level with the user-definable submodule for new vehicle sales. The estimate for the change in new vehicle sales starts with an assumption of sales volumes in the Context Policy (the "no-action alternative"). These estimates can be an exogenous input from the analysis context, or estimated within the Consumer Module. Sales volumes under a defined policy (an "action alternative") can be responsive to policy if the estimation is defined as relying, at least in part, on inputs from the Producer Module, or may be unresponsive to policy if the estimation is defined to rely solely on inputs from the analysis context. In defining how the Consumer Module estimates sales volumes, the user must ensure consistency between the inputs available from both the Producer Module and the analysis context, as well as with the other user-definable submodules within the Consumer Module. For example, if a user defines sales volumes as responsive to a specific vehicle attribute, that attribute must be included in the set of candidate vehicles and their attributes input from the Producer Module.

.. admonition:: Demo example: New vehicle sales estimates

    In the demo analysis, sales volumes under the no-action policy alternative, which is also the Context Policy, are an exogenous input from the analysis context. An elasticity of demand, defined by the user, is used in conjunction with the change in price between a no-action alternative and an action alternative to estimate the change in sales from the no-action alternative level. Demand elasticity is defined as the percent change in the quantity of a good demanded for a 1%  change in the price of that good, where the good demanded in the Consumer Module is new light duty vehicles. They are almost always negative: as the price of a good increases (a positive denominator), the amount of that good purchased falls (a negative numerator). Larger (in absolute value) negative values are associated with more "elastic", or larger, changes in demand for a given change in price. This value represents how responsive consumers are to a change in price. The general elasticity equation is:

    .. Math::
      :label: al_label_eqn_demand_elasticity

      E_D=\frac{\frac{\Delta Q} {Q}} {\frac{\Delta P} {P}}

    Where:

    * :math:`E_D` is the elasticity of demand
    * :math:`\Delta Q` is the change in the quantity demanded
    * :math:`Q` is the quantity demanded before the price changes
    * :math:`\Delta P` is the change in the good's price
    * :math:`P` is the good's price before the change

    In the demo analysis, the default elasticity of demand is set to -1. This means, for a 1% change in the consumer generalized price (described below), the vehicles demanded by consumers will fall by 1%.
    In order to estimate the change in sales expected as function of the estimated change in price, this equation is rearranged:

    .. Math::
       :label: change in sales

       \Delta Q=E_D * Q *  \frac{P} {\Delta P}

    At an aggregate level, the average expected change in the price of new vehicles is multiplied by the defined demand elasticity to get the estimated change in vehicles demanded. This change is combined with projected new vehicle sales under the no-action alternative to get the total new vehicle sales under the action alternative outlined in the Policy Module.

If a user adopts the demo analysis method of estimating sales volumes using an elasticity of demand, they must ensure that net vehicle price, *P*, is defined. This net price is estimated under the no-action and the action alternatives, and the no-action alternative net price is subtracted from the action alternative net price to get an estimated change in net price, :math:`\Delta P`, that can be used with the user-specified elasticity. The net price should include factors the user assumes consumers consider in their purchase decision. Some factors that might be included are the share of total costs the producers pass onto the consumers, and the amount of future fuel costs consumers consider in their purchase decision.

.. admonition:: Demo example: Net price

    In the demo analysis, the net price value in the sales volume estimate includes assumptions about the share of the total cost that producers pass onto the consumer and the amount of fuel consumption considered in the purchase decision. With respect to the share of total cost that producers pass onto consumers, the demo analysis assumes "full cost pass-through." This means that the full increase in cost that producers are subject to in achieving emission reduction targets is passed on to the consumers. However, due to cross-subsidization, those costs may be spread across multiple market classes.

    The role of fuel consumption in the purchase decision is represented by the number of years of fuel consumption consumers consider when purchasing a new vehicle, and can range from 0 through the full lifetime of the vehicle. Fuel costs are estimated using vehicle fuel consumption rates from the Producer Module, projections of fuel prices from the analysis context, the user-specified VMT schedules, and the user-specified vehicle reregistration schedules. The resulting portion of fuel costs considered by consumers is added to the candidate vehicle prices from the Producer Module to produce a net vehicle price, which is then used in conjunction with the elasticity of demand to estimate the change in vehicle sales. The demo analysis assumes that consumers consider 5 years of fuel costs in the vehicle purchase decision.

**Sales shares**

The new vehicles sold are categorized into the user-definable market classes using estimates of sales shares. As mentioned above, those market classes can be nonresponsive or responsive to the policy being analyzed. Nonresponsive vehicle shares do not change with updated candidate vehicle sets or across policy alternatives. Though not responsive to endogenous inputs, the nonresponsive sales shares do not have to be constant. For example, they may be provided as a set of values for different points in time if the shares are expected to change exogenously over time. In addition, users can define sales shares to explicitly consider consumer heterogeneity by defining separate sales share estimates for different consumer groups. For example, sales share responses can differ between rural and urban consumers. If users identify heterogenous consumer groups with separate sales share responses, the analysis context must include the appropriate inputs. For example, the proportion of the vehicle buying population in urban and rural areas for each year being analyzed within the model.

.. admonition:: Demo example: Nonresponsive market share estimates

    Within the demo analysis, the hauling/non-hauling market classes are nonresponsive. The sales shares for these classes are defined using exogenous inputs from the analysis context. The shares change over time as relative projections of hauling and non-hauling vehicles change over time. However, within a given analysis context, the shares do not change across the no-action and action alternatives defined in the Batch Input File.

For responsive market classes, users can define how market shares are responsive to attributes of candidate vehicle sets fed in from the Producer Module, for example vehicle price. In addition, the inputs used to estimate shares must be available within the set of candidate vehicles and their attributes, or as part of the analysis context.

.. admonition:: Demo example: Responsive market share estimates

    The demo analysis defines BEV and ICE market classes as responsive to the action alternatives being analyzed. The method used to estimate BEV shares is based on an S-shaped curve, estimated using the logit curve functional form. Logit curves have been used to estimate technology adoption over time in peer reviewed literature as far back as 1957, and are still widely used today, including in estimating adoption of electric vehicle technologies. Technology adoption in a logit curve is modeled as a period of low adoption, followed by a period of rapid adoption, and then a period where the rate of adoption slows. This can be thought of as analogous to the "early adopter", "mainstream adopter" and "laggard" framework in technology adoption literature. The logit curve equation in the demo analysis estimates the share of BEVs demanded by consumers, accounting for how quickly (or slowly) new technology is phased into public acceptance, as well as how responsive consumers are to the candidate vehicle prices input from the Producer Module. The basic logit equation is:

    .. Math::
       :label: logit_curve

       s_{i}=\frac{\alpha_{i} * p_{i}^{\gamma}} {\Sigma_{j=1}^{N} \alpha_{j} * p_{j}^{\gamma}}

    Where:

    * :math:`s_{i}` is the share of vehicles in market class *i*
    * :math:`\alpha_{i}` is the share weight of market class *i*. This determines how quickly consumers accept new technology.
    * :math:`p_{i}` is the generalized cost of each vehicle in market class *i*
    * :math:`\gamma` represents how sensitive the model is to price.

   The table below shows a subset of input parameters used to estimate sales shares in the demo analysis for Context A. Context B uses the same parameters with slightly different values. The full list of parameter values used in the demo analysis for each context can be found in the demo inputs for the contexts in the file 'sales_share_params-cntxt_*.csv', where * is either a or b.

    .. _al_label_table_sales_share_parameter_inputs:
    .. csv-table:: Example of Sales Share Parameters in 'sales_share_params.csv'
        :widths: auto
        :header-rows: 1

        market_class_id,start_year,annual_vmt,payback_years,price_amortization_period,share_weight,discount_rate,o_m_costs,average_occupancy,logit_exponent_mu
        hauling.BEV,2020,12000,5,5,0.142,0.1,1600,1.58,-8
        hauling.BEV,2021,12000,5,5,0.142,0.1,1600,1.58,-8
        hauling.BEV,2030,12000,5,5,0.5,0.1,1600,1.58,-8
        hauling.BEV,2031,12000,5,5,0.55,0.1,1600,1.58,-8
        non_hauling.BEV,2020,12000,5,5,0.142,0.1,1600,1.58,-8
        non_hauling.BEV,2021,12000,5,5,0.142,0.1,1600,1.58,-8
        non_hauling.BEV,2030,12000,5,5,0.5,0.1,1600,1.58,-8
        non_hauling.BEV,2031,12000,5,5,0.55,0.1,1600,1.58,-8


If the user retains the demo analysis method of determining responsive BEV shares (using a logit curve as described above), the parameters representing the speed of acceptance, :math:`\alpha_{i}`, and price responsiveness, :math:`\gamma`, are factors the user can modify in the sales share submodule inputs (see :any:`sales share inputs <omega_model.consumer.sales_share>`)

In addition, the user must specify the price used in the logit equation. This price should include factors the user estimates are significant in determining relative market shares; cost factors can be monetary, such as capital and maintenance costs, or non-monetary, such as time. In addition, price estimation needs to be consistent with the speed of acceptance and price responsiveness parameters.

.. admonition:: Demo example: BEV share parameters

    The share weight and price sensitivity parameters in the demo analysis are currently informed by the inputs and assumptions used in the market share logit equation in the passenger transportation section of GCAM-USA (documentation and information on how to download GCAM-ISA can be found at https://jgcri.github.io/gcam-doc/gcam-usa.html ) In addition, the price used in estimating BEV shares is the consumer generalized cost used by the GCAM-USA share weight estimation method. The consumer generalized cost estimation from GCAM includes capital costs (including candidate vehicle prices fed in from the Producer Module, and the cost of a home charger), fuel costs, maintenance costs, and parameter values for amortization period and discount rate. The amortization period and discount rate, like most of the user-definable submodule, can be defined by a user. In the demo analysis, they are set at 10 years and 10%. These parameters are used to estimate an annualized vehicle cost. That annualized cost is then divided by a user defined annual vehicle mileage to convert the value to dollars per mile. Note that fuel costs are also included in GCAM’s generalized costs as $/mi, and are not discounted.


Phase 2: Vehicle Stock and Use
------------------------------
If convergence with respect to the sales and shares of new vehicles is achieved, the Consumer Module estimates total vehicle stock and use. To do so, it needs to keep internal consistency between-  the number of vehicles demanded and the use of those vehicles. The method of determining total vehicle stock and vehicle use are in user-definable submodules represented by the used vehicle market response element and the new and used vehicle use element in :numref:`al_label_inside_cm`. Vehicle stock is the total onroad registered fleet, including both new vehicles sales and the reregistered (used) vehicles. The data contained in the set of vehicle stock includes both vehicle count, as well as the attributes of the vehicles in the set, including model year and the vehicle features or attributes used to designate market classes. Vehicle use is the measure of how much each vehicle is driven in the analysis year, measured in vehicle miles traveled (VMT). VMT is determined at the vehicle level.

**Vehicle stock**

:numref:`mo_label_stockflow` below steps through the flow of how total vehicle stock is estimated in OMEGA. To estimate vehicle stock, the model starts with a base year stock of vehicles, which is an input from the analysis context. The base year is the last year actual observations, and is unmodified during the analysis. The analysis start year is the first year in which modeling is performed and immediately follows the base year. The stock of vehicles at the end of the analysis start year includes the new vehicles produced, plus the set of vehicles that were reregistered from the base year stock. For each subsequent modeled (analysis) year, the total stock is determined from the new vehicles produced in that year plus the reregistered vehicles from the prior year.

.. _mo_label_stockflow:
.. figure:: _static/al_figures/stock_flow.png
    :align: center

    Vehicle stock estimation flow diagram

The method of estimating the reregistered fleet is in a user-definable used vehicle reregistration submodule. This method can make use of a static schedule, for example, where a vehicle's age is the only determinant of the proportion of vehicles remaining in the fleet over time, or depend on other vehicle attributes, like cumulative VMT. If users modify the reregistration submodule to follow a different prescribed static rate, or to allow interdependencies between the rate of reregistration and other vehicle attributes, they need to retain consistency between the reregistration submodule and other submodules, for example the submodules estimating new vehicle sales and total VMT.

.. admonition:: Demo example: Vehicle stock estimates

    In the demo analysis, the analysis start year stock of vehicles comes from the analysis context, and reregistration is estimated using fixed schedules based on vehicle age. For every calendar year, a specified proportion of vehicles in each model year is assumed to be reregistered for use in the following calendar year. In this fixed schedule, the proportion of vehicles of a given model year remaining in the registered stock (i.e. the survival rate) falls as the vehicles age. For example, in 2030, the proportion of the original MY 2025 vehicles remaining is larger than the proportion of MY 2015 vehicles remaining.

**Vehicle use**

Vehicle use is estimated as the vehicle miles traveled for each vehicle in the stock for the analysis year. This can be thought of as a measure of consumer demand for mobility. The method of estimating total VMT for the stock of vehicles is in a user-definable new and used vehicle use submodule. VMT can be estimated simply as a function of vehicle age, or may be a function of age, market class, analysis context inputs or more. Use could also include estimates of rebound driving. Rebound driving is estimated as the additional VMT consumers might drive as a function of reduced cost of driving.

.. admonition:: Demo example: VMT estimates

    In the demo analysis, total VMT demanded is an input from the analysis context and is constant across policy alternatives. Total VMT demanded is combined with the initial stock of vehicles and their attributes from the analysis context to determine the proportion of VMT attributed to cohorts of vehicles separated by age and market class. For each calendar year, the total VMT projected in the analysis context is allocated across the internally estimated stock of vehicles using this fixed relationship. This method allows VMT per vehicle to change with the total stock of vehicles, while assuming that consumer demand for mobility is not affected by the action alternatives under consideration. The demo analysis does not currently implement VMT rebound estimations.


.. _Iteration and Convergence Algorithms:

Iteration and Convergence Algorithms
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
OMEGA finds a solution in each analysis year using iterative search algorithms. As shown in the process flow diagram in :numref:`al_label_overallprocessflow`, the model uses two iterative loops; a Producer-Policy loop and a Producer-Consumer loop. For both loops, convergence criteria must be achieved within a specified tolerance for the simulation to proceed. This section describes those loops in more detail, with additional information from the demo example.

**'Producer-Policy' Iteration: Compliance Search**

The iteration process begins with a search for the vehicle design options and market class shares that minimize producer generalized costs and achieve the desired compliance outcome, independent of any feedback from the Consumer Module regarding vehicle demand. In this step, individual compliance options are built up, with each option fully defining the shares of each market class, and the technology package applications on each of the producer’s vehicles. From all these compliance options, up to a pair of points is selected which are closest, above and below, to the strategic GHG target (i.e. Mg CO2e.). If all points are under- or over-target then the point nearest to the target is chosen. The market shares and technologies of the selected point(s) become seed values for the next sub-iteration.  In each successive sub-iteration, the search area becomes narrower while also covering the options with greater resolution. Finally, when a point falls below the convergence tolerance for Mg CO2 credits or the search range has fallen below a minimum tolerance, the closest point is selected as the compliance option for the initial compliance search.

.. admonition:: Demo example: Initial compliance search

    :numref:`al_label_figure_2025_0_compliance_search` shows the various sub-iterations for the initial compliance search in the demo example for 2025. The left figure shows a number of blue points for the 0th sub-iteration. The two low cost points nearest to 0 Mg CO2e credits form the basis for the search in the next sub-iteration. The right figure show all 15 sub-iterations (0th to 14th), including the points selected in the 0th sub-iteration (blue stars.) Note that the sub-iterations shown by the colored gradient scale have progressively lower costs, and more closely focused around 0 Mg CO2e. The selected compliance option from the initial Producer-Policy compliance search is shown by a single red star.

    .. |fig_al_ic_1_a| image:: _static/al_figures/2025_0_producer_compliance_search.png
        :scale: 50%
    .. |fig_al_ic_1_b| image:: _static/al_figures/2025_0_producer_compliance_search_colored.png
        :scale: 50%

    .. csv-table::
        :widths: auto

        |fig_al_ic_1_a|,|fig_al_ic_1_b|

    .. _al_label_figure_2025_0_compliance_search:
    .. figure:: _static/1x1.png
        :align: center

        Initial compliance search (2025_0)

    :numref:`al_label_figure_2025_0_compliance_search_zoom_in` is another view of the same search, with greater magnification around the selected production option and surrounding options which were not selected.

    .. _al_label_figure_2025_0_compliance_search_zoom_in:
    .. figure:: _static/al_figures/2025_0_producer_compliance_search_final.png
        :align: center

        Zoom in on producer's initial compliance selection (2025_0)

**'Producer-Consumer' Iteration: Market Shares and Pricing**

After a purely cost-minimizing option is selected in the initial compliance search, the Producer Module provides the vehicle attributes and prices, at the market class level, for consideration by the Consumer Module. Within a given Producer-Consumer iteration loop, the vehicle design options are fixed. The search for a solution is based on consideration of various market class share and pricing options. Criteria for convergence include 1) the percent change in average total price, and 2) the difference in the producer and consumer market shares. To achieve convergence, both of these metrics must be close to zero, within the specified tolerance.

.. admonition:: Demo example: Consumer-Producer iteration

    Within a single Producer-Consumer iteration loop, vehicle designs are fixed, but pricing and market class shares vary. :numref:`al_label_figure_2025_0_initial_producer_consumer_iteration` shows the various components of the first Producer-Consumer iteration loop for 2025 in the demo example (Context A, no action policy alternative.)

    The upper left panel shows the range of producer cross-subsidy price multiplier options.  The full range of multipliers in the 0th sub-iteration are dark blue points, which then narrow in range over eight sub-iterations. The final range of multipliers is shown by the red points.

    In the upper right panel, those same pricing options are shown in terms of absolute prices. While the multipliers applied to hauling and non-hauling vehicles cover a similar range of values, the lower absolute prices for non-hauling vehicles results in a range of prices that is somewhat narrower than the range for hauling vehicles.

    The two convergence criteria are illustrated in the bottom two panels of :numref:`al_label_figure_2025_0_initial_producer_consumer_iteration` (share delta for hauling BEVs in the lower left panel, and average total price delta in the lower right panel.) In this Producer-Consumer iteration, the market class shares offered by the producer do not converge with the shares demanded by the consumer over the range of cross-subsidy pricing options available. This is visible in the lower left panel, since the 0.4% share delta value in the final sub-iteration does not meet the convergence criteria. If convergence had been achieved, the iteration process of this analysis year would be complete, and the produced vehicles would be finalized. Otherwise, the iteration will proceed, with a new consideration of vehicle design options offered by the Producer Module.

    .. |fig_al_ic_2_a| image:: _static/al_figures/2025_0_producer_cross_subsidy_multipliers.png
        :scale: 50%
    .. |fig_al_ic_2_b| image:: _static/al_figures/2025_0_producer_cross_subsidized_prices.png
        :scale: 50%
    .. |fig_al_ic_2_c| image:: _static/al_figures/2025_0_hauling_BEV_abs_market_share_delta.png
        :scale: 50%
    .. |fig_al_ic_2_d| image:: _static/al_figures/2025_0_average_total_price_absolute_percent_delta.png
        :scale: 50%

    .. csv-table::
        :widths: auto

        |fig_al_ic_2_a|,|fig_al_ic_2_b|
        |fig_al_ic_2_c|,|fig_al_ic_2_d|

    .. _al_label_figure_2025_0_initial_producer_consumer_iteration:
    .. figure:: _static/1x1.png
        :align: center

        Initial Producer-Consumer iteration (2025_0)

**Repeat Iteration of 'Producer-Policy' and 'Producer-Consumer'**

If the prior round of iterations is unable to find a converged solution, the process will continue by repeating a series of Producer-Policy compliance searches and Producer-Consumer market share and pricing searches. The process is the same as in the initial iteration, with one exception: that the Producer-Policy compliance search will use the market shares from the prior iteration’s Producer-Consumer search.

These iterations are repeated until the market class share and average total price convergence criteria are met, and the compliance search is complete. Alternatively, if the number of Producer-Consumer iterations exceeds the set limit, then the sales and market shares from the last iteration are used. In this case, any deviation from the Producer’s strategic compliance target in that analysis year must be made up for through the use of banked credits. Finally, the produced vehicles are logged for consideration in the Consumer Module’s vehicle stock and use submodules, and in the Effects Module.

.. admonition:: Demo example: First iteration beyond initial Producer-Policy and Producer-Consumer iterations

    :numref:`al_label_figure_2025_1_compliance_search` shows the points considered in the compliance search in the first iteration (2025_1) following the initial iteration(2025_0). Similar to the initial iteration, each point represents a compliance option that is the result of a unique combination of candidate vehicle design choices and market class shares. Note that compared to :numref:`al_label_figure_2025_0_compliance_search`, the points in :numref:`al_label_figure_2025_1_compliance_search` are more sparse since the market shares in this iteration have been constrained to the shares selected in the prior Producer-Consumer iteration.

    .. |fig_al_ic_3_a| image:: _static/al_figures/2025_1_producer_compliance_search.png
        :scale: 50%
    .. |fig_al_ic_3_b| image:: _static/al_figures/2025_1_producer_compliance_search_colored.png
        :scale: 50%

    .. csv-table::
        :widths: auto

        |fig_al_ic_3_a|,|fig_al_ic_3_b|

    .. _al_label_figure_2025_1_compliance_search:
    .. figure:: _static/1x1.png
        :align: center

        Compliance search iteration (2025_1) following initial iteration (2025_0)

    .. _al_label_figure_2025_1_compliance_search_zoom_in:
    .. figure:: _static/al_figures/2025_1_producer_compliance_search_final.png
        :align: center

        Zoom in on producer's compliance selection (iteration 2025_1)

    :numref:`al_label_figure_2025_1_further_producer_consumer_iteration` is similar to :numref:`al_label_figure_2025_0_initial_producer_consumer_iteration`, and represents the Producer-Consumer pricing and market class share search in a subsequent round of iteration, after the producer has revised the vehicle design options. Unlike the initial iteration, the range of cross-subsidy pricing flexibility is now sufficient to allow the convergence criteria to be met, as shown in the lower left and lower right panels.

    .. |fig_al_ic_4_a| image:: _static/al_figures/2025_1_producer_cross_subsidy_multipliers.png
        :scale: 50%
    .. |fig_al_ic_4_b| image:: _static/al_figures/2025_1_producer_cross_subsidized_prices.png
        :scale: 50%
    .. |fig_al_ic_4_c| image:: _static/al_figures/2025_1_hauling_BEV_abs_market_share_delta.png
        :scale: 50%
    .. |fig_al_ic_4_d| image:: _static/al_figures/2025_1_average_total_price_absolute_percent_delta.png
        :scale: 50%

    .. csv-table::
        :widths: auto

        |fig_al_ic_4_a|,|fig_al_ic_4_b|
        |fig_al_ic_4_c|,|fig_al_ic_4_d|

    .. _al_label_figure_2025_1_further_producer_consumer_iteration:
    .. figure:: _static/1x1.png
        :align: center

        Producer-Consumer iteration (2025_1) beyond initial iteration (2025_0)

.. _Effects Module:

Effects Module
^^^^^^^^^^^^^^
In its primary function as a regulatory support tool, OMEGA’s modeled outputs are intended to inform the type of benefit-cost analyses used
in EPA rulemakings and other analyses. We would likely use many of OMEGA’s outputs directly in the analysis for a regulatory action. In other cases, OMEGA
produces values that might help inform other models like MOVES. The scope of OMEGA’s effects modeling includes estimating both monetized
or cost effects and physical effects. The Effects Module builds on the outputs of the Consumer and Producer modules along with the analysis
context inputs as shown in :numref:`effects_module_figure`.

.. _effects_module_figure:
.. figure:: _static/al_figures/effectsmod_ov.png
    :align: center

    Overview of the Effects Module

* Key examples of physical effects that OMEGA will estimate:
	* Stock of registered vehicles, along with key attributes
	* VMT of registered vehicles
	* Tailpipe GHG and criteria pollutant emissions
	* Upstream (refinery, power sector) GHG and criteria pollutant emissions
* Key examples of monetized effects that OMEGA will estimate:
	* Vehicle production costs
	* Vehicle ownership and operation costs, including fuel and maintenance
	* Other consumer effects
	* Impacts of criteria air pollutants
	* Impacts of greenhouse gas pollutants
	* Congestion, noise, and safety costs

The Effects Module generates three output files: physical effects, cost effects and technology tracking. In general, the cost effects output file builds upon the physical effects output file in conjunction with several of the context input files. Those context input files are the cost factor and emission factor input files. For example, the cost effects file would present CO2-related costs as the CO2 cost factor (a cost/Mg CO2e value set in the input file) multiplied by the emissions of CO2 as presented in the physical effects file. Similarly, fuel costs would be calculated as fuel prices (dollars/gallon as provided in the input file) multiplied by gallons consumed as presented in the physical effects file.

Each of these physical and cost effects are calculated on an absolute basis. In other words, an inventory of CO2 emissions multiplied by unit “costs” of CO2 emissions provides an absolute “cost” of CO2 emissions. However, the calculation of criteria and GHG emission impacts is done using the damage cost estimates included in the cost_factors-criteria.csv and cost_factors-scc.csv input files. These estimates are best understood to be the marginal costs associated with the reduction of the individual pollutants as opposed to the absolute costs associated with a ton of each pollutant. As such, the criteria and climate “costs” calculated for a given policy alternative, in isolation, should not be interpreted as representative of absolute damage costs from all emissions. Instead those costs are intended to be used for the comparison with another policy alternative (presumably via calculation of a difference in “costs” between two scenarios) the result can be interpreted as a benefit.

There are certain other parameters included in the cost effects file that must be handled differently than discussed above. For example, drive surplus is the economic value of the increased owner/operator surplus provided by added driving and is estimated as one half of the product of the decline in vehicle operating costs per vehicle-mile and the resulting increase in the annual number of miles driven via the rebound effect. Since the drive surplus is calculated using a change in operating costs, the new operating costs must be compared to another operating cost. Drive surplus, safety effects and net
benefits are not currently included in OMEGA.

Importantly, the cost factor inputs (as OMEGA calls them) have been generated using several discount rates. The values calculated using each of the different discount rates should not be added to one another. In other words, PM costs calculated using a 3 percent discount rate and a 7 percent discount rate should never be added together. Similarly, climate costs calculated using a 3 percent discount rate and a 2.5 percent discount rate should never be added. This does not necessarily hold true when adding criteria air pollutant costs and climate costs when it is acceptable to add costs using different discount rates. Lastly, when discounting future values, the same discount rate must be used as was used in generating the cost factors.

The tech volumes output file provides the volume of each vehicle equipped with the technologies for which tech flags or tech data is present in the simulated_vehicles.csv input file. For example, if vehicle number 1 had 100 sales and half were HEVs while the other half were BEVs, the tech volumes output file would show that vehicle as having the following tech volumes: HEV=50; BEV=50. This is not the case for the weight-related technologies where curb weight is presented as the curb weight of the vehicle, weight reduction is presented as the weight reduction that has been applied to the vehicle to achieve that curb weight, and fleet pounds is the registered count of the vehicle multiplied by its curb weight.

Each of the above files presents vehicle-level data for each analysis year that has been run and for each age of vehicle present in that
calendar year. The model year of each vehicle is also provided.

Physical Effects Calculations
-----------------------------
Physical effects are calculated at the vehicle level for all calendar years included in the analysis. Vehicle_ID and VMT driven by the given vehicle are pulled from the VehicleAnnualData class. Vehicle attributes are pulled from VehicleFinal class. Fuel attributes are pulled from the OnroadFuel class which draws them from the onroad_fuels input file.

Fuel Consumption
----------------
Liquid fuel consumption and electricity consumption are calculated for a given Vehicle ID as:

**Liquid fuel consumption**

.. Math::
    :label: ice_fuel_consumption

    FuelConsumption_{gallons}=VMT_{liquid fuel} * \frac{(CO_{2} grams/mile)_{onroad, direct}} {(CO_{2} grams/gallon) * TransmissionEfficiency}

Where:

* :math:`VMT_{liquid fuel}=VMT * FuelShare_{liquid fuel}`
* :math:`(CO_{2} grams/mile)_{onroad, direct}` is calculated within OMEGA and accounts for any credits that do not improve fuel consumption and test-to-onroad gaps
* :math:`(CO_{2} grams/gallon)` is the :math:`CO_{2}` content of the in-use, or retail, fuel
* :math:`TransmissionEfficiency` is the efficiency of liquid fuel transmission as set by the user

**Electricity consumption**

.. Math::
    :label: bev_fuel_consumption

    FuelConsumption_{kWh}=VMT_{electricity} * \frac{(kWh/mile)_{onroad, direct}} {TransmissionEfficiency}

Where:

* :math:`VMT_{electricity}=VMT * FuelShare_{electricity}`
* :math:`(kWh/mile)_{onroad, direct}` is calculated within OMEGA and accounts for any credits that do not improve fuel consumption and test-to-onroad gaps
* :math:`TransmissionEfficiency` is the efficiency of the power grid as set by the user

.. note:: Multi-fuel vehicle fuel consumption

    Multi-fuel vehicles consume both electricity and liquid fuel. Consumption of both is calculated for such vehicles and emission effects such
    as upstream and tailpipe emissions are calculated uniquely for both fuels.

Emission Inventories
--------------------
Emission inventories are calculated for a given Vehicle ID as:

**Tailpipe Criteria Emissions (except for SO2)**

.. Math::
    :label: tailpipe_criteria_tons

    TailpipeEmissions_{Pollutant, US tons}=VMT_{liquid fuel} * \frac{(grams/mile)_{Pollutant}} {grams/US ton}

Where:

* :math:`Pollutant` would be any of the criteria air pollutants such as VOC, PM2.5, NOx, etc., with the exception of :math:`SO_{2}`
* :math:`VMT_{liquid fuel}=VMT * FuelShare_{liquid fuel}`
* :math:`(grams/mile)_{Pollutant}` is an emission factor (e.g., a MOVES emission factor) from the emission factors input file
* :math:`grams/US ton` = 907,185

**Tailpipe SO2**

.. Math::
    :label: tailpipe_so2_tons

    TailpipeEmissions_{SO_{2}, US tons}=FuelConsumption_{liquid fuel} * \frac{(grams/gallon)_{SO_{2}}} {grams/US ton}

Where:

* :math:`FuelConsumption_{liquid fuel}` is calculated by equation :math:numref:`ice_fuel_consumption`
* :math:`(grams/gallon)_{SO_{2}}` is the :math:`SO_{2}` emission factor (e.g., a MOVES emission factor) from the emission factors input file
* :math:`grams/US ton` = 907,185

**Tailpipe CH4 and N2O Emissions**

.. Math::
    :label: tailpipe_non_co2_tons

    TailpipeEmissions_{Pollutant, Metric tons}=VMT_{liquid fuel} * \frac{(grams/mile)_{Pollutant}} {grams/Metric ton}

Where:

* :math:`Pollutant` would be either :math:`CH_{4}` or :math:`N_{2}O`
* :math:`VMT_{liquid fuel}=VMT * FuelShare_{liquid fuel}`
* :math:`(grams/mile)_{Pollutant}` is an emission factor (e.g., a MOVES emission factor) from the emission factors input file
* :math:`grams/Metric ton` = 1,000,000

**Tailpipe CO2 Emissions**

.. Math::
    :label: tailpipe_co2_tons

    TailpipeEmissions_{CO_{2}, Metric tons}=VMT_{liquid fuel} * \frac{(CO_{2} grams/mile)_{onroad, direct}} {grams/Metric ton}

Where:

* :math:`VMT_{liquid fuel}=VMT * FuelShare_{liquid fuel}`
* :math:`(CO_{2} grams/mile)_{onroad, direct}` is calculated within OMEGA and accounts for any credits that do not improve fuel consumption and test-to-onroad gaps
* :math:`grams/Metric ton` = 1,000,000

**Upstream Criteria Emissions**

.. Math::
    :label: upstream_criteria_tons

    & UpstreamEmissions_{Pollutant, US tons} \\
    & =\frac{FC_{kWh} * (grams/kWh)_{Pollutant, EGU} - FC_{gallons} * (grams/gallon)_{Pollutant, Refinery}} {grams/US ton}

Where:

* :math:`Pollutant` would be any of the criteria air pollutants such as VOC, PM2.5, NOx, etc.
* :math:`FC_{kWh}` is :math:`FuelConsumption_{kWh}` calculated by equation :math:numref:`bev_fuel_consumption`
* :math:`(grams/kWh)_{Pollutant, EGU}` is the Electricity Generating Unit (or Power Sector) emission factor for the given Pollutant
* :math:`FC_{gallons}` is :math:`FuelConsumption_{gallons}` calculated by equation :math:numref:`ice_fuel_consumption`
* :math:`(grams/gallon)_{Pollutant, Refinery}` is the Refinery emission factor for the given pollutant
* :math:`grams/US ton` = 907,185

**Upstream GHG Emissions**

.. Math::
    :label: upstream_ghg_tons

    & UpstreamEmissions_{Pollutant, Metric tons} \\
    & =\frac{FC_{kWh} * (grams/kWh)_{Pollutant, EGU} - FC_{gallons} * (grams/gallon)_{Pollutant, Refinery}} {grams/Metric ton}

Where:

* :math:`Pollutant` would be any of the criteria air pollutants such as VOC, PM2.5, NOx, etc.
* :math:`FC_{kWh}` is :math:`FuelConsumption_{kWh}` calculated by equation :math:numref:`bev_fuel_consumption`
* :math:`(grams/kWh)_{Pollutant, EGU}` is the Electricity Generating Unit (or Power Sector) emission factor for the given Pollutant
* :math:`FC_{gallons}` is :math:`FuelConsumption_{gallons}` calculated by equation :math:numref:`ice_fuel_consumption`
* :math:`(grams/gallon)_{Pollutant, Refinery}` is the Refinery emission factor for the given pollutant
* :math:`grams/Metric ton` = 1,000,000

**Total Criteria Emissions**

.. Math::
    :label: total_criteria_tons

    & TotalEmissions_{Pollutant, US tons} \\
    & = TailpipeEmissions_{Pollutant, US tons} - UpstreamEmissions_{Pollutant, US tons}

Where:

* :math:`TailpipeEmissions_{Pollutant, US tons}` is calculated by equation :math:numref:`tailpipe_criteria_tons` or :math:numref:`tailpipe_so2_tons`
* :math:`UpstreamEmissions_{Pollutant, US tons}` is calculated by equation :math:numref:`upstream_criteria_tons`

**Total GHG Emissions**

.. Math::
    :label: total_ghg_tons

    & TotalEmissions_{Pollutant, Metric tons} \\
    & = TailpipeEmissions_{Pollutant, Metric tons} - UpstreamEmissions_{Pollutant, Metric tons}

Where:

* :math:`TailpipeEmissions_{Pollutant, Metric tons}` is calculated by equation :math:numref:`tailpipe_non_co2_tons` or :math:numref:`tailpipe_co2_tons`
* :math:`UpstreamEmissions_{Pollutant, Metric tons}` is calculated by equation :math:numref:`upstream_ghg_tons`

Cost Effects Calculations
-------------------------
Cost effects are calculated at the vehicle level for all calendar years included in the analysis and for, primarily,
the physical effects described above.

ALPHA Package Costs Module
^^^^^^^^^^^^^^^^^^^^^^^^^^

The ALPHA package costs module generates the simulated_vehicles.csv file used as an input to OMEGA. This section describes
the calculations done in the module to generate the simulated_vehicles.csv file. The module uses, as an input, the
alpha_package_costs_module_inputs.xlsx file, described in SECTION 7.3.1.1.2 (insert a code pointer to this?) and individual
ALPHA files which provide CO2 g/mi results over EPA test cycles for various classes of vehicles and hundreds
of technology packages applied to each.

In general, individual technology costs are read from the alpha_package_costs_module_inputs file inclusive of
markups to cover indirect costs. The markups applied within the alpha_package_costs_module_inputs file, which are applied
to ICE engine-related and all aero, non-aero and weight-related costs, are controllable via user input on the inputs_workbook
worksheet. The markups to be applied to electrification technology (battery and non-battery costs for HEVs, PHEVs and BEVs)
is controllable via user input on the electrified_metrics worksheet. Importantly, the electrification markups are applied
"in-code" via the alpha_package_costs module so their application is not reflected within the alpha_package_costs_module_inputs
file. The inputs_code worksheet contains learning rate inputs for various technologies. These learning rates are applied
year-over-year to technologies within the category beginning with the start_year setting on the inputs_code worksheet.
Every cost within the alpha_package_costs_module_inputs file has an associated dollar basis to specify the dollar valuation
of the given cost (i.e., is the cost in 2016 dollars, 2020 dollars, etc.). On the inputs_code worksheet, the user can
specify the dollar basis for the module's output file. Running the module generates a simulated_vehicles.csv file, along
with other output files, with all cost values converted to the dollar_basis specified on the inputs_code worksheet. When
the simulated_vehicles.csv file is subsequently read into OMEGA, the simulated_vehicles.csv costs will again be converted
to be consistent with the dollar_basis specified for the given OMEGA run. So the alpha_package_costs_module_inputs file
dollar_basis (set via the dollar_basis_for_output_file setting) does not need to be consistent with the desired OMEGA-run
dollar basis value. All of the inputs applied in-code, as just discussed, are shown in :numref:`inputs_code_sheet`.

.. _inputs_code_sheet:
.. csv-table:: Inputs Applied "In-code"
    :widths: auto
    :header-rows: 1

    item,value
    run_ID,0
    optional_run_description,
    dollar_basis_for_output_file,2020
    start_year,2020
    end_year,2050
    learning_rate_weight,0.005
    learning_rate_ice_powertrain,0.01
    learning_rate_roadload,0.015
    learning_rate_bev,0.025
    learning_rate_phev,0.025
    learning_rate_aftertreatment,0.01
    Pt_dollars_per_troy_oz,990.58
    Pd_dollars_per_troy_oz,1952.23
    Rh_dollars_per_troy_oz,16328.67
    boost_multiplier,1.2

Where,

* :math:`run\_ID` will be added to output filenames (leave as "0" to include nothing but a date and time stamp)
* :math:`optional\_run\_description` is optional and is simply included in the copy/paste version of the input file into the output file
* :math:`dollar\_basis\_for\_output\_file` sets the desired dollar basis for outputs of the alpha_package_costs module
* :math:`start\_year` sets the start year for cost calculations and application of learning effects
* :math:`end\_year` sets the final year for cost calculations
* :math:`learning\_rate\_weight` sets the learning rate for weight-related costs
* :math:`learning\_rate\_ice\_powertrain` sets the learning rate for ICE powertrain technologies applied to ICE, HEV and PHEV packages and HEV battery and non-battery components
* :math:`learning\_rate\_roadload` sets the learning rate for aero and non-aero roadload reduction technolgies
* :math:`learning\_rate\_bev` and :math:`learning_rate_phev` set the learning rates for battery and non-battery components on BEV and PHEV packages
* :math:`boost\_multiplier` sets the multiplier applied to boosted packages

ICE Engine-Related Costs
------------------------
To estimate ICE engine-related costs, the module starts first with the engine name which is read directly from the "Engine"
column of the ALPHA input file. The engine names included in the ALPHA runs, and the pertinent technologies on those
engines, are shown in :numref:`engines_and_techs`.

.. _engines_and_techs:
.. csv-table:: Engines and Associated Technologies
    :widths: auto
    :header-rows: 1

    Engine Name, Technologies
    engine_2013_GM_Ecotec_LCV_2L5_PFI_Tier3, "PFI"
    engine_2013_GM_Ecotec_LCV_2L5_Tier3, "DI"
    engine_2014_GM_EcoTec3_LV3_4L3_Tier2_PFI_no_deac, "PFI"
    engine_2014_GM_EcoTec3_LV3_4L3_Tier2_no_deac, "DI"
    engine_2015_Ford_EcoBoost_2L7_Tier2, "TURB11, DI"
    engine_2013_Ford_EcoBoost_1L6_Tier2, "TURB11, DI"
    engine_2016_Honda_L15B7_1L5_Tier2, "TURB12, DI, CEGR"
    engine_2014_Mazda_Skyactiv_US_2L0_Tier2, "DI, ATK2"
    engine_2016_toyota_TNGA_2L5_paper_image, "DI, ATK2, CEGR"
    engine_future_EPA_Atkinson_r2_2L5, "DI, ATK2, CEGR"

Where,

* :math:`PFI` is port fuel-injection
* :math:`DI` is direct fuel injection
* :math:`TURB` refers to turbocharging while the number represents a boost level and vintage combination (i.e., 11=level1, vintage1; 12=level1, vintage2)
* :math:`CEGR` is cooled EGR
* :math:`ATK` refers to Atkinson cycle (high compression ratio) while the number refers to a compression level

To calculate engine-related costs, the module makes use of the table on the engines worksheet of the alpha_package_costs_module_inputs
file. That table is shown in :numref:`engine_sheet`.

.. _engine_sheet:
.. csv-table:: Engine Tech Costs
    :widths: auto
    :header-rows: 1

    item,item_cost,dmc,dollar_basis
    dollars_per_cyl_8,750,500,2019
    dollars_per_cyl_6,825,550,2019
    dollars_per_cyl_4,900,600,2019
    dollars_per_cyl_3,975,650,2019
    dollars_per_liter,600,400,2019
    DI_3,366,244,2012
    DI_4,366,244,2012
    DI_6,551,368,2012
    DI_8,663,442,2012
    TURB11_3,694,463,2012
    TURB11_4,694,463,2012
    TURB11_6,1170,780,2012
    TURB11_8,1170,780,2012
    TURB12_3,694,463,2012
    TURB12_4,694,463,2012
    TURB12_6,1170,780,2012
    TURB12_8,1170,780,2012
    TURB21_3,1110,740,2012
    TURB21_4,1110,740,2012
    TURB21_6,1892,1261,2012
    TURB21_8,1892,1261,2012
    CEGR,170,114,2012
    DeacPD_3,114,76,2006
    DeacPD_4,114,76,2006
    DeacPD_6,204,136,2006
    DeacPD_8,228,152,2006
    DeacFC,231,154,2017
    ATK2_3,129,86,2010
    ATK2_4,129,86,2010
    ATK2_6,194,129,2010
    ATK2_8,306,204,2010

Where,

* :math:`dmc` refers to Direct Manufacturing Cost
* :math:`item\_cost` refers to the cost inclusive of indirect costs using the "Markup" value on the inputs_workbook worksheet

The module reads the displacement of the engine and the number of cylinders from the "Engine Displacement L" and "Engine Cylinders"
columns, respectively, of the ALPHA input file. Engine displacement and cylinder count costs are calculated as shown
in equation :math:numref:`cyl_count_and_displ_cost`.

.. Math::
    :label: cyl_count_and_displ_cost

    Cost_{Displacement, Cylinders} = Displacement \times \frac{$} {liter} + CylinderCount \times \frac{$} {cylinder}

Where,

* :math:`Cost_{Displacement, Cylinders}` is the cost of the engine block
* :math:`Displacement` comes from the package description in the ALPHA input file
* :math:`CylinderCount` comes from the package description in the ALPHA input file
* :math:`\frac{$} {liter}` comes from :numref:`engine_sheet`
* :math:`\frac{$} {cylinder}` comes from :numref:`engine_sheet`

If the engine is turbocharged (see :numref:`engines_and_techs`), the costs associated with turbocharging are calculated
as shown in equation :math:numref:`turbo_cost`.

.. Math::
    :label: turbo_cost

    & Cost_{turbocharging} \\
    & = \small Cost_{Displacement, Cylinders} \times (BoostMultiplier - 1) + TurboCost_{Level-Vintage, CylinderCount}

Where,

* :math:`Cost_{turbocharging}` is the cost associated with turbocharging including costs to improve robustness
* :math:`Cost_{Displacement, Cylinders}` is from equation :math:numref:`cyl_count_and_displ_cost`
* :math:`BoostMultiplier` is from the inputs_code worksheet of the alpha_package_costs_module_inputs file
* :math:`Level-Vintage` associated with the turbo is from :numref:`engines_and_techs`
* :math:`CylinderCount` comes from the package description in the ALPHA input file
* :math:`TurboCost_{Level-Vintage, CylinderCount}` comes from :numref:`engine_sheet`

If the engine is equipped with cooled EGR (see :numref:`engines_and_techs`), the costs associated with that technology
are read directly from :numref:`engine_sheet`.

If the engine is equipped with direct fuel-injection (see :numref:`engines_and_techs`), the costs associated with that
technology are read directly from :numref:`engine_sheet` along with the "Engine Cylinders" column of the ALPHA input file.

The presence of cylinder deactivation is read directly from the "DEAC D Cyl." and "DEAC C Cyl." columns of the ALHPA
input file where "DEAC D Cyl." refers to "Cylinder Deactivation: Partial Discrete," or DeacPD, and "DEAC C Cyl." refers
to "Cylinder Deactivation: Full Continuous," or DeacFC. The cylinder count data is read directly from the "Engine Cylinders"
column of the ALPHA input file.

The presence of Atkinson cycle technology is taken from :numref:`engines_and_techs` and the cylinder count data is read
directly from the "Engine Cylinders" column of the ALPHA input file.

Stop-start technology is also included in the engine-related costs and makes use of the table on the start_stop worksheet of the
alpha_package_costs_module_inputs file. That table is shown in :numref:`start_stop_sheet`.

.. _start_stop_sheet:
.. csv-table:: Start-Stop System Costs
    :widths: auto
    :header-rows: 1

    index,curb_weight_min,curb_weight_max,item_cost,dmc,dollar_basis
    0,0,3800,481.5,321,2015
    1,3800.1,4800,546,364,2015
    2,4800.1,8500,600,400,2015

Where,

* :math:`curb\_weight\_min` and :math:`curb\_weight\_max` are in pounds
* :math:`dmc` refers to Direct Manufacturing Cost
* :math:`item\_cost` refers to the cost inclusive of indirect costs using the "Markup" value on the inputs_workbook worksheet

The module determines the presence of start-stop from the "Start Stop" column of the ALPHA input file and determines curb
weight using the "Test Weight lbs" column of the ALPHA input file less 300 pounds (test weight is defined as curb weight
plus 300 pounds). Based on the curb weight, the start-stop system costs are determined based on the values in :numref:`start_stop_sheet`.

The engine-related costs can then be summed as shown in equation :math:numref:`engine_cost_equation`.

.. Math::
    :label: engine_cost_equation

    & Cost_{engine} \\
    & = \small Cost_{Displacement, Cylinders} + Cost_{turbocharging} + Cost_{cegr} \\
    & + \small Cost_{fuel\ system} + Cost_{cylinder\ deactivation} + Cost_{atk} + Cost_{start-stop}

Where,

* :math:`Cost_{engine}` is the cost of the ICE engine
* :math:`Cost_{Displacement, Cylinders}` is from equation :math:numref:`cyl_count_and_displ_cost`
* :math:`Cost_{turbocharging}` is from equation :math:numref:`turbo_cost` (note: this might be $0)
* :math:`Cost_{cegr}` is from :numref:`engines_and_techs` (note: this might be $0)
* :math:`Cost_{fuel\ system}` is from :numref:`engines_and_techs` (note: this might be $0)
* :math:`Cost_{cylinder\ deactivation}` is from :numref:`engines_and_techs` (note: this might be $0)
* :math:`Cost_{atk}` is from :numref:`engines_and_techs` (note: this might be $0)
* :math:`Cost_{start-stop}` is from :numref:`start_stop_sheet` (note: this might be $0)

ICE Transmission Costs
----------------------
To estimate ICE transmission costs, the module makes use of the "Transmission" column of the ALPHA input file and the
table on the trans worksheet of the alpha_package_costs_module_inputs file. That table is shown in :numref:`trans_sheet`.

.. _trans_sheet:
.. csv-table:: Transmission Costs
    :widths: auto
    :header-rows: 1

    trans_key,trans,drive,alpha_class,item_cost,dmc,dmc_increment,dollar_basis
    TRX10_FWD_LPW_LRL,TRX10,FWD,LPW_LRL,1200,800,0,2012
    TRX10_FWD_LPW_HRL,TRX10,FWD,LPW_HRL,1200,800,0,2012
    TRX10_FWD_MPW_LRL,TRX10,FWD,MPW_LRL,1200,800,0,2012
    TRX10_FWD_MPW_HRL,TRX10,FWD,MPW_HRL,1200,800,0,2012
    TRX10_FWD_HPW,TRX10,FWD,HPW,1200,800,0,2012
    TRX10_FWD_Truck,TRX10,FWD,Truck,1200,800,0,2012
    TRX11_FWD_LPW_LRL,TRX11,FWD,LPW_LRL,1261.5,841,41,2012
    TRX11_FWD_LPW_HRL,TRX11,FWD,LPW_HRL,1261.5,841,41,2012
    TRX11_FWD_MPW_LRL,TRX11,FWD,MPW_LRL,1261.5,841,41,2012
    TRX11_FWD_MPW_HRL,TRX11,FWD,MPW_HRL,1261.5,841,41,2012
    TRX11_FWD_HPW,TRX11,FWD,HPW,1261.5,841,41,2012
    TRX11_FWD_Truck,TRX11,FWD,Truck,1261.5,841,41,2012
    TRX12_FWD_LPW_LRL,TRX12,FWD,LPW_LRL,1594.5,1063,263,2012
    TRX12_FWD_LPW_HRL,TRX12,FWD,LPW_HRL,1594.5,1063,263,2012
    TRX12_FWD_MPW_LRL,TRX12,FWD,MPW_LRL,1594.5,1063,263,2012
    TRX12_FWD_MPW_HRL,TRX12,FWD,MPW_HRL,1594.5,1063,263,2012
    TRX12_FWD_HPW,TRX12,FWD,HPW,1594.5,1063,263,2012
    TRX12_FWD_Truck,TRX12,FWD,Truck,1594.5,1063,263,2012
    TRX21_FWD_LPW_LRL,TRX21,FWD,LPW_LRL,1467,978,178,2012
    TRX21_FWD_LPW_HRL,TRX21,FWD,LPW_HRL,1467,978,178,2012
    TRX21_FWD_MPW_LRL,TRX21,FWD,MPW_LRL,1467,978,178,2012
    TRX21_FWD_MPW_HRL,TRX21,FWD,MPW_HRL,1467,978,178,2012
    TRX21_FWD_HPW,TRX21,FWD,HPW,1467,978,178,2012
    TRX21_FWD_Truck,TRX21,FWD,Truck,1467,978,178,2012
    TRX22_FWD_LPW_LRL,TRX22,FWD,LPW_LRL,1801.5,1201,401,2012
    TRX22_FWD_LPW_HRL,TRX22,FWD,LPW_HRL,1801.5,1201,401,2012
    TRX22_FWD_MPW_LRL,TRX22,FWD,MPW_LRL,1801.5,1201,401,2012
    TRX22_FWD_MPW_HRL,TRX22,FWD,MPW_HRL,1801.5,1201,401,2012
    TRX22_FWD_HPW,TRX22,FWD,HPW,1801.5,1201,401,2012
    TRX22_FWD_Truck,TRX22,FWD,Truck,1801.5,1201,401,2012
    TRX10_AWD_LPW_LRL,TRX10,AWD,LPW_LRL,1440,960,0,2012
    TRX10_AWD_LPW_HRL,TRX10,AWD,LPW_HRL,1440,960,0,2012
    TRX10_AWD_MPW_LRL,TRX10,AWD,MPW_LRL,1440,960,0,2012
    TRX10_AWD_MPW_HRL,TRX10,AWD,MPW_HRL,1440,960,0,2012
    TRX10_AWD_HPW,TRX10,AWD,HPW,1440,960,0,2012
    TRX10_AWD_Truck,TRX10,AWD,Truck,1440,960,0,2012
    TRX11_AWD_LPW_LRL,TRX11,AWD,LPW_LRL,1513.8,1009.2,41,2012
    TRX11_AWD_LPW_HRL,TRX11,AWD,LPW_HRL,1513.8,1009.2,41,2012
    TRX11_AWD_MPW_LRL,TRX11,AWD,MPW_LRL,1513.8,1009.2,41,2012
    TRX11_AWD_MPW_HRL,TRX11,AWD,MPW_HRL,1513.8,1009.2,41,2012
    TRX11_AWD_HPW,TRX11,AWD,HPW,1513.8,1009.2,41,2012
    TRX11_AWD_Truck,TRX11,AWD,Truck,1513.8,1009.2,41,2012
    TRX12_AWD_LPW_LRL,TRX12,AWD,LPW_LRL,1913.4,1275.6,263,2012
    TRX12_AWD_LPW_HRL,TRX12,AWD,LPW_HRL,1913.4,1275.6,263,2012
    TRX12_AWD_MPW_LRL,TRX12,AWD,MPW_LRL,1913.4,1275.6,263,2012
    TRX12_AWD_MPW_HRL,TRX12,AWD,MPW_HRL,1913.4,1275.6,263,2012
    TRX12_AWD_HPW,TRX12,AWD,HPW,1913.4,1275.6,263,2012
    TRX12_AWD_Truck,TRX12,AWD,Truck,1913.4,1275.6,263,2012
    TRX21_AWD_LPW_LRL,TRX21,AWD,LPW_LRL,1760.4,1173.6,178,2012
    TRX21_AWD_LPW_HRL,TRX21,AWD,LPW_HRL,1760.4,1173.6,178,2012
    TRX21_AWD_MPW_LRL,TRX21,AWD,MPW_LRL,1760.4,1173.6,178,2012
    TRX21_AWD_MPW_HRL,TRX21,AWD,MPW_HRL,1760.4,1173.6,178,2012
    TRX21_AWD_HPW,TRX21,AWD,HPW,1760.4,1173.6,178,2012
    TRX21_AWD_Truck,TRX21,AWD,Truck,1760.4,1173.6,178,2012
    TRX22_AWD_LPW_LRL,TRX22,AWD,LPW_LRL,2161.8,1441.2,401,2012
    TRX22_AWD_LPW_HRL,TRX22,AWD,LPW_HRL,2161.8,1441.2,401,2012
    TRX22_AWD_MPW_LRL,TRX22,AWD,MPW_LRL,2161.8,1441.2,401,2012
    TRX22_AWD_MPW_HRL,TRX22,AWD,MPW_HRL,2161.8,1441.2,401,2012
    TRX22_AWD_HPW,TRX22,AWD,HPW,2161.8,1441.2,401,2012
    TRX22_AWD_Truck,TRX22,AWD,Truck,2161.8,1441.2,401,2012
    TRX10_RWD_LPW_LRL,TRX10,RWD,LPW_LRL,1200,800,0,2012
    TRX10_RWD_LPW_HRL,TRX10,RWD,LPW_HRL,1200,800,0,2012
    TRX10_RWD_MPW_LRL,TRX10,RWD,MPW_LRL,1200,800,0,2012
    TRX10_RWD_MPW_HRL,TRX10,RWD,MPW_HRL,1200,800,0,2012
    TRX10_RWD_HPW,TRX10,RWD,HPW,1200,800,0,2012
    TRX10_RWD_Truck,TRX10,RWD,Truck,1200,800,0,2012
    TRX11_RWD_LPW_LRL,TRX11,RWD,LPW_LRL,1261.5,841,41,2012
    TRX11_RWD_LPW_HRL,TRX11,RWD,LPW_HRL,1261.5,841,41,2012
    TRX11_RWD_MPW_LRL,TRX11,RWD,MPW_LRL,1261.5,841,41,2012
    TRX11_RWD_MPW_HRL,TRX11,RWD,MPW_HRL,1261.5,841,41,2012
    TRX11_RWD_HPW,TRX11,RWD,HPW,1261.5,841,41,2012
    TRX11_RWD_Truck,TRX11,RWD,Truck,1261.5,841,41,2012
    TRX12_RWD_LPW_LRL,TRX12,RWD,LPW_LRL,1594.5,1063,263,2012
    TRX12_RWD_LPW_HRL,TRX12,RWD,LPW_HRL,1594.5,1063,263,2012
    TRX12_RWD_MPW_LRL,TRX12,RWD,MPW_LRL,1594.5,1063,263,2012
    TRX12_RWD_MPW_HRL,TRX12,RWD,MPW_HRL,1594.5,1063,263,2012
    TRX12_RWD_HPW,TRX12,RWD,HPW,1594.5,1063,263,2012
    TRX12_RWD_Truck,TRX12,RWD,Truck,1594.5,1063,263,2012
    TRX21_RWD_LPW_LRL,TRX21,RWD,LPW_LRL,1467,978,178,2012
    TRX21_RWD_LPW_HRL,TRX21,RWD,LPW_HRL,1467,978,178,2012
    TRX21_RWD_MPW_LRL,TRX21,RWD,MPW_LRL,1467,978,178,2012
    TRX21_RWD_MPW_HRL,TRX21,RWD,MPW_HRL,1467,978,178,2012
    TRX21_RWD_HPW,TRX21,RWD,HPW,1467,978,178,2012
    TRX21_RWD_Truck,TRX21,RWD,Truck,1467,978,178,2012
    TRX22_RWD_LPW_LRL,TRX22,RWD,LPW_LRL,1801.5,1201,401,2012
    TRX22_RWD_LPW_HRL,TRX22,RWD,LPW_HRL,1801.5,1201,401,2012
    TRX22_RWD_MPW_LRL,TRX22,RWD,MPW_LRL,1801.5,1201,401,2012
    TRX22_RWD_MPW_HRL,TRX22,RWD,MPW_HRL,1801.5,1201,401,2012
    TRX22_RWD_HPW,TRX22,RWD,HPW,1801.5,1201,401,2012
    TRX22_RWD_Truck,TRX22,RWD,Truck,1801.5,1201,401,2012

Where,

* :math:`trans\_key` corresponds to the "Transmission" column of the ALPHA input file
* :math:`dmc\_increment` refers to the incremental cost relative to the TRX10 level transmission
* :math:`TRX10` refers to a base-level or "Null" transmission (nominally a 4 speed automatic transmission with no efficiency improvements)
* :math:`FWD`, :math:`AWD` and :math:`RWD` refer to front, all and rear wheel drive, respectively
* :math:`AWD` transmissions include a multiplicative scaler as specified via the user-defined "AWD_scaler" input on the inputs_workbook worksheet
* :math:`dmc` refers to the Direct Manufacturing Cost
* :math:`item\_cost` refers to the cost inclusive of indirect costs using the "Markup" value on the inputs_workbook worksheet

Accessories Costs
-----------------
To estimate ICE accessories costs, the module makes use of the "Accessory" column of the ALPHA input file and the
table on the accessories worksheet of the alpha_package_costs_module_inputs file. That table is shown in :numref:`accessories_sheet`.

.. _accessories_sheet:
.. csv-table:: Accessories Costs
    :widths: auto
    :header-rows: 1

    Accessory,item_cost,dmc,dollar_basis
    EPS,150,100,2015
    IACC1,0,0,2015
    IACC2,75,50,2015
    electric_EPS_LPW_LRL,150,100,2015
    electric_EPS_LPW_HRL,150,100,2015
    electric_EPS_MPW_LRL,150,100,2015
    electric_EPS_MPW_HRL,150,100,2015
    electric_EPS_HPW,150,100,2015
    electric_EPS_Truck,150,100,2015
    electric_HPS_LPW_LRL,150,100,2015
    electric_HPS_LPW_HRL,150,100,2015
    electric_HPS_MPW_LRL,150,100,2015
    electric_HPS_MPW_HRL,150,100,2015
    electric_HPS_HPW,150,100,2015
    electric_HPS_Truck,150,100,2015
    electric_EPS_HEA_REGEN_LPW_LRL,225,150,2015
    electric_EPS_HEA_REGEN_LPW_HRL,225,150,2015
    electric_EPS_HEA_REGEN_MPW_LRL,225,150,2015
    electric_EPS_HEA_REGEN_MPW_HRL,225,150,2015
    electric_EPS_HEA_REGEN_HPW,225,150,2015
    electric_EPS_HEA_REGEN_Truck,225,150,2015

Where,

* :math:`EPS` refers to electric power steering
* :math:`HPS` refers to hydraulic power steering
* :math:`IACC1` and :math:`IACC2` refer to levels of improved accessories with IACC2 including some level of regeneration
* :math:`HEA\_REGEN` refers to high efficiency alternator with regeneration (i.e., IACC2).
* :math:`dmc` refers to the Direct Manufacturing Cost
* :math:`item\_cost` refers to the cost inclusive of indirect costs using the "Markup" value on the inputs_workbook worksheet

Air Conditioning Costs
----------------------
Air conditioning costs are added to all packages using the table on the ac worksheet of the alpha_package_costs_module_inputs
file. That table is shown in :numref:`ac_sheet`.

.. _ac_sheet:
.. csv-table:: Air Conditioning Costs
    :widths: auto
    :header-rows: 1

    structure_class,item_cost,dmc,dollar_basis
    unibody,171,114,2010
    ladder,171,114,2010

Where,

* :math:`structure\_class` refers to the basic structure of the package
* :math:`unibody` and :math:`ladder` are determined by the module where ALPHA class "Truck" is ladder and all other ALPHA classes are unibody
* :math:`dmc` refers to the Direct Manufacturing Cost
* :math:`item\_cost` refers to the cost inclusive of indirect costs using the "Markup" value on the inputs_workbook worksheet

Aerodynamic Roadload Reduction Costs
------------------------------------
To estimate aerodynamic-related costs, the module makes use of the "Aero Improvement %" column of the ALPHA input file and the
table on the aero worksheet of the alpha_package_costs_module_inputs file. That table is shown in :numref:`aero_sheet`.

.. _aero_sheet:
.. csv-table:: Aerodynamic Roadload Reduction Costs
    :widths: auto
    :header-rows: 1

    aero_class,structure_class,Tech,aero,item_cost,dmc,dollar_basis
    unibody_0,unibody,Aero00,0,0,0,2015
    unibody_5,unibody,Aero05,5,15,10,2015
    unibody_10,unibody,Aero10,10,45,30,2015
    unibody_15,unibody,Aero15,15,111,74,2015
    unibody_20,unibody,Aero20,20,201,134,2015
    ladder_0,ladder,Aero00,0,0,0,2015
    ladder_5,ladder,Aero05,5,22.5,15,2015
    ladder_10,ladder,Aero10,10,45,30,2015
    ladder_15,ladder,Aero15,15,187.5,125,2015
    ladder_20,ladder,Aero20,20,292.5,195,2015

Where,

* :math:`structure\_class` refers to the basic structure of the package
* :math:`unibody` and :math:`ladder` are determined by the module where ALPHA class "Truck" is ladder and all other ALPHA classes are unibody
* :math:`aero` refers to varying levels of aerodynamic drag coefficient improvements (0% through 20% drag coefficient improvements)
* :math:`dmc` refers to the Direct Manufacturing Cost
* :math:`item\_cost` refers to the cost inclusive of indirect costs using the "Markup" value on the inputs_workbook worksheet

Non-Aerodynamic Roadload Reduction Costs
----------------------------------------
To estimate aerodynamic-related costs, the module makes use of the "Aero Improvement %" column of the ALPHA input file and the
table on the aero worksheet of the alpha_package_costs_module_inputs file. That table is shown in :numref:`nonaero_sheet`.

.. _nonaero_sheet:
.. csv-table:: Non-Aerodynamic Roadload Reduction Costs
    :widths: auto
    :header-rows: 1

    nonaero_class,structure_class,Tech,nonaero,item_cost,dmc,dollar_basis
    LDB,,LDB,99,82.5,55,2006
    LRRT1,,LRRT1,99,7.5,5,2006
    LRRT2,,LRRT2,99,60,40,2009
    unibody_0,unibody,NADR0,0,0,0,2015
    unibody_5,unibody,NADR1,5,7.5,5,2006
    unibody_10,unibody,NADR2,10,60,40,2009
    unibody_15,unibody,NADR3,15,90,60,2009
    unibody_20,unibody,NADR4,20,142.5,95,2009
    ladder_0,ladder,NADR0,0,0,0,2015
    ladder_5,ladder,NADR1,5,7.5,5,2006
    ladder_10,ladder,NADR2,10,60,40,2009
    ladder_15,ladder,NADR3,15,90,60,2009
    ladder_20,ladder,NADR4,20,142.5,95,2009

Where,

* :math:`LDB` refers to low-drag brakes
* :math:`LRRT1` and :math:`LRRT2` refer to low rolling resistence tires, level1 and level2
* :math:`NADR` refers to non-aero drag reduction at varying levels 0% through 20%
* :math:`structure\_class` refers to the basic structure of the package
* :math:`unibody` and :math:`ladder` are determined by the module where ALPHA class "Truck" is ladder and all other ALPHA classes are unibody
* :math:`aero` refers to varying levels of aerodynamic drag coefficient improvements (0% through 20% drag coefficient improvements)
* :math:`dmc` refers to the Direct Manufacturing Cost
* :math:`item\_cost` refers to the cost inclusive of indirect costs using the "Markup" value on the inputs_workbook worksheet

Roadload Reduction Costs
------------------------
Roadload reduction costs are calculated as the sum of Aerodynamic Roadload Reduction and Non-Aerodynamic Roadload Reduction Costs
as shown in equation :math:numref:`roadload_reduction_cost_equation`.

.. Math::
    :label: roadload_reduction_cost_equation

    Cost_{roadload\_reduction} = Cost_{aero\_roadload\_reduction} + Cost_{nonaero\_roadload\_reduction}

Where,

* :math:`Cost_{roadload\_reduction}` are costs associated with roadload reduction
* :math:`Cost_{aero\_roadload\_reduction}` is from :numref:`aero_sheet`
* :math:`Cost_{nonaero\_roadload\_reduction}` is from :numref:`nonaero_sheet`

Electrified Vehicle Costs
-------------------------
For any battery electric vehicle (BEV), plug-in hybrid electric vehicle (PHEV), or hybrid electric vehicle (HEV), battery
costs are estimated using the table on the electrification metrics worksheet worksheet of the alpha_package_costs_module_inputs file.
That table is shown in :numref:`electrified_metrics_sheet`.

.. _electrified_metrics_sheet:
.. csv-table:: Electrification Metrics
    :widths: auto
    :header-rows: 1

    item,bev,phev,hev
    usable_soc,0.9,0.8,0.4
    gap,0.3,0.25,0.2
    electrification_markup,1.5,1.5,1.5
    co2_reduction_cycle,1,0.6,0.2
    co2_reduction_city,1,0.733333333,0.244444444
    co2_reduction_hwy,1,0.490909091,0.163636364

Where,

* :math:`usable\_soc` refers to the usable state-of-charge of the battery pack
* :math:`gap` refers to the 2-cycle to onroad "gap"
* :math:`powertrain\_markup` refers to the markup factors applied to direct manufacturing costs to cover indirect costs
* :math:`co2\_reduction\_cycle` refers to the 2-cycle CO2 reduction provided by the electrification (user defined)
* :math:`co2\_reduction\_city` refers to the city-cycle CO2 reduction (calculated as 55/45 times the 2-cycle value)
* :math:`co2\_reduction\_hwy` refers to the highway-cycle CO2 reduction (calculated as 45/55 times the 2-cycle value)

Battery costs also make use of the tables from the appropriate bev_curves, phev_curves and hev_curves worksheets of the
alpha_package_costs_module_inputs file. Those tables and how they are used are discussed below for BEV batteries, HEV
batteries and then PHEV batteries.

BEV Battery Costs
+++++++++++++++++
For BEV battery costs, the module first determines the gross energy content of the BEV battery pack. This is done using the
"Combined Consumption Rate" column of the ALPHA input file which is expressed in kWh/100 miles. The gross energy content
of the BEV battery pack is then calculated as shown in equation :math:numref:`bev_kwh_gross_equation`.

.. Math::
    :label: bev_kwh_gross_equation

    kWh_{gross} = \frac{(\frac{kWh} {100 miles} \times \frac{OnroadRange} {usable\_soc})} {(1 - gap)}

Where,

* :math:`kWh_{gross}` refers to the gross energy content of the BEV battery pack
* :math:`\frac{kWh} {100 miles}` is from the "Combined Consumption Rate" column of the ALPHA input file
* :math:`OnroadRange` is in miles and is currently set via the InputSettings class of the alpha_package_costs module (currently=300)
* :math:`usable\_soc` and :math:`gap` are from the "bev" column of :numref:`electrified_metrics_sheet`

The module then uses the table on the bev_curves worksheet of the alpha_package_costs_module_inputs
file. That table is shown in :numref:`bev_curves_sheet`.

.. _bev_curves_sheet:
.. csv-table:: BEV Battery Curves
    :widths: auto
    :header-rows: 1

    item,x_cubed_factor,x_squared_factor,x_factor,constant,dollar_basis
    dollars_per_kWh_curve,-0.00009556,0.02652171,-2.56085176,193.1905512,2019
    kWh_pack_per_kg_pack_curve,8.47E-08,-2.49011E-05,0.002368641,0.124566816,0

The BEV battery cost is then calculated as shown in equation :math:numref:`battery_cost_equation`.

HEV Battery Costs
+++++++++++++++++
For HEV battery costs, the module first determines the gross energy content of the HEV battery pack. This is done by first
creating HEV packages from the ALPHA ICE packages via the make_hev_from_alpha_ice module. The make_hev_from_alpha_ice module
selects specific ICE packages for use as HEVs using the "Vehicle Type" and "Start Stop" columns of the ALPHA input file
and applying the following logic:

    - if "Vehicle Type" is "Truck" select only turbocharged packages;
    - if "Vehicle Type" is not "Truck" select only non-turbocharged packages;
    - if "Start Stop" is TRUE (value=1) then eliminate the package

This logic leaves only turbocharged Truck packages without start-stop and non-turbocharged non-Truck packages without
start-stop. Start-stop packages are eliminated in this process because the costs of start-stop technologies are included
in the HEV non-battery costs, and the GHG reducing impacts of the start-stop technologies are included in the co2_reduction entries
shown in :numref:`electrified_metrics_sheet`. Turbocharged truck packages are chosen since trucks are assumed to
require the hauling capability provided by turbocharging.

The make_hev_from_alpha_ice module then makes use of the "Test Weight lbs" column of the chosen packages less 300 pounds
to determine the curb weight of the package and converts that to kg by dividing by 2.2 pounds/kg. The make_hev_from_alpha_ice module
then makes use of the table on the hev_curves worksheet of the alpha_package_costs_module_inputs file. That table is
shown in :numref:`hev_curves_sheet`.

.. _hev_curves_sheet:
.. csv-table:: HEV Battery & Motor Curves
    :widths: auto
    :header-rows: 1

    item,x_cubed_factor,x_squared_factor,x_factor,constant,dollar_basis
    kWh_pack_per_kg_curbwt_curve,0,0,0.001,0.141,0
    kW_motor_per_kg_curbwt_curve,0,0,0.0279,-13.269,0
    kWh_pack_per_kg_pack_curve,0,0,0.0142,0.0648,0
    dollars_per_kWh_curve,0,0,-250.72,1058.2,2017

With the curb weight of the package and the kWh_pack_per_kg_curbwt_curve entries shown in :numref:`hev_curves_sheet`, the
HEV battery energy content is then calculated as shown in equation :math:numref:`hev_kwh_gross`.

.. Math::
    :label: hev_kwh_gross_equation

    kWh_{gross} = A \times CurbWeight^3 + B \times CurbWeight^2 + C \times CurbWeight + D

Where,

* :math:`A` refers to the x_cubed_factor of the kWh_pack_per_kg_curbwt_curve from :numref:`hev_curves_sheet`
* :math:`B` refers to the x_squared_factor of the kWh_pack_per_kg_curbwt_curve from :numref:`hev_curves_sheet`
* :math:`C` refers to the x_factor of the kWh_pack_per_kg_curbwt_curve from :numref:`hev_curves_sheet`
* :math:`D` refers to the constant factor of the kWh_pack_per_kg_curbwt_curve from :numref:`hev_curves_sheet`

The HEV battery cost is then calculated as shown in equation :math:numref:`battery_cost_equation`.

PHEV Battery Costs
++++++++++++++++++
For PHEV battery costs, the make_hev_from_alpha_ice module uses the same packages chosen for conversion to HEV, but makes
use of the table on the phev_curves worksheet of the alpha_package_costs_module_inputs file. That table is
shown in :numref:`phev_curves_sheet`.

.. _phev_curves_sheet:
.. csv-table:: PHEV Battery & Motor Curves
    :widths: auto
    :header-rows: 1

    item,x_cubed_factor,x_squared_factor,x_factor,constant,dollar_basis
    kWh_pack_per_kg_curbwt_curve,0,0,0.004,3.525,0
    kW_motor_per_kg_curbwt_curve,0,0,0.0279,-13.269,0
    dollars_per_kWh_curve,-0.00009556,0.02652171,-2.56085176,193.1905512,2019
    kWh_pack_per_kg_pack_curve,8.47E-08,-2.49011E-05,0.002368641,0.124566816,0

With the curb weight of the package and the kWh_pack_per_kg_curbwt_curve entries shown in :numref:`phev_curves_sheet`, the
PHEV battery energy content is then calculated as shown in equation :math:numref:`phev_kwh_gross`.

.. Math::
    :label: phev_kwh_gross_equation

    kWh_{gross} = A \times CurbWeight^3 + B \times CurbWeight^2 + C \times CurbWeight + D

Where,

* :math:`A` refers to the x_cubed_factor of the kWh_pack_per_kg_curbwt_curve from :numref:`phev_curves_sheet`
* :math:`B` refers to the x_squared_factor of the kWh_pack_per_kg_curbwt_curve from :numref:`phev_curves_sheet`
* :math:`C` refers to the x_factor of the kWh_pack_per_kg_curbwt_curve from :numref:`phev_curves_sheet`
* :math:`D` refers to the constant factor of the kWh_pack_per_kg_curbwt_curve from :numref:`phev_curves_sheet`

The PHEV battery cost is then calculated as shown in equation :math:numref:`battery_cost_equation`.

Battery Cost Equation
+++++++++++++++++++++
With the gross energy content of the battery pack and the dollars_per_kWh_curve entries of :numref:`bev_curves_sheet`
or :numref:`phev_curves_sheet` or :numref:`hev_curves_sheet`, depending on the package
being considered, the battery pack cost is calculated as shown in equation :math:numref:`battery_cost_equation`.

.. Math::
    :label: battery_cost_equation

    Cost_{battery} = \small kWh_{gross} \times (A \times kWh_{gross}^3 + B \times kWh_{gross}^2 + C \times kWh_{gross} + D) \times Markup

Where,

* :math:`Cost_{battery}` is the cost of the battery pack
* :math:`kWh_{gross}` refers to the gross energy content of the battery pack from equation :math:numref:`bev_kwh_gross_equation` or :math:numref:`hev_kwh_gross_equation` or :math:numref:`phev_kwh_gross_equation`
* :math:`A` refers to the x_cubed_factor of the dollars_per_kWh_curve from :numref:`bev_curves_sheet`, :numref:`hev_curves_sheet` or :numref:`phev_curves_sheet`
* :math:`B` refers to the x_squared_factor of the dollars_per_kWh_curve from :numref:`bev_curves_sheet`, :numref:`hev_curves_sheet` or :numref:`phev_curves_sheet`
* :math:`C` refers to the x_factor of the dollars_per_kWh_curve from :numref:`bev_curves_sheet`, :numref:`hev_curves_sheet` or :numref:`phev_curves_sheet`
* :math:`D` refers to the constant factor of the dollars_per_kWh_curve from :numref:`bev_curves_sheet`, :numref:`hev_curves_sheet` or :numref:`phev_curves_sheet`
* :math:`Markup` refers to the applicable electrification markup factor from :numref:`electrified_metrics_sheet`

BEV, PHEV and HEV Non-Battery Costs
+++++++++++++++++++++++++++++++++++
For BEV, PHEV and HEV non-battery costs (motors, inverters, etc.), the alpha_package_costs module makes use of the tables on
the bev_nonbattery_single, bev_nonbattery_dual, phev_nonbattery_single, or phev_nonbattery_dual or hev_nonbattery worksheets
of the alpha_package_costs_module_inputs file. These four tables are shown in :numref:`bev_nonbattery_single_sheet`
and :numref:`bev_nonbattery_dual_sheet` and :numref:`phev_nonbattery_single_sheet` and :numref:`phev_nonbattery_dual_sheet`
and :numref:`hev_nonbattery_sheet`.

.. _bev_nonbattery_single_sheet:
.. csv-table:: BEV Non-Battery Curves for Single Motor Systems
    :widths: auto
    :header-rows: 1

    item,quantity,slope,intercept,scale_by,dollar_basis
    motor,1,4.29,0,Vehicle kW,2019
    inverter,1,2.5,0,Vehicle kW,2019
    induction_motor,0,0,0,,0
    induction_inverter,0,0,0,,0
    kW_DCDC_converter,1,0,3.5,kW value to be added to OBC kW value,0
    OBC_and_DCDC_converter,1,39.7537931,0,"DC-DC kW (3.5) + OBC kW (7,11,19)",2019
    HV_orange_cables,1,9.5,161.5,Vehicle size class (1-7),2019
    LV_battery,1,3,51,Vehicle size class (1-7),2019
    HVAC,1,11.5,195.5,Vehicle size class (1-7),2019
    single_speed_gearbox,1,0,410,none at this time,2019
    powertrain_cooling_loop,1,0,300,none at this time,2019
    charging_cord_kit,1,0,200,none at this time,2019
    DC_fast_charge_circuitry,1,0,160,none at this time,2019
    power_management_and_distribution,1,0,720,none at this time,2019
    brake_sensors_actuators,0,0,0,,0
    additional_pair_of_half_shafts,0,0,0,,0

.. _bev_nonbattery_dual_sheet:
.. csv-table:: BEV Non-Battery Curves for Dual Motor Systems
    :widths: auto
    :header-rows: 1

    item,quantity,slope,intercept,scale_by,dollar_basis
    motor,1,4.29,0,Vehicle kW / 2,2019
    inverter,1,2.5,0,Vehicle kW / 2,2019
    induction_motor,1,3.12,0,Vehicle kW / 2,0
    induction_inverter,1,4,0,Vehicle kW / 2,0
    kW_DCDC_converter,1,0,3.5,kW value to be added to OBC kW value,0
    OBC_and_DCDC_converter,1,39.7537931,0,"DC-DC kW (3.5) + OBC kW (7,11,19)",2019
    HV_orange_cables,1,9.5,161.5,Vehicle size class (1-7),2019
    LV_battery,1,3,51,Vehicle size class (1-7),2019
    HVAC,1,11.5,195.5,Vehicle size class (1-7),2019
    single_speed_gearbox,2,0,410,none at this time,2019
    powertrain_cooling_loop,2,0,300,none at this time,2019
    charging_cord_kit,1,0,200,none at this time,2019
    DC_fast_charge_circuitry,1,0,160,none at this time,2019
    power_management_and_distribution,1,0,720,none at this time,2019
    brake_sensors_actuators,0,0,0,,0
    additional_pair_of_half_shafts,1,0,190,none at this time,0

.. _phev_nonbattery_single_sheet:
.. csv-table:: PHEV Non-Battery Curves for Single Motor Systems
    :widths: auto
    :header-rows: 1

    item,quantity,slope,intercept,scale_by,dollar_basis
    motor,1,4.29,0,Vehicle kW,2019
    inverter,1,2.5,0,Vehicle kW,2019
    induction_motor,0,0,0,,0
    induction_inverter,0,0,0,,0
    kW_DCDC_converter,1,0,3.5,kW value to be added to OBC kW value,0
    OBC_and_DCDC_converter,1,39.7537931,0,"DC-DC kW (3.5) + OBC kW (0.7,1.1,1.9)",2019
    HV_orange_cables,1,9.5,161.5,Vehicle size class (1-7),2019
    LV_battery,1,3,51,Vehicle size class (1-7),2019
    HVAC,1,11.5,195.5,Vehicle size class (1-7),2019
    single_speed_gearbox,1,0,410,none at this time,2019
    powertrain_cooling_loop,1,0,300,none at this time,2019
    charging_cord_kit,1,0,200,none at this time,2019
    DC_fast_charge_circuitry,1,0,160,none at this time,2019
    power_management_and_distribution,1,0,720,none at this time,2019
    brake_sensors_actuators,0,0,0,,0
    additional_pair_of_half_shafts,0,0,0,,0

.. _phev_nonbattery_dual_sheet:
.. csv-table:: PHEV Non-Battery Curves for Dual Motor Systems
    :widths: auto
    :header-rows: 1

    item,quantity,slope,intercept,scale_by,dollar_basis
    motor,1,4.29,0,Vehicle kW / 2,2019
    inverter,1,2.5,0,Vehicle kW / 2,2019
    induction_motor,1,3.12,0,Vehicle kW / 2,0
    induction_inverter,1,4,0,Vehicle kW / 2,0
    kW_DCDC_converter,1,0,3.5,kW value to be added to OBC kW value,0
    OBC_and_DCDC_converter,1,39.7537931,0,"DC-DC kW (3.5) + OBC kW (0.7,1.1,1.9)",2019
    HV_orange_cables,1,9.5,161.5,Vehicle size class (1-7),2019
    LV_battery,1,3,51,Vehicle size class (1-7),2019
    HVAC,1,11.5,195.5,Vehicle size class (1-7),2019
    single_speed_gearbox,2,0,410,none at this time,2019
    powertrain_cooling_loop,2,0,300,none at this time,2019
    charging_cord_kit,1,0,200,none at this time,2019
    DC_fast_charge_circuitry,1,0,160,none at this time,2019
    power_management_and_distribution,1,0,720,none at this time,2019
    brake_sensors_actuators,0,0,0,,0
    additional_pair_of_half_shafts,1,0,190,none at this time,0

.. _hev_nonbattery_sheet:
.. csv-table:: HEV Non-Battery Curves
    :widths: auto
    :header-rows: 1

    item,quantity,slope,intercept,scale_by,dollar_basis
    motor,1,6.91,-8.64,Motor kW,2019
    inverter,1,2.4,231,Motor kW,2019
    induction_motor,0,0,0,,0
    induction_inverter,0,0,0,,0
    kW_DCDC_converter,1,0,3.5,kW value,0
    OBC_and_DCDC_converter,1,39.7537931,0,DCDC converter kW (3.5),2019
    HV_orange_cables,1,9.5,161.5,Vehicle size class (1-7),2019
    LV_battery,1,3,51,Vehicle size class (1-7),2019
    HVAC,1,11.5,195.5,Vehicle size class (1-7),2019
    single_speed_gearbox,0,0,0,,0
    powertrain_cooling_loop,0,0,0,,0
    charging_cord_kit,0,0,0,,0
    DC_fast_charge_circuitry,0,0,0,,0
    power_management_and_distribution,0,0,0,,0
    brake_sensors_actuators,1,0,200,none at this time,2019
    additional_pair_of_half_shafts,0,0,0,,0

The first step makes use of the structure_class determination for the given package and specifies that unibody packages
have a single motor system while ladder-frame packages have a dual motor system for hauling. For BEV packages, the motor power is
currently set in the InputSettings class of the alpha_package_costs module (the current setting is 150 kW). For HEV and
PHEV packages, the motor power is determined in the make_hev_from_alpha_ice module using the kW_motor_per_kg_curbwt_curve
entries shown in :numref:`hev_curves_sheet` and :numref:`phev_curves_sheet`, respectively, according to equation :math:numref:`motor_power_equation`.

.. Math::
    :label: motor_power_equation

    kW_{motor} = A \times CurbWeight^3 + B \times CurbWeight^2 + C \times CurbWeight + D

Where,

* :math:`kW_{motor}` is the motor power of the electrified system
* :math:`A` refers to the x_cubed_factor of the kW_motor_per_kg_curbwt_curve from :numref:`hev_curves_sheet` or :numref:`phev_curves_sheet`
* :math:`B` refers to the x_squared_factor of the kW_motor_per_kg_curbwt_curve from :numref:`hev_curves_sheet` or :numref:`phev_curves_sheet`
* :math:`C` refers to the x_factor of the kW_motor_per_kg_curbwt_curve from :numref:`hev_curves_sheet` or :numref:`phev_curves_sheet`
* :math:`D` refers to the constant factor of the kW_motor_per_kg_curbwt_curve from :numref:`hev_curves_sheet` or :numref:`phev_curves_sheet`

The motor cost for BEV, PHEV and HEV packages is then calculated as shown in equation :math:numref:`motor_cost_equation`.

.. Math::
    :label: motor_cost_equation

    Cost_{motor} = Quantity_{motor} \times Slope_{motor} \times \frac{kW_{motor}} {PowerDivisor_{motor}} + Intercept_{motor}

Where,

* :math:`Cost_{motor}` is the cost of the motor(s) in the electrified system
* :math:`Quantity_{motor}` and :math:`Slope_{motor}` and :math:`Intercept_{motor}` are from the applicable Non-Battery Curve table
* :math:`kW_{motor}` is from the InputSettings class for BEVs (currently set at 150 kW) or from equation :math:numref:`motor_power_equation` for PHEVs and HEVs
* :math:`PowerDivisor_{motor}` is 1 for single motor systems and 2 for dual motor systems

The inverter cost is then calculated as shown in equation :math:numref:`inverter_cost_equation`.

.. Math::
    :label: inverter_cost_equation

    Cost_{inverter} = Quantity_{inverter} \times Slope_{inverter} \times \frac{kW_{motor}} {PowerDivisor_{motor}} + Intercept_{inverter}

Where,

* :math:`Cost_{inverter}` is the cost of motors in the system
* :math:`Quantity_{inverter}` and :math:`Slope_{inverter}` and :math:`Intercept_{inverter}` are from the applicable Non-Battery Curve table
* :math:`kW_{motor}` is from the InputSettings class for BEVs (currently set at 150 kW) or from equation :math:numref:`motor_power_equation` for PHEVs and HEVs
* :math:`PowerDivisor_{motor}` is 1 for single motor systems and 2 for dual motor systems

The induction motor cost is then calculated as shown in equation :math:numref:`induction_motor_cost_equation`.

.. Math::
    :label: induction_motor_cost_equation

    & \small Cost_{induction\_motor} = Quantity_{induction\_motor} \times Slope_{induction\_motor} \times \frac{kW_{motor}} {PowerDivisor_{motor}} \\
    & \small + Intercept_{induction\_motor}

Where,

* :math:`Cost_{induction\_motor}` is the cost of motors in the system
* :math:`Quantity_{induction\_motor}` and :math:`Slope_{induction\_motor}` and :math:`Intercept_{induction\_motor}` are from the applicable Non-Battery Curve table
* :math:`kW_{motor}` is from the InputSettings class for BEVs (currently set at 150 kW) or from equation :math:numref:`motor_power_equation` for PHEVs and HEVs
* :math:`PowerDivisor_{motor}` is 1 for single motor systems and 2 for dual motor systems

The induction inverter cost is then calculated as shown in equation :math:numref:`induction_inverter_cost_equation`.

.. Math::
    :label: induction_inverter_cost_equation

    & \small Cost_{induction\_inverter} = Quantity_{induction\_inverter} \times Slope_{induction\_inverter} \times \frac{kW_{motor}} {PowerDivisor_{motor}} \\
    & \small + Intercept_{induction\_inverter}

Where,

* :math:`Cost_{induction\_inverter}` is the cost of motors in the system
* :math:`Quantity_{induction\_inverter}` and :math:`Slope_{induction\_inverter}` and :math:`Intercept_{induction\_inverter}` are from the applicable Non-Battery Curve table
* :math:`kW_{motor}` is from the InputSettings class for BEVs (currently set at 150 kW) or from equation :math:numref:`motor_power_equation` for PHEVs and HEVs
* :math:`PowerDivisor_{motor}` is 1 for single motor systems and 2 for dual motor systems

To estimate the onboard charger and DC-DC converter cost, the module first determines the onboard charger power
based on the energy content of the battery pack (see equation :math:numref:`bev_kwh_gross` or equation :math:numref:`hev_kwh_gross`
or equation :math:numref:`phev_kwh_gross`). The onboard charger power is then determined according to the parameters shown
in :numref:`onboard_charger_table`.

.. _onboard_charger_table:
.. csv-table:: Onboard Charger Power Table
    :widths: auto
    :header-rows: 1

    type,battery pack gross energy content (kWh),onboard charger power (kW)
    bev,<70,7
     ,70 to <100,11
     ,>=100,19
    phev,<7,0.7
     ,7 to <10,1.1
     ,>=10,1.9

The cost of the onboard charger (OBD) and DC-DC converter are then calculated as shown in equation :math:numref:`obc_and_dcdc_converter_cost_equation`.

.. Math::
    :label: obc_and_dcdc_converter_cost_equation

    & \small Cost_{OBC\_and\_DCDC\_converter} = Quantity_{OBC\_and\_DCDC\_converter} \times Slope_{OBC\_and\_DCDC\_converter} \\
    & \small \times (kW_{OBC} + kW_{DC-DC\_converter})

Where,

* :math:`Cost_{OBC\_and\_DCDC\_converter}` is the cost of onboard charger (OBC) plus the DC-DC converter
* :math:`Quantity_{OBC\_and\_DCDC\_converter}` and :math:`Slope_{OBC\_and\_DCDC\_converter}` are from are from the applicable Non-Battery Curve table
* :math:`kW_{OBC}` is the power of the OBC from :numref:`onboard_charger_table`
* :math:`kW_{DC-DC\_converter}` is from the applicable Non-Battery Curve table

Costs associated with high voltage orange cables (hv_orange_cables) are calculated as shown in equation :math:numref:`hv_orange_cables_cost_equation`
which includes a "SizeScaler" parameter. The size scaler considers the full range of curb weights within the given electrified
vehicle category (BEV, PHEV, HEV) and breaks that range into a number of equal sized bins where the number of bins is
currently controlled via the InputSettings class of the alpha_package_costs module. Currently the number of bins is set to
seven for each electrified vehicle category. This results in an integer scaler value from 1 to the number of bins (currently 7).
Depending on the curb weight of the given package, the applicable SizeScaler will be applied within equation :math:numref:`hv_orange_cables_cost_equation`.

.. Math::
    :label: hv_orange_cables_cost_equation

    & Cost_{hv\_orange\_cables} = Quantity_{hv\_orange\_cables} \times Slope_{hv\_orange\_cables} \times SizeScaler \\
    & + Intercept_{hv\_orange\_cables}

Where,

* :math:`Cost_{hv\_orange\_cables}` is the cost of the high voltage orange cables
* :math:`Quantity_{hv\_orange\_cables}` and :math:`Slope_{hv\_orange\_cables}` and :math:`Intercept_{hv\_orange\_cables}` are from the applicable Non-Battery Curve table
* :math:`SizeScaler` is determined within the alpha_package_costs module (see explanation above)

The low voltage battery (lv_battery) cost is then calculated as shown in equation :math:numref:`low_voltage_battery_cost_equation`.

.. Math::
    :label: low_voltage_battery_cost_equation

    Cost_{lv\_battery} = Quantity_{lv\_battery} \times Slope_{lv\_battery} \times SizeScaler + Intercept_{lv\_battery}

Where,

* :math:`Cost_{lv\_battery}` is the cost of the low voltage battery
* :math:`Quantity_{lv\_battery}` and :math:`Slope_{lv\_battery}` and :math:`Intercept_{lv\_battery}` are from the applicable Non-Battery Curve table
* :math:`SizeScaler` is determined within the alpha_package_costs module (see explanation above).

The heating-ventilation-air conditioning (hvac) associated costs are then calculated as shown in equation :math:numref:`hvac_cost_equation`.

.. Math::
    :label: hvac_cost_equation

    Cost_{hvac} = Quantity_{hvac} \times Slope_{hvac} \times SizeScaler + Intercept_{hvac}

Where,

* :math:`Cost_{hvac}` is the cost associated with heating-ventilation-air conditioning (hvac)
* :math:`Quantity_{hvac}` and :math:`Slope_{hvac}` and :math:`Intercept_{hvac}` are from the applicable Non-Battery Curve table

The single-speed gearbox costs are then calculated as shown in equation :math:numref:`single_speed_gearbox_cost_equation`.

.. Math::
    :label: single_speed_gearbox_cost_equation

    Cost_{single\_speed\_gearbox} = Quantity_{single\_speed\_gearbox} \times Intercept_{single\_speed\_gearbox}

Where,

* :math:`Cost_{single\_speed\_gearbox}` is the cost of the single-speed gearbox
* :math:`Quantity_{single\_speed\_gearbox}` and :math:`Intercept_{single\_speed\_gearbox}` are from the applicable Non-Battery Curve table

The powertrain cooling loop costs are then calculated as shown in equation :math:numref:`powertrain_cooling_loop_cost_equation`.

.. Math::
    :label: powertrain_cooling_loop_cost_equation

    Cost_{powertrain\_cooling\_loop} = Quantity_{powertrain\_cooling\_loop} \times Intercept_{powertrain\_cooling\_loop}

Where,

* :math:`Cost_{powertrain\_cooling\_loop}` is the cost of the powertrain cooling loop
* :math:`Quantity_{powertrain\_cooling\_loop}` and :math:`Intercept_{powertrain\_cooling\_loop}` are from the applicable Non-Battery Curve table

The charging cord kit costs are then calculated as shown in equation :math:numref:`charging_cord_kit_cost_equation`.

.. Math::
    :label: charging_cord_kit_cost_equation

    Cost_{charging\_cord\_kit} = Quantity_{charging\_cord\_kit} \times Intercept_{charging\_cord\_kit}

Where,

* :math:`Cost_{charging\_cord\_kit}` is the cost of the charging cord kit
* :math:`Quantity_{charging\_cord\_kit}` and :math:`Intercept_{charging\_cord\_kit}` are from the applicable Non-Battery Curve table

The DC fast charge circuitry costs are then calculated as shown in equation :math:numref:`dc_fast_charge_circuitry_cost_equation`.

.. Math::
    :label: dc_fast_charge_circuitry_cost_equation

    Cost_{DC\_fast\_charge\_circuitry} = Quantity_{DC\_fast\_charge\_circuitry} \times Intercept_{DC\_fast\_charge\_circuitry}

Where,

* :math:`Cost_{DC\_fast\_charge\_circuitry}` is the cost of the DC fast charge circuitry
* :math:`Quantity_{DC\_fast\_charge\_circuitry}` and :math:`Intercept_{DC\_fast\_charge\_circuitry}` are from the applicable Non-Battery Curve table

The power management and distribution (power_mgmt_dist) costs are then calculated as shown in equation :math:numref:`power_mgmt_dist_cost_equation`.

.. Math::
    :label: power_mgmt_dist_cost_equation

    Cost_{power\_mgmt\_dist} = Quantity_{power\_mgmt\_dist} \times Intercept_{power\_mgmt\_dist}

Where,

* :math:`Cost_{power\_mgmt\_dist}` is the cost of power management and distribution
* :math:`Quantity_{power\_mgmt\_dist}` and :math:`Intercept_{power\_mgmt\_dist}` are from the applicable Non-Battery Curve table

The cost of an additional pair of half-shafts (on dual motor PEVs) are then calculated as shown in equation :math:numref:`half_shaft_cost_equation`.

.. Math::
    :label: half_shaft_cost_equation

    Cost_{additional\_half\_shafts} = Quantity_{additional\_half\_shafts} \times Intercept_{additional\_half\_shafts}

Where,

* :math:`Cost_{additional\_half\_shafts}` is the cost of an additional pair of half-shafts on dual motor PEVs
* :math:`Quantity_{additional\_half\_shafts}` and :math:`Intercept_{additional\_half\_shafts}` are from the applicable Non-Battery Curve table

The cost of brake sensors and actuators (on HEVs) are then calculated as shown in equation :math:numref:`brake_sensors_cost_equation`.

.. Math::
    :label: brake_sensors_cost_equation

    \small Cost_{brake\_sensors\_and\_actuators} = Quantity_{brake\_sensors\_and\_actuators} \times Intercept_{brake\_sensors\_and\_actuators}

Where,

* :math:`Cost_{brake\_sensors\_and\_actuators}` is the cost of brake sensors and actuators on HEVs
* :math:`Quantity_{brake\_sensors\_and\_actuators}` and :math:`Intercept_{brake\_sensors\_and\_actuators}` are from the applicable Non-Battery Curve table

The non-battery system costs can then be calculated by summing the above as shown in equation :math:numref:`non_battery_cost_equation`.

.. Math::
    :label: non_battery_cost_equation

    & \small Cost_{non\_battery} = Markup \times (Cost_{motor} + Cost_{inverter} + Cost_{induction\_motor} \\
    & \small + Cost_{induction\_inverter} + Cost_{OBC\_and\_DCDC\_converter} + Cost_{hv\_orange\_cables} + Cost_{low\_voltage\_battery} \\
    & \small + Cost_{hvac} + Cost_{single\_speed\_gearbox} + Cost_{powertrain\_cooling\_loop} + Cost_{charging\_cord\_kit} \\
    & \small + Cost_{DC\_fast\_charge\_circuitry} + Cost_{power\_mgmt\_dist} + Cost_{additional\_half\_shafts} + Cost_{brake\_sensors\_and\_actuators})

Where,

* :math:`Cost_{non\_battery}` is the cost of the non-battery elements of electrified vehicles
* :math:`Markup` is from :numref:`electrified_metrics_sheet`
* :math:`Cost_{motor}` is from equation :math:numref:`motor_cost_equation`
* :math:`Cost_{inverter}` is from equation :math:numref:`inverter_cost_equation`
* :math:`Cost_{induction\_motor}` is from equation :math:numref:`induction_motor_cost_equation`
* :math:`Cost_{induction\_inverter}` is from equation :math:numref:`induction_inverter_cost_equation`
* :math:`Cost_{OBC\_and\_DCDC\_converter}` is from equation :math:numref:`obc_and_dcdc_converter_cost_equation`
* :math:`Cost_{hv\_orange\_cables}` is from equation :math:numref:`hv_orange_cables_cost_equation`
* :math:`Cost_{lv\_battery}` is from equation :math:numref:`low_voltage_battery_cost_equation`
* :math:`Cost_{hvac}` is from equation :math:numref:`hvac_cost_equation`
* :math:`Cost_{single\_speed\_gearbox}` is from equation :math:numref:`single_speed_gearbox_cost_equation`
* :math:`Cost_{powertrain\_cooling\_loop}` is from equation :math:numref:`powertrain_cooling_loop_cost_equation`
* :math:`Cost_{charging\_cord\_kit}` is from equation :math:numref:`charging_cord_kit_cost_equation`
* :math:`Cost_{DC\_fast\_charge\_circuitry}` is from equation :math:numref:`dc_fast_charge_circuitry_cost_equation`
* :math:`Cost_{power\_mgmt\_dist}` is from equation :math:numref:`power_mgmt_dist_cost_equation`
* :math:`Cost_{additional\_half\_shafts}` is from equation :math:numref:`half_shaft_cost_equation`
* :math:`Cost_{brake\_sensors\_and\_actuators}` is from equation :math:numref:`brake_sensors_cost_equation`

Weight Costs
------------
Weight-related costs rely on four primary weight-related parameters: the curb weight of the package; the glider weight of
the package; the battery weight of the package (if electrified); and, the weight removed via application of weight reduction
applied to the package. Note that weight reduction is applied to the glider and not the full curb weight of the vehicle.
A secondary factor is applied to some weight-related costs which is referred to as the "price class." The price class is
meant to be a means of scaling costs for luxury or upscale versus mainstream vehicles. The price class values come from
the price_class worksheet of the alpha_package_cost_module_inputs file and are shown in :numref:`price_class_sheet`. As
shown, currently all packages are designated as having a price class scaler of 1 (and all packages are designated as price
class 1).

.. _price_class_sheet:
.. csv-table:: Price Classes and Scalers
    :widths: auto
    :header-rows: 1

    price_class,scaler
    0,1
    1,1
    2,1
    3,1

The curb weight of the package is determined from "Test Weight lbs." column of the ALPHA input file, less 300 pounds. The
percentage weight reduction applied to any package is determined from the "Weight Reduction %" column of the ALPHA input
file. The other needed weights are calculated differently for different types of packages as described below.

Battery Weight Calculation
++++++++++++++++++++++++++
For electrified packages, the curb weight and weight reduction values are as described above. To calculate the battery weight, the
kWh_pack_per_kg_pack_curve entries of :numref:`bev_curves_sheet` or :numref:`hev_curves_sheet` or :numref:`phev_curves_sheet`
are used as shown in equation :math:numref:`battery_weight_equation`.

.. Math::
    :label: battery_weight_equation

    Weight_{battery} = 2.2 \frac {pounds} {kg} \times \frac{kWh_{gross}} {(A \times kWh_{gross}^3 + B \times kWh_{gross}^2 + C \times kWh_{gross} + D)}

Where,

* :math:`Weight_{battery}` is the weight of the battery in pounds (this would be 0 for a non-electrified ICE package)
* :math:`kWh_{gross}` is the gross energy content of the battery pack from equation :math:numref:`bev_kwh_gross_equation` or :math:numref:`hev_kwh_gross_equation` or :math:numref:`phev_kwh_gross_equation`
* :math:`A` refers to the x_cubed_factor of the kWh_pack_per_kg_pack_curve from :numref:`bev_curves_sheet`, :numref:`hev_curves_sheet` or :numref:`phev_curves_sheet`
* :math:`B` refers to the x_squared_factor of the kWh_pack_per_kg_pack_curve from :numref:`bev_curves_sheet`, :numref:`hev_curves_sheet` or :numref:`phev_curves_sheet`
* :math:`C` refers to the x_factor of the kWh_pack_per_kg_pack_curve from :numref:`bev_curves_sheet`, :numref:`hev_curves_sheet` or :numref:`phev_curves_sheet`
* :math:`D` refers to the constant factor of the kWh_pack_per_kg_pack_curve from :numref:`bev_curves_sheet`, :numref:`hev_curves_sheet` or :numref:`phev_curves_sheet`

Glider Weight Calculation
+++++++++++++++++++++++++
The glider weight of is calculated as shown in equation :math:numref:`glider_weight_equation`.

.. Math::
    :label: glider_weight_equation

    Weight_{glider} = CurbWeight \times GliderShare - Weight_{battery}

Where,

* :math:`Weight_{glider}` is the weight of the glider
* :math:`CurbWeight` is the curb weight, equal to the TestWeight - 300, in pounds
* :math:`GliderShare` is the glider weight as a share of the curb weight and is set via the InputSettings class (current settings are 0.85 for non-BEV, 1 for BEV)
* :math:`Weight_{battery}` is from equation :math:numref:`battery_weight_equation`

Weight Removed Calculation
++++++++++++++++++++++++++
With the glider weight, the pounds removed via weight reduction are calculated as shown in equation :math:numref:`weight_removed_equation`.

.. Math::
    :label: weight_removed_equation

    Weight_{removed} = \frac{Weight_{glider}} {(1 - Weight_{reduction})} - Weight_{glider}

Where,

* :math:`Weight_{removed}` is the weight removed from the glider, in pounds
* :math:`Weight_{glider}` is from equation :math:numref:`glider_weight_equation`
* :math:`Weight_{reduction}` is from the "Weight Reduction %" column of the ALPHA input file

Base Weight Calculation
+++++++++++++++++++++++
The base weight of any package is determined as shown in equation :math:numref:`base_weight_equation`. In other words,
the base weight is the glider weight of the package before any weight reduction being applied.

.. Math::
    :label: base_weight_equation

    Weight_{base} = Weight_{glider} + Weight_{removed}

Where,

* :math:`Weight_{base}` is the base weight of the glider (i.e., before any weight reduction applied to the glider)
* :math:`Weight_{glider}` is from equation :math:numref:`glider_weight_equation`
* :math:`Weight_{removed}` is from equation :math:numref:`weight_removed_equation`

Weight Cost Calculation
+++++++++++++++++++++++
With the weight-related parameters calculated as above, the weight-related costs can then be calculated as shown in equation
:math:numref:`weight_cost_equation`. To do this, the alpha_package_costs module makes use of the tables on the weight_ice and weight_bev
worksheets of the alpha_package_costs_module_inputs file. Those tables are shown in :numref:`weight_ice_sheet` and :numref:`weight_bev_sheet`.

.. _weight_ice_sheet:
.. csv-table:: Weight Cost Curves for ICE Vehicles, HEVs and PHEVs
    :widths: auto
    :header-rows: 1

    structure_class,item_cost,dmc_per_pound,DMC_ln_coefficient,DMC_constant,IC_slope,dollar_basis
    unibody,5.25,3.5,0.921371846,1.673159093,5.062263982,2016
    ladder,6,4,1.64895973,3.942416562,7.618568107,2016

.. _weight_bev_sheet:
.. csv-table:: Weight Cost Curves for BEVs
    :widths: auto
    :header-rows: 1

    structure_class,item_cost,dmc_per_pound,DMC_ln_coefficient,DMC_constant,IC_slope,dollar_basis
    unibody,5.25,3.5,0.921371846,1.673159093,5.062263982,2016
    ladder,6,4,1.64895973,3.942416562,7.618568107,2016

Where,

* :math:`structure\_class` refers to the basic structure of the package
* :math:`unibody` and :math:`ladder` are determined by the module where ALPHA class "Truck" is ladder and all other ALPHA classes are unibody
* :math:`dmc` and :math:`DMC` refer to the Direct Manufacturing Cost
* :math:`item\_cost` refers to the dmc_per_pound cost inclusive of indirect costs using the "Markup" value on the inputs_workbook worksheet (applied to :math:`Weight_{base}`, see below)
* :math:`DMC\_ln\_coefficient` and :math:`DMC\_constant` and :math:`IC\_slope` (or indirect cost slope) are applied to weight reduction (%) (see below)

The item_cost value is applied to the base weight of any package while the DMC_ln_coefficient, DMC_constant and IC_slope
values are applied to the weight reduction levels.

The costs associated with the base weight are calculated as shown in equation :math:numref:`base_weight_cost_equation`.

.. Math::
    :label: base_weight_cost_equation

    Cost_{base\_weight} = Weight_{base} \times \frac{cost} {pound} \times PriceScaler_{price\_class}

Where,

* :math:`Cost_{base\_weight}` is the cost of the glider prior to any weight reduction
* :math:`Weight_{base}` is from equation :math:numref:`base_weight_equation`
* :math:`\frac{cost} {pound}` is the :math:`item\_cost` value from :numref:`weight_ice_sheet` or :numref:`weight_bev_sheet` for the applicable :math:`structure\_class`
* :math:`PriceScaler_{price\_class}` is from :numref:`price_class_sheet`

The costs associated with weight reduction are calculated as shown in equation :math:numref:`weight_removed_cost_equation`.

.. Math::
    :label: weight_removed_cost_equation

    & Cost_{weight\_reduction} \\
    & \small = Weight_{removed} \times [DMC_{ln\_coefficient} \times ln(Weight_{reduction}) + DMC_{constant} + IC_{slope} \times Weight_{reduction}] \\

Where,

* :math:`Cost_{weight\_reduction}` is the cost associated with weight reduction
* :math:`Weight_{removed}` is the number of pounds removed as determined by equation :math:numref:`weight_removed_equation`
* :math:`DMC_{ln\_coefficient}` and :math:`DMC_{constant}` and :math:`IC_{slope}` are from :numref:`weight_ice_sheet` or :numref:`weight_bev_sheet` for the applicable :math:`structure\_class`
* :math:`Weight_{reduction}` is from the "Weight Reduction %" column of the ALPHA input file

The final weight-related cost is the sum of the base weight cost and the cost of weight reduction as shown in equation
:math:numref:`weight_cost_equation`.

.. Math::
    :label: weight_cost_equation

    Cost_{weight} = Cost_{base\_weight} + Cost_{weight\_reduction}

Where,

* :math:`Cost_{weight}` is the cost for weight-related elements of the package
* :math:`Cost_{base\_weight}` is from equation :math:numref:`base_weight_cost_equation`
* :math:`Cost_{weight\_reduction}` is from equation :math:numref:`weight_removed_cost_equation`

Aftertreatment Costs
--------------------
To estimate aftertreatment costs, the alpha_package_costs module makes use of the "Engine Displacement L" column of the
ALPHA input file and the table on the aftertreatment worksheet of the alpha_package_costs_module_inputs file. That table is
shown in :numref:`aftertreatment_sheet`.

.. _aftertreatment_sheet:
.. csv-table:: Aftertreatment System Costs
    :widths: auto
    :header-rows: 1

    item,value,dmc_slope,dmc_intercept,dollar_basis
    substrate_twc,0,6.108,1.95456,2012
    washcoat_twc,0,5.09,0,2012
    canning_twc,0,2.4432,0,2012
    swept_volume_twc,1.2,0,0,0
    Pt_grams_per_liter_twc,0,,,
    Pd_grams_per_liter_twc,2,,,
    Rh_grams_per_liter_twc,0.11,,,
    markup_twc,1.5,,,
    substrate_gpf,0,1,1,2020
    washcoat_gpf,0,1,0,2020
    canning_gpf,0,1,0,2020
    swept_volume_gpf,1.2,0,0,0
    Pt_grams_per_liter_gpf,1,,,
    Pd_grams_per_liter_gpf,0,,,
    Rh_grams_per_liter_gpf,0,,,
    markup_gpf,1.5,,,

Where,

* :math:`twc` and :math:`gpf` refer to 3-way catalyst (TWC) and gasoline particulate filter (GPF), respectively
* :math:`Pt` and :math:`Pd` and :math:`Rh` refer to Platinum, Palladium and Rhodium, respectively

The module treats the TWC and GPF systems separately, and treats each of those separate systems as a whole, not as individual
devices (i.e., a V8 engine that might have two close coupled catalysts and one underbody catalyst is treated as a single TWC
system in the calculations described here. In the descriptions that follow, a "system" or "device" is meant to refer to
the TWC system as a whole, or the GPF system as a whole, and not the combination of the two until they are summed as shown
in equation :math:numref:`aftertreatment_cost_equation`.

To do this, the module first determines the total volume of the aftertreatment system (TWC or GPF) as shown in equation
:math:numref:`aftertreatment_volume_equation`.

.. Math::
    :label: aftertreatment_volume_equation

    Volume_{system} = Displacement_{engine} \times SweptVolume_{system}

Where,

* :math:`Volume_{system}` is the volume of the TWC or GPF system, in Liters
* :math:`Displacement_{engine}` is from the "Engine Displacement L" column of the ALPHA input file
* :math:`SweptVolume_{system}` is from :numref:`aftertreatment_sheet` for the appropriate device (TWC or GPF)

The module then calculates the total cost of each precious group metal (PGM) in the TWC or GPF system as shown in equation
:math:numref:`pgm_cost_equation`.

.. Math::
    :label: pgm_cost_equation

    Cost_{PGM} = Volume_{system} \times (\frac{$} {TroyOz})_{PGM} \times \frac{TroyOz} {gram} \times (\frac{grams} {Liter})_{PGM}

Where,

* :math:`Cost_{PGM}` is the cost ($) of Platinum or Palladium or Rhodium in the applicable system (TWC or GPF)
* :math:`Volume_{system}` in Liters is from equation :math:numref:`aftertreatment_volume_equation`
* :math:`\frac{$} {TroyOz}` is from :numref:`inputs_code_sheet` for the applicable PGM
* :math:`\frac{TroyOz} {gram}` converts Troy ounces to grams, equal to 0.032 Troy ounce per gram, or 31.1 grams per Troy ounce
* :math:`\frac{grams} {Liter}` is from :numref:`aftertreatment_sheet` for the applicable system (TWC or GPF) and PGM

The cost of Platinum, Palladium and Rhodium are calculated separately as shown equation :math:numref:`pgm_cost_equation`
and separately for the TWC and the GPF system.

The cost of the substrate(s), washcoat and canning in the applicable TWC or GPF system is then calculated as shown in equation
:math:numref:`substrate_cost_equation`.

.. Math::
    :label: substrate_cost_equation

    & Cost_{substrate;washcoat;canning} = Volume_{system} \times dmc\_slope_{substrate} + dmc\_intercept_{substrate} \\
    & + Volume_{system} \times dmc\_slope_{washcoat} + dmc\_intercept_{washcoat} \\
    & + Volume_{system} \times dmc\_slope_{canning} + dmc\_intercept_{canning}

The cost of the full aftertreatment system -- TWC and GPF combined -- is then calculated as shown in equation
:math:numref:`aftertreatment_cost_equation`.

.. Math::
    :label: aftertreatment_cost_equation

    & Cost_{aftertreatment} = (Cost_{Pt} + Cost_{Pd} + Cost_{Rh} + Cost_{substrate;washcoat;canning})_{TWC} \\
    & + (Cost_{Pt} + Cost_{Pd} + Cost_{Rh} + Cost_{substrate;washcoat;canning})_{GPF}

Where,

* :math:`Cost_{aftertreatment}` is the cost of the full aftertreatment system (TWC and GPF combined)
* :math:`Cost_{Pt}` and :math:`Cost_{Pd}` and :math:`Cost_{Rh}` are calculated using equation :math:numref:`pgm_cost_equation`
* :math:`Cost_{substrate;washcoat;canning}` is calculated using equation :math:numref:`aftertreatment_cost_equation`

Package Costs
-------------
ICE package costs consist of the ICE powertrain and the weight-related costs as described here.

ICE Powertrain Costs
++++++++++++++++++++
ICE powertrain costs consist of engine-related costs, the transmission, accessories, and air conditioning as shown in equation
:math:numref:`ice_powertrain_cost_equation`. Year-over-year costs then apply the learning_rate_ice_powertrain entry from
:numref:`inputs_code_sheet`.

.. Math::
    :label: ice_powertrain_cost_equation

    Cost_{ICE\_powertrain} = Cost_{engine} + Cost_{transmission} + Cost_{accessories} + Cost_{air\_conditioning}

Where,

* :math:`Cost_{ICE\_powertrain}` is the cost of the ICE powertrain
* :math:`Cost_{engine}` is from equation :math:numref:`engine_cost_equation`
* :math:`Cost_{transmission}` is the :math:`item\_cost` entry for the applicable transmission from :numref:`trans_sheet`
* :math:`Cost_{accessories}` is the :math:`item\_cost` entry for the applicable accessory from :numref:`accessories_sheet`
* :math:`Cost_{air\_conditioning}` is the :math:`item\_cost` entry for the applicable :math:`structure\_class` from :numref:`ac_sheet`

Roadload Costs
++++++++++++++
Roadload costs (i.e., costs associated with non-weight related roadload reductions) are the sum of the aero and non-aero
related costs as shown in equation :math:numref:`roadload_cost_equation`. Year-over-year costs then apply the learning_rate_roadload
entry from :numref:`inputs_code_sheet`.

.. Math::
    :label: roadload_cost_equation

    Cost_{roadload} = Cost_{aero} + Cost_{non\_aero}

Where,

* :math:`Cost_{roadload}` is the cost associated with aero and non-aero roadload reductions
* :math:`Cost_{aero}` is the :math:`item\_cost` entry for the applicable aero technology from :numref:`aero_sheet`
* :math:`Cost_{non\_aero}` is the :math:`item\_cost` entry for the applicable non-aero technology from :numref:`nonaero_sheet`

Weight Costs
++++++++++++
The weight costs are taken directly from equation :math:numref:`weight_cost_equation`. Year-over-year costs then apply
the learning_rate_weight entry from :numref:`inputs_code_sheet`.

Electrification Costs
+++++++++++++++++++++
Electrification costs are the sum of the battery and the non-battery costs as shown in equation :math:numref:`electrification_cost_equation`.
Year-over-year costs then apply the learning_rate_ice_powertrain entry, the learning_rate_bev entry or the learning_rate_phev
entry for HEVs, BEVs and PHEVs, respectively, from :numref:`inputs_code_sheet`.

.. Math::
    :label: electrification_cost_equation

    Cost_{electrification} = Cost_{battery} + Cost_{non\_battery}

Where,

* :math:`Cost_{electrification}` is the cost associated with battery and non-battery elements of electrified packages
* :math:`Cost_{battery}` is from equation :math:numref:`battery_cost_equation`
* :math:`Cost_{non\_battery}` is from equation :math:numref:`non_battery_cost_equation`

ICE Package Costs
+++++++++++++++++
The ICE package costs are the sum of the ICE powertrain, roadload and weight costs as shown in equation :math:numref:`ice_package_cost_equation`.

.. Math::
    :label: ice_package_cost_equation

    Cost_{package} = Cost_{powertrain} + Cost_{roadload} + Cost_{weight} + Cost_{aftertreatment}

Where,

* :math:`Cost_{package}` is the total cost of the ICE package
* :math:`Cost_{powertrain}` is the cost of the ICE powertrain, which includes air conditioning, from equation :math:numref:`ice_powertrain_cost_equation`
* :math:`Cost_{roadload}` is from equation :math:numref:`roadload_cost_equation`
* :math:`Cost_{weight}` is from equation :math:numref:`weight_cost_equation`
* :math:`Cost_{aftertreatment}` is from equation :math:numref:`aftertreatment_cost_equation`

HEV & PHEV Package Costs
++++++++++++++++++++++++
The HEV and PHEV package costs are the sum of the ICE powertrain, roadload, weight and electrification costs as shown in
equation :math:numref:`hev_package_cost_equation`.

.. Math::
    :label: hev_package_cost_equation

    Cost_{package} = Cost_{powertrain} + Cost_{roadload} + Cost_{weight} + Cost_{aftertreatment} + Cost_{electrification}

Where,

* :math:`Cost_{package}` is the total cost of the HEV or PHEV package
* :math:`Cost_{powertrain}` is the cost of the ICE powertrain, which includes air conditioning, from equation :math:numref:`ice_powertrain_cost_equation`
* :math:`Cost_{roadload}` is from equation :math:numref:`roadload_cost_equation`
* :math:`Cost_{weight}` is from equation :math:numref:`weight_cost_equation`
* :math:`Cost_{aftertreatment}` is from equation :math:numref:`aftertreatment_cost_equation`
* :math:`Cost_{electrification}` is from equation :math:numref:`electrification_cost_equation`


BEV Package Costs
+++++++++++++++++
BEVs do not have an ICE engine or powertrain. For BEVs, the package costs are the sum of the roadload, weight, electrification
and the air conditioning costs as shown in :math:numref:`bev_package_cost_equation`.

.. Math::
    :label: bev_package_cost_equation

    Cost_{package} = Cost_{roadload} + Cost_{weight} + Cost_{electrification} + Cost_{air\_conditioning}

Where,

* :math:`Cost_{package}` is the cost of the BEV package
* :math:`Cost_{roadload}` is from equation :math:numref:`roadload_cost_equation`
* :math:`Cost_{weight}` is from equation :math:numref:`weight_cost_equation`
* :math:`Cost_{electrification}` is from equation :math:numref:`electrification_cost_equation`
* :math:`Cost_{air\_conditioning}` is the :math:`item\_cost` entry for the applicable :math:`structure\_class` from :numref:`ac_sheet`

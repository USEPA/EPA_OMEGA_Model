.. image:: _static/epa_logo_1.jpg

User Guide
==========

The primary input to OMEGA is the batch definition file which contains rows for each user input required to define a simulation session or group of sessions.

The line-by-line documentation of the batch definition file is available at :any:`omega_model/omega_batch.py<omega_model.omega_batch>` and won't be repeated here.

Batch definition inputs can be scalar values or input file paths (relative to the batch file and/or absolute).

Several of the input files may dynamically load user-definable modules at runtime.  These files are indicated as ``user_definable`` in the table below.  User-definable inputs and modules are loaded by interpreting the input file ``input_template_name:`` field.  For example, if the input template name of a user-definable input is ``consumer.market_classes`` then the Python module ``omega_model/consumer/market_classes.py`` will be used to load the rest of the input file, which may contain an arbitrary format known to the module.  The process of creating user-definable modules is a topic for :any:`developers<6_developer_guide>`

Below is a table with links to the modules that load the files and their documentation of the input file formats.

Batch Input Files and Loaders
    .. csv-table::
        :header-rows: 1
        :stub-columns: 1

        Parameter,Loaded By
        Context Fuel Prices File, :any:`omega_model/context/fuel_prices.py<omega_model.context.fuel_prices>`
        Context New Vehicle Market File, :any:`omega_model/context/new_vehicle_market.py<omega_model.context.new_vehicle_market>`
        Manufacturers File, :any:`omega_model/producer/manufacturers.py<omega_model.producer.manufacturers>`
        Market Classes File, ``user_definable`` e.g. :any:`omega_model/consumer/market_classes.py<omega_model.consumer.market_classes>`
        Onroad Fuels File, :any:`omega_model/context/onroad_fuels.py<omega_model.context.onroad_fuels>`
        Onroad Vehicle Calculations File, :any:`omega_model/producer/vehicles.py<omega_model.producer.vehicles>`
        Onroad VMT File, ``user_definable`` e.g. :any:`omega_model/consumer/annual_vmt_fixed_by_age.py<omega_model.consumer.annual_vmt_fixed_by_age>`
        Producer Generalized Cost File, ``user_definable`` e.g. :any:`omega_model/producer/producer_generalized_cost.py<omega_model.producer.producer_generalized_cost>`
        Production Constraints File, :any:`omega_model/context/production_constraints.py<omega_model.context.production_constraints>`
        Sales Share File, ``user_definable`` e.g. :any:`omega_model/consumer/sales_share.py<omega_model.consumer.sales_share>`
        Vehicle Price Modifications File, :any:`omega_model/context/price_modifications.py<omega_model.context.price_modifications>`
        Vehicle Reregistration File, ``user_definable`` e.g. :any:`omega_model/consumer/reregistration_fixed_by_age.py<omega_model.consumer.reregistration_fixed_by_age>`
        Vehicle Simulation Results and Costs File, :any:`omega_model/context/cost_clouds.py<omega_model.context.cost_clouds>`
        Vehicles File, :any:`omega_model/producer/vehicles.py<omega_model.producer.vehicles>`
        Context Criteria Cost Factors File, :any:`omega_model/effects/cost_factors_criteria.py<omega_model.effects.cost_factors_criteria>`
        Context SCC Cost Factors File, :any:`omega_model/effects/cost_factors_scc.py<omega_model.effects.cost_factors_scc>`
        Context Energy Security Cost Factors File, :any:`omega_model/effects/cost_factors_energysecurity.py<omega_model.effects.cost_factors_energysecurity>`
        Context Congestion-Noise Cost Factors File, :any:`omega_model/effects/cost_factors_congestion_noise.py<omega_model.effects.cost_factors_congestion_noise>`
        Context Powersector Emission Factors File, :any:`omega_model/effects/emission_factors_powersector.py<omega_model.effects.emission_factors_powersector>`
        Context Refinery Emission Factors File, :any:`omega_model/effects/emission_factors_refinery.py<omega_model.effects.emission_factors_refinery>`
        Context Vehicle Emission Factors File, :any:`omega_model/effects/emission_factors_vehicles.py<omega_model.effects.emission_factors_vehicles>`
        Context Implicit Price Deflators File, *read by multiple effects files*:any:`<>`
        Context Consumer Price Index File, :any:`omega_model/effects/cost_factors_criteria.py<omega_model.effects.cost_factors_criteria>`
        ,
        Session Policy Alternatives Settings,
        Drive Cycle Weights File, :any:`omega_model/policy/drive_cycle_weights.py<omega_model.policy.drive_cycle_weights>`
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

Simulation Context
    The context inputs apply to all sessions within a batch.  Multiple batch files must be defined to run multiple contexts.

Simulation Sessions
    The Reference Session
        The batch file must define at least one simulation session, known as the reference session, which is the left-most session in the batch definition file.  The reference session should align with the provided context inputs.  For example, if the context fuel price and new vehicle market data are from AEO, then the policy inputs of the reference session must be consistent with the assumptions used by AEO to generate their projections.  For example, the sales projections take into account ghg and fuel economy policies in force or projected at the time and the policy inputs used for the reference session should be consistent with those.  It would be inconsistent to assume the same sales for a different ghg/fuel economy policy.
    Policy Alternative Sessions
        Optionally, one or more alternative policy sessions may be defined in subsequent columns. Typically these would be various policies under evaluation via OMEGA or perhaps a single policy with various alternative inputs or assumptions.

"""

**Routines to load and run a batch of one or more OMEGA simulation sessions.**

Sessions are defined by columns of data, some rows support multiple comma-separated values, which are expanded in a
full-factorial fashion.  All required session data, including source code, is "bundled" to a common folder,
thereby providing a standalone archive of the batch that can be inspected or re-run at any time.

The batch process supports parallel processing via multi-core and/or multi-machine running of batches via the optional
``dispy`` package.  Parallel processing requires the machine(s) to have running instances of ``dispynode`` s and
optionally a ``dispyscheduler``.  Parallel processing is an advanced topic and is not covered in detail here.

Example command-line shell script for launching a dispy node:

    ::

        #! /bin/zsh

        PYTHONPATH="/Users/omega_user/Code/GitHub/USEPA_OMEGA2/venv3.8/bin"
        DISPYPATH="/Users/omega_user/Code/GitHub/USEPA_OMEGA2/venv3.8/lib/python3.8/site-packages/dispy"

        $PYTHONPATH/python3 $DISPYPATH/dispynode.py --clean --cpus=8 --client_shutdown --ping_interval=15 --daemon --zombie_interval=5

**INPUT FILE FORMAT**

The file format consists of a two-column header followed by a one or more session definition columns.  Batch settings
(settings that apply to all sessions) are defined in the first column (at the top, by convention).  The data rows
do not need to be defined in any particular order.

Sample Data Columns
    .. csv-table::
        :widths: auto

        Parameter,Type,Value,
        Batch Settings,,,
        Batch Name,String,test_batch,
        Analysis Final Year,#,2050,
        Consolidate Manufacturers,TRUE / FALSE,TRUE,
        Cost Accrual,end-of-year / beginning-of-year,end-of-year,
        Discount Values to Year,#,2021,
        Analysis Dollar Basis,#,2020,
        ,,,
        Batch Analysis Context Settings,,,
        Context Name,String,AEO2021,
        Context Case,String,Reference case,
        Context Fuel Prices File,String,context_fuel_prices.csv,
        Context New Vehicle Market File,String,context_new_vehicle_market.csv,
        Maintenance Costs File,String,maintenance_cost_inputs.csv,
        Repair Costs File,String,repair_cost_inputs.csv,
        Refueling Costs File,String,refueling_cost_inputs.csv,
        Manufacturers File,String,manufacturers.csv,
        Market Classes File,String,market_classes.csv,
        New Vehicle Price Elasticity of Demand,#,-0.5,
        Onroad Fuels File,String,onroad_fuels.csv,
        Onroad Vehicle Calculations File,String,onroad_vehicle_calculations.csv,
        Onroad VMT File,String,annual_vmt_fixed_by_age.csv,
        Producer Cross Subsidy Multiplier Max,#,1.05,
        Producer Cross Subsidy Multiplier Min,#,0.95,
        Producer Generalized Cost File,String,producer_generalized_cost.csv,
        Production Constraints File,String,production_constraints.csv,
        Sales Share File,String,sales_share_params.csv,
        Vehicle Price Modifications File,String,vehicle_price_modifications.csv,
        Vehicle Reregistration File,String,reregistration_fixed_by_age.csv,
        Vehicle Simulation Results and Costs File,String,simulated_vehicles.csv,
        Vehicles File,String,vehicles.csv,
        ,,,
        Session Settings,,,
        Enable Session,TRUE / FALSE,TRUE,TRUE
        Session Name,String,NoActionPolicy,ActionAlternative
        ,,,
        Session Policy Alternatives Settings,,,
        Drive Cycle Weights File,String,drive_cycle_weights.csv,drive_cycle_weights.csv
        Drive Cycles File,String,drive_cycles.csv,drive_cycles.csv
        GHG Credit Params File,String,ghg_credit_params.csv,ghg_credit_params.csv
        GHG Credits File,String,ghg_credits.csv,ghg_credits.csv
        GHG Standards File,String,ghg_standards-footprint.csv,ghg_standards-alternative.csv
        Off-Cycle Credits File,String,offcycle_credits.csv,offcycle_credits.csv
        Policy Fuel Upstream Methods File,String,policy_fuel_upstream_methods.csv,policy_fuel_upstream_methods.csv
        Policy Fuels File,String,policy_fuels.csv,policy_fuels.csv
        Production Multipliers File,String,production_multipliers.csv,production_multipliers.csv
        Regulatory Classes File,String,regulatory_classes.csv,regulatory_classes.csv
        Required Sales Share File,String,required_sales_share.csv,required_sales_share.csv
        ,,,
        Session Postproc Settings,,,
        General Inputs for Effects File,String,general_inputs_for_effects.csv,general_inputs_for_effects.csv
        Context Criteria Cost Factors File,String,cost_factors-criteria.csv,cost_factors-criteria.csv
        Context SCC Cost Factors File,String,cost_factors-scc.csv,cost_factors-scc.csv
        Context Energy Security Cost Factors File,String,cost_factors-energysecurity.csv,cost_factors-energysecurity.csv
        Context Congestion-Noise Cost Factors File,String,cost_factors-congestion-noise.csv,cost_factors-congestion-noise.csv
        Context Powersector Emission Factors File,String,emission_factors-powersector.csv,emission_factors-powersector.csv
        Context Refinery Emission Factors File,String,emission_factors-refinery.csv,emission_factors-refinery.csv
        Context Vehicle Emission Factors File,String,emission_factors-vehicles.csv,emission_factors-vehicles.csv
        Context Implicit Price Deflators File,String,implicit_price_deflators.csv,implicit_price_deflators.csv
        Context Consumer Price Index File,String,cpi_price_deflators.csv,cpi_price_deflators.csv

The first column defines the parameter name, the second column is a type-hint and does not get evaluated.  Subsequent
columns contain the data to define batch settings and session settings.

File names in the batch definition file are relative to the batch file location, unless they are specified as absolute
paths.

Data Row Name and Description

:Batch Settings:
    Decorator, not evaluated

:Batch Name *(str)*:
    The name of the batch, combined with a timestamp (YYYY_MM_DD_hh_mm_ss) becomes the name of the bundle folder

:Analysis Final Year *(int)*:
    Analysis Final Year, e.g. ``2050``

:Consolidate Manufacturers *(TRUE or FALSE)*:
    If ``TRUE`` then manufacturers will be conslidated into a "consolidated_OEM", otherwise manufacturers will be run independently

:Cost Accrual:
    The time of year when costs are assumed to accrue, ``end-of-year`` or ``beginning-of-year``

:Discount Values to Year:
    The year to which all monetized values in the cost effects outputs will be discounted, default is ``2021``

:Analysis Dollar Basis:
    The dollar valuation for all monetized values in the cost effects outputs, i.e., costs are expressed in "Dollar Basis" dollars

:Batch Analysis Context Settings:
    Decorator, not evaluated

:Context Name *(str)*:
    Context name, e.g. ``AEO2021``

:Context Case *(str)*:
    Context case name, e.g. ``Reference case``

:Context Fuel Prices File *(str)*:
    The relative or absolute path to the context fuel prices file,
    loaded by ``context.fuel_prices.FuelPrice``

:Context New Vehicle Market File *(str)*:
    The relative or absolute path to the context new vehicle market file,
    loaded by ``context.new_vehicle_market.NewVehicleMarket``

:Maintenance Costs File *(str)*:
    The relative or absolute path to the maintenance cost inputs file,
    loaded by ``context.maintenance_cost_inputs.MaintenanceCostInputs``

:Repair Costs File *(str)*:
    The relative or absolute path to the repair cost inputs file,
    loaded by ``context.repair_cost_inputs.RepairCostInputs``

:Refueling Costs File *(str)*:
    The relative or absolute path to the refueling cost inputs file,
    loaded by ``context.refueling_cost_inputs.RefuelingCostInputs``

:Manufacturers File *(str)*:
    The relative or absolute path to the manufacturers file,
    loaded by ``producer.manufacturers.Manufacturer``

:Market Classes File *(str)*:
    The relative or absolute path to the market classes file,
    loaded by ``consumer.market_classes.MarketClass``

:New Vehicle Price Elasticity of Demand *(float, ...)*:
    Numeric value of the new vehicle price elasticity of demand, typically <= 0, e.g. ``-0.5``
    Supports multiple comma-separated values

:Onroad Fuels File *(str)*:
    The relative or absolute path to the onroad fuels file,
    loaded by ``context.onroad_fuels.OnroadFuel``

:Onroad Vehicle Calculations File *(str)*:
    The relative or absolute path to the onroad vehicle calculations (onroad gap) file,
    loaded by ``producer.vehicles.VehicleFinal``

:Onroad VMT File *(str)*:
    The relative or absolute path to the onroad VMT file,
    loaded dynamically by the ``OnroadVMT`` class defined in the module specified by the file header,
    e.g. ``consumer.annual_vmt_fixed_by_age``

:Producer Cross Subsidy Multiplier Max *(float, ...)*:
    Numeric value of the minimum producer cross subsidy multiplier, typically >= 1, e.g. ``1.05``
    Supports multiple comma-separated values

:Producer Cross Subsidy Multiplier Min *(float, ...)*:
    Numeric value of the minimum producer cross subsidy multiplier, typically <= 1, e.g. ``0.95``
    Supports multiple comma-separated values

:Producer Generalized Cost File *(str)*:
    The relative or absolute path to the vehicle producer generalized costs file,
    loaded dynamically by the ``ProducerGeneralizedCost`` class defined in the module specified by the file header,
    e.g. ``producer.producer_generalized_cost``

:Production Constraints File *(str)*:
    The relative or absolute path to the production constraints file,
    loaded by ``context.production_constraints.ProductionConstraints``

:Sales Share File *(str)*:
    The relative or absolute path to the sales share (consumer sales response) file,
    loaded dynamically by the ``SalesShare`` class defined in the module specified by the file header,
    e.g. ``consumer.sales_share_gcam``

:Vehicle Price Modifications File *(str)*:
    The relative or absolute path to the vehicle price modifications file,
    loaded by ``context.price_modifications.PriceModifications``

:Vehicle Reregistration File *(str)*:
    The relative or absolute path to the vehicle re-registration file,
    loaded dynamically by the ``Reregistration`` class defined in the module specified by the file header,
    e.g. ``consumer.reregistration_fixed_by_age``

:Vehicle Simulation Results and Costs File *(str)*:
    The relative or absolute path to the vehicle simulation results and costs file,
    loaded by ``context.cost_clouds.CostCloud``

:Vehicles File *(str)*:
    The relative or absolute path to the vehicles (base year fleet) file,
    loaded by ``producer.vehicles.VehicleFinal``

:General Inputs for Effects File *(str)*:
    The relative or absolute path to the general inputs used for effects calculations,
    loaded by ``effects.general_inputs_for_effects.GeneralInputsForEffects``

:Context Criteria Cost Factors File *(str)*:
    The relative or absolute path to the criteria pollutant costs file,
    loaded by ``effects.cost_factors_criteria.CostFactorsCriteria``

:Context SCC Cost Factors File *(str)*:
    The relative or absolute path to the social cost of carbon and carbon-equivalent pollutants file,
    loaded by ``effects.cost_factors_scc.CostFactorsSCC``

:Context Energy Security Cost Factors File *(str)*:
    The relative or absolute path to the energy security cost factors file,
    loaded by ``effects.cost_factors_energysecurity.CostFactorsEnergySecurity``

:Context Congestion-Noise Cost Factors File *(str)*:
    The relative or absolute path to the congestion and noise cost factors file,
    loaded by ``effects.cost_factors_congestion_noise.CostFactorsCongestionNoise``

:Context Powersector Emission Factors File *(str)*:
    The relative or absolute path to the power sector emission factors file,
    loaded by ``effects.emission_factors_powersector.EmissionFactorsPowersector``

:Context Refinery Emission Factors File *(str)*:
    The relative or absolute path to the refinery emission factors file,
    loaded by ``effects.emission_factors_refinery.EmissionFactorsRefinery``

:Context Vehicle Emission Factors File *(str)*:
    The relative or absolute path to the vehicle emission factors file,
    loaded by ``effects.emission_factors_vehicles.EmissionFactorsVehicles``

:Context Implicit Price Deflators File *(str)*:
    The relative or absolute path to the implicit price deflators file,
    loaded by ``effects.cost_factors_scc.CostFactorsSCC``

:Context Consumer Price Index File *(str)*:
    The relative or absolute path to the consumer price index file,
    loaded by ``effects.cost_factors_criteria.CostFactorsCriteria``

----

:Session Settings:
    Decorator, not evaluated

:Enable Session *(TRUE or FALSE)*:
    If ``TRUE`` then run the session(s)

:Session Name *(str)*:
    Session Name

----

:Session Policy Alternatives Settings:
    Decorator, not evaluated

:Drive Cycle Weights File *(str)*:
    The relative or absolute path to the drive cycle weights file,
    loaded by ``policy.drive_cycle_weights.DriveCycleWeights``

:Drive Cycles File *(str)*:
    The relative or absolute path to the drive cycles file,
    loaded by ``policy.drive_cycles.DriveCycles``

:GHG Credits File *(str)*:
    The relative or absolute path to the GHG credits file,
    loaded by ``policy.credit_banking.CreditBank``

:GHG Standards File *(str)*:
    The relative or absolute path to the GHG Standards / policy targets file,
    loaded dynamically by the VehicleTargets class defined in the module specified by the file header,
    e.g. ``policy.targets_footprint``

:Off-Cycle Credits File *(str)*:
    The relative or absolute path to the off-cycle credits file,
    loaded by ``policy.offcycle_credits.OffCycleCredits``

:Policy Fuel Upstream Methods File *(str)*:
    The relative or absolute path to the policy fuel upstream methods file,
    loaded by ``policy.upstream_methods.UpstreamMethods``

:Policy Fuels File *(str)*:
    The relative or absolute path to the policy fuels file,
    loaded by ``policy.policy_fuels.PolicyFuel``

:Production Multipliers File *(str)*:
    The relative or absolute path to the production multipliers file,
    loaded by ``policy.incentives.Incentives``

:Regulatory Classes File *(str)*:
    The relative or absolute path to the regulatory classes file,
    loaded dynamically by the RegulatoryClasses class defined in the module specified by the file header,
    e.g. ``policy.regulatory_classes``

:Required Sales Share File *(str)*:
    The relative or absolute path to the required sales share file,
    loaded by ``policy.required_sales_share.RequiredSalesShare``

----

**DEVELOPER SETTINGS**

These settings are primarily for debugging or code development, if not provided by the user then default values will be
applied.

:Developer Settings:
    Decorator, not evaluated

:Cost Curve Frontier Affinity Factor *(float, ...)*:
    Determines how closely the frontier hews to the source points of the cost cloud, typically ``0.75``
    Supports multiple comma-separated values

:Flat Context *(TRUE or FALSE)*:
    If TRUE then all context values will come from a fixed year

:Flat Context Year *(int)*:
    The fixed year when using flat context, default value is ``2020``

:Iterate Producer-Consumer *(TRUE or FALSE, ...)*:
    If ``TRUE`` then multiple producer-consumer tech and market share convergence iterations are enabled
    Supports multiple comma-separated values

:Log Consumer Iteration Years *(['all'] or [int(s)])*:
    List of year(s) to log producer-consumer market share iteration, default value is ``2050``, which writes the log
    file in the year 2050 and contains all prior years

:Log Producer Decision and Response Years *(['all'] or [int(s)])*:
    List of year(s) to log producer decision and consumer response data (costs, market shares and tech decision).
    Default value is ``[]``

:Log Producer Compliance Search Years *(['all'] or [int(s)])*:
    List of year(s) to log detailed producer iteration data, including composite vehicle cost curves and compliance
    search data (cost clouds).  Default value is ``[]``

:Num Market Share Options *(int, ...)*:
    Number of market share options to generate as part of the producer compliance search, typically ``5``.
    Supports multiple comma-separated values

:Num Tech Options per BEV Vehicle *(int, ...)*:
    Number of tech options to generate for BEV vehicles as part of the producer compliance search, typically ``1``
    Supports multiple comma-separated values

:Num Tech Options per ICE Vehicle *(int, ...)*:
    Number of tech options to generate for ICE vehicles as part of the producer compliance search, typically ``5``
    Supports multiple comma-separated values

:Producer Compliance Search Convergence Factor *(float)*:
    Determines the search progression of tech options and market shares, used in
    ``producer.compliance_search.create_tech_and_share_sweeps()`` and
    ``producer.compliance_search.search_production_options()``.  Default value is ``0.33``

:Producer Compliance Search Min Share Range *(float)*:
    Used in ``producer.compliance_search.search_production_options()``, minimum share range limit, stops compliance
    search when below.
    Default value is ``1e-4``

:Producer Compliance Search Tolerance *(float)*:
    Used in ``producer.compliance_search.search_production_options()``, used to determine accuracy of compliance
    outcome relative to the targeted CO2e Mg, default value is ``1e-6``

:Producer Cross Subsidy Price Tolerance *(float)*:
    Used in ``omega_model.detect_convergence()``, applied to the total average cost accuracy, default value is ``1e-4``

:Producer-Consumer Convergence Tolerance *(float)*:
    Used in ``omega_model.detect_convergence()``, compared with the convergence error.  Default is ``1e-3``

:Producer-Consumer Max Iterations *(int)*:
    Maximum number of market share iterations between the producer and consumer.  Recommended minimum is ``2``

:Run Profiler *(TRUE or FALSE)*:
    If TRUE then the model with run with profiling enabled.  See ``omega_model.run_omega()``

:Slice Tech Combo Tables *(TRUE or FALSE)*:
    If ``TRUE`` then partial clouds are saved as part of debugging the producer search convergence

:Verbose Log Modules *([strs])*:
    List of modules to activate detailed logfile output, may contain ``'database'``, ``'producer_compliance_search'``,
        ``'cv_cost_curves'``, ``'v_cost_curves'``. Default value is ``[]``

:Verbose Console Modules *([strs])*:
    List of modules to activate detailed console output, may contain ``'producer_compliance_search'``,
                                            ``'p-c_shares_and_costs'``, ``'p-c_max_iterations'``,
                                            ``'cross_subsidy_search'``, ``'cross_subsidy_multipliers'``,
                                            ``'cross_subsidy_convergence'``. Default value is ``[]``

:Verbose Output *(TRUE or FALSE, ...)*:
    Enables detailed console and logfile output if ``TRUE``
    Supports multiple comma-separated values

"""

print('importing %s' % __file__)

import os, sys

# make sure top-level project folder is on the path (i.e. folder that contains omega_model)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.omega_types import OMEGABase
from omega_model import OMEGASessionSettings
from common.file_io import validate_file, relocate_file, get_filenameext

bundle_input_folder_name = 'in'
bundle_output_folder_name = OMEGASessionSettings().output_folder

true_false_dict = dict({True: True, False: False, 'True': True, 'False': False, 'TRUE': True, 'FALSE': False})


def validate_predefined_input(input_str, valid_inputs):
    """
    Validate the input string against set or dictionary of valid inputs. If ``valid_inputs`` is a set the
    ``input_str`` is checked for inclusion and returned, if ``valid_inputs`` is a dict, the value associated with the
    ``input_str`` key is returned.

    Args:
        input_str (str): the string to be validated
        valid_inputs (set, dict): set or dict of valid inputs

    Returns:
        Raises Exception if ``input_str`` not in ``valid_inputs`` or if ``valid_inputs`` is not a set or dict,
        else ``input_str`` if ``valid_inputs`` is a set,
        else ``valid_inputs[input_str]`` if ``valid_inputs`` is a dict.

    """
    if input_str in valid_inputs:
        if type(valid_inputs) is dict:
            return valid_inputs[input_str]
        elif type(valid_inputs) is set:
            return input_str
        else:
            raise Exception(
                'validate_predefined_input(...,valid_inputs) error: valid_inputs must be a set or dictionary')
    else:
        raise Exception('Invalid input "%s", expecting %s' % (input_str, str(valid_inputs)))


def is_absolute_path(source_file_path):
    """
    Check if source file path is absolute (as opposed to relative).  Wrapper for ``os.path.isabs()``

    Args:
        source_file_path (str): file path

    Returns: True if file path is absolute

    """
    # return source_file_path.startswith('/') or source_file_path.startswith('\\') or (source_file_path[1] == ':')
    import os
    return os.path.isabs(source_file_path)


class OMEGABatchObject(OMEGABase):
    """
    **Manages batch-level settings and contains a list of sessions.**

    """
    def __init__(self, name='', analysis_final_year=None, calc_effects=None):
        """
        Create an ``OMEGABatchObject``

        Args:
            name (str): the name of the batch
            analysis_final_year (int): optional externally-provided analysis final year, otherwise the analysis final
                year is determined by the batch file
            calc_effects (str): 'None', 'Physical' or 'Physical and Costs', determines which effects calcs to run
                post-compliance modeling

        """
        import pandas as pd

        self.name = name
        self.batch_definition_path = ''
        self.output_path = "." + os.sep
        self.sessions = []
        self.dataframe = pd.DataFrame()
        self.batch_log = None

        self.settings = OMEGASessionSettings()
        self.settings.analysis_final_year = analysis_final_year
        self.settings.calc_effects = calc_effects

    def force_numeric_user_params(self):
        """
        Force certain user batch inputs to be numeric values. List of numeric params must be updated manually when
        new numeric params are added to the batch settings.

        Returns:
            Nothing, changes ``self.dataframe`` values to numeric values as required

        """
        import pandas as pd

        numeric_params = {
            'Analysis Final Year',
            'Discount Values to Year',
            'Analysis Dollar Basis',
            'New Vehicle Price Elasticity of Demand',
            'Producer Cross Subsidy Multiplier Min',
            'Producer Cross Subsidy Multiplier Max',
        }

        for p in numeric_params:
            self.dataframe.loc[p] = pd.to_numeric(self.dataframe.loc[p])

    def force_numeric_developer_params(self):
        """
        Force certain developer batch inputs to be numeric values. List of numeric params must be updated manually when
        new numeric params are added to the batch settings.

        Returns:
            Nothing, changes ``self.dataframe`` values to numeric values as required

        """
        import pandas as pd

        numeric_params = {
            'Num Market Share Options',
            'Num Tech Options per ICE Vehicle',
            'Num Tech Options per BEV Vehicle',
            'Cost Curve Frontier Affinity Factor',
            'Producer-Consumer Max Iterations',
            'Producer-Consumer Convergence Tolerance',
            'Producer Compliance Search Min Share Range',
            'Producer Compliance Search Convergence Factor',
            'Producer Compliance Search Tolerance',
            'Producer Cross Subsidy Price Tolerance',
            'Flat Context Year',
        }

        for p in numeric_params:
            if p in self.dataframe:
                self.dataframe.loc[p] = pd.to_numeric(self.dataframe.loc[p])

    def read_parameter(self, param_name):
        """
        Read batch-level parameter, setting applies to all sessions.

        Args:
            param_name (str): the name of the parameter to read

        Returns:
            The value of the batch setting, taken from the first data column of the batch file

        """
        return self.dataframe.loc[param_name][0]

    def parse_parameter(self, param_name, session_num):
        """
        Returns the evaluated value of the requested row (``param_name``) and column (``session_num``) from the
        batch file.

        Args:
            param_name (str): the name of the parameter to evaluate
            session_num (int): which session to evaluate, the first session is session ``0``

        Returns:
            The raw value, ``True`` for 'TRUE' and ``False`` for 'FALSE', or the valid python object created by
            evaluating the raw parameter string (i.e. for tuples or dicts in the batch file inputs)

        """
        raw_param = self.dataframe.loc[param_name][session_num]
        params_dict = {'TRUE': True,
                       'FALSE': False,
                       }

        param = raw_param  # default is to pass through the raw value

        if type(raw_param) is str:
            try:
                # try to evaluate the param as a python code-compatible string
                param = eval(raw_param, {'__builtins__': None}, params_dict)
            except:
                pass

        return param

    def set_parameter(self, param_name, session_num, value):
        """
        Set the value of a given parameter for a given session in the batch dataframe

        Args:
            param_name (str): the name of the parameter to evaluate
            session_num (int): which session to set the value of, the first session is session ``0``
            value: the value to be set

        Returns:
            Nothing, sets the value for the parameter in the given session in the batch dataframe

        """
        self.dataframe.loc[param_name][session_num] = value

    def parse_session_params(self, session_num, verbose=False):
        """
        Parse session params and determine the full factorial dimensions of the session

        Args:
            session_num (int): the number of the session to parse, the first session is session ``0``
            verbose (bool): enables additional console output if ``True``

        Returns:
            The full factorial dimensions of the given session, e.g. (1,1,2,1...)

        """
        fullfact_dimensions = []
        for param_name in self.dataframe.index:
            if type(param_name) is str:
                param = self.parse_parameter(param_name, session_num)
                self.set_parameter(param_name, session_num, param)
                if type(param) is tuple:
                    if verbose:
                        print('found tuple')
                    fullfact_dimensions.append(len(param))
                else:
                    fullfact_dimensions.append(1)
            else:
                fullfact_dimensions.append(1)
        if verbose:
            print('fullfact dimensions = %s' % fullfact_dimensions)
        return fullfact_dimensions

    def parse_batch_params(self, verbose=False):
        """
        Parse settings for each session and return the full factorial dimensions of all sessions

        Args:
            verbose (bool): enables additional console output if ``True``

        Returns:
            A list of tuples of the full factorial dimensions of each session, e.g. [(1,1,2,1...), (1,2,2,1...)]

        """
        fullfact_dimensions_vectors = []
        for session_num in range(0, len(self.dataframe.columns)):
            fullfact_dimensions_vectors.append(self.parse_session_params(session_num, verbose))
            if session_num == 0 and max(fullfact_dimensions_vectors[0]) > 1:
                raise Exception('Reference session of batch (first session column) must not contain any '
                                'comma-separated values')
        return fullfact_dimensions_vectors

    def expand_dataframe(self, verbose=False):
        """
        Expand dataframe as necessary, creating new session names that represent the multi-valued parameters.

        Args:
            verbose (bool): enables additional console output if ``True``

        Returns:
            Nothing, but sets the batch dataframe to the newly expanded dataframe, raises Exception if multiple values
            are found in a parameter that does not support multiple values

        """
        import pyDOE2 as doe
        import pandas as pd
        import numpy as np

        # dict of acronyms for auto-generating session names from parameters that support multiple values
        acronyms_dict = {
            False: '0',
            True: '1',
            'Num Market Share Options': 'NMSO',
            'Num Tech Options per ICE Vehicle': 'NTOI',
            'Num Tech Options per BEV Vehicle': 'NTOB',
            'Cost Curve Frontier Affinity Factor': 'CFAF',
            'Iterate Producer-Consumer': 'IPC',
            'Producer-Consumer Max Iterations': 'PCMI',
            'Producer-Consumer Convergence Tolerance': 'PCCT',
            'Producer Compliance Search Min Share Range': 'PCSMSR',
            'Producer Compliance Search Convergence Factor': 'PCSCF',
            'Producer Compliance Search Tolerance': 'PCST',
            'Producer Cross Subsidy Price Tolerance': 'PCSPT',
            'Flat Context Year': 'FCY',
        }

        fullfact_dimensions_vectors = self.parse_batch_params(verbose=verbose)

        dfx = pd.DataFrame()  # create expanded dataframe
        dfx['Parameters'] = self.dataframe.index
        dfx.set_index('Parameters', inplace=True)
        session_params_start_index = np.where(dfx.index == 'Enable Session')[0][0]

        expanded_session_num = 0
        # for each column in dataframe, copy or expand into dfx
        for session_num in range(0, len(self.dataframe.columns)):
            df_ff_dimensions_vector = fullfact_dimensions_vectors[session_num]
            df_ff_matrix = np.int_(doe.fullfact(df_ff_dimensions_vector))
            num_expanded_columns = np.product(df_ff_dimensions_vector)
            # expand variations and write to dfx
            for variation_index in range(0, num_expanded_columns):
                column_name = self.dataframe.loc['Session Name'][session_num]
                session_name = column_name
                if num_expanded_columns > 1:  # expand variations
                    column_name = column_name + '_%d' % variation_index
                    dfx[column_name] = np.nan  # add empty column to dfx
                    ff_param_indices = df_ff_matrix[variation_index]
                    num_params = len(dfx.index)
                    for param_index in range(0, num_params):
                        param_name = dfx.index[param_index]
                        if type(param_name) is str:  # i.e. if param_name is not blank (np.nan):
                            if (expanded_session_num == 0) or (param_index >= session_params_start_index):
                                # copy all data for df_column 0 (includes batchsettings) or
                                # just session settings for subsequent columns
                                if type(self.dataframe.loc[param_name][session_num]) == tuple:
                                    # index tuple and get this variations element
                                    value = self.dataframe.loc[param_name][session_num][ff_param_indices[param_index]]
                                else:
                                    value = self.dataframe.loc[param_name][session_num]  # else copy source value

                                if value == []:
                                    # special case for assigning empty list (occurs with some developer settings)
                                    dfx.loc[param_name][dfx.columns[expanded_session_num]] = value
                                else:
                                    # normal assignment, avoid setting a value on a copy errors...
                                    dfx.loc[param_name, dfx.columns[expanded_session_num]] = value

                                if df_ff_dimensions_vector[param_index] > 1:
                                    if value in acronyms_dict and param_name in acronyms_dict:
                                        session_name = session_name + '-' + acronyms_dict[param_name] + '=' + \
                                                       acronyms_dict[value]
                                    elif param_name in acronyms_dict:
                                        session_name = session_name + '-' + acronyms_dict[param_name] + '=' + str(value)
                                    else:
                                        msg = 'Unsupported multi-value field %s = %s in session "%s"' % \
                                                        (param_name, self.dataframe.loc[param_name][session_num],
                                                         self.dataframe.loc['Session Name'][session_num])
                                        self.batch_log.logwrite(msg)
                                        raise Exception(msg)
                    dfx.loc['Session Name', column_name] = session_name
                else:  # just copy column
                    dfx[column_name] = self.dataframe.iloc[:, session_num]
                expanded_session_num = expanded_session_num + 1
        self.dataframe = dfx

    def get_batch_settings(self):
        """
        Get batch settings, settings apply to all sessions

        Returns:
            Nothing, updates ``self.settings``

        """
        self.name = self.read_parameter('Batch Name')
        if self.settings.analysis_final_year is not None:
            self.dataframe.loc['Analysis Final Year'][0] = self.settings.analysis_final_year
        self.settings.analysis_final_year = int(self.read_parameter('Analysis Final Year'))
        self.dataframe.loc['Calc Effects'] = self.settings.calc_effects
        self.settings.consolidate_manufacturers = self.read_parameter('Consolidate Manufacturers')
        self.settings.cost_accrual = validate_predefined_input(self.read_parameter('Cost Accrual'),
                                                      {'end-of-year', 'beginning-of-year'})
        self.settings.discount_values_to_year = int(self.read_parameter('Discount Values to Year'))
        self.settings.analysis_dollar_basis = self.read_parameter('Analysis Dollar Basis')

        # read context scalar settings
        self.settings.context_id = self.read_parameter('Context Name')
        self.settings.context_case_id = self.read_parameter('Context Case')
        self.settings.new_vehicle_price_elasticity_of_demand = \
            self.read_parameter('New Vehicle Price Elasticity of Demand')
        self.settings.consumer_pricing_multiplier_max = \
            self.read_parameter('Producer Cross Subsidy Multiplier Max')
        self.settings.consumer_pricing_multiplier_min = \
            self.read_parameter('Producer Cross Subsidy Multiplier Min')

        # read context file settings
        self.settings.context_fuel_prices_file = self.read_parameter('Context Fuel Prices File')
        self.settings.context_new_vehicle_market_file = self.read_parameter('Context New Vehicle Market File')
        self.settings.maintenance_cost_inputs_file = self.read_parameter('Maintenance Costs File')
        self.settings.repair_cost_inputs_file = self.read_parameter('Repair Costs File')
        self.settings.refueling_cost_inputs_file = self.read_parameter('Refueling Costs File')
        self.settings.manufacturers_file = self.read_parameter('Manufacturers File')
        self.settings.market_classes_file = self.read_parameter('Market Classes File')
        self.settings.onroad_fuels_file = self.read_parameter('Onroad Fuels File')
        self.settings.onroad_vehicle_calculations_file = self.read_parameter('Onroad Vehicle Calculations File')
        self.settings.onroad_vmt_file = self.read_parameter('Onroad VMT File')
        self.settings.producer_generalized_cost_file = self.read_parameter('Producer Generalized Cost File')
        self.settings.production_constraints_file = self.read_parameter('Production Constraints File')
        self.settings.sales_share_file = self.read_parameter('Sales Share File')
        self.settings.vehicle_price_modifications_file = self.read_parameter('Vehicle Price Modifications File')
        self.settings.vehicle_reregistration_file = self.read_parameter('Vehicle Reregistration File')
        self.settings.vehicle_simulation_results_and_costs_file = \
            self.read_parameter('Vehicle Simulation Results and Costs File')
        self.settings.vehicles_file = self.read_parameter('Vehicles File')

        # read postproc settings
        self.settings.general_inputs_for_effects_file = self.read_parameter('General Inputs for Effects File')
        self.settings.criteria_cost_factors_file = self.read_parameter('Context Criteria Cost Factors File')
        self.settings.scc_cost_factors_file = self.read_parameter('Context SCC Cost Factors File')
        self.settings.energysecurity_cost_factors_file = \
            self.read_parameter('Context Energy Security Cost Factors File')
        self.settings.congestion_noise_cost_factors_file = \
            self.read_parameter('Context Congestion-Noise Cost Factors File')
        self.settings.emission_factors_powersector_file = \
            self.read_parameter('Context Powersector Emission Factors File')
        self.settings.emission_factors_refinery_file = self.read_parameter('Context Refinery Emission Factors File')
        self.settings.emission_factors_vehicles_file = self.read_parameter('Context Vehicle Emission Factors File')
        self.settings.ip_deflators_file = self.read_parameter('Context Implicit Price Deflators File')
        self.settings.cpi_deflators_file = self.read_parameter('Context Consumer Price Index File')

    def num_sessions(self):
        """
        Get the number of sessions

        Returns:
            The number of sessions in the batch

        """
        return len(self.dataframe.columns)

    def add_sessions(self, verbose=True):
        """
        Create an ``OMEGASessionObject`` for each session in the batch file and add it to the ``self.sessions`` list

        Args:
            verbose (bool): enables additional console output if ``True``

        Returns:
            Nothing, updates ``self.sessions`` list

        """
        if verbose:
            self.batch_log.logwrite('')
            self.batch_log.logwrite("In Batch '{}':".format(self.name))
        for s in range(0, self.num_sessions()):
            self.sessions.append(OMEGASessionObject("session_{%d}" % s))
            self.sessions[s].batch = self
            self.sessions[s].get_session_settings(s)
            if verbose:
                self.batch_log.logwrite("Found Session %s:'%s'" % (s, self.sessions[s].name))
        if verbose:
            self.batch_log.logwrite('')


class OMEGASessionObject(OMEGABase):
    """
    **Holds settings and information for a single OMEGA simulation session.**
    
    """
    def __init__(self, name):
        """
        Create an ``OMEGASessionObject``
        
        Args:
            name (str): the name of the session
            
        """
        from omega import OMEGASessionSettings

        self.batch = []
        self.name = name
        self.num = 0
        self.output_path = "." + os.sep
        self.enabled = False
        self.settings = OMEGASessionSettings()
        self.result = []

    def read_parameter(self, param_name, default_value=None):
        """
        Read a parameter from the batch dataframe, if present in the batch file, or set it to a default value.
        Raises an Exception if the parameter is not present and no default value is provided

        Args:
            param_name (str): the name of the parameter to read
            default_value: optional default value for the parameter if it's not provided by the batch file

        Returns:
            The value of the parameter, or raises an Exception on error

        """
        try:
            param = self.batch.dataframe.loc[param_name][self.num]
        except:
            if default_value is None:
                if param_name not in self.batch.dataframe:
                    raise Exception('Batch file missing row "%s"' % param_name)
            else:
                param = default_value
        finally:
            return param

    def get_session_settings(self, session_num):
        """
        Set the session number, get the name of the session and whether it is enabled or not.
        Set the output path of the session.

        Args:
            session_num (int): the session to get settings for, the first session is session ``0``

        Returns:
            Nothing, updates session attributes

        """
        from omega import OMEGASessionSettings

        self.num = session_num
        self.enabled = session_num == 0 or \
                       validate_predefined_input(self.read_parameter('Enable Session'), true_false_dict)
        self.name = self.read_parameter('Session Name')
        self.output_path = OMEGASessionSettings().output_folder

    def get_user_settings(self):
        """
        Get non-developer settings for the session from the batch.

        Returns:
            Nothing, updates ``self.settings``

        """
        from copy import copy

        self.batch.batch_log.logwrite('Getting User settings...')

        self.settings = copy(self.batch.settings)    # copy batch-level settings to session

        self.settings.session_name = self.name
        self.settings.session_unique_name = self.batch.name + '_' + self.name
        self.settings.session_is_reference = self.num == 0
        self.settings.output_folder = self.name + os.sep + self.settings.output_folder
        self.settings.database_dump_folder = self.name + os.sep + self.settings.database_dump_folder
        self.settings.generate_context_new_vehicle_generalized_costs_file = (self.num == 0)

        # read context settings
        self.settings.context_fuel_prices_file = self.read_parameter('Context Fuel Prices File')
        self.settings.context_new_vehicle_market_file = self.read_parameter('Context New Vehicle Market File')
        self.settings.maintenance_cost_inputs_file = self.read_parameter('Maintenance Costs File')
        self.settings.repair_cost_inputs_file = self.read_parameter('Repair Costs File')
        self.settings.refueling_cost_inputs_file = self.read_parameter('Refueling Costs File')
        self.settings.manufacturers_file = self.read_parameter('Manufacturers File')
        self.settings.market_classes_file = self.read_parameter('Market Classes File')
        self.settings.onroad_fuels_file = self.read_parameter('Onroad Fuels File')
        self.settings.onroad_vehicle_calculations_file = self.read_parameter('Onroad Vehicle Calculations File')
        self.settings.onroad_vmt_file = self.read_parameter('Onroad VMT File')
        self.settings.producer_generalized_cost_file = self.read_parameter('Producer Generalized Cost File')
        self.settings.production_constraints_file = self.read_parameter('Production Constraints File')
        self.settings.sales_share_file = self.read_parameter('Sales Share File')
        self.settings.vehicle_price_modifications_file = self.read_parameter('Vehicle Price Modifications File')
        self.settings.vehicle_reregistration_file = self.read_parameter('Vehicle Reregistration File')
        self.settings.vehicle_simulation_results_and_costs_file = \
            self.read_parameter('Vehicle Simulation Results and Costs File')
        self.settings.vehicles_file = self.read_parameter('Vehicles File')

        # read postproc settings
        self.settings.general_inputs_for_effects_file = self.read_parameter('General Inputs for Effects File')
        self.settings.criteria_cost_factors_file = self.read_parameter('Context Criteria Cost Factors File')
        self.settings.scc_cost_factors_file = self.read_parameter('Context SCC Cost Factors File')
        self.settings.energysecurity_cost_factors_file = \
            self.read_parameter('Context Energy Security Cost Factors File')
        self.settings.congestion_noise_cost_factors_file = \
            self.read_parameter('Context Congestion-Noise Cost Factors File')
        self.settings.emission_factors_powersector_file = \
            self.read_parameter('Context Powersector Emission Factors File')
        self.settings.emission_factors_refinery_file = self.read_parameter('Context Refinery Emission Factors File')
        self.settings.emission_factors_vehicles_file = self.read_parameter('Context Vehicle Emission Factors File')
        self.settings.ip_deflators_file = self.read_parameter('Context Implicit Price Deflators File')
        self.settings.cpi_deflators_file = self.read_parameter('Context Consumer Price Index File')

        # read policy settings
        self.settings.drive_cycle_weights_file = self.read_parameter('Drive Cycle Weights File')
        self.settings.drive_cycles_file = self.read_parameter('Drive Cycles File')
        self.settings.ghg_credit_params_file = self.read_parameter('GHG Credit Params File')
        self.settings.ghg_credits_file = self.read_parameter('GHG Credits File')
        self.settings.policy_targets_file = self.read_parameter('GHG Standards File')
        self.settings.offcycle_credits_file = self.read_parameter('Off-Cycle Credits File')
        self.settings.fuel_upstream_methods_file = self.read_parameter('Policy Fuel Upstream Methods File')
        self.settings.policy_fuels_file = self.read_parameter('Policy Fuels File')
        self.settings.production_multipliers_file = self.read_parameter('Production Multipliers File')
        self.settings.policy_reg_classes_file = self.read_parameter('Regulatory Classes File')
        self.settings.required_sales_share_file = self.read_parameter('Required Sales Share File')

    def get_developer_settings(self):
        """
        Get developer settings for the session from the batch.

        Returns:
            Nothing, updates ``self.settings``

        """
        self.batch.batch_log.logwrite('Getting Developer Settings...')

        self.settings.cost_curve_frontier_affinity_factor = \
            float(self.read_parameter('Cost Curve Frontier Affinity Factor',
                                self.settings.cost_curve_frontier_affinity_factor))

        self.settings.flat_context = validate_predefined_input(
            self.read_parameter('Flat Context', self.settings.flat_context),
            true_false_dict)

        self.settings.flat_context_year = \
            int(self.read_parameter('Flat Context Year',
                                    self.settings.flat_context_year))

        self.settings.iterate_producer_consumer = validate_predefined_input(
            self.read_parameter('Iterate Producer-Consumer', self.settings.iterate_producer_consumer),
            true_false_dict)

        self.settings.log_consumer_iteration_years = \
            self.read_parameter('Log Consumer Iteration Years',
                                self.settings.log_consumer_iteration_years)

        self.settings.log_producer_decision_and_response_years = \
            self.read_parameter('Log Producer Decision and Response Years',
                                self.settings.log_producer_decision_and_response_years)

        self.settings.log_producer_compliance_search_years = \
            self.read_parameter('Log Producer Iteration Years',
                                self.settings.log_producer_compliance_search_years)

        self.settings.producer_num_market_share_options = \
            int(self.read_parameter('Num Market Share Options',
                                    self.settings.producer_num_market_share_options))

        self.settings.producer_num_tech_options_per_ice_vehicle = \
            int(self.read_parameter('Num Tech Options per ICE Vehicle',
                                    self.settings.producer_num_tech_options_per_ice_vehicle))

        self.settings.producer_num_tech_options_per_bev_vehicle = \
            int(self.read_parameter('Num Tech Options per BEV Vehicle',
                                    self.settings.producer_num_tech_options_per_bev_vehicle))

        self.settings.producer_compliance_search_convergence_factor = \
            float(self.read_parameter('Producer Compliance Search Convergence Factor',
                                self.settings.producer_compliance_search_convergence_factor))

        self.settings.producer_compliance_search_min_share_range = \
            float(self.read_parameter('Producer Compliance Search Min Share Range',
                                    self.settings.producer_compliance_search_min_share_range))

        self.settings.producer_compliance_search_tolerance = \
            float(self.read_parameter('Producer Compliance Search Tolerance',
                                self.settings.producer_compliance_search_tolerance))

        self.settings.producer_cross_subsidy_price_tolerance = \
            float(self.read_parameter('Producer Cross Subsidy Price Tolerance',
                                self.settings.producer_cross_subsidy_price_tolerance))

        self.settings.producer_consumer_convergence_tolerance = \
            float(self.read_parameter('Producer-Consumer Convergence Tolerance',
                                self.settings.producer_consumer_convergence_tolerance))

        self.settings.producer_consumer_max_iterations = \
            int(self.read_parameter('Producer-Consumer Max Iterations',
                                    self.settings.producer_consumer_max_iterations))

        self.settings.run_profiler = validate_predefined_input(
            self.read_parameter('Run Profiler', self.settings.run_profiler),
            true_false_dict)

        self.settings.slice_tech_combo_cloud_tables = validate_predefined_input(
            self.read_parameter('Slice Tech Combo Tables', self.settings.slice_tech_combo_cloud_tables),
            true_false_dict)

        self.settings.verbose_log_modules = \
            self.read_parameter('Verbose Log Modules',
                                self.settings.verbose_log_modules)

        self.settings.verbose_console_modules = \
            self.read_parameter('Verbose Console Modules',
                                self.settings.verbose_console_modules)

        self.settings.verbose = validate_predefined_input(
            self.read_parameter('Verbose Output', self.settings.verbose),
            true_false_dict)

    def init(self, verbose=False):
        """
        Get user and developer settings for the session

        Args:
            verbose (bool): enables additional console output if ``True``

        Returns:
            Nothing, updates ``self.settings``

        """
        if not verbose:
            self.batch.batch_log.logwrite("Initializing Session '%s' -> %s" % (self.name, self.output_path))
        self.get_user_settings()
        self.get_developer_settings()

    def run(self):
        """
        Initialize and run the session

        Returns:
            The result of running the session

        See Also:
            ``omega_model.omega.run_omega()``

        """
        from omega import run_omega

        self.init()

        self.batch.batch_log.logwrite("Starting Compliance Run %s ..." % self.name)
        result = run_omega(self.settings)
        return result


def validate_folder(batch_root, batch_name='', session_name=''):
    """
    Confirm the existence of a batch folder (bundle folder or subfolder), create it if it doesn't exist.
    Raises an Exception on error

    Args:
        batch_root (str): the root of the folder to validate
        batch_name (str): optional argument, the name of the batch
        session_name (str): optional argument, the name of the session

    Returns:
        The pathname of the folder, e.g. '/Users/omega_user/Code/GitHub/USEPA_OMEGA2/bundle/'

    """
    dstfolder = batch_root + os.sep
    if not batch_name == '':
        dstfolder = dstfolder + batch_name + os.sep
    if not session_name == '':
        dstfolder = dstfolder + session_name + os.sep

    if not os.access(dstfolder, os.F_OK):
        try:
            os.makedirs(dstfolder, exist_ok=True)  # try create folder if necessary
        except:
            import traceback

            print('Couldn''t access or create {"%s"}' % (dstfolder), file=sys.stderr)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            raise Exception(traceback.format_exc())

    return dstfolder


class OMEGABatchCLIOptions(OMEGABase):
    """
    **Stores command-line interface arguments**

    Attempts to get the IP address of the computer for use with ``dispy`` parallel processing and logs the start
    time of batch processing for timestamping the batch and sessions

    """
    def __init__(self):
        """
        Create an OMEGABatchCLIOptions, get the IP address of the computer and log the start time of batch processing.

        """
        import time
        import socket
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)

        self.start_time = time.time()
        self.validate_batch = True
        self.no_sim = False
        self.bundle_path_root = ''
        self.no_bundle = False
        self.batch_file = ''
        self.batch_path = ''
        self.session_path = ''
        self.logfilename = 'batch_logfile.txt'
        self.session_num = []
        self.verbose = False
        self.timestamp = None
        self.auto_close_figures = True
        self.dispy = False
        self.dispy_ping = False
        self.dispy_debug = False
        self.dispy_exclusive = False
        self.dispy_scheduler = ip_address  # local ip_address by default
        self.local = True
        self.network = False
        self.analysis_final_year = None
        self.calc_effects = 'None'


def run_bundled_sessions(options, remote_batchfile, session_list):
    """
    Run a bundled batch.  Bundling copies the source code and all input files to a single directory structure that
    contains everything needed to run the batch at any time without any external dependencies (except of course a
    Python install with the required packages)

    Args:
        options (OMEGABatchCLIOptions): the command line arguments, contains the path to the remote batch, etc
        remote_batchfile (str): the name of the remote batch file, e.g. '2021_08_26_15_35_16_test_batch.csv'
        session_list (list): a list containing the session number(s) to run from the remote batch, e.g. ``[0]`` or
            ``[0, 1, 4, ...], etc``

    Returns:
        The ``OMEGABatchObject`` created to run the remote batch

    """
    import pandas as pd
    from common.omega_log import OMEGABatchLog
    import time

    batch = OMEGABatchObject(analysis_final_year=options.analysis_final_year, calc_effects=options.calc_effects)
    batch.batch_definition_path = options.batch_path
    batch.batch_log = OMEGABatchLog(options)
    batch.batch_log.logwrite('REMOTE BATCHFILE = %s' % remote_batchfile)
    batch.dataframe = pd.read_csv(remote_batchfile, index_col=0)
    batch.dataframe.replace(to_replace={'True': True, 'False': False, 'TRUE': True, 'FALSE': False},
                            inplace=True)
    batch.dataframe.drop('Type', axis=1, inplace=True,
                         errors='ignore')  # drop Type column, no error if it's not there
    batch.parse_batch_params()  # convert '[2020]' -> [2020], etc
    batch.force_numeric_user_params()
    batch.force_numeric_developer_params()
    batch.get_batch_settings()
    batch.settings.auto_close_figures = options.auto_close_figures
    batch.add_sessions(verbose=False)
    # process sessions:
    for s_index in session_list:
        batch.batch_log.logwrite("\nProcessing Session %d (%s):" % (s_index, batch.sessions[s_index].name))

        if not batch.sessions[s_index].enabled:
            batch.batch_log.logwrite("Skipping Disabled Session '%s'" % batch.sessions[s_index].name)
            batch.batch_log.logwrite('')
        else:
            batch.sessions[s_index].result = batch.sessions[s_index].run()

            if not batch.sessions[s_index].result:
                # normal run, no failures
                time.sleep(1)  # wait for files to close
                summary_filename = os.path.join(options.bundle_path_root, batch.name,
                                                batch.sessions[s_index].name, bundle_output_folder_name,
                                                'o2log_%s_%s.txt' % (
                                                    batch.name, batch.sessions[s_index].name))

                # check session completion status and add status prefix to session folder
                if os.path.exists(summary_filename) and os.path.getsize(summary_filename) > 0:
                    with open(summary_filename, "r") as f_read:
                        last_line = f_read.readlines()[-1]
                    batch_path = os.path.join(options.bundle_path_root, batch.name)
                    if 'Session Complete' in last_line:
                        completion_prefix = '_'
                        batch.batch_log.logwrite('$$$ Session Completed, Session "%s" $$$' %
                                                 batch.sessions[s_index].name)
                    elif 'Session Fail' in last_line:
                        completion_prefix = '#FAIL_'
                        batch.batch_log.logwrite(
                            '*** Session Failed, Session "%s" ***' % batch.sessions[s_index].name)
                    else:
                        completion_prefix = '#WEIRD_'
                        batch.batch_log.logwrite('??? Weird Summary File for Session "%s" : last_line = "%s" ???' % (
                            batch.sessions[s_index].name, last_line))

                    os.rename(os.path.join(batch_path, batch.sessions[s_index].name),
                              os.path.join(batch_path, completion_prefix + batch.sessions[s_index].name))
            else:
                # abnormal run, display fault
                batch.batch_log.logwrite(
                    '\n*** Session Failed, Session "%s" ***' % batch.sessions[s_index].name)
                for idx, r in enumerate(batch.sessions[s_index].result):
                    if idx == 0:
                        # strip leading '\n'
                        r = r[1:]
                    batch.batch_log.logwrite(r)

    batch.batch_log.end_logfile("$$$ batch complete $$$")
    return batch


def run_omega_batch(no_validate=False, no_sim=False, bundle_path=None, no_bundle=False,
                    batch_file='', session_num=None, verbose=False, timestamp=None, show_figures=False, dispy=False,
                    dispy_ping=False, dispy_debug=False, dispy_exclusive=False, dispy_scheduler=None, local=False,
                    network=False, analysis_final_year=None, calc_effects='None'):
    """
    The top-level entry point for running a batch with the given settings, called from the GUI with a dictionary
    of arguments.  Reads the source batch file, expanding factorially where there are multi-valued parameters, bundles
    the source code and input files to a common directory and runs the batch from there.  Also handles parallel
    processing via ``dispy`` options

    Args:
        no_validate (bool): don't validate (ensure the existence of) source files
        no_sim (bool): skip simulation if ``True``, otherwise run as normal.  Typically not used except for debugging
        bundle_path (str): the full path to the bundle folder, e.g. '/Users/omega_user/Code/GitHub/USEPA_OMEGA2/bundle'
        no_bundle (bool): don't bundle files if ``True``, else bundle
        batch_file (str): the path name of the source (original, non-expanded, non-bundled) batch file,
            e.g. 'omega_model/test_inputs/test_batch.csv'
        session_num (int): the number of the session to run, if ``None`` all sessions are run
        verbose (bool): enables additional console and logfile output if ``True``
        timestamp (str): optional externally created timestamp (e.g. from the GUI)
        show_figures (bool): output figure windows are created when ``True``, otherwise figures are only save to files
        dispy (bool): enables parallel processing via the ``dispy`` Python package when ``True``
        dispy_ping (bool): ping ``dispy`` nodes if ``True`` and ``dispy`` is ``True``
        dispy_debug (bool): enables additional console output for investigating ``dispy`` behavior when ``True``
        dispy_exclusive (bool): if ``True`` then the ``dispy`` node runs a non-shared ``dispy`` cluster
        dispy_scheduler (str): the name / IP address of a shared ``dispy`` scheduler,
            available when ``dispy_exclusive`` is ``False``
        local (bool): if ``True`` then run ``dispy`` parallel processing on the local machine only, no network nodes
        network (bool): if ``True`` then allow ``dispy`` parallel processing on networked nodes
        analysis_final_year (int): optional override for the analysis final year batch parameter
        calc_effects (str): 'None', 'Physical' or 'Physical and Costs', determines what kind of effects post-processing
            to run

    Returns:
        Nothing

    """
    import sys

    # print('run_omega_batch sys.path = %s' % sys.path)
    from common import omega_globals

    if bundle_path is None:
        bundle_path = os.getcwd() + os.sep + 'bundle'

    options = OMEGABatchCLIOptions()
    options.validate_batch = not no_validate
    options.no_sim = no_sim
    options.bundle_path_root = bundle_path
    options.no_bundle = no_bundle
    options.batch_file = batch_file
    options.session_num = session_num
    options.verbose = verbose
    options.timestamp = timestamp
    options.auto_close_figures = not show_figures
    options.dispy = dispy
    options.dispy_ping = dispy_ping
    options.dispy_debug = dispy_debug
    options.dispy_exclusive = dispy_exclusive
    if dispy_scheduler:
        options.dispy_scheduler = dispy_scheduler
    options.local = local
    options.network = network
    options.analysis_final_year = analysis_final_year
    options.calc_effects = calc_effects

    if options.no_bundle:
        batchfile_path = os.path.split(args.batch_file)[0]

        package_folder = batchfile_path + os.sep + 'omega_model'

        subpackage_list = [package_folder + os.sep + d for d in os.listdir(package_folder)
                           if os.path.isdir(package_folder + os.sep + d)
                           and '__init__.py' in os.listdir('%s%s%s' % (package_folder, os.sep, d))]

        sys.path.extend([batchfile_path, batchfile_path + os.sep + package_folder] + subpackage_list)

    omega_globals.options = options

    # get batch info
    import shutil
    import pandas as pd
    from datetime import datetime

    from common.omega_dispy import DispyCluster

    if options.dispy_ping:
        dispycluster = DispyCluster(options)
        dispycluster.find_nodes()
        print("*** ping complete ***")
    else:
        batch = OMEGABatchObject(analysis_final_year=options.analysis_final_year,
                                 calc_effects=options.calc_effects)
        batch.batch_definition_path = os.path.dirname(os.path.abspath(options.batch_file)) + os.sep

        if '.csv' in options.batch_file:
            batch.dataframe = pd.read_csv(options.batch_file, index_col=0)
        else:
            batch.dataframe = pd.read_excel(options.batch_file, index_col=0, sheet_name="Sessions")

        batch.dataframe = batch.dataframe.replace(
            to_replace={'True': True, 'False': False, 'TRUE': True, 'FALSE': False})
        batch.dataframe = batch.dataframe.drop('Type', axis=1,
                                               errors='ignore')  # drop Type column, no error if it's not there

        batch.name = batch.read_parameter('Batch Name')
        if not options.no_bundle:
            if not options.timestamp:
                options.timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            batch.dataframe.loc['Batch Name'][0] = batch.name = options.timestamp + '_' + batch.name

        # validate session files
        validate_folder(options.bundle_path_root)
        options.batch_path = validate_folder(options.bundle_path_root, batch_name=batch.name)

        options.logfilename = options.batch_path + options.logfilename

        from common.omega_log import OMEGABatchLog
        batch.batch_log = OMEGABatchLog(options)

        if len(batch.dataframe.loc['Session Name']) != len(batch.dataframe.loc['Session Name'].unique()):
            msg = 'Duplicate Session Name, all Sessions must have a unique name %s' \
                  % str(tuple(batch.dataframe.loc['Session Name']))
            batch.batch_log.logwrite(msg)
            raise Exception(msg)

        batch.expand_dataframe(verbose=options.verbose)
        batch.force_numeric_user_params()
        batch.force_numeric_developer_params()
        batch.get_batch_settings()

        batch.add_sessions(verbose=options.verbose)

        import copy

        expanded_batch = copy.deepcopy(batch)
        expanded_batch.name = os.path.splitext(os.path.basename(options.batch_file))[0] + '_expanded' + \
                              os.path.splitext(options.batch_file)[1]

        if options.validate_batch:
            batch.batch_log.logwrite('Validating batch definition source files...')
            # validate (make sure they exist) shared (batch) files
            validate_file(options.batch_file)

            sys.path.insert(0, os.getcwd())

            print('\nbatch_definition_path = %s\n' % batch.batch_definition_path)

            for s in range(0, batch.num_sessions()):
                session = batch.sessions[s]
                batch.batch_log.logwrite("\nValidating Session %d ('%s') Files..." % (s, session.name))

                # automatically validate files and folders based on parameter naming convention
                for i in batch.dataframe.index:
                    # if options.verbose and (str(i).endswith(' Folder Name') or str(i).endswith(' File')):
                    #     batch.batch_log.logwrite('validating %s=%s' % (i, session.read_parameter(i)))
                    # elif str(i).endswith(' Folder Name'):
                    #     validate_folder(session.read_parameter(i))
                    # elif str(i).endswith(' File'):
                    #     validate_file(session.read_parameter(i))
                    if str(i).endswith(' File'):
                        source_file_path = session.read_parameter(i)
                        if type(source_file_path) is str:
                            source_file_path = source_file_path.replace('\\', os.sep)
                            if is_absolute_path(source_file_path):
                                if options.verbose: batch.batch_log.logwrite('validating %s=%s' % (i, source_file_path))
                                validate_file(source_file_path)
                            else:
                                if options.verbose: batch.batch_log.logwrite(
                                    'validating %s=%s' % (i, batch.batch_definition_path + source_file_path))
                                validate_file(batch.batch_definition_path + source_file_path)

                batch.batch_log.logwrite('Validating Session %d Parameters...' % s)
                session.init(verbose=True)

        batch.batch_log.logwrite("\n*** validation complete ***")

        if not options.no_bundle:
            # copy files to network_batch_path

            batch.batch_log.logwrite('Bundling Source Files and Requirements...')
            v = sys.version_info
            if getattr(sys, 'frozen', False):
                # running from executable
                with open('%sGUI_requirements.txt' % options.batch_path, 'w') as file_descriptor:
                    from omega_model import code_version
                    file_descriptor.write('OMEGA GUI %s' % code_version)
            else:
                # bundle requirements
                import subprocess
                cmd = '"%s" -m pip freeze > "%s"python_%s_%s_%s_requirements.txt' % \
                      (sys.executable, options.batch_path, v.major, v.minor, v.micro)
                subprocess.call(cmd, shell=True)

            # go to project top level so we can copy source files
            os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

            package_folder = 'omega_model'
            subpackage_list = [package_folder + os.sep + d for d in os.listdir(package_folder)
                               if os.path.isdir(package_folder + os.sep + d)
                               and '__init__.py' in os.listdir('%s%s%s' % (package_folder, os.sep, d))]

            for source_folder in [package_folder] + subpackage_list:
                source_files = [fn for fn in os.listdir(source_folder) if '.py' in fn]
                validate_folder(options.batch_path + source_folder)
                for f in source_files:
                    relocate_file(options.batch_path + source_folder, source_folder + os.sep + f)

            # write a copy of the original batch definition file to the bundle
            relocate_file(options.batch_path, options.batch_file)

            if options.verbose:
                # write a copy of the expanded, validated batch to the source batch_file directory:
                if '.csv' in options.batch_file:
                    expanded_batch.dataframe.to_csv(os.path.dirname(options.batch_file) + os.sep + expanded_batch.name)
                else:
                    expanded_batch.dataframe.to_excel(os.path.dirname(options.batch_file) + os.sep + expanded_batch.name,
                                                      "Sessions")

            if options.session_num is None:
                session_list = list({0}.union([s.num for s in batch.sessions if s.enabled]))
            else:
                session_list = list({0, options.session_num})

            for session in batch.sessions:
                # set Enable Session correctly in expanded batch based on session list
                session.enabled = session.num in session_list
                batch.dataframe.loc['Enable Session'][session.num] = session.enabled

            batch.dataframe_orig = batch.dataframe.copy()

            # copy session inputs to session folder(s) for active session(s)
            for s in session_list:
                if batch.sessions[s].enabled:
                    batch.batch_log.logwrite('Bundling Session %d Files...' % s)
                    session = batch.sessions[s]
                    options.session_path = validate_folder(options.bundle_path_root, batch_name=batch.name,
                                                           session_name=session.name)
                    validate_folder(options.bundle_path_root, batch_name=batch.name,
                                    session_name=session.name + os.sep + bundle_input_folder_name)
                    # indicate source batch
                    if is_absolute_path(options.batch_file):
                        # batch file path is absolute
                        batch.dataframe.loc['Batch Settings'][0] = 'FROM %s' % options.batch_file
                    else:
                        # batch file path is relative
                        batch.dataframe.loc['Batch Settings'][0] = 'FROM %s' % (
                                os.getcwd() + os.sep + options.batch_file)

                    # automatically rename and relocate source files
                    for i in batch.dataframe.index:
                        # if str(i).endswith(' Folder Name'):
                        #     if options.verbose:
                        #         batch.batch_log.logwrite('renaming %s to %s' % (batch.dataframe.loc[i][session.num],
                        #                                      session.name + os.sep + batch.dataframe.loc[i][
                        #                                          session.num]))
                        #     batch.dataframe.loc[i][session.num] = \
                        #         session.name + os.sep + batch.dataframe.loc[i][session.num]
                        if str(i).endswith(' File'):
                            source_file_path = batch.dataframe.loc[i][session.num]

                            if s > 0 and type(source_file_path) is float:
                                # assume file is a batch setting, not a session setting
                                source_file_path = batch.dataframe_orig.loc[i][0]

                            if type(source_file_path) is str:
                                # fix path separators, if necessary
                                source_file_path = source_file_path.replace('\\', os.sep)

                            if is_absolute_path(source_file_path):
                                # file_path is absolute path
                                if options.verbose:
                                    batch.batch_log.logwrite('relocating %s to %s' % (
                                    source_file_path, options.session_path + get_filenameext(source_file_path)))
                                batch.dataframe.loc[i][session.num] = session.name + os.sep + bundle_input_folder_name + os.sep + relocate_file(
                                    options.session_path + bundle_input_folder_name, source_file_path)
                            else:
                                # file_path is relative path
                                if options.verbose:
                                    batch.batch_log.logwrite('relocating %s to %s' % (
                                        batch.batch_definition_path + source_file_path,
                                        options.session_path + bundle_input_folder_name))
                                batch.dataframe.loc[i][session.num] = session.name + os.sep + bundle_input_folder_name + os.sep + relocate_file(
                                    options.session_path + bundle_input_folder_name, batch.batch_definition_path + source_file_path)

        import time

        time.sleep(5)  # was 10, wait for files to fully transfer...

        os.chdir(options.batch_path)

        remote_batchfile = batch.name + '.csv'
        batch.dataframe.to_csv(remote_batchfile)

        # print("Batch name = " + batch.name)
        batch.batch_log.logwrite("Batch name = " + batch.name)

        if options.session_num is None:
            session_list = list({0}.union([s.num for s in batch.sessions if s.enabled]))
        else:
            session_list = list({0, options.session_num})

        if not options.no_sim:
            if options.dispy:  # run remote job on cluster, except for first job if generating context vehicle prices
                dispy_session_list = session_list

                import copy
                # run reference case to generate vehicle prices then dispy the rest
                run_bundled_sessions(options, remote_batchfile, [0])
                dispy_session_list = dispy_session_list[1:]

                if dispy_session_list:
                    retry_count = dict()  # track retry attempts for terminated or abandoned jobs

                    dispycluster = DispyCluster(options)
                    dispycluster.find_nodes()
                    dispycluster.submit_sessions(batch, batch.name, options.bundle_path_root,
                                                 options.batch_path + batch.name,
                                                 dispy_session_list, options.calc_effects)
                    batch.batch_log.end_logfile("*** dispy batch complete ***")
            else:  # run from here
                batch = run_bundled_sessions(options, remote_batchfile, session_list)

            # if not running a session inside a dispy batch (i.e. we are the top-level batch):
            if options.session_num is None:
                # post-process sessions (collate summary files)
                session_summary_dfs = []
                annual_physical_effects_dfs = []
                apa_cost_effects_dfs = [] # this is short for annual_present_and_annualized_cost_effects
                for idx, s_index in enumerate(session_list):
                    if not batch.sessions[s_index].result or options.dispy:
                        batch.batch_log.logwrite("\nPost-Processing Session %d (%s):" % (s_index, batch.sessions[s_index].name))
                        session_summary_filename = options.batch_path + '_' \
                                                   + batch.sessions[s_index].settings.output_folder \
                                                   + batch.sessions[s_index].settings.session_unique_name \
                                                   + '_summary_results.csv'
                        session_summary_dfs.append(pd.read_csv(session_summary_filename))

                        annual_physical_effects_filename = options.batch_path + '_' \
                                                           + batch.sessions[s_index].settings.output_folder \
                                                           + batch.sessions[s_index].settings.session_unique_name \
                                                           + '_annual_physical_effects.csv'
                        annual_physical_effects_dfs.append(pd.read_csv(annual_physical_effects_filename))

                        apa_cost_effects_filename = options.batch_path + '_' \
                                                    + batch.sessions[s_index].settings.output_folder \
                                                    + batch.sessions[s_index].settings.session_unique_name \
                                                    + '_annual_present_and_annualized_cost_effects.csv'
                        apa_cost_effects_dfs.append(pd.read_csv(apa_cost_effects_filename))

                batch_summary_df = pd.concat(session_summary_dfs, ignore_index=True, sort=False)
                batch_summary_filename = batch.name + '_summary_results.csv'
                batch_summary_df.to_csv(batch_summary_filename, index=False)

                batch_annual_physical_effects_df = pd.concat(annual_physical_effects_dfs, ignore_index=True, sort=False)
                batch_annual_physical_effects_filename = batch.name + '_annual_physical_effects.csv'
                batch_annual_physical_effects_df.to_csv(batch_annual_physical_effects_filename, index=False)

                batch_apa_cost_effects_df = pd.concat(apa_cost_effects_dfs, ignore_index=True, sort=False)
                batch_apa_cost_effects_filename = batch.name + '_annual_present_and_annualized_cost_effects.csv'
                batch_apa_cost_effects_df.to_csv(batch_apa_cost_effects_filename, index=False)


if __name__ == '__main__':
    import os, sys, time
    import argparse

    parser = argparse.ArgumentParser(description='Run OMEGA batch simulation')
    parser.add_argument('--no_validate', action='store_true', help='Skip validating batch file')
    parser.add_argument('--no_sim', action='store_true', help='Skip running simulations')
    parser.add_argument('--bundle_path', type=str, help='Path to bundle folder',
                        default=os.getcwd() + os.sep + 'bundle')
    parser.add_argument('--no_bundle', action='store_true',
                        help='Do NOT gather and copy all source files to bundle_path')
    parser.add_argument('--batch_file', type=str, help='Path to batch definition file')
    parser.add_argument('--session_num', type=int, help='ID # of session to run from batch')
    parser.add_argument('--analysis_final_year', type=int, help='Override analysis final year')
    parser.add_argument('--calc_effects', type=str,
                        help='Type of effects calcs to run: "None", "Physical", or "Physical and Costs"',
                        default='None')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose omega_batch messages)')
    parser.add_argument('--timestamp', type=str,
                        help='Timestamp string, overrides creating timestamp from system clock', default=None)
    parser.add_argument('--show_figures', action='store_true', help='Display figure windows (no auto-close)')
    parser.add_argument('--dispy', action='store_true', help='Run sessions on dispynode(s)')
    parser.add_argument('--dispy_ping', action='store_true', help='Ping dispynode(s)')
    parser.add_argument('--dispy_debug', action='store_true', help='Enable verbose dispy debug messages)')
    parser.add_argument('--dispy_exclusive', action='store_true', help='Run exclusive job, do not share dispynodes')
    parser.add_argument('--dispy_scheduler', type=str, help='Override default dispy scheduler IP address',
                        default=None)

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--local', action='store_true', help='Run only on local machine, no network nodes')
    group.add_argument('--network', action='store_true', help='Run on local machine and/or network nodes')

    if len(sys.argv) > 1:
        args = parser.parse_args()

        try:
            run_omega_batch(no_validate=args.no_validate, no_sim=args.no_sim, bundle_path=args.bundle_path,
                            no_bundle=args.no_bundle, batch_file=args.batch_file, session_num=args.session_num,
                            verbose=args.verbose, timestamp=args.timestamp, show_figures=args.show_figures,
                            dispy=args.dispy, dispy_ping=args.dispy_ping, dispy_debug=args.dispy_debug,
                            dispy_exclusive=args.dispy_exclusive, dispy_scheduler=args.dispy_scheduler,
                            local=args.local,
                            network=args.network, analysis_final_year=args.analysis_final_year,
                            calc_effects=args.calc_effects)
        except:
            import traceback

            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)

    else:
        parser.parse_args(['--help'])

"""

**Routines to load base-year vehicle data, data structures to represent vehicles during compliance modeling
(transient or ephemeral vehicles), finalized vehicles (manufacturer-produced compliance vehicles), and composite
vehicles (used to group vehicles by various characteristics during compliance modeling).**

Classes are also implemented to handle composition and decomposition of vehicle attributes as part of the composite
vehicle workflow.  Some vehicle attributes are known and fixed in advance, others are created at runtime (e.g. off-cycle
credit attributes which may vary by policy).

----

**INPUT FILE FORMAT (Onroad Vehicle Calculations File)**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.  The data header uses a dynamic column notation, as detailed below.

The data represents the "gap" between on-cycle and onroad GHG performance.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,onroad_vehicle_calculations,input_template_version:,0.22,notes:,20221028a FTP US06 for w no gap for onroad and 2cycle w BEV 0.75 adjust for battery sizing

The data header consists of a ``drive_cycle_weight_year`` column followed by calculation columns.

Dynamic Data Header
    .. csv-table::
        :widths: auto

        drive_cycle_weight_year, ``{vehicle_select_attribute}:{vehicle_select_attribute_value}:{operator}:{vehicle_source_attribute}->{vehicle_destination_attribute}``, ...

Sample Data Columns
    .. csv-table::
        :widths: auto

        onroad_drive_cycle_weight_year,battery_sizing_drive_cycle_weight_year,fueling_class:BEV:/:nominal_onroad_direct_kwh_per_mile->battery_sizing_onroad_direct_kwh_per_mile,fueling_class:BEV:/:nominal_onroad_direct_kwh_per_mile->onroad_direct_kwh_per_mile,fueling_class:ICE:/:nominal_onroad_direct_co2e_grams_per_mile->onroad_direct_co2e_grams_per_mile
        0,2012,0.75,1,1

Data Column Name and Description

:onroad_drive_cycle_weight_year:
    Year to use for cert drive cycle weight calculations

:battery_sizing_drive_cycle_weight_year:
    Year to use for battery sizing drive cycle weight calculations

**Optional Columns**

Subsequent columns have the format
{vehicle_select_attribute}:{vehicle_select_attribute_value}:{operator}:
{vehicle_source_attribute}->{vehicle_destination_attribute}, the row value is a numeric value to applied to the source
attribute to calculate the destination attribute.

For example, a ``fueling_class:BEV:/:cert_direct_kwh_per_mile->onroad_direct_kwh_per_mile`` column with a row value of
``0.7`` would be evaluated as:

    ::

        if vehicle.fueling_class == 'BEV':
            vehicle.onroad_direct_kwh_per_mile = vehicle.cert_direct_kwh_per_mile / 0.7

----

**CODE**

"""

print('importing %s' % __file__)

import math

from omega_model import *

from policy.drive_cycle_weights import DriveCycleWeights
from policy.offcycle_credits import OffCycleCredits
from policy.upstream_methods import UpstreamMethods

from common.omega_functions import cartesian_prod, calc_frontier
from common.omega_plot import figure, label_xyt, vlineat
from common.omega_functions import weighted_value

from context.fuel_prices import FuelPrice
from context.onroad_fuels import OnroadFuel

from producer.vehicle_annual_data import VehicleAnnualData

cost_curve_interp_key = 'credits_co2e_Mg_per_vehicle'  # was 'cert_co2e_grams_per_mile'


class DecompositionAttributes(OMEGABase):
    """
    **Stores vehicle-specific attributes that will be tracked at each point of a vehicle or composite vehicle frontier**

    Decomposition Attributes are interpolated from the composite vehicle frontier during decomposition, using
    composite vehicle cert_co2e_grams_per_mile

    """

    values = []  #: list of all decomposition attribute names
    offcycle_values = []  #: list of off cycle credits that in the simulated vehicle file AND in the off cycle credits intput file
    other_values = []  #: non-base, non-offcycle, non-drive-cycle attribute names from the simulated vehicles input file, e.g. tech application columns like `cooled EGR`, etc

    @classmethod
    def init(cls):
        """
        Initialize DecompositionAttributes.

        Returns:
            Nothing, updates class data regarding available decomposition attibutes

        """
        from policy.offcycle_credits import OffCycleCredits
        from policy.drive_cycles import DriveCycles

        # set base values
        base_values = ['credits_co2e_Mg_per_vehicle',
                       'target_co2e_Mg_per_vehicle',
                       'cert_co2e_Mg_per_vehicle',

                       'cert_co2e_grams_per_mile',
                       'new_vehicle_mfr_generalized_cost_dollars',

                       'new_vehicle_mfr_cost_dollars',

                       'cert_indirect_co2e_grams_per_mile',

                       'cert_direct_co2e_grams_per_mile',
                       'cert_direct_kwh_per_mile',

                       'onroad_direct_co2e_grams_per_mile',
                       'onroad_direct_kwh_per_mile',

                       'cert_direct_oncycle_kwh_per_mile',
                       'cert_direct_offcycle_kwh_per_mile',

                       'cert_direct_oncycle_co2e_grams_per_mile',
                       'cert_direct_offcycle_co2e_grams_per_mile',

                       'cert_indirect_offcycle_co2e_grams_per_mile',
                       ]

        # determine dynamic values
        simulation_drive_cycles = list(set.intersection(set(omega_globals.options.CostCloud.cost_cloud_data_columns),
                                                        set(DriveCycles.drive_cycle_names)))

        cls.offcycle_values = list(set.intersection(set(omega_globals.options.CostCloud.cost_cloud_data_columns),
                                                    set(OffCycleCredits.offcycle_credit_names)))

        cls.other_values = list(set(omega_globals.options.CostCloud.cost_cloud_data_columns).
                                difference(base_values).
                                difference(simulation_drive_cycles).
                                difference(cls.offcycle_values))

        # combine base and dynamic values
        cls.values = base_values + cls.offcycle_values + simulation_drive_cycles + cls.other_values

    @staticmethod
    def interp1d(vehicle, cost_curve, index_column, index_value, attribute_name):
        """
        Interpolate the given cost curve using the given index column name, index value(s), vehicle and attribute name.

        Args:
            vehicle (Vehicle or CompositeVehicle): the vehicle object
            cost_curve (DataFrame): the cost curve to interpolate
            index_column (str): the name of the x-axis / index column
            index_value (numeric): the x-axis / index value(s) at which to interpolate
            attribute_name (str): name of the attribute to interpolate

        Returns:
            A float or numeric Array of values and each index value

        """
        if type(vehicle) != CompositeVehicle:
            prefix = 'veh_%s_' % vehicle.vehicle_id
        else:
            prefix = ''

        cn = '%s%s' % (prefix, attribute_name)

        if cn in cost_curve:
            if len(cost_curve) > 1:
                return np.interp(index_value, cost_curve[index_column].values,
                          cost_curve[cn].values)
            else:
                return cost_curve[cn].item()
        else:
            return None

    @staticmethod
    def interp1d_non_numeric(vehicle, cost_curve_non_numeric_data, index_column, index_value, attribute_name):
        """
        Interpolate non-numeric data

        Args:
            vehicle (Vehicle or CompositeVehicle): the vehicle object
            cost_curve_non_numeric_data (DataFrame): the cost curve non-numeric data to interpolate
            index_column (str): the name of the x-axis / index column
            index_value (numeric): the x-axis / index value(s) at which to interpolate
            attribute_name (str): name of the attribute to interpolate

        Returns:
            None, updates vehicle attributes based on interpolation

        """

        if attribute_name in cost_curve_non_numeric_data:
            if index_column not in cost_curve_non_numeric_data:
                cost_curve_non_numeric_data[index_column] = vehicle.cost_curve[
                    'veh_%s_%s' % (vehicle.vehicle_id, index_column)]
                cost_curve_non_numeric_data.reset_index(inplace=True)

            interp_index = np.interp(index_value,
                                  cost_curve_non_numeric_data[index_column],
                                  cost_curve_non_numeric_data.index)

            if interp_index <= 0:
                value = cost_curve_non_numeric_data[attribute_name].iloc[0]
            elif interp_index >= max(cost_curve_non_numeric_data.index):
                value = cost_curve_non_numeric_data[attribute_name].iloc[-1]
            elif cost_curve_non_numeric_data[attribute_name].iloc[math.trunc(interp_index)] != \
                    cost_curve_non_numeric_data[attribute_name].iloc[math.trunc(interp_index) + 1]:

                offset = interp_index - math.trunc(interp_index)

                # CU RV for intermediate string values

                if offset < 0.5:
                    value = cost_curve_non_numeric_data[attribute_name].iloc[math.trunc(interp_index)]
                else:
                    value = cost_curve_non_numeric_data[attribute_name].iloc[math.trunc(interp_index) + 1]

            else:
                value = cost_curve_non_numeric_data[attribute_name].iloc[math.trunc(interp_index)]
        else:
            value = None

        return value

    @classmethod
    def rename_decomposition_columns(cls, vehicle, cost_curve):
        """
        Rename the cost curve decomposition columns from non-vehicle specific to vehicle-specific (unique) columns,
        e.g. 'cert_co2e_grams_per_mile' -> 'veh_0_cert_co2e_grams_per_mile'.  Used to track the data associated with
        individual Vehicles in a CompositeVehicle cost curve.

        Args:
            vehicle (Vehicle): the vehicle associated with the new column names
            cost_curve (DataFrame): the cost curve to rename columns in

        Returns:
            ``cost_curve`` with renamed columns

        """
        rename_dict = dict()

        for ccv in cls.values:
            rename_dict[ccv] = 'veh_%s_%s' % (vehicle.vehicle_id, ccv)

        return cost_curve.rename(columns=rename_dict)


class VehicleOnroadCalculations(OMEGABase):
    """
    **Performs vehicle attribute calculations, as outlined in the input file.**

    Currently used to calculate the on-road "gap" in GHG performance.  See the input file format above for more
    information.

    """
    _cache = dict()

    onroad_drive_cycle_weight_year = None
    battery_sizing_drive_cycle_weight_year = None

    @staticmethod
    def init_vehicle_attribute_calculations_from_file(filename, clear_cache=False, verbose=False):
        """

        Initialize class data from input file.

        Args:
            filename (str): name of input file
            clear_cache (bool): if ``True`` then clear ``VehicleAttributeCalculations._cache``
            verbose (bool): enable additional console and logfile output if ``True``

        Returns:
            List of template/input errors, else empty list on success

        """
        if clear_cache:
            VehicleOnroadCalculations._cache = dict()

        if verbose:
            omega_log.logwrite('\nInitializing from %s...' % filename)

        input_template_name = 'onroad_vehicle_calculations'
        input_template_version = 0.22
        input_template_columns = {'onroad_drive_cycle_weight_year', 'battery_sizing_drive_cycle_weight_year'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns,
                                                             verbose=verbose)

            if not template_errors:
                VehicleOnroadCalculations.onroad_drive_cycle_weight_year = \
                    int(df['onroad_drive_cycle_weight_year'].iloc[0])
                VehicleOnroadCalculations.battery_sizing_drive_cycle_weight_year = \
                    int(df['battery_sizing_drive_cycle_weight_year'].iloc[0])

                df = df.set_index('onroad_drive_cycle_weight_year')
                df = df.drop([c for c in df.columns if 'Unnamed' in c], axis='columns')
                df = df.drop('battery_sizing_drive_cycle_weight_year', axis='columns')

                VehicleOnroadCalculations._cache = df.to_dict(orient='index')

                VehicleOnroadCalculations._cache['onroad_drive_cycle_weight_year'] = \
                    np.array([*VehicleOnroadCalculations._cache])

        return template_errors

    @staticmethod
    def perform_onroad_calculations(vehicle, cost_cloud=None):
        """
        Perform onroad calculations as specified by the input file.  Calculations may be applied to the vehicle
        directly, or to values in the cost_cloud if provided.

        Args:
            vehicle (Vehicle): the vehicle to perform calculations on
            cost_cloud (DataFrame): optional dataframe to perform calculations on

        Returns:
            Nothing, If ``cost_cloud`` is not provided then attribute calculations are performed on the vehicle object
            else they are performed on the cost cloud data

        """
        cache_key = VehicleOnroadCalculations.onroad_drive_cycle_weight_year

        if cache_key in VehicleOnroadCalculations._cache:
            calcs = VehicleOnroadCalculations._cache[cache_key]
            for calc, value in calcs.items():
                select_attribute, select_value, operator, action = calc.split(':')
                if vehicle.__getattribute__(select_attribute) == select_value:
                    attribute_source, attribute_target = action.split('->')

                    if cost_cloud is not None:
                        cost_cloud[attribute_target] = \
                            Eval.eval("cost_cloud['%s'] %s %s" % (attribute_source, operator, value),
                                                                  {}, {'cost_cloud': cost_cloud})
                    else:
                        vehicle.__setattr__(attribute_target,
                                            Eval.eval('vehicle.%s %s %s' % (attribute_source, operator, value),
                                                      {}, {'vehicle': vehicle}))
        else:
            raise Exception('Missing vehicle attribute (vehicle onroad) calculations for %d, or prior'
                            % vehicle.model_year)


class CompositeVehicle(OMEGABase):
    """
    **Implements vehicle composition and decomposition.**

    A CompositeVehicle contains a list of Vehicle objects whose attributes are weighted and combined to create
    "composite" attributes.  The weighting may be by sales (initial registered count), for example.
    The sum of the weights do not need to add up to 1.0 or any other particular value within the group of Vehicles,
    they are normalized internally by the class, so ultimately the relative weights are what determine the composite
    attributes.

    Of particular importance is the composite cost curve since it determines the range of technologies available to the
    manufacturer and their costs.  The producer compliance search is on the basis of composite vehicles in order to
    reduce the mathematical complexity of the factorial search process.

    During decomposition, the composite attributes are used to determine the attributes of the source Vehicles by
    reversing the weighting process.  Vehicles **must** be grouped in such a way that the weighting values do not
    change within a simulation year or else the composition and decomposition process will be invalid since the weights
    must remain the same throughout the process.

    Composite, normalized, target and cert CO2e Mg attributes are calculated from the bottom up based on the source
    Vehicle reg classes, physical attributes, etc, and the active policy.

    """
    def __init__(self, vehicles_list, vehicle_id, calc_composite_cost_curve=True,
                 weight_by='initial_registered_count'):
        """
        Create composite vehicle from list of Vehicle objects.

        Args:
            vehicles_list ([Vehicle, ...]: list of one or more ``Vehicle`` objects
            verbose (bool): enable additional console and logfile output if ``True``
            calc_composite_cost_curve (bool): if ``True`` then calculate the composite cost curve
            weight_by (str): name of the ``Vehicle`` attribute to weight by, e.g. 'initial_registered_count' or
            'base_year_market_share'

        """
        self.vehicle_list = vehicles_list  # CU
        self.vehicle_id = vehicle_id
        self.name = 'composite vehicle (%s)' % vehicle_id
        self.weight_by = weight_by

        self.model_year = self.vehicle_list[0].model_year  # RV
        self.reg_class_id = self.vehicle_list[0].reg_class_id
        self.fueling_class = self.vehicle_list[0].fueling_class
        self.market_class_id = self.vehicle_list[0].market_class_id
        self.alt_type = ''  # 'ALT' / 'NO_ALT'

        # weighted values are applied to the source vehicles by interpolating the composite cost curve after production
        # decisions are applied to composite vehicles, then those values are re-calculated for the composite vehicle
        # based on the relative share weights of the source vehicles.  See ``decompose()``
        # Composite vehicle weighted values are used to calculate market class/category sales-weighted average values
        # used by the ``omega_globals.options.SalesShare`` module to determine market shares
        self.weighted_values = ['credits_co2e_Mg_per_vehicle',
                                'target_co2e_Mg_per_vehicle',
                                'cert_co2e_Mg_per_vehicle',
                                'cert_co2e_grams_per_mile',
                                'cert_direct_co2e_grams_per_mile',
                                'cert_direct_kwh_per_mile',
                                'onroad_direct_co2e_grams_per_mile',
                                'onroad_direct_kwh_per_mile',
                                'new_vehicle_mfr_cost_dollars',
                                'new_vehicle_mfr_generalized_cost_dollars',
                                'battery_kwh',
                                # these are needed for NEMS market share calcs (in addition to g/mi and kWh/hi):
                                'curbweight_lbs',
                                'rated_hp',
                                'footprint_ft2'
                                ]

        # calc weighted values
        for wv in self.weighted_values:
            self.__setattr__(wv, weighted_value(self.vehicle_list, self.weight_by, wv))

        self.total_weight = 0
        self.initial_registered_count = 0
        for v in self.vehicle_list:
            self.total_weight += v.__getattribute__(self.weight_by)
            self.initial_registered_count += v.initial_registered_count
            v.set_target_co2e_Mg()

        for v in self.vehicle_list:
            if self.total_weight != 0:
                v.composite_vehicle_share_frac = v.__getattribute__(self.weight_by) / self.total_weight
            else:
                v.composite_vehicle_share_frac = 0

        if calc_composite_cost_curve:
            plot_cost_curve = ((omega_globals.options.log_vehicle_cloud_years == 'all') or
                              (self.model_year in omega_globals.options.log_vehicle_cloud_years)) and \
                              'v_cloud_plots' in omega_globals.options.verbose_log_modules
            # CU
            self.cost_curve = self.calc_composite_cost_curve(plot=plot_cost_curve)

        self.tech_option_iteration_num = 0

    def retail_fuel_price_dollars_per_unit(self, calendar_year=None):
        """
        Calculate the weighted retail fuel price in dollars per unit from the Vehicles in the ``vehicle_list``.

        Args:
            calendar_year (int): the year to perform calculations in

        Returns:
            Weighted Vehicle ``retail_fuel_price_dollars_per_unit``

        """
        if calendar_year is None:
            calendar_year = self.model_year

        return weighted_value(self.vehicle_list, self.weight_by, 'retail_fuel_price_dollars_per_unit',
                              calendar_year)

    def decompose(self):
        """
        Decompose composite vehicle attributes to source Vehicles in the ``vehicle_list``.  In addition to assigning
        Vehicle initial registered counts, attributes stored in the weighted cost curve are interpolated on the basis
        of composite ``cert_co2e_grams_per_mile`` and assigned the Vehicles.

        Returns:
            Nothing, updates attributes of Vehicles in the ``vehicle_list``

        See Also:
            ``producer.vehicles.DecompositionAttributes``

        """
        plot_cost_curve = ((omega_globals.options.log_producer_compliance_search_years == 'all') or
                           (self.model_year in omega_globals.options.log_producer_compliance_search_years)) and \
            any([v.name in omega_globals.options.plot_and_log_vehicles for v in self.vehicle_list])

        if plot_cost_curve:
            from common.omega_plot import figure, label_xyt

            fig, ax1 = figure()
            label_xyt(ax1, 'CO2e [g/mi]', 'Generalized Cost [$]', '%s' % self.name)

        for v in self.vehicle_list:
            if 'cost_curve' in self.__dict__:
                for ccv in DecompositionAttributes.values:
                    v.__setattr__(ccv,
                              DecompositionAttributes.interp1d(v, self.cost_curve, cost_curve_interp_key,
                                                               self.__getattribute__(cost_curve_interp_key),
                                                               ccv))

                for ccv in omega_globals.options.CostCloud.cloud_non_numeric_data_columns:
                    v.__setattr__(ccv,
                          DecompositionAttributes.interp1d_non_numeric(v, v.cost_curve_non_numeric_data,
                                                                       cost_curve_interp_key,
                                                                       v.__getattribute__(cost_curve_interp_key),
                                                                       ccv))

            v.initial_registered_count = self.initial_registered_count * v.composite_vehicle_share_frac
            v.set_target_co2e_Mg()  # varies by model year and initial_registered_count
            v.set_cert_co2e_Mg()  # varies by model year and initial_registered_count

            if plot_cost_curve:
                if v.name in omega_globals.options.plot_and_log_vehicles:
                    ax1.plot(v.cost_curve['veh_%s_cert_co2e_grams_per_mile' % v.vehicle_id],
                             v.cost_curve['veh_%s_new_vehicle_mfr_generalized_cost_dollars' % v.vehicle_id], 's-',
                             color='black',
                             label='veh %s %s' % (v.vehicle_id, v.name))

                    ax1.plot(v.cert_co2e_grams_per_mile,
                             v.new_vehicle_mfr_generalized_cost_dollars, '*',
                             color=ax1.get_lines()[-1].get_color(), markersize=15)

                else:
                    ax1.plot(v.cost_curve['veh_%s_cert_co2e_grams_per_mile' % v.vehicle_id],
                             v.cost_curve['veh_%s_new_vehicle_mfr_generalized_cost_dollars' % v.vehicle_id], '.--',
                             linewidth=1,
                             label='veh %s %s' % (v.vehicle_id, v.name))

                    ax1.plot(v.cert_co2e_grams_per_mile,
                             v.new_vehicle_mfr_generalized_cost_dollars, '*',
                             color=ax1.get_lines()[-1].get_color(), markersize=10)

        # calc weighted values
        for wv in self.weighted_values:
            self.__setattr__(wv, weighted_value(self.vehicle_list, self.weight_by, wv))

        if plot_cost_curve:
            ax1.relim()
            ax1.autoscale()

            ax1.plot(self.cost_curve[cost_curve_interp_key],
                     self.cost_curve['new_vehicle_mfr_generalized_cost_dollars'], '-', linewidth=3,
                     label='Composite Vehicle')

            ax1.plot(self.cert_co2e_grams_per_mile, self.new_vehicle_mfr_generalized_cost_dollars, '*', markersize=25,
                     color=ax1.get_lines()[-1].get_color())

            ax1.legend(fontsize='medium', bbox_to_anchor=(1.04, 0), loc="lower left",
                       borderaxespad=0)

            figname = '%s%s_%s_cost_curve_decomposition.png' % (omega_globals.options.output_folder, self.model_year,
                                                                ax1.get_title())
            figname = figname.replace('(', '_').replace(')', '_').replace('.', '_').replace(' ', '_')\
                .replace('__', '_').replace('_png', '.png')
            fig.savefig(figname, bbox_inches='tight')

    def calc_composite_cost_curve(self, plot=False):
        """
        Calculate a composite ``cost_curve`` from the cost curves of Vehicles in the ``vehicle_list``.

        Each Vehicle's cost curve is sequentially weighted into the composite cost curve by performing a full
        factorial combination of the points in the prior composite curve with the new Vehicle's curve and then
        calculating a new frontier from the resulting cloud.  In this way the mathematical complexity of calculating
        the full factorial combination of all Vehicle cost curve points is avoided, while still arriving at the correct
        weighted answer for the frontier.

        Args:
            plot (bool): plot composite curve if ``True``

        Returns:
            DataFrame containing the composite cost curve

        """
        if plot:
            fig, ax1 = figure()
            label_xyt(ax1, cost_curve_interp_key, 'Generalized Cost [$]', '%s' % self.name)

        composite_frontier_df = pd.DataFrame()
        composite_frontier_df['market_share_frac'] = [0]

        # calc weighted values
        for wv in self.weighted_values:
            composite_frontier_df[wv] = [0]

        for v in self.vehicle_list:
            vehicle_frontier = v.cost_curve
            vehicle_frontier['veh_%s_market_share' % v.vehicle_id] = v.composite_vehicle_share_frac

            composite_frontier_df = cartesian_prod(composite_frontier_df, vehicle_frontier)

            prior_market_share_frac = composite_frontier_df['market_share_frac'].values
            veh_market_share_frac = composite_frontier_df['veh_%s_market_share' % v.vehicle_id].values

            for wv in self.weighted_values:
                composite_frontier_df[wv] = \
                    (composite_frontier_df[wv].values * prior_market_share_frac +
                     composite_frontier_df['veh_%s_%s' % (v.vehicle_id, wv)].values * veh_market_share_frac) / \
                    (prior_market_share_frac + veh_market_share_frac)

            # update running total market share
            composite_frontier_df['market_share_frac'] = prior_market_share_frac + veh_market_share_frac

            drop_columns = [c for c in composite_frontier_df.columns if c.endswith('_y') or c.endswith('_x') or
                            c.endswith('_market_share')] + ['_']

            # calculate new sales-weighted frontier
            composite_frontier_df = calc_frontier(composite_frontier_df, cost_curve_interp_key,
                                                  'new_vehicle_mfr_generalized_cost_dollars',
                                                  allow_upslope=True)

            # CU
            composite_frontier_df = \
                composite_frontier_df.drop(drop_columns + ['frontier_factor'], axis=1, errors='ignore')

            if plot:
                if v.name in omega_globals.options.plot_and_log_vehicles:
                    ax1.plot(vehicle_frontier['veh_%s_%s' % (v.vehicle_id, cost_curve_interp_key)],
                             vehicle_frontier['veh_%s_new_vehicle_mfr_generalized_cost_dollars' % v.vehicle_id], 's-',
                             color='black',
                             label='veh %s %s' % (v.vehicle_id, v.name))
                else:
                    ax1.plot(vehicle_frontier['veh_%s_%s' % (v.vehicle_id, cost_curve_interp_key)],
                             vehicle_frontier['veh_%s_new_vehicle_mfr_generalized_cost_dollars' % v.vehicle_id], '.--',
                             linewidth=1, label='veh %s %s' % (v.vehicle_id, v.name))

        if plot:
            ax1.plot(composite_frontier_df[cost_curve_interp_key],
                     composite_frontier_df['new_vehicle_mfr_generalized_cost_dollars'], '-', linewidth=3,
                     label='Composite Vehicle')

            ax1.legend(fontsize='medium', bbox_to_anchor=(1.04, 0), loc="lower left", borderaxespad=0)

            figname = '%s%s_%s_cost_curve_composition.png' % (omega_globals.options.output_folder, self.model_year,
                                                              ax1.get_title())
            figname = figname.replace('(', '_').replace(')', '_').replace('.', '_').replace(' ', '_')\
                .replace('__', '_').replace('_png', '.png')
            fig.savefig(figname, bbox_inches='tight')

        return composite_frontier_df

    def get_from_cost_curve(self, attribute_name, query_points):
        """
        Get new vehicle manufacturer cost from the composite cost curve for the provided cert CO2e g/mi value(s).

        Args:
            attribute_name (str): the name of the attribute to query
            query_points (numeric list or Array): the values at which to query the cost curve

        Returns:
            A float or numeric Array of new vehicle manufacturer costs

        """

        return DecompositionAttributes.interp1d(self, self.cost_curve, cost_curve_interp_key, query_points,
                                                attribute_name)

    def get_max_cost_curve_index(self):
        """
        Get maximum value from the cost curve interpolation axis, see ``vehicles.cost_curve_interp_key``.

        Returns:
            A float, max value from the cost curve interpolation axis

        """
        return self.cost_curve[cost_curve_interp_key].values.max()

    def get_min_cost_curve_index(self):
        """
        Get minimum value from the cost curve interpolation axis, see ``vehicles.cost_curve_interp_key``.

        Returns:
            A float, min value from the cost curve interpolation axis

        """
        return self.cost_curve[cost_curve_interp_key].values.min()

    def get_weighted_attribute(self, attribute_name):
        """
        Calculate the weighted value of the given attribute.

        Args:
            attribute_name (str): the name of the attribute to weight

        Returns:
            The weighted value of the given attribute.

        """
        return weighted_value(self.vehicle_list, self.weight_by, attribute_name)


def calc_vehicle_frontier(vehicle):
    """
    Calculate the cost cloud and the frontier of the cost cloud for the given vehilce.

    Args:
        vehicle (Vehicle): the vehicle to calculate a frontier for

    Returns:
        Returns ``vehicle`` with updated frontier

    """
    cost_cloud = omega_globals.options.CostCloud.get_cloud(vehicle)
    vehicle.calc_cost_curve(cost_cloud)
    return vehicle


def is_up_for_redesign(vehicle):
    """
        Return ``True`` if vehicle is available for production and/or redesign

    Args:
        vehicle (VehicleFinal, Vehicle): the vehicle object

    Returns:
        ``True`` if vehicle is at or past its redesign interval

    """
    redesign_interval_gain = \
        np.interp(vehicle.model_year,
                  omega_globals.options.redesign_interval_gain_years,
                  omega_globals.options.redesign_interval_gain)

    return vehicle.model_year - int(vehicle.prior_redesign_year) >= \
        int(vehicle.redesign_interval) * redesign_interval_gain


def transfer_vehicle_data(from_vehicle, to_vehicle, model_year=None):
    """

    Transfer data from a VehicleFinal to Vehicle object, or vice versa.  Transfer from VehicleFinal to Vehicle
    creates a new cost curve, based on the simulated vehicles data and policy factors for the model year.

    Args:
        from_vehicle (VehicleFinal, Vehicle): the vehicle to convert from
        to_vehicle (Vehicle, VehicleFinal): the vehicle to convert to
        model_year (int): if provided, sets the ``to_vehicle`` model year, otherwise model year comes from the
            ``from_vehicle``

    Returns:
        Nothing, updates ``to_vehicle`` attributes

    """
    base_properties = ('name', 'manufacturer_id', 'compliance_id', 'model_year', 'fueling_class',
                       'cost_curve_class', 'reg_class_id', 'in_use_fuel_id',
                       'cert_fuel_id', 'market_class_id', 'lifetime_VMT',
                       'context_size_class',
                       'unibody_structure', 'drive_system', 'dual_rear_wheel', 'curbweight_lbs', 'eng_rated_hp',
                       'footprint_ft2',
                       'base_year_target_coef_a', 'base_year_target_coef_b', 'base_year_target_coef_c', 'body_style',
                       'structure_material', 'base_year_powertrain_type', 'base_year_reg_class_id',
                       'base_year_market_share',
                       'base_year_vehicle_id', 'base_year_glider_non_structure_mass_lbs', 'base_year_cert_fuel_id',
                       'base_year_glider_non_structure_cost_dollars',
                       'base_year_footprint_ft2', 'base_year_curbweight_lbs', 'base_year_curbweight_lbs_to_hp',
                       'base_year_msrp_dollars', 'battery_kwh', 'motor_kw', 'charge_depleting_range_mi',
                       'prior_redesign_year', 'redesign_interval', 'in_production', 'base_year_product',
                       'workfactor', 'gvwr_lbs', 'gcwr_lbs', 'base_year_workfactor', 'base_year_gvwr_lbs',
                       'base_year_gcwr_lbs', )

    # transfer base properties
    for attr in base_properties:
        to_vehicle.__setattr__(attr, from_vehicle.__getattribute__(attr))

    if model_year:
        to_vehicle.model_year = model_year

    # transfer dynamic attributes
    for attr in VehicleFinal.dynamic_attributes:
        to_vehicle.__setattr__(attr, from_vehicle.__getattribute__(attr))

    # assign user-definable reg class
    to_vehicle.reg_class_id = omega_globals.options.RegulatoryClasses.get_vehicle_reg_class(to_vehicle)

    to_vehicle.set_target_co2e_grams_per_mile()  # varies by model year

    if type(from_vehicle) == Vehicle:
        # finish transfer from Vehicle to VehicleFinal
        to_vehicle.from_vehicle_id = from_vehicle.vehicle_id

        to_vehicle.initial_registered_count = from_vehicle.initial_registered_count

        # set dynamic attributes
        for attr in DecompositionAttributes.values:
            to_vehicle.__setattr__(attr, from_vehicle.__getattribute__(attr))

        to_vehicle.target_co2e_Mg = from_vehicle.target_co2e_Mg
        to_vehicle.cert_co2e_Mg = from_vehicle.cert_co2e_Mg


class Vehicle(OMEGABase):
    """
    **Implements "candidate" or "working" vehicles for use during the producer compliance search.**

    ``Vehicle`` objects are initialized from ``VehicleFinal`` objects and then appropriate attributes are transferred
    from ``Vehicle`` objects to ``VehicleFinal`` objects at the conclusion of the producer search and producer-consumer
    iteration.

    Each ``Vehicle`` object has a unique ``cost_curve`` (and potentially ``cost_cloud``) that tracks multiple aspects
    of vehicle technology application as a function of cert CO2e g/mi and the data contained in the simulated
    vehicles file.  The cost curve is calculated from the cost cloud at the start of each model year as a function
    of the active policy and the simulated vehicle data and costs.  For example, the value of off-cycle credits may
    vary from one model year to the next and technology costs may decrease over time.

    See Also:
        ``producer.vehicles.transfer_vehicle_data()``, ``VehicleFinal``, ``context.CostCloud``

    """
    next_vehicle_id = 0

    _cache = dict()

    def __init__(self):
        """
        Create a new ``Vehicle`` object

        """
        self.vehicle_id = Vehicle.next_vehicle_id
        Vehicle.set_next_vehicle_id()
        self.name = ''
        self.manufacturer_id = None
        self.compliance_id = None
        self.model_year = None
        self.fueling_class = None
        self.cost_curve_class = None
        self.reg_class_id = None
        self.context_size_class = None
        self.target_co2e_grams_per_mile = 0
        self.lifetime_VMT = 0
        self.cert_co2e_Mg = 0
        self.target_co2e_Mg = 0
        self.in_use_fuel_id = None
        self.cert_fuel_id = None
        self.market_class_id = None
        self.initial_registered_count = 0
        self.projected_sales = 0
        self.cost_curve = None
        self.cost_curve_non_numeric_data = None
        self.unibody_structure = 1
        self.drive_system = 1
        self.dual_rear_wheel = 0
        self.curbweight_lbs = 0
        self.footprint_ft2 = 0
        self.eng_rated_hp = 0
        self.base_year_target_coef_a = 0
        self.base_year_target_coef_b = 0
        self.base_year_target_coef_c = 0
        self.prior_redesign_year = 0
        self.redesign_interval = 0
        self.in_production = False
        self.body_style = ''
        self.structure_material = ''
        self.base_year_product = False
        self.base_year_powertrain_type = ''
        self.base_year_reg_class_id = None
        self.base_year_cert_fuel_id = None
        self.base_year_vehicle_id = 0
        self.base_year_market_share = 0
        self.model_year_prevalence = 0
        self.base_year_glider_non_structure_mass_lbs = 0
        self.base_year_glider_non_structure_cost_dollars = 0
        self.base_year_footprint_ft2 = 0
        self.base_year_curbweight_lbs = 0
        self.base_year_curbweight_lbs_to_hp = 0
        self.base_year_msrp_dollars = 0
        self.battery_kwh = 0
        self.motor_kw = 0
        self.charge_depleting_range_mi = 0
        self.workfactor = 0
        self.gvwr_lbs = 0
        self.gcwr_lbs = 0
        self.base_year_workfactor = 0
        self.base_year_gvwr_lbs = 0
        self.base_year_gcwr_lbs = 0

        # additional attriutes are added dynamically and may vary based on user inputs (such as off-cycle credits)
        for ccv in DecompositionAttributes.values:
            self.__setattr__(ccv, 0)

        for dc in VehicleFinal.dynamic_columns:
            self.__setattr__(dc, 0)

    @staticmethod
    def reset_vehicle_ids():
        """
        Reset vehicle IDs.  Sets ``Vehicle.next_vehicle_id`` to an initial value.

        """
        Vehicle.next_vehicle_id = 0

    @staticmethod
    def set_next_vehicle_id():
        """
        Increments ``Vehicle.next_vehicle_id``.

        """
        Vehicle.next_vehicle_id = Vehicle.next_vehicle_id + 1

    def retail_fuel_price_dollars_per_unit(self, calendar_year=None):
        """
        Get the retail fuel price for the Vehicle in dollars per unit for the given calendar year.
        Used to calculate producer generalized cost and also average fuel cost by market class.

        Args:
            calendar_year (int): the year to get the price in

        Returns:
            The retail fuel price in dollars per unit for the given year.

        """
        cache_key = (self.vehicle_id, 'retail_fuel_price', calendar_year)

        if cache_key not in self._cache:
            if calendar_year is None:
                calendar_year = self.model_year

            price = 0
            fuel_dict = Eval.eval(self.in_use_fuel_id, {'__builtins__': None}, {})
            for fuel, fuel_share in fuel_dict.items():
                price += FuelPrice.get_fuel_prices(calendar_year, 'retail_dollars_per_unit', fuel) * fuel_share

            self._cache[cache_key] = price

        return self._cache[cache_key]

    def onroad_co2e_emissions_grams_per_unit(self):
        """
        Calculate the onroad (in-use) CO2e emission in grams per unit of onroad fuel, including refuel efficiency.
        Used to calculate producer generalized cost.

        Returns:
            The onroad CO2e emission in grams per unit of onroad fuel, including refuel efficiency.

        """
        cache_key = (self.vehicle_id, 'onroad_co2e_emissions_grams_per_unit', self.model_year)

        if cache_key not in self._cache:

            co2_emissions_grams_per_unit = 0
            fuel_dict = Eval.eval(self.in_use_fuel_id, {'__builtins__': None}, {})
            for fuel, fuel_share in fuel_dict.items():
                co2_emissions_grams_per_unit += \
                    (OnroadFuel.get_fuel_attribute(self.model_year, fuel, 'direct_co2e_grams_per_unit') /
                     OnroadFuel.get_fuel_attribute(self.model_year, fuel, 'refuel_efficiency') * fuel_share)

            self._cache[cache_key] = co2_emissions_grams_per_unit

        return self._cache[cache_key]

    def set_target_co2e_grams_per_mile(self):
        """
        Set the vehicle cert target CO2e grams per mile based on the current policy and vehicle attributes.

        Returns:
            Nothing, updates ``target_co2e_grams_per_mile``

        """
        self.target_co2e_grams_per_mile = omega_globals.options.VehicleTargets.calc_target_co2e_gpmi(self)

    def set_target_co2e_Mg(self):
        """
        Set the vehicle cert target CO2e megagrams based on the current policy and vehicle attributes.

        Returns:
            Nothing, updates ``target_co2e_Mg``

        """
        self.target_co2e_Mg = omega_globals.options.VehicleTargets.calc_target_co2e_Mg(self)

    def set_cert_co2e_Mg(self):
        """
        Set the vehicle cert CO2e megagrams based on the current policy and vehicle attributes.

        Returns:
            Nothing, updates ``cert_co2e_Mg``

        """
        self.cert_co2e_Mg = omega_globals.options.VehicleTargets.calc_cert_co2e_Mg(self)

    def calc_battery_sizing_onroad_direct_kWh_per_mile(self, cloud):
        """

        Args:
            cloud:

        Returns:

        """
        drive_cycle_weight_year = VehicleOnroadCalculations.battery_sizing_drive_cycle_weight_year

        kwh_per_mile_scale = np.interp(self.model_year, omega_globals.options.kwh_per_mile_scale_years,
                                       omega_globals.options.kwh_per_mile_scale)

        cloud['battery_sizing_onroad_direct_kwh_per_mile'] = 0
        cloud['nominal_onroad_direct_kwh_per_mile'] = kwh_per_mile_scale * \
                                                      DriveCycleWeights.calc_cert_direct_oncycle_kwh_per_mile(
                                                          drive_cycle_weight_year, self.fueling_class, cloud)

        # calc onroad_direct values
        VehicleOnroadCalculations.perform_onroad_calculations(self, cloud)

        cloud['battery_sizing_onroad_direct_kwh_per_mile'] = cloud['battery_sizing_onroad_direct_kwh_per_mile']

        return cloud

    def calc_cert_values(self, cloud):
        """

        Args:
            cloud:

        Returns:

        """
        # calculate onroad values -------------------------------------------------------------------------------------

        drive_cycle_weight_year = VehicleOnroadCalculations.onroad_drive_cycle_weight_year

        cloud['onroad_direct_co2e_grams_per_mile'] = 0
        cloud['onroad_direct_kwh_per_mile'] = 0

        if self.fueling_class != 'BEV':
            cloud['onroad_direct_oncycle_co2e_grams_per_mile'] = \
                DriveCycleWeights.calc_cert_direct_oncycle_co2e_grams_per_mile(drive_cycle_weight_year,
                                                                               self.fueling_class,
                                                                               cloud)
        else:
            cloud['onroad_direct_oncycle_co2e_grams_per_mile'] = 0

        if self.fueling_class != 'ICE':
            cloud['onroad_direct_oncycle_kwh_per_mile'] = \
                DriveCycleWeights.calc_cert_direct_oncycle_kwh_per_mile(drive_cycle_weight_year,
                                                                        self.fueling_class, cloud)
        else:
            cloud['onroad_direct_oncycle_kwh_per_mile'] = 0

        # calculate offcycle values before calculating onroad
        cloud = OffCycleCredits.calc_off_cycle_credits(drive_cycle_weight_year, self, cloud)

        cloud['nominal_onroad_direct_co2e_grams_per_mile'] = \
            cloud['onroad_direct_oncycle_co2e_grams_per_mile'] - \
            cloud['cert_direct_offcycle_co2e_grams_per_mile']

        cloud['nominal_onroad_direct_kwh_per_mile'] = \
            cloud['onroad_direct_oncycle_kwh_per_mile'] - \
            cloud['cert_direct_offcycle_kwh_per_mile']

        # calc onroad_direct values
        VehicleOnroadCalculations.perform_onroad_calculations(self, cloud)

        # calculate cert values ---------------------------------------------------------------------------------------
        if self.fueling_class != 'BEV':
            cloud['cert_direct_oncycle_co2e_grams_per_mile'] = \
                DriveCycleWeights.calc_cert_direct_oncycle_co2e_grams_per_mile(self.model_year, self.fueling_class,
                                                                               cloud)
        else:
            cloud['cert_direct_oncycle_co2e_grams_per_mile'] = 0

        if self.fueling_class != 'ICE':
            cloud['cert_direct_oncycle_kwh_per_mile'] = \
                DriveCycleWeights.calc_cert_direct_oncycle_kwh_per_mile(self.model_year, self.fueling_class, cloud)
        else:
            cloud['cert_direct_oncycle_kwh_per_mile'] = 0

        # re-calculate off cycle credits before calculating upstream
        cloud = OffCycleCredits.calc_off_cycle_credits(self.model_year, self, cloud)

        cloud['cert_direct_co2e_grams_per_mile'] = \
            cloud['cert_direct_oncycle_co2e_grams_per_mile'] - \
            cloud['cert_direct_offcycle_co2e_grams_per_mile']

        cloud['cert_direct_kwh_per_mile'] = \
            cloud['cert_direct_oncycle_kwh_per_mile'] - \
            cloud['cert_direct_offcycle_kwh_per_mile']

        # add upstream calcs
        upstream_method = UpstreamMethods.get_upstream_method(self.model_year)

        cloud['cert_indirect_co2e_grams_per_mile'] = \
            upstream_method(self, cloud['cert_direct_co2e_grams_per_mile'],
                            cloud['cert_direct_kwh_per_mile'])

        cloud['cert_co2e_grams_per_mile'] = \
            cloud['cert_direct_co2e_grams_per_mile'] + \
            cloud['cert_indirect_co2e_grams_per_mile'] - \
            cloud['cert_indirect_offcycle_co2e_grams_per_mile']

        return cloud

    """
        Create a frontier ("cost curve") from a vehicle's cloud of simulated vehicle points ("cost cloud") based
        on the current policy and vehicle attributes.  The cost values are a function of the producer generalized cost
        and the CO2e values are a function of the simulated vehicle data and the policy.

        Policy factors that modify the cost cloud and may modify the frontier from year to year include off cycle
        credit values, drive cycle weightings, upstream values, etc.  This method is also where costs could be
        updated dynamically before calculating the frontier (for example, cost reductions due to learning may
        already be present in the cost cloud, or could be implemented here instead).

        Additionally, each point in the frontier contains the values as determined by ``DecompositionAttributes``.

        Args:
            cost_cloud (DataFrame): vehicle cost cloud

        Returns:
            None, updates vehicle.cost_curve with vehicle tecnhology frontier / cost curve as a DataFrame.

        """
    def calc_cost_curve(self, cost_cloud):
        """
        Calculate vehicle cost curve from cost cloud.

        Args:
            cost_cloud (dataframe): cloud of costed powertrain variants

        Returns:
            Nothing, updates vehicle ``cost_curve`` attribute

        """
        # cull cost_cloud points here, based on producer constraints or whatever #

        # calculate frontier from updated cloud
        allow_upslope = False

        # special handling for the case where all cost_curve_interp_key values are the same value, e.g. 0
        if cost_cloud[cost_curve_interp_key].values.min() == cost_cloud[cost_curve_interp_key].values.max():
            # try to take lowest generalized cost point
            cost_curve = cost_cloud[cost_cloud['new_vehicle_mfr_generalized_cost_dollars'] == cost_cloud[
                'new_vehicle_mfr_generalized_cost_dollars'].values.min()]
            # if somehow more than one point, just take the first one...
            if len(cost_curve) > 1:
                cost_curve = cost_curve.iloc[[0]]
        else:
            cost_curve = calc_frontier(cost_cloud, cost_curve_interp_key,
                                       'new_vehicle_mfr_generalized_cost_dollars', allow_upslope=allow_upslope)

        # CU

        # rename generic columns to vehicle-specific columns
        cost_curve = DecompositionAttributes.rename_decomposition_columns(self, cost_curve)

        # drop frontier factor
        cost_curve = cost_curve.drop(columns=['frontier_factor'], errors='ignore')

        self.cost_curve_non_numeric_data = \
            cost_cloud[omega_globals.options.CostCloud.cloud_non_numeric_data_columns].iloc[cost_curve.index]

        # save vehicle cost cloud, with indicated frontier points
        if (omega_globals.options.log_vehicle_cloud_years == 'all') or \
                (self.model_year in omega_globals.options.log_vehicle_cloud_years):

            if 'v_cloud_plots' in omega_globals.options.verbose_log_modules:
                from common.omega_plot import figure, label_xyt

                fig, ax1 = figure()
                label_xyt(ax1, cost_curve_interp_key, 'Cost [$]', 'veh %s %s' % (self.vehicle_id, self.name))

                ax1.plot(cost_cloud[cost_curve_interp_key],
                         cost_cloud['new_vehicle_mfr_generalized_cost_dollars'], 'x',
                         label='Cloud Points')

                ax1.plot(cost_curve['veh_%s_%s' % (self.vehicle_id, cost_curve_interp_key)],
                         cost_curve['veh_%s_new_vehicle_mfr_generalized_cost_dollars' % self.vehicle_id], 'x-',
                         color='black',
                         label='Cost Curve')

                ax1.legend(fontsize='medium', bbox_to_anchor=(0, 1.07), loc="lower left", borderaxespad=0)
                figname = '%s%d_%s_%s_cost_curve.png' % \
                          (omega_globals.options.output_folder, self.model_year, self.name, self.vehicle_id,)
                fig.savefig(figname.replace(' ', '_').replace(':', '-'), bbox_inches='tight')

                fig, ax1 = figure()
                label_xyt(ax1, cost_curve_interp_key, 'CO2e [g/mi]', 'veh %s %s' % (self.vehicle_id, self.name))

                ax1.plot(cost_cloud[cost_curve_interp_key],
                         cost_cloud['cert_co2e_grams_per_mile'], '.',
                         label='CO2e g/mi')

                ax1.plot(cost_curve['veh_%s_%s' % (self.vehicle_id, cost_curve_interp_key)],
                         cost_curve['veh_%s_cert_co2e_grams_per_mile' % self.vehicle_id], 's-',
                         color='black',
                         label='CO2e Curve')

                ax1.legend(fontsize='medium', bbox_to_anchor=(0, 1.07), loc="lower left", borderaxespad=0)
                figname = '%s%d_%s_%s_co2e_curve.png' % \
                          (omega_globals.options.output_folder, self.model_year, self.name, self.vehicle_id,)
                fig.savefig(figname.replace(' ', '_').replace(':', '-'), bbox_inches='tight')

            if 'v_cost_clouds' in omega_globals.options.verbose_log_modules:
                cost_cloud = DecompositionAttributes.rename_decomposition_columns(self, cost_cloud)
                cost_cloud['frontier'] = False
                cost_cloud.loc[cost_curve.index, 'frontier'] = True

                filename = '%s%d_%s_%s_cost_cloud.csv' % (omega_globals.options.output_folder, self.model_year,
                                                          self.name.replace(' ', '_').replace(':', '-'),
                                                          self.vehicle_id)
                cost_cloud.to_csv(filename, columns=sorted(cost_cloud.columns), index=False)

            if 'v_cost_curves' in omega_globals.options.verbose_log_modules:
                filename = '%s%d_%s_%s_cost_curve.csv' % (omega_globals.options.output_folder, self.model_year,
                                                          self.name.replace(' ', '_').replace(':', '-'),
                                                          self.vehicle_id)
                cc = pd.merge(cost_curve, self.cost_curve_non_numeric_data, left_index=True, right_index=True)
                cc.to_csv(filename, columns=sorted(cc.columns), index=False)

        self.cost_curve = cost_curve

    @property
    def fueling_class_reg_class_id(self):
        """
        Create string combining fueling class id and regulatory class id.

        Returns:
            String combining fueling class id and regulatory class id, e.g. 'ICE.car'

        """
        return '%s.%s' % (self.fueling_class, self.reg_class_id)


class VehicleFinal(SQABase, Vehicle):
    """
    **Loads the base year vehicle data and stores finalized vehicles in the database.**

    Finalized vehicles are those ultimately produced by the manufacturer and are the basis for the effect and cost
    calculations performed after the compliance modeling.

    """
    # --- database table properties ---
    __tablename__ = 'vehicles'
    __table_args__ = {'extend_existing': True}  # fix sphinx-apidoc crash
    vehicle_id = Column(Integer, primary_key=True)  #: unique vehicle ID, database table primary key
    from_vehicle_id = Column(String)  #: transferred vehicle ID from Vehicle object
    name = Column(String)  #: vehicle name
    manufacturer_id = Column(String, ForeignKey('manufacturers.manufacturer_id'))  #: vehicle manufacturer ID
    compliance_id = Column(String)  #: compliance ID, may be the manufacturer ID or 'consolidated_OEM'
    manufacturer = relationship('Manufacturer', back_populates='vehicles')  #: SQLAlchemy relationship link to manufacturer table

    model_year = Column(Numeric)  #: vehicle model year
    fueling_class = Column(Enum(*fueling_classes, validate_strings=True))  #: fueling class, e.g. 'BEV', 'ICE'
    reg_class_id = Column(String)  #: regulatory class assigned according the active policy
    context_size_class = Column(String)  #: context size class, used to project future vehicle sales based on the context
    target_co2e_grams_per_mile = Column(Float)  #: cert target CO2e g/mi, as determined by the active policy
    lifetime_VMT = Column('lifetime_vmt', Float)  #: lifetime VMT, used to calculate CO2e Mg
    cert_co2e_Mg = Column('cert_co2e_megagrams', Float)  #: cert CO2e Mg, as determined by the active policy
    target_co2e_Mg = Column('target_co2e_megagrams', Float)  #: cert CO2e Mg, as determined by the active policy
    in_use_fuel_id = Column(String)  #: in-use / onroad fuel ID
    cert_fuel_id = Column(String)  #: cert fuel ID
    market_class_id = Column(String)  #: market class ID, as determined by the consumer subpackage
    unibody_structure = Column(Float)  #: unibody structure flag, e.g. 0,1
    drive_system = Column(Float)  #: drive system, 1=FWD, 2=RWD, 4=AWD
    dual_rear_wheel = Column(Float)  #: dual_rear_wheel, 0=No, 1=Yes
    body_style = Column(String)  #: vehicle body style, e.g. 'sedan'
    base_year_powertrain_type = Column(String)  #: vehicle powertrain type, e.g. 'ICE', 'HEV', etc
    charge_depleting_range_mi = Column(Float)  #: vehicle charge-depleting range, miles
    prior_redesign_year = Column(Float)  #: prior redesign year
    redesign_interval = Column(Float)  #: redesign interval
    in_production = Column(Boolean)  #: True if vehicle is in production
    price_modification_dollars = Column(Float)  #: vehicle price modification (i.e. incentive value) in dollars
    modified_cross_subsidized_price_dollars = Column(Float)  #: vehicle modified cross subsidized price in dollars
    price_dollars = Column(Float)  #: vehicle price in dollars
    market_class_cross_subsidy_multiplier = Column(Float)  #: vehicle market class cross subsidy multiplier

    # "base year properties" - things that may change over time but we want to retain the original values
    base_year_product = Column(Boolean)  #: True if vehicle was in production in base year
    base_year_reg_class_id = Column(Enum(*legacy_reg_classes, validate_strings=True))  #: base year regulatory class, historical data
    base_year_vehicle_id = Column(Float)  #: base year vehicle id from vehicles.csv
    base_year_market_share = Column(Float)  #: base year market share, used to maintain market share relationships within context size classes
    model_year_prevalence = Column(Float)  #: used to maintain market share relationships within context size classes during market projection
    base_year_glider_non_structure_mass_lbs = Column(Float)  #: base year non-structure mass lbs (i.e. "content")
    base_year_glider_non_structure_cost_dollars = Column(Float)  #: base year non-structure cost dollars
    base_year_footprint_ft2 = Column(Float)  #: base year vehicle footprint, square feet
    base_year_curbweight_lbs = Column(Float)  #: base year vehicle curbweight, pounds
    base_year_curbweight_lbs_to_hp = Column(Float)  #: base year curbweight to power ratio (pounds per hp)
    base_year_msrp_dollars = Column(Float)  #: base year Manufacturer Suggested Retail Price (dollars)
    base_year_target_coef_a = Column(Float)  #: roadload A coefficient, lbs
    base_year_target_coef_b = Column(Float)  #: roadload B coefficient, lbs/mph
    base_year_target_coef_c = Column(Float)  #: roadload C coefficient, lbs/mph^2
    base_year_workfactor = Column(Float)
    base_year_gvwr_lbs = Column(Float)
    base_year_gcwr_lbs = Column(Float)
    base_year_cert_fuel_id = Column(String)

    # non-numeric attributes that could change based on interpolating the frontier:
    cost_curve_class = Column(String)  #: ALPHA modeling result class
    structure_material = Column(String)  #: vehicle body structure material, e.g. 'steel'
    # numeric attributes that can change based on interpolating the frontier:
    battery_kwh = Column(Float)  #: vehicle propulsion battery kWh
    motor_kw = Column(Float)  #: vehicle propulsion motor(s) total power, kW
    curbweight_lbs = Column(Float)  #: vehicle curbweight, pounds
    footprint_ft2 = Column(Float)  #: vehicle footprint, square feet
    # RV
    eng_rated_hp = Column(Float)  #: engine rated horsepower
    workfactor = Column(Float)
    gvwr_lbs = Column(Float)
    gcwr_lbs = Column(Float)

    _initial_registered_count = Column('_initial_registered_count', Float)
    projected_sales = Column(Float)  #: used to project context size class sales

    # --- static properties ---
    compliance_ids = set()  #: the set of compliance IDs (manufacturer IDs or 'consolidated_OEM')
    mfr_base_year_share_data = dict()  #: dict of base year market shares by compliance ID and various categories, used to project future vehicle sales based on the context

    # these are used to validate vehicles.csv:
    # mandatory input file columns, the rest can be optional numeric columns:
    mandatory_input_template_columns = {'vehicle_name', 'manufacturer_id', 'model_year', 'reg_class_id',
                                   'context_size_class', 'electrification_class', 'cost_curve_class', 'in_use_fuel_id',
                                   'cert_fuel_id', 'sales', 'footprint_ft2', 'eng_rated_hp',
                                   'unibody_structure', 'drive_system', 'dual_rear_wheel', 'curbweight_lbs', 'gvwr_lbs',
                                   'gcwr_lbs', 'target_coef_a', 'target_coef_b', 'target_coef_c',
                                   'body_style', 'msrp_dollars', 'structure_material',
                                   'prior_redesign_year', 'redesign_interval'}  # RV any other columns

    dynamic_columns = []  #: additional data columns such as footprint, passenger capacity, etc
    dynamic_attributes = []  #: list of dynamic attribute names, from dynamic_columns

    # **additional attributes are dynamically added from DecompositionAttributes.values during omega2.init_omega()**

    @property
    def initial_registered_count(self):
        """
        Get the vehicle initial registered count

        Returns:
            The vehicle initial registered count

        """
        return self._initial_registered_count

    @initial_registered_count.setter
    def initial_registered_count(self, initial_registered_count):
        """
        Setter for vehicle initial registered count

        Args:
            initial_registered_count (numeric): the vehicle initial registered count

        Returns:
            Nothing, updates vehicle initial registered count

        """
        self._initial_registered_count = initial_registered_count

        omega_globals.session.add(self)  # update database so vehicle_annual_data foreign key succeeds...
        omega_globals.session.flush()  # update vehicle_id, otherwise it's None

        VehicleAnnualData.update_registered_count(self,
                                                  calendar_year=int(self.model_year),
                                                  registered_count=initial_registered_count)

    @staticmethod
    def get_max_model_year():
        """
        Get the maximum model year present in the base year vehicle data, used to set the analysis initial year

        Returns:
            The maximum model year present in the base year vehicle data

        """
        return omega_globals.session.query(func.max(VehicleFinal.model_year)).scalar()

    @staticmethod
    def get_compliance_vehicles(calendar_year, compliance_id):
        """
        Get vehicles by year and compliance ID.  Used at the beginning of the producer compliance search to pull in
        the prior year vehicles

        Args:
            calendar_year (int): the calendar year (model year) to pull vehicles from
            compliance_id (str): manufacturer name, or 'consolidated_OEM'

        Returns:
            A list of ``VehicleFinal`` objects for the given year and compliance ID

        """
        return omega_globals.session.query(VehicleFinal). \
            filter(VehicleFinal.compliance_id == compliance_id). \
            filter(VehicleFinal.model_year == calendar_year).all()

    @staticmethod
    def get_vehicle_attributes(vehicle_id, attributes):
        """
        A generic 'getter' to retrieve one or more ``VehicleFinal`` object attributes

        Args:
            vehicle_id (int): the vehicle ID
            attributes (str, [strs]): the name or list of names of vehicle attributes to get

        Returns:
            The value(s) of the requested attribute(s)

        """
        if type(attributes) is not list:
            attributes = [attributes]
        attrs = VehicleFinal.get_class_attributes(attributes)
        return omega_globals.session.query(*attrs).filter(VehicleFinal.vehicle_id == vehicle_id).one()

    @staticmethod
    def calc_target_co2e_Mg(model_year, compliance_id):
        """
        Calculate the total cert target CO2e Mg for the given model year and compliance ID

        Args:
            model_year (int): the model year of the cert target
            compliance_id (str): manufacturer name, or 'consolidated_OEM'

        Returns:
            The sum of vehicle cert target CO2e Mg for the given model year and compliance ID

        """
        return omega_globals.session.query(func.sum(VehicleFinal.target_co2e_Mg)). \
            filter(VehicleFinal.compliance_id == compliance_id). \
            filter(VehicleFinal.model_year == model_year).scalar()

    @staticmethod
    def calc_cert_co2e_Mg(model_year, compliance_id):
        """
        Calculate the total cert CO2e Mg for the given model year and compliance ID

        Args:
            model_year (int): the model year of the cert Mg
            compliance_id (str): manufacturer name, or 'consolidated_OEM'

        Returns:
            The sum of vehicle cert CO2e Mg for the given model year and compliance ID

        """
        return omega_globals.session.query(func.sum(VehicleFinal.cert_co2e_Mg)). \
            filter(VehicleFinal.compliance_id == compliance_id). \
            filter(VehicleFinal.model_year == model_year).scalar()

    @staticmethod
    def clone_vehicle(vehicle):
        """
        Make a "clone" of a vehicle, used to create alternate powertrain versions of vehicles in the base year fleet

        Args:
            vehicle (VehicleFinal): the vehicle to clone

        Returns:
            A new ``VehicleFinal`` object with non-powertrain attributes copied from the given vehicle

        """
        inherit_properties = ['name', 'manufacturer_id', 'compliance_id',
                              'reg_class_id', 'context_size_class', 'unibody_structure', 'body_style',
                              'base_year_reg_class_id', 'base_year_market_share', 'base_year_vehicle_id',
                              'curbweight_lbs', 'base_year_glider_non_structure_mass_lbs', 'base_year_cert_fuel_id',
                              'base_year_glider_non_structure_cost_dollars',
                              'footprint_ft2', 'base_year_footprint_ft2', 'base_year_curbweight_lbs', 'drive_system',
                              'dual_rear_wheel', 'base_year_curbweight_lbs_to_hp', 'base_year_msrp_dollars',
                              'base_year_target_coef_a', 'base_year_target_coef_b', 'base_year_target_coef_c',
                              'prior_redesign_year', 'redesign_interval', 'workfactor', 'gvwr_lbs', 'gcwr_lbs',
                              'base_year_workfactor', 'base_year_gvwr_lbs', 'base_year_gcwr_lbs'] \
                              + VehicleFinal.dynamic_attributes

        # model year and registered count are required to make a full-blown VehicleFinal object, compliance_id
        # is required for vehicle annual data init
        veh = VehicleFinal(model_year=vehicle.model_year,
                           compliance_id=vehicle.compliance_id,
                           initial_registered_count=1)

        # get the rest of the attributes from the list
        for p in inherit_properties:
            veh.__setattr__(p, vehicle.__getattribute__(p))

        return veh

    @staticmethod
    def init_vehicles_from_dataframe(df, verbose=False):
        """

        Load data from the base year vehicle dataframe

        Args:
            df (DataFrame): dataframe of aggregated vehicle data
            verbose (bool): enable additional console and logfile output if True

        Returns:
            List of template/input errors, else empty list on success

        """
        from context.new_vehicle_market import NewVehicleMarket

        vehicle_shares_dict = {'total': 0}

        VehicleFinal.compliance_ids = set()
        vehicles_list = []

        if verbose:
            omega_log.logwrite('\nInitializing vehicle data ...')

        from producer.manufacturers import Manufacturer
        from context.mass_scaling import MassScaling
        from context.body_styles import BodyStyles

        # load data into database
        for i in df.index:
            veh = VehicleFinal(
                name=df.loc[i, 'vehicle_name'],
                vehicle_id=i,
                manufacturer_id=df.loc[i, 'manufacturer_id'],
                model_year=df.loc[i, 'model_year'],
                context_size_class=df.loc[i, 'context_size_class'],
                cost_curve_class=df.loc[i, 'cost_curve_class'],
                in_use_fuel_id=df.loc[i, 'in_use_fuel_id'],
                cert_fuel_id=df.loc[i, 'cert_fuel_id'],
                unibody_structure=df.loc[i, 'unibody_structure'],
                drive_system=df.loc[i, 'drive_system'],
                dual_rear_wheel=df.loc[i, 'dual_rear_wheel'],
                curbweight_lbs=df.loc[i, 'curbweight_lbs'],
                footprint_ft2=df.loc[i, 'footprint_ft2'],
                eng_rated_hp=df.loc[i, 'eng_rated_hp'],
                base_year_target_coef_a=df.loc[i, 'target_coef_a'],
                base_year_target_coef_b=df.loc[i, 'target_coef_b'],
                base_year_target_coef_c=df.loc[i, 'target_coef_c'],
                body_style=df.loc[i, 'body_style'],
                structure_material=df.loc[i, 'structure_material'],
                base_year_reg_class_id=df.loc[i, 'reg_class_id'],
                base_year_footprint_ft2=df.loc[i, 'footprint_ft2'],
                base_year_curbweight_lbs=df.loc[i, 'curbweight_lbs'],
                base_year_msrp_dollars=df.loc[i, 'msrp_dollars'],
                base_year_glider_non_structure_mass_lbs=df.loc[i, 'glider_non_structure_mass_lbs'],
                base_year_glider_non_structure_cost_dollars=df.loc[i, 'glider_non_structure_cost_dollars'],
                base_year_workfactor=df.loc[i, 'workfactor'],
                base_year_vehicle_id=i,  # i.e. aggregated_vehicles.csv index number...
                base_year_cert_fuel_id=df.loc[i, 'cert_fuel_id'],
                battery_kwh=df.loc[i, 'battery_kwh'],
                motor_kw=df.loc[i, 'motor_kw'],
                charge_depleting_range_mi=df.loc[i, 'charge_depleting_range_mi'],
                base_year_powertrain_type=df.loc[i, 'base_year_powertrain_type'],
                prior_redesign_year=df.loc[i, 'prior_redesign_year'],
                redesign_interval=df.loc[i, 'redesign_interval'],
                in_production=True,
                base_year_product=True,
                workfactor=df.loc[i, 'workfactor'],
                gvwr_lbs=df.loc[i, 'gvwr_lbs'],
                gcwr_lbs=df.loc[i, 'gcwr_lbs'],
                base_year_gvwr_lbs=df.loc[i, 'gvwr_lbs'],
                base_year_gcwr_lbs=df.loc[i, 'gcwr_lbs'],
            )

            electrification_class = df.loc[i, 'electrification_class']

            for attr, dc in zip(VehicleFinal.dynamic_attributes, VehicleFinal.dynamic_columns):
                veh.__setattr__(attr, df.loc[i, dc])

            if omega_globals.options.consolidate_manufacturers:
                veh.compliance_id = 'consolidated_OEM'
            else:
                veh.compliance_id = veh.manufacturer_id

            if not omega_globals.manufacturer_aggregation:
                veh.manufacturer_id = 'consolidated_OEM'

            VehicleFinal.compliance_ids.add(veh.compliance_id)

            # update initial registered count >after< setting compliance id, it's required for vehicle annual data
            veh.initial_registered_count = df.loc[i, 'sales']

            # RV
            if veh.base_year_powertrain_type in ['BEV', 'FCV']:
                if veh.base_year_powertrain_type == 'FCV':
                    # RV
                    veh.in_use_fuel_id = "{'US electricity':1.0}"
                    veh.cert_fuel_id = "{'electricity':1.0}"
                    veh.base_year_powertrain_type = 'BEV'
                veh.fueling_class = 'BEV'
            else:
                veh.fueling_class = 'ICE'

            veh.cert_direct_oncycle_co2e_grams_per_mile = df.loc[i, 'cert_direct_oncycle_co2e_grams_per_mile']
            veh.cert_direct_co2e_grams_per_mile = veh.cert_direct_oncycle_co2e_grams_per_mile

            veh.cert_co2e_grams_per_mile = None
            veh.cert_direct_kwh_per_mile = df.loc[i, 'cert_direct_oncycle_kwh_per_mile']  # RV
            veh.onroad_direct_co2e_grams_per_mile = 0
            veh.onroad_direct_kwh_per_mile = 0

            # RV
            if veh.base_year_powertrain_type in ['BEV', 'FCV']:
                rated_hp = veh.motor_kw * 1.34102
            elif electrification_class in ['HEV', 'PHEV']:
                rated_hp = veh.eng_rated_hp + veh.motor_kw * 1.34102
            else:
                rated_hp = veh.eng_rated_hp

            veh.base_year_curbweight_lbs_to_hp = veh.curbweight_lbs / rated_hp

            vehicle_shares_dict['total'] += veh.initial_registered_count

            if veh.context_size_class not in vehicle_shares_dict:
                vehicle_shares_dict[veh.context_size_class] = 0

            vehicle_shares_dict[veh.context_size_class] += veh.initial_registered_count

            vehicles_list.append(veh)

            # assign user-definable market class
            veh.market_class_id = omega_globals.options.MarketClass.get_vehicle_market_class(veh)
            veh.manufacturer.update_market_class_data(veh.compliance_id, veh.market_class_id)

            non_responsive_market_category = \
                omega_globals.options.MarketClass.get_non_responsive_market_category(veh.market_class_id)

            if non_responsive_market_category not in NewVehicleMarket.context_size_class_info_by_nrmc:
                NewVehicleMarket.context_size_class_info_by_nrmc[non_responsive_market_category] = dict()

            if veh.context_size_class not in \
                    NewVehicleMarket.context_size_class_info_by_nrmc[non_responsive_market_category]:
                NewVehicleMarket.context_size_class_info_by_nrmc[non_responsive_market_category][veh.context_size_class] = \
                    {'total': veh.initial_registered_count, 'share': 0}
            else:
                NewVehicleMarket.context_size_class_info_by_nrmc[non_responsive_market_category][veh.context_size_class]['total'] += \
                    veh.initial_registered_count

            # update base year sales data by context size class (used for specifically for sales projections)
            if veh.context_size_class not in NewVehicleMarket.base_year_context_size_class_sales:
                NewVehicleMarket.base_year_context_size_class_sales[veh.context_size_class] = \
                    veh.initial_registered_count
            else:
                NewVehicleMarket.base_year_context_size_class_sales[veh.context_size_class] += \
                    veh.initial_registered_count

            key = veh.compliance_id + '_' + veh.context_size_class
            if key not in NewVehicleMarket.manufacturer_base_year_sales_data:
                NewVehicleMarket.manufacturer_base_year_sales_data[key] = veh.initial_registered_count
            else:
                NewVehicleMarket.manufacturer_base_year_sales_data[key] += veh.initial_registered_count

            # update base year sales data by market class id
            if veh.market_class_id not in NewVehicleMarket.base_year_other_sales:
                NewVehicleMarket.base_year_other_sales[veh.market_class_id] = veh.initial_registered_count
            else:
                NewVehicleMarket.base_year_other_sales[veh.market_class_id] += veh.initial_registered_count

            key = veh.compliance_id + '_' + veh.market_class_id
            if key not in NewVehicleMarket.manufacturer_base_year_sales_data:
                NewVehicleMarket.manufacturer_base_year_sales_data[key] = veh.initial_registered_count
            else:
                NewVehicleMarket.manufacturer_base_year_sales_data[key] += veh.initial_registered_count

            # update base year sales data by market category
            for market_category in veh.market_class_id.split('.'):
                if market_category not in NewVehicleMarket.base_year_other_sales:
                    NewVehicleMarket.base_year_other_sales[market_category] = veh.initial_registered_count
                else:
                    NewVehicleMarket.base_year_other_sales[market_category] += veh.initial_registered_count

            for market_category in veh.market_class_id.split('.'):
                key = veh.compliance_id + '_' + market_category
                if key not in NewVehicleMarket.manufacturer_base_year_sales_data:
                    NewVehicleMarket.manufacturer_base_year_sales_data[key] = veh.initial_registered_count
                else:
                    NewVehicleMarket.manufacturer_base_year_sales_data[key] += veh.initial_registered_count

            if verbose:
                print(veh)

        # Update market share and create alternative vehicles (a BEV equivalent for every ICE vehicle, etc).
        # Alternative vehicles maintain fleet utility mix across model years and prevent all future vehicles
        # from becoming midsize car BEVs, for example, just because that's the dominant BEV in the base year
        # fleet
        for v in vehicles_list:
            v.base_year_market_share = v.initial_registered_count / vehicle_shares_dict['total']

            if v.fueling_class != 'BEV' or omega_globals.options.allow_ice_of_bev:
                alt_veh = v.clone_vehicle(v)  # create alternative powertrain clone of vehicle
                alt_veh.in_production = is_up_for_redesign(alt_veh)
                alt_veh.base_year_product = False

                if v.fueling_class == 'ICE':
                    alt_veh.fueling_class = 'BEV'
                    alt_veh.base_year_powertrain_type = 'BEV'
                    alt_veh.name = 'BEV of ' + v.name
                    for tf in omega_globals.options.CostCloud.tech_flags:
                        alt_veh.__setattr__(tf, None)
                    alt_veh.bev = 1
                    alt_veh.in_use_fuel_id = "{'US electricity':1.0}"
                    alt_veh.cert_fuel_id = "{'electricity':1.0}"
                    alt_veh.battery_kwh = 60  # RV
                    alt_veh.motor_kw = 150 + 100 * (v.drive_system == 4)  # RV
                    if alt_veh.base_year_reg_class_id == 'mediumduty' and alt_veh.body_style == 'cuv_suv':
                        alt_veh.charge_depleting_range_mi = 150
                    else:
                        alt_veh.charge_depleting_range_mi = 300  # RV
                    alt_veh.eng_rated_hp = 0
                    alt_veh.eng_cyls_num = 0
                    alt_veh.eng_disp_liters = 0
                else:
                    alt_veh.fueling_class = 'ICE'
                    alt_veh.base_year_powertrain_type = 'ICE'
                    alt_veh.name = 'ICE of ' + v.name
                    for tf in omega_globals.options.CostCloud.tech_flags:
                        alt_veh.__setattr__(tf, None)
                    alt_veh.ice = 1
                    alt_veh.in_use_fuel_id = "{'pump gasoline':1.0}"
                    alt_veh.cert_fuel_id = "{'gasoline':1.0}"
                    alt_veh.eng_rated_hp = v.motor_kw * 1.34102  # RV
                    alt_veh.motor_kw = 0
                    alt_veh.charge_depleting_range_mi = 0
                    alt_veh.battery_kwh = 0
                    alt_veh.eng_cyls_num = None
                    alt_veh.eng_disp_liters = None

                alt_veh.market_class_id = omega_globals.options.MarketClass.get_vehicle_market_class(alt_veh)
                v.manufacturer.update_market_class_data(v.compliance_id, alt_veh.market_class_id)

                alt_veh.cert_direct_oncycle_co2e_grams_per_mile = 0
                alt_veh.cert_direct_co2e_grams_per_mile = 0
                alt_veh.cert_direct_kwh_per_mile = 0

        for nrmc in NewVehicleMarket.context_size_class_info_by_nrmc:
            for csc in NewVehicleMarket.context_size_class_info_by_nrmc[nrmc]:
                NewVehicleMarket.context_size_class_info_by_nrmc[nrmc][csc]['share'] = \
                    NewVehicleMarket.context_size_class_info_by_nrmc[nrmc][csc]['total'] / vehicle_shares_dict[csc]

        # calculate manufacturer base year context size class shares
        VehicleFinal.compliance_ids = sorted(list(VehicleFinal.compliance_ids))

        VehicleFinal.mfr_base_year_share_data = dict()
        for compliance_id in VehicleFinal.compliance_ids:
            for size_class in NewVehicleMarket.base_year_context_size_class_sales:
                if compliance_id not in VehicleFinal.mfr_base_year_share_data:
                    VehicleFinal.mfr_base_year_share_data[compliance_id] = dict()

                key = compliance_id + '_' + size_class

                if key not in NewVehicleMarket.manufacturer_base_year_sales_data:
                    NewVehicleMarket.manufacturer_base_year_sales_data[key] = 0

                if verbose:
                    print('%s: %s / %s: %.2f' % (key,
                                                 NewVehicleMarket.manufacturer_base_year_sales_data[key],
                                                 NewVehicleMarket.base_year_context_size_class_sales[size_class],
                                                 NewVehicleMarket.manufacturer_base_year_sales_data[key] /
                                                 NewVehicleMarket.base_year_context_size_class_sales[size_class]))

                VehicleFinal.mfr_base_year_share_data[compliance_id][size_class] = \
                    NewVehicleMarket.manufacturer_base_year_sales_data[key] / \
                    NewVehicleMarket.base_year_context_size_class_sales[size_class]

        for compliance_id in VehicleFinal.compliance_ids:
            for other in NewVehicleMarket.base_year_other_sales:
                if compliance_id not in VehicleFinal.mfr_base_year_share_data:
                    VehicleFinal.mfr_base_year_share_data[compliance_id] = dict()

                key = compliance_id + '_' + other

                if key not in NewVehicleMarket.manufacturer_base_year_sales_data:
                    NewVehicleMarket.manufacturer_base_year_sales_data[key] = 0

                if verbose:
                    print('%s: %s / %s: %.2f' % (key,
                                                 NewVehicleMarket.manufacturer_base_year_sales_data[key],
                                                 NewVehicleMarket.base_year_other_sales[other],
                                                 NewVehicleMarket.manufacturer_base_year_sales_data[key] /
                                                 NewVehicleMarket.base_year_other_sales[other]))

                VehicleFinal.mfr_base_year_share_data[compliance_id][other] = \
                    NewVehicleMarket.manufacturer_base_year_sales_data[key] / \
                    NewVehicleMarket.base_year_other_sales[other]

        if verbose:
            print_dict(NewVehicleMarket.base_year_context_size_class_sales)
            print_dict(NewVehicleMarket.base_year_other_sales)
            print_dict(VehicleFinal.mfr_base_year_share_data)

    @staticmethod
    def init_from_file(vehicle_onroad_calculations_file, verbose=False):
        """
        Init vehicle database from the base year vehicles file and set up the onroad / vehicle attribute calculations.
        Also initializes decomposition attributes.

        Args:
            vehicle_onroad_calculations_file (str): the name of the vehicle onroad calculations
                (vehicle attribute calculations) file
            verbose (bool): enable additional console and logfile output if True

        Returns:
            List of template/input errors, else empty list on success

        See Also:
            ``VehicleAttributeCalculations``, ``DecompositionAttributes``

        """
        _init_fail = []

        DecompositionAttributes.init()   # offcycle_credits must be initalized first

        VehicleFinal.init_vehicles_from_dataframe(omega_globals.options.vehicles_df, verbose=verbose)

        _init_fail += VehicleOnroadCalculations.init_vehicle_attribute_calculations_from_file(
            vehicle_onroad_calculations_file, clear_cache=True, verbose=verbose)

        return _init_fail


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        init_fail = []

        if not init_fail:
            pass

        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        dump_omega_db_to_csv(omega_globals.options.database_dump_folder)
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)

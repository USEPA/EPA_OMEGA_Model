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
from collections.abc import Iterable

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
        if type(vehicle) is not CompositeVehicle:
            prefix = 'veh_%s_' % vehicle.vehicle_id
        else:
            prefix = ''

        cn = '%s%s' % (prefix, attribute_name)

        if cn in cost_curve:
            if len(cost_curve) > 1:
                if isinstance(index_value, Iterable):
                    # true interpolation (multiple values passed as index):
                    return np.interp(index_value, cost_curve[index_column].values, cost_curve[cn].values)
                else:
                    # nearest result retrieval (get final result, single value):
                    return cost_curve[cn].loc[abs(index_value - cost_curve[index_column]).idxmin()]
            else:
                return cost_curve[cn].item()
        else:
            return vehicle.__getattribute__(attribute_name)  # None

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

            interp_index = float(np.interp(index_value,
                                  cost_curve_non_numeric_data[index_column],
                                  cost_curve_non_numeric_data.index))

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
            vehicle_id (str): the vehicle id
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
                              'cv_cloud_plots' in omega_globals.options.verbose_log_modules
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
        return max(self.cost_curve[cost_curve_interp_key].values)

    def get_min_cost_curve_index(self):
        """
        Get minimum value from the cost curve interpolation axis, see ``vehicles.cost_curve_interp_key``.

        Returns:
            A float, min value from the cost curve interpolation axis

        """
        return min(self.cost_curve[cost_curve_interp_key].values)

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

    if vehicle.base_year_vehicle_id == omega_globals.options.canary_byvid and \
            (not omega_globals.options.log_vehicle_cloud_years or
             vehicle.model_year in omega_globals.options.log_vehicle_cloud_years):
        vehicle.to_csv('%s_%s_%s%d_%d_vehicle.csv' %
                       (omega_globals.options.session_name, vehicle.compliance_id, vehicle.fueling_class,
                        vehicle.base_year_vehicle_id, vehicle.model_year))

        cc = cost_cloud.transpose().sort_index()
        cc.to_csv('%s_%s_%s%d_%d_cost_cloud.csv' %
                  (omega_globals.options.session_name, vehicle.compliance_id, vehicle.fueling_class,
                   vehicle.base_year_vehicle_id, vehicle.model_year))

        cc = vehicle.cost_curve.transpose().sort_index()
        cc.to_csv('%s_%s_%s%d_%d_cost_curve.csv' %
                  (omega_globals.options.session_name, vehicle.compliance_id, vehicle.fueling_class,
                   vehicle.base_year_vehicle_id, vehicle.model_year))

    return vehicle


def is_up_for_redesign(vehicle):
    """
        Return ``True`` if vehicle is available for production and/or redesign

    Args:
        vehicle (Vehicle, Vehicle): the vehicle object

    Returns:
        ``True`` if vehicle is at or past its redesign interval

    """
    redesign_interval_gain = \
        np.interp(vehicle.model_year,
                  omega_globals.options.redesign_interval_gain_years,
                  omega_globals.options.redesign_interval_gain)

    return bool(vehicle.model_year - int(vehicle.prior_redesign_year) >=
                int(vehicle.redesign_interval) * redesign_interval_gain)


def update_dynamic_attributes(vehicle):
    """
    Update vehicle dynamic attributes

    Args:
        vehicle(Vehicle): the source vehicle

    Returns:
        Nothing, updates vehicle dynamic attributes

    See Also ``transfer_vehicle_data()``

    """
    # assign user-definable reg class
    vehicle.reg_class_id = omega_globals.options.RegulatoryClasses.get_vehicle_reg_class(vehicle)

    # assign policy-based target for the current model year
    vehicle.set_target_co2e_grams_per_mile()


def transfer_vehicle_data(from_vehicle, model_year):
    """

    Transfer data from a prior year Vehicle to a new Vehicle object.  Updates reg class ID and target CO2e g/mi based
    on the model year and current policy.

    Args:
        from_vehicle (Vehicle): the source vehicle
        model_year (int): sets the ``to_vehicle`` model year

    Returns:
        Returns new ``Vehicle`` object for the current model year

    """
    to_vehicle = from_vehicle.copy()

    # set unique vehicle id
    to_vehicle.vehicle_id = Vehicle.get_next_vehicle_id(to_vehicle.manufacturer_id)

    # update model year
    to_vehicle.model_year = model_year

    # update dynamic attributes
    update_dynamic_attributes(to_vehicle)

    return to_vehicle


class Vehicle(OMEGABase):
    """
    **Implements "candidate" or "working" vehicles for use during the producer compliance search.**

    ``Vehicle`` objects are initialized from ``Vehicle`` objects and then appropriate attributes are transferred
    from ``Vehicle`` objects to ``Vehicle`` objects at the conclusion of the producer search and producer-consumer
    iteration.

    Each ``Vehicle`` object has a unique ``cost_curve`` (and potentially ``cost_cloud``) that tracks multiple aspects
    of vehicle technology application as a function of cert CO2e g/mi and the data contained in the simulated
    vehicles file.  The cost curve is calculated from the cost cloud at the start of each model year as a function
    of the active policy and the simulated vehicle data and costs.  For example, the value of off-cycle credits may
    vary from one model year to the next and technology costs may decrease over time.

    See Also:
        ``producer.vehicles.transfer_vehicle_data()``, ``Vehicle``, ``context.CostCloud``

    """
    _next_vehicle_ids = dict()

    _cache = dict()

    compliance_ids = set()  #: the set of compliance IDs (manufacturer IDs or 'consolidated_OEM')
    mfr_base_year_share_data = dict()  #: dict of base year market shares by compliance ID and various categories, used to project future vehicle sales based on the context

    # mandatory input file columns, the rest can be optional numeric columns:
    mandatory_input_template_columns = {'vehicle_name', 'manufacturer_id', 'model_year', 'reg_class_id',
                                        'context_size_class', 'electrification_class', 'cost_curve_class',
                                        'in_use_fuel_id', 'cert_fuel_id', 'sales', 'footprint_ft2', 'eng_rated_hp',
                                        'unibody_structure', 'drive_system', 'dual_rear_wheel', 'curbweight_lbs',
                                        'gvwr_lbs', 'gcwr_lbs', 'target_coef_a', 'target_coef_b', 'target_coef_c',
                                        'body_style', 'msrp_dollars', 'structure_material', 'prior_redesign_year',
                                        'redesign_interval', 'application_id', 'battery_gross_kwh',
                                        'tractive_motor_kw',
                                        'total_emachine_kw', }

    dynamic_columns = []  #: additional data columns such as footprint, passenger capacity, etc
    dynamic_attributes = []  #: list of dynamic attribute names, from dynamic_columns

    def __init__(self, manufacturer_id):
        """
        Create a new ``Vehicle`` object

        Args:
            manufacturer_id (str): manufacturer id, e.g. 'consolidated_OEM', 'Ford', etc

        """
        self._initial_registered_count = 0  #: vehicle initial registered count (i.e. sales)
        self.application_id = ''  #: application ID 'SLA' -> standard load application, 'HLA' -> high load application
        self.battery_kwh = 0  #: vehicle propulsion battery kWh
        self.battery_sizing_onroad_direct_kwh_per_mile = 0  #: battery-sizing onroad direct kWh/mi
        self.body_style = ''  #: vehicle body style, e.g. 'sedan'
        self.cert_co2e_Mg = 0  #: cert CO2e Mg, as determined by the active policy
        self.cert_engine_on_distance_frac = 0  #: xHEV cert engine-on distance frac
        self.cert_fuel_id = None  #: cert fuel ID
        self.cert_utility_factor = 0  #: PHEV cert utility factor (weighted average)
        self.compliance_id = None  #: compliance ID, may be the manufacturer ID or 'consolidated_OEM'
        self.context_size_class = None  #: context size class, used to project future vehicle sales based on the context
        self.cost_curve = None
        self.cost_curve_class = None  #: vehicle simulation (e.g. ALPHA) modeling result class
        self.cost_curve_non_numeric_data = None
        self.curbweight_lbs = 0  #: vehicle curbweight, pounds
        self.drive_system = ''  #: drive system, 'FWD', 'RWD', 'AWD'
        self.dual_rear_wheel = 0  #: dual_rear_wheel, 0=No, 1=Yes
        self.footprint_ft2 = 0   #: vehicle footprint, square feet
        self.fueling_class = None  #: fueling class, e.g. 'BEV', 'ICE'
        self.gcwr_lbs = 0  #: gross combined weight rating, lbs
        self.gvwr_lbs = 0  #: gross vehicle weight rating, lbs
        self.in_production = False  #: ``True`` if vehicle is in production
        self.in_use_fuel_id = None  #: in-use / onroad fuel ID
        self.lifetime_VMT = 0  #: lifetime VMT, used to calculate CO2e Mg
        self.manufacturer_id = manufacturer_id  #: vehicle manufacturer ID
        self.market_class_id = None  #: market class ID, as determined by the consumer subpackage
        self.market_class_cross_subsidy_multiplier = 0  #: vehicle market class cross subsidy multiplier
        self.model_year = 0  #: vehicle model year
        self.model_year_prevalence = 0  #: used to maintain market share relationships within context size classes during market projection
        self.modified_cross_subsidized_price_dollars = 0  #: vehicle modified cross subsidized price in dollars
        self.name = ''  #: vehicle name
        self.onroad_engine_on_distance_frac = 0  #: xHEV onroad engine-on disance frac
        self.onroad_charge_depleting_range_mi = 0  #: on-road charge-depleting range, miles
        self.onroad_direct_oncycle_co2e_grams_per_mile = 0  #: onroad direct oncycle CO2e g/mi
        self.onroad_direct_oncycle_kwh_per_mile = 0  #: onroad direct oncycle kWh/mi
        self.onroad_utility_factor = 0  #: PHEV onroad utility factor (weighted average)
        self.price_dollars = 0  #: vehicle price in dollars
        self.price_modification_dollars = 0  #: vehicle price modification (i.e. incentive value) in dollars
        self.prior_redesign_year = 0  #: prior redesign year
        self.projected_sales = 0  #: used to project context size class sales
        self.redesign_interval = 0  #: redesign interval, years
        self.reg_class_id = None  #: regulatory class assigned according the active policy
        self.structure_material = ''  #: vehicle body structure material, e.g. 'steel'
        self.target_co2e_Mg = 0  #: target CO2e Mg, as determined by the active policy
        self.target_co2e_grams_per_mile = 0  #: cert target CO2e g/mi, as determined by the active policy
        self.total_emachine_kw = 0  #: vehicle motor/generator total combined power, kW
        self.tractive_motor_kw = 0  #: on-cycle tractive motor power, kW
        self.unibody_structure = 1  #: unibody structure flag, e.g. 0,1
        self.vehicle_id = Vehicle.get_next_vehicle_id(manufacturer_id)  #: unique vehicle ID
        self.workfactor = 0  #: medium-duty workfactor

        # base year vehicle attributes, used to track changes from original vehicle
        self.base_year_battery_kwh = 0  #: vehicle propulsion battery kWh
        self.base_year_cert_direct_oncycle_co2e_grams_per_mile = 0  #: base year cert direct oncycle CO2e g/mi
        self.base_year_cert_direct_oncycle_kwh_per_mile = 0  #: base year cert direct oncycle kWh/mi
        self.base_year_cert_fuel_id = None  #: base year cert fuel ID
        self.base_year_cost_curve_class = ''  #: base year cost curve class
        self.base_year_curbweight_lbs = 0   #: base year vehicle curbweight, pounds
        self.base_year_curbweight_lbs_to_hp = 0  #: base year curbweight to power ratio (pounds per hp)
        self.base_year_eng_rated_hp = 0  #: base year engine rated horsepower
        self.base_year_footprint_ft2 = 0  #: base year vehicle footprint, square feet
        self.base_year_gcwr_lbs = 0  #: base year gross combined weight rating, lbs
        self.base_year_glider_non_structure_mass_lbs = 0  #: base year non-structure mass lbs (i.e. "content")
        self.base_year_glider_non_structure_cost_dollars = 0  #: base year glider non-structure cost dollars
        self.base_year_glider_structure_cost_dollars = 0   #: base year glider structure cost dollars
        self.base_year_gvwr_lbs = 0  #: base year gross vehicle weight rating, lbs
        self.base_year_market_share = 0  #: base year market share, used to maintain market share relationships within context size classes
        self.base_year_msrp_dollars = 0  #: base year Manufacturer Suggested Retail Price (dollars)
        self.base_year_onroad_charge_depleting_range_mi = 0  #: charge depleting range, miles
        self.base_year_onroad_direct_oncycle_co2e_grams_per_mile = 0  #: base year onroad direct oncycle CO2e g/mi
        self.base_year_onroad_direct_oncycle_kwh_per_mile = 0  #: base year onroad direct oncycle kWh/mi
        self.base_year_powertrain_type = ''  #: vehicle powertrain type, e.g. 'ICE', 'HEV', etc
        self.base_year_product = 0  #: ``1`` if vehicle was in production in base year, else ``0``
        self.base_year_reg_class_id = None  #: base year regulatory class, historical data
        self.base_year_target_coef_a = 0  #: roadload A coefficient, lbs
        self.base_year_target_coef_b = 0  #: roadload B coefficient, lbs/mph
        self.base_year_target_coef_c = 0  #: roadload C coefficient, lbs/mph^2
        self.base_year_total_emachine_kw = 0  #: vehicle motor/generator total combined power, kW
        self.base_year_tractive_motor_kw = 0  #: on-cycle tractive motor power, kW
        self.base_year_vehicle_id = 0  #: base year vehicle id from vehicles.csv
        self.base_year_workfactor = 0  #: base year medium-duty workfactor

        # additional attriutes are added dynamically and may vary based on user inputs (such as off-cycle credits)
        for ccv in DecompositionAttributes.values:
            self.__setattr__(ccv, 0)

        for dc in Vehicle.dynamic_columns:
            self.__setattr__(dc, 0)

    def __lt__(self, other):
        """
            "less-than" function for sorting vehicle lists by ``vehicle_id``

        Args:
            other (Vehicle): the comparison vehicle

        Returns:
            ``True`` if ``self.vehicle_id`` is less than ``other.vehicle_id``

        """
        self_mfr_id, self_id = self.vehicle_id.split('_')
        other_mfr_id, other_id = other.vehicle_id.split('_')
        if self_mfr_id == other_mfr_id:
            return int(self_id) < int(other_id)
        else:
            return self_mfr_id < other_mfr_id

    @staticmethod
    def reset_vehicle_ids():
        """
        Reset vehicle IDs.  Sets ``Vehicle.next_vehicle_id`` to an initial value.

        """
        Vehicle._next_vehicle_ids = dict()

    @staticmethod
    def _set_next_vehicle_id(manufacturer_id):
        """
        Increments ``Vehicle._next_vehicle_id`` for the given manufacturer

        Args:
            manufacturer_id (str): manufacturer id, e.g. 'consolidated_OEM', 'Ford', etc

        """
        Vehicle._next_vehicle_ids[manufacturer_id] = Vehicle._next_vehicle_ids[manufacturer_id] + 1

    @staticmethod
    def get_next_vehicle_id(manufacturer_id):
        """
        Gets vehicle id and increments ``Vehicle.next_vehicle_id``.

        Args:
            manufacturer_id (str): manufacturer id, e.g. 'consolidated_OEM', 'Ford', etc

        """
        if manufacturer_id not in Vehicle._next_vehicle_ids:
            Vehicle._next_vehicle_ids[manufacturer_id] = 0

        next_vehicle_id = '%s_%d' % (manufacturer_id, Vehicle._next_vehicle_ids[manufacturer_id])

        Vehicle._set_next_vehicle_id(manufacturer_id)

        return next_vehicle_id

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

        VehicleAnnualData.update_registered_count(self,
                                                  calendar_year=int(self.model_year),
                                                  registered_count=initial_registered_count)

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
                if 'electricity' in fuel:
                    price += omega_globals.options.ElectricityPrices.get_fuel_price(calendar_year) * fuel_share
                else:
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
                                                          drive_cycle_weight_year, self.fueling_class, cloud,
                                                          charge_depleting_only=True)[0]

        cloud['nominal_onroad_direct_co2e_grams_per_mile'] = 0  # needed for PHEV even though not needed for this calc

        # calc onroad_direct values
        VehicleOnroadCalculations.perform_onroad_calculations(self, cloud)

        return cloud

    def calc_cert_and_onroad_values(self, cloud):
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
            cloud['onroad_direct_oncycle_kwh_per_mile'], cloud['onroad_utility_factor'] = \
                DriveCycleWeights.calc_cert_direct_oncycle_kwh_per_mile(drive_cycle_weight_year,
                                                                        self.fueling_class, cloud)
        else:
            cloud['onroad_direct_oncycle_kwh_per_mile'] = 0
            cloud['onroad_utility_factor'] = 0

        if self.fueling_class == 'ICE':
            cloud['onroad_engine_on_distance_frac'] = \
                DriveCycleWeights.calc_engine_on_distance_frac(drive_cycle_weight_year, self.fueling_class, cloud)
        elif self.fueling_class == 'PHEV':
            cloud['onroad_engine_on_distance_frac'] = \
                DriveCycleWeights.calc_engine_on_distance_frac(drive_cycle_weight_year, self.fueling_class, cloud,
                                                               cloud['onroad_utility_factor'])
        else:
            cloud['onroad_engine_on_distance_frac'] = 0

        # calculate offcycle values before calculating onroad
        cloud = OffCycleCredits.calc_off_cycle_credits(drive_cycle_weight_year, self, cloud)

        cloud['nominal_onroad_direct_co2e_grams_per_mile'] = \
            cloud['onroad_direct_oncycle_co2e_grams_per_mile'] - \
            cloud['cert_direct_offcycle_co2e_grams_per_mile']

        cloud['nominal_onroad_direct_kwh_per_mile'] = \
            cloud['onroad_direct_oncycle_kwh_per_mile'] - \
            cloud['cert_direct_offcycle_kwh_per_mile']

        # calc onroad_direct values and save/restore battery sizing onroad direct kwh per mile, which gets overwritten
        if 'battery_sizing_onroad_direct_kwh_per_mile' in cloud:
            battery_sizing_onroad_direct_kwh_per_mile = cloud['battery_sizing_onroad_direct_kwh_per_mile']

        VehicleOnroadCalculations.perform_onroad_calculations(self, cloud)

        if 'battery_sizing_onroad_direct_kwh_per_mile' in cloud:
            cloud['battery_sizing_onroad_direct_kwh_per_mile'] = battery_sizing_onroad_direct_kwh_per_mile

        # calculate cert values ---------------------------------------------------------------------------------------
        if self.fueling_class != 'BEV':
            cloud['cert_direct_oncycle_co2e_grams_per_mile'] = \
                DriveCycleWeights.calc_cert_direct_oncycle_co2e_grams_per_mile(self.model_year, self.fueling_class,
                                                                               cloud)
        else:
            cloud['cert_direct_oncycle_co2e_grams_per_mile'] = 0

        if self.fueling_class != 'ICE':
            cloud['cert_direct_oncycle_kwh_per_mile'], cloud['cert_utility_factor'] = \
                DriveCycleWeights.calc_cert_direct_oncycle_kwh_per_mile(self.model_year, self.fueling_class, cloud)
        else:
            cloud['cert_direct_oncycle_kwh_per_mile'] = 0
            cloud['cert_utility_factor'] = 0

        if self.fueling_class == 'ICE':
            cloud['cert_engine_on_distance_frac'] = \
                DriveCycleWeights.calc_engine_on_distance_frac(self.model_year, self.fueling_class, cloud)
        elif self.fueling_class == 'PHEV':
            cloud['cert_engine_on_distance_frac'] = \
                DriveCycleWeights.calc_engine_on_distance_frac(self.model_year, self.fueling_class, cloud,
                                                               cloud['cert_utility_factor'])
        else:
            cloud['cert_engine_on_distance_frac'] = 0

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
        # if cost_cloud[cost_curve_interp_key].values.min() == cost_cloud[cost_curve_interp_key].values.max():
        if min(cost_cloud[cost_curve_interp_key].values) == max(cost_cloud[cost_curve_interp_key].values):
            # try to take lowest generalized cost point
            cost_curve = cost_cloud[cost_cloud['new_vehicle_mfr_generalized_cost_dollars'] == min(cost_cloud[
                'new_vehicle_mfr_generalized_cost_dollars'].values)]

            # if somehow more than one point, just take the first one...
            if len(cost_curve) > 1:
                cost_curve = cost_curve.iloc[[0]]

            # drop non-numeric columns so dtypes don't become "object"
            cost_curve = cost_curve.drop(columns=omega_globals.options.CostCloud.cloud_non_numeric_columns,
                                         errors='ignore')
        else:
            cost_curve = calc_frontier(cost_cloud, cost_curve_interp_key,
                                       'new_vehicle_mfr_generalized_cost_dollars', allow_upslope=allow_upslope)

        # CU

        # rename generic columns to vehicle-specific columns
        cost_curve = DecompositionAttributes.rename_decomposition_columns(self, cost_curve)

        # drop frontier factor
        cost_curve = cost_curve.drop(columns=['frontier_factor'], errors='ignore')

        self.cost_curve_non_numeric_data = \
            cost_cloud[omega_globals.options.CostCloud.cloud_non_numeric_data_columns].loc[cost_curve.index]

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

    @staticmethod
    def assign_vehicle_market_class_ID(vehicle):
        """
        Assign market class ID to the given vehicle and update manufacturer market class data.

        Args:
            vehicle (Vehicle): the vehicle to assign a market class ID to

        Returns:
            Nothing, updates vehicle market class ID and manufacturer market class data

        """
        from producer.manufacturers import Manufacturer
        vehicle.market_class_id = omega_globals.options.MarketClass.get_vehicle_market_class(vehicle)
        # vehicle.manufacturer.update_market_class_data(vehicle.compliance_id, vehicle.market_class_id)
        Manufacturer.update_market_class_data(vehicle.compliance_id, vehicle.market_class_id)

    @staticmethod
    def set_fueling_class(veh):
        """

        Args:
            veh:

        Returns:

        """
        if veh.base_year_powertrain_type in ['BEV', 'FCV']:
            if veh.base_year_powertrain_type == 'FCV':
                # RV FCV
                veh.in_use_fuel_id = "{'US electricity':1.0}"
                veh.cert_fuel_id = 'electricity'
                veh.base_year_powertrain_type = 'BEV'
            veh.fueling_class = 'BEV'
        elif veh.base_year_powertrain_type == 'PHEV':
            veh.fueling_class = 'PHEV'
        else:
            veh.fueling_class = 'ICE'

    @property
    def fueling_class_reg_class_id(self):
        """
        Create string combining fueling class id and regulatory class id.

        Returns:
            String combining fueling class id and regulatory class id, e.g. 'ICE.car'

        """
        return '%s.%s' % (self.fueling_class, self.reg_class_id)

    @staticmethod
    def create_vehicle_clone(vehicle):
        """
        Create vehicle clone.

        Args:
            vehicle (Vehicle): the vehicle to clone

        Returns:
            Cloned vehicle

        """
        alt_veh = vehicle.clone_vehicle(vehicle)  # create alternative powertrain clone of vehicle
        alt_veh.in_production = is_up_for_redesign(alt_veh)
        alt_veh.base_year_product = 0

        alt_veh.cert_direct_oncycle_co2e_grams_per_mile = 0
        alt_veh.cert_direct_co2e_grams_per_mile = 0
        alt_veh.cert_direct_kwh_per_mile = 0

        return alt_veh

    @staticmethod
    def clone_vehicle(vehicle):
        """
        Make a "clone" of a vehicle, used to create alternate powertrain versions of vehicles in the base year fleet

        Args:
            vehicle (Vehicle): the vehicle to clone

        Returns:
            A new ``Vehicle`` object with non-powertrain attributes copied from the given vehicle

        """
        inherit_properties = ['name', 'compliance_id',
                              'reg_class_id', 'context_size_class', 'unibody_structure', 'body_style',
                              'base_year_reg_class_id', 'base_year_market_share', 'base_year_vehicle_id',
                              'curbweight_lbs', 'base_year_glider_non_structure_mass_lbs', 'base_year_cert_fuel_id',
                              'base_year_glider_non_structure_cost_dollars', 'base_year_glider_structure_cost_dollars',
                              'footprint_ft2', 'base_year_footprint_ft2', 'base_year_curbweight_lbs', 'drive_system',
                              'dual_rear_wheel', 'base_year_curbweight_lbs_to_hp', 'base_year_msrp_dollars',
                              'base_year_target_coef_a', 'base_year_target_coef_b', 'base_year_target_coef_c',
                              'prior_redesign_year', 'redesign_interval', 'workfactor', 'gvwr_lbs', 'gcwr_lbs',
                              'base_year_workfactor', 'base_year_gvwr_lbs', 'base_year_gcwr_lbs', 'application_id',
                              'base_year_cost_curve_class',
                              ] \
                              + Vehicle.dynamic_attributes

        # model year and registered count are required to make a full-blown Vehicle object, compliance_id
        # is required for vehicle annual data init
        veh = Vehicle(vehicle.manufacturer_id)
        veh.model_year = vehicle.model_year
        veh.compliance_id = vehicle.compliance_id
        veh.initial_registered_count = 1

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

        Vehicle.compliance_ids = set()
        vehicles_list = []

        if verbose:
            omega_log.logwrite('\nInitializing vehicle data ...')

        from producer.manufacturers import Manufacturer
        from context.mass_scaling import MassScaling
        from context.body_styles import BodyStyles

        for i in df.index:
            veh = Vehicle(df.loc[i, 'manufacturer_id'])
            veh.name = df.loc[i, 'vehicle_name']
            # veh.vehicle_id = i
            # veh.manufacturer_id = df.loc[i, 'manufacturer_id']
            veh.model_year = df.loc[i, 'model_year']
            veh.context_size_class = df.loc[i, 'context_size_class']
            veh.cost_curve_class = df.loc[i, 'cost_curve_class']
            veh.in_use_fuel_id = df.loc[i, 'in_use_fuel_id']
            veh.cert_fuel_id = df.loc[i, 'cert_fuel_id']
            veh.unibody_structure = df.loc[i, 'unibody_structure']
            veh.drive_system = df.loc[i, 'drive_system']
            veh.application_id = df.loc[i, 'application_id']
            veh.dual_rear_wheel = df.loc[i, 'dual_rear_wheel']
            veh.curbweight_lbs = df.loc[i, 'curbweight_lbs']
            veh.footprint_ft2 = df.loc[i, 'footprint_ft2']
            veh.body_style = df.loc[i, 'body_style']
            veh.structure_material = df.loc[i, 'structure_material']
            veh.total_emachine_kw = df.loc[i, 'total_emachine_kw']
            veh.tractive_motor_kw = df.loc[i, 'tractive_motor_kw']
            veh.battery_kwh = df.loc[i, 'battery_gross_kwh']
            veh.onroad_charge_depleting_range_mi = df.loc[i, 'onroad_charge_depleting_range_mi']
            veh.prior_redesign_year = df.loc[i, 'prior_redesign_year']
            veh.redesign_interval = df.loc[i, 'redesign_interval']
            veh.in_production = True
            veh.workfactor = df.loc[i, 'workfactor']
            veh.reg_class_id = df.loc[i, 'reg_class_id']
            veh.gvwr_lbs = df.loc[i, 'gvwr_lbs']
            veh.gcwr_lbs = df.loc[i, 'gcwr_lbs']
            veh.base_year_cost_curve_class = df.loc[i, 'cost_curve_class']
            veh.base_year_eng_rated_hp = df.loc[i, 'eng_rated_hp']
            veh.base_year_target_coef_a = df.loc[i, 'target_coef_a']
            veh.base_year_target_coef_b = df.loc[i, 'target_coef_b']
            veh.base_year_target_coef_c = df.loc[i, 'target_coef_c']
            veh.base_year_reg_class_id = df.loc[i, 'reg_class_id']
            veh.base_year_footprint_ft2 = df.loc[i, 'footprint_ft2']
            veh.base_year_curbweight_lbs = df.loc[i, 'curbweight_lbs']
            veh.base_year_msrp_dollars = df.loc[i, 'msrp_dollars']
            veh.base_year_glider_non_structure_mass_lbs = df.loc[i, 'glider_non_structure_mass_lbs']
            veh.base_year_glider_non_structure_cost_dollars = df.loc[i, 'glider_non_structure_cost_dollars']
            veh.base_year_glider_structure_cost_dollars = df.loc[i, 'glider_structure_cost_dollars']
            veh.base_year_workfactor = df.loc[i, 'workfactor']
            veh.base_year_vehicle_id = i  # i.e. aggregated_vehicles.csv index number...
            veh.base_year_cert_fuel_id = df.loc[i, 'cert_fuel_id']
            veh.base_year_battery_kwh = df.loc[i, 'battery_kwh']
            veh.base_year_total_emachine_kw = df.loc[i, 'total_emachine_kw']
            veh.base_year_tractive_motor_kw = df.loc[i, 'tractive_motor_kw']
            veh.base_year_onroad_charge_depleting_range_mi = df.loc[i, 'onroad_charge_depleting_range_mi']
            veh.base_year_powertrain_type = df.loc[i, 'base_year_powertrain_type']
            veh.base_year_product = 1
            veh.base_year_gvwr_lbs = df.loc[i, 'gvwr_lbs']
            veh.base_year_gcwr_lbs = df.loc[i, 'gcwr_lbs']

            # electrification_class = df.loc[i, 'electrification_class']

            for attr, dc in zip(Vehicle.dynamic_attributes, Vehicle.dynamic_columns):
                veh.__setattr__(attr, df.loc[i, dc])

            if omega_globals.options.consolidate_manufacturers:
                veh.compliance_id = 'consolidated_OEM'
            else:
                veh.compliance_id = veh.manufacturer_id

            if not omega_globals.manufacturer_aggregation:
                veh.manufacturer_id = 'consolidated_OEM'

            Vehicle.compliance_ids.add(veh.compliance_id)

            # update initial registered count >after< setting compliance id, it's required for vehicle annual data
            veh.initial_registered_count = df.loc[i, 'sales']

            Vehicle.set_fueling_class(veh)

            veh.cert_direct_oncycle_co2e_grams_per_mile = 0
            veh.cert_direct_co2e_grams_per_mile = 0
            veh.cert_co2e_grams_per_mile = 0
            veh.cert_direct_kwh_per_mile = 0

            veh.onroad_direct_co2e_grams_per_mile = 0
            veh.onroad_direct_kwh_per_mile = 0

            if veh.base_year_powertrain_type in ['BEV', 'FCV']:
                rated_hp = veh.base_year_total_emachine_kw / 0.746
            else:
                rated_hp = veh.base_year_eng_rated_hp

            veh.base_year_curbweight_lbs_to_hp = veh.curbweight_lbs / rated_hp

            vehicle_shares_dict['total'] += veh.initial_registered_count

            if veh.context_size_class not in vehicle_shares_dict:
                vehicle_shares_dict[veh.context_size_class] = 0

            vehicle_shares_dict[veh.context_size_class] += veh.initial_registered_count

            vehicles_list.append(veh)

            # assign user-definable market class
            Vehicle.assign_vehicle_market_class_ID(veh)

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

            # clear tech flags:
            for tech_flag in omega_globals.options.CostCloud.tech_flags:
                veh.__setattr__(tech_flag, 0)

            # set tech flags based on cost curve class:
            for tech_flag, value in omega_globals.options.CostCloud.get_tech_flags(veh).items():
                veh.__setattr__(tech_flag, value)

            if verbose:
                print(veh)

            omega_globals.options.PowertrainCost.calc_cost(veh, update_tracker=True)  # update build dict

            omega_globals.finalized_vehicles.append(veh)

        # Update market share and create alternative vehicles (a BEV equivalent for every ICE vehicle, etc).
        # Alternative vehicles maintain fleet utility mix across model years and prevent all future vehicles
        # from becoming midsize car BEVs, for example, just because that's the dominant BEV in the base year
        # fleet
        for v in vehicles_list:
            v.base_year_market_share = v.initial_registered_count / vehicle_shares_dict['total']

            if v.fueling_class != 'BEV' or omega_globals.options.allow_ice_of_bev:
                if v.fueling_class == 'ICE':
                    # create BEV of ICE
                    alt_veh = Vehicle.create_vehicle_clone(v)
                    alt_veh.fueling_class = 'BEV'
                    alt_veh.base_year_powertrain_type = 'BEV'
                    alt_veh.name = 'BEV of ' + v.name
                    for tf in omega_globals.options.CostCloud.tech_flags:
                        alt_veh.__setattr__(tf, 0)
                    alt_veh.bev = 1
                    alt_veh.in_use_fuel_id = "{'US electricity':1.0}"
                    alt_veh.cert_fuel_id = 'electricity'
                    alt_veh.battery_kwh = 0  # pack sizes determined by range target
                    alt_veh.total_emachine_kw = 0  # motor size determined during cost curve generation
                    alt_veh.tractive_motor_kw = 0
                    alt_veh.base_year_tractive_motor_kw = 1
                    if v.drive_system == 'AWD':
                        # ratio of AWD total power to tractive power
                        alt_veh.base_year_total_emachine_kw = 1.75
                    else:
                        alt_veh.base_year_total_emachine_kw = 1
                    alt_veh.onroad_charge_depleting_range_mi = 0  # determined during cost curve generation
                    alt_veh.base_year_eng_rated_hp = 0
                    alt_veh.engine_cylinders = 0
                    alt_veh.engine_displacement_liters = 0
                    Vehicle.assign_vehicle_market_class_ID(alt_veh)
                    omega_globals.finalized_vehicles.append(alt_veh)

                    # create PHEV of ICE
                    alt_veh = Vehicle.create_vehicle_clone(v)
                    alt_veh.fueling_class = 'PHEV'
                    alt_veh.base_year_powertrain_type = 'PHEV'
                    alt_veh.name = 'PHEV of ' + v.name
                    for tf in omega_globals.options.CostCloud.tech_flags:
                        alt_veh.__setattr__(tf, 0)
                    alt_veh.phev = 1
                    alt_veh.in_use_fuel_id = "{'pump gasoline':1.0}"
                    alt_veh.cert_fuel_id = 'gasoline'
                    alt_veh.battery_kwh = 0  # pack sizes determined by range target
                    alt_veh.total_emachine_kw = 0  # motor size determined during cost curve generation
                    alt_veh.tractive_motor_kw = 0
                    alt_veh.onroad_charge_depleting_range_mi = 0  # determined during cost curve generation
                    alt_veh.base_year_onroad_charge_depleting_range_mi = alt_veh.onroad_charge_depleting_range_mi
                    alt_veh.base_year_eng_rated_hp = v.base_year_eng_rated_hp
                    alt_veh.engine_cylinders = v.engine_cylinders
                    alt_veh.engine_displacement_liters = v.engine_displacement_liters
                    Vehicle.assign_vehicle_market_class_ID(alt_veh)
                    omega_globals.finalized_vehicles.append(alt_veh)

                elif v.fueling_class == 'BEV':
                    # create ICE of BEV
                    alt_veh = Vehicle.create_vehicle_clone(v)
                    alt_veh.fueling_class = 'ICE'
                    alt_veh.base_year_powertrain_type = 'ICE'
                    alt_veh.name = 'ICE of ' + v.name
                    for tf in omega_globals.options.CostCloud.tech_flags:
                        alt_veh.__setattr__(tf, 0)
                    alt_veh.ice = 1
                    alt_veh.in_use_fuel_id = "{'pump gasoline':1.0}"
                    alt_veh.cert_fuel_id = 'gasoline'
                    alt_veh.base_year_eng_rated_hp = v.total_emachine_kw / 0.746
                    alt_veh.total_emachine_kw = 0
                    alt_veh.tractive_motor_kw = 0
                    alt_veh.onroad_charge_depleting_range_mi = 0
                    alt_veh.battery_kwh = 0
                    alt_veh.engine_cylinders = None
                    alt_veh.engine_displacement_liters = None
                    Vehicle.assign_vehicle_market_class_ID(alt_veh)
                    omega_globals.finalized_vehicles.append(alt_veh)

        for nrmc in NewVehicleMarket.context_size_class_info_by_nrmc:
            for csc in NewVehicleMarket.context_size_class_info_by_nrmc[nrmc]:
                NewVehicleMarket.context_size_class_info_by_nrmc[nrmc][csc]['share'] = \
                    NewVehicleMarket.context_size_class_info_by_nrmc[nrmc][csc]['total'] / vehicle_shares_dict[csc]

        # calculate manufacturer base year context size class shares
        Vehicle.compliance_ids = sorted(list(Vehicle.compliance_ids))

        Vehicle.mfr_base_year_share_data = dict()
        for compliance_id in Vehicle.compliance_ids:
            for size_class in NewVehicleMarket.base_year_context_size_class_sales:
                if compliance_id not in Vehicle.mfr_base_year_share_data:
                    Vehicle.mfr_base_year_share_data[compliance_id] = dict()

                key = compliance_id + '_' + size_class

                if key not in NewVehicleMarket.manufacturer_base_year_sales_data:
                    NewVehicleMarket.manufacturer_base_year_sales_data[key] = 0

                if verbose:
                    print('%s: %s / %s: %.2f' % (key,
                                                 NewVehicleMarket.manufacturer_base_year_sales_data[key],
                                                 NewVehicleMarket.base_year_context_size_class_sales[size_class],
                                                 NewVehicleMarket.manufacturer_base_year_sales_data[key] /
                                                 NewVehicleMarket.base_year_context_size_class_sales[size_class]))

                Vehicle.mfr_base_year_share_data[compliance_id][size_class] = \
                    NewVehicleMarket.manufacturer_base_year_sales_data[key] / \
                    NewVehicleMarket.base_year_context_size_class_sales[size_class]

        for compliance_id in Vehicle.compliance_ids:
            for other in NewVehicleMarket.base_year_other_sales:
                if compliance_id not in Vehicle.mfr_base_year_share_data:
                    Vehicle.mfr_base_year_share_data[compliance_id] = dict()

                key = compliance_id + '_' + other

                if key not in NewVehicleMarket.manufacturer_base_year_sales_data:
                    NewVehicleMarket.manufacturer_base_year_sales_data[key] = 0

                if verbose:
                    print('%s: %s / %s: %.2f' % (key,
                                                 NewVehicleMarket.manufacturer_base_year_sales_data[key],
                                                 NewVehicleMarket.base_year_other_sales[other],
                                                 NewVehicleMarket.manufacturer_base_year_sales_data[key] /
                                                 NewVehicleMarket.base_year_other_sales[other]))

                Vehicle.mfr_base_year_share_data[compliance_id][other] = \
                    NewVehicleMarket.manufacturer_base_year_sales_data[key] / \
                    NewVehicleMarket.base_year_other_sales[other]

        if verbose:
            print_dict(NewVehicleMarket.base_year_context_size_class_sales)
            print_dict(NewVehicleMarket.base_year_other_sales)
            print_dict(Vehicle.mfr_base_year_share_data)

    @staticmethod
    def init_from_file(vehicle_onroad_calculations_file, verbose=False):
        """
        Init vehicle data from the base year vehicles file and set up the onroad / vehicle attribute calculations.
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

        Vehicle._cache.clear()
        Vehicle.reset_vehicle_ids()
        Vehicle.init_vehicles_from_dataframe(omega_globals.options.vehicles_df, verbose=verbose)

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
            sys.exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)

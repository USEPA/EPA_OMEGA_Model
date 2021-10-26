"""

**Routines to load base-year vehicle data, data structures to represent vehicles during compliance modeling
(transient or ephemeral vehicles), finalized vehicles (manufacturer-produced compliance vehicles), and composite
vehicles (used to group vehicles by various characterstics during compliance modeling).**

Classes are also implemented to handle composition and decomposition of vehicle attributes as part of the composite
vehicle workflow.  Some vehicle attributes are known and fixed in advance, others are created at runtime (e.g. off-cycle
credit attributes which may vary by policy).

**INPUT FILE FORMAT (Vehicles File)**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents base-year (and eventually 'historic') vehicle attributes and sales.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,vehicles,input_template_version:,0.43

Sample Data Columns
    .. csv-table::
        :widths: auto

        vehicle_name,manufacturer_id,model_year,reg_class_id,epa_size_class,context_size_class,electrification_class,cost_curve_class,in_use_fuel_id,cert_fuel_id,sales,cert_direct_oncycle_co2e_grams_per_mile,cert_direct_oncycle_kwh_per_mile,footprint_ft2,eng_rated_hp,tot_road_load_hp,etw_lbs,length_in,width_in,height_in,ground_clearance_in,wheelbase_in,interior_volume_cuft,msrp_dollars,passenger_capacity,payload_capacity_lbs,towing_capacity_lbs,unibody_structure
        ICE Compact car,OEM_B,2019,car,Compact Cars,Compact,N,ice_LPW_LRL,{'pump gasoline':1.0},{'gasoline':1.0},839879,257.8936409,0,44.28736034,175.8843009,10.89410333,3401.137407,179.9070854,70.60266938,57.67845524,5.539186933,105.9507198,117.7314786,30396.74418,4.906687002,941.7256279,2175.140322,1
        BEV Large Utility truck,OEM_B,2019,truck,Standard SUV 4WD,Large Utility,EV,bev_MPW_HRL,{'US electricity':1.0},{'electricity':1.0},10416,0,0.36,51.8,,13.4,6000,193,76.3,65.5,6.9,115.1,,78300,5,,4000,1

Data Column Name and Description

    **REQUIRED COLUMNS**

    :vehicle_name:
        The vehicle name or description, e.g. 'ICE Small Utility truck', 'BEV Subcompact car', etc

    :manufacturer_id:
        Manufacturer name, must be consistent with the data loaded by ``class manufacturers.Manufacturer``

    :model_year:
        The model year of the vehicle data, e.g. 2020

    :reg_class_id:
        Vehicle regulatory class at the time of certification, e.g. 'car','truck'.  Reg class definitions may differ
        across years within the simulation based on policy changes. ``reg_class_id`` can be considered a 'historical'
        or 'legacy' reg class.

    :epa_size_class:
        The EPA size class of the vehicle

    :context_size_class:
        The context size class of the vehicle, for future sales mix projections.  Must be consistent with the context
        input file loaded by ``class context_new_vehicle_market.ContextNewVehicleMarket``

    :electrification_class:
        The electrification class of the vehicle, such as 'EV', 'HEV', (or 'N' for none - final format TBD)

    :cost_curve_class:
        The name of the cost curve class of the vehicle, used to determine which technology options and associated costs
        are available to be applied to this vehicle.  Must be consistent with the data loaded by
        ``class cost_clouds.CostCloud``

    :in_use_fuel_id:
        In-use fuel id, for use with context fuel prices, must be consistent with the context data read by
        ``class context_fuel_prices.ContextFuelPrices``

    :cert_fuel_id:
        Certification fuel id, for determining certification upstream CO2e grams/mile, must be in the table loaded by
        ``class fuels.Fuel``

    :sales:
        Number of vehicles sold in the ``model_year``

    **OPTIONAL COLUMNS**
        These columns become object attributes that may be used to determine vehicle regulatory class
        (e.g. 'car','truck') based on the simulated policy, or they may be used for other purposes.

    :cert_co2e_grams_per_mile:
        Vehicle certification emissions CO2e grams/mile

    :cert_direct_kwh_per_mile:
        Vehicle certification electricity consumption kWh/mile

    :eng_rated_hp:
        Vehicle engine rated power (horsepower)

    :tot_road_load_hp:
        Vehicle roadload power (horsepower) at a vehicle speed of 50 miles per hour

    :footprint_ft2:
        Vehicle footprint based on vehicle wheelbase and track (square feet)

    :etw_lbs:
        Vehicle equivalent test weight (ETW) (pounds)

    :length_in:
        Vehicle overall length (inches)

    :width_in:
        Vehicle overall width (inches)

    :height_in:
        Vehicle overall height (inches)

    :ground_clearance_in:
        Vehicle ground clearance (inches)

    :wheelbase_in:
        Vehicle wheelbase (inches)

    :interior_volume_cuft:
        Vehicle interior volume (cubic feet)

    :msrp_dollars:
        Vehicle manufacturer suggested retail price (MSRP)

    :passenger_capacity:
        Vehicle passenger capacity (number of occupants)

    :payload_capacity_lbs:
        Vehicle payload capacity (pounds)

    :towing_capacity_lbs:
        Vehicle towing capacity (pounds)

    :unibody_structure:
        Vehicle body structure; 1 = unibody, 0 = body-on-frame

----

**INPUT FILE FORMAT (Onroad Vehicle Calculations File)**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.  The data header uses a dynamic column notation, as detailed below.

The data represents the "gap" between on-cycle and onroad GHG performance.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,vehicle_attribute_calculations,input_template_version:,0.2

The data header consists of a ``start_year`` column followed by zero or more calculation columns.

Dynamic Data Header
    .. csv-table::
        :widths: auto

        start_year, ``{vehicle_select_attribute}:{vehicle_select_attribute_value}:{operator}:{vehicle_source_attribute}->{vehicle_destination_attribute}``, ...

Sample Data Columns
    .. csv-table::
        :widths: auto

        start_year,fueling_class:BEV:/:cert_direct_kwh_per_mile->onroad_direct_kwh_per_mile,fueling_class:ICE:/:cert_direct_co2e_grams_per_mile->onroad_direct_co2e_grams_per_mile
        2020,0.7,0.8

Data Column Name and Description

:start_year:
    Start year of price modification, modification applies until the next available start year

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

from omega_model import *


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
        from policy.offcycle_credits import OffCycleCredits
        from policy.drive_cycles import DriveCycles
        from context.cost_clouds import CostCloud

        # set base values
        base_values = ['cert_co2e_grams_per_mile',
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
        simulation_drive_cycles = list(set.intersection(set(CostCloud.cost_cloud_data_columns),
                                                        set(DriveCycles.drive_cycle_names)))

        cls.offcycle_values = list(set.intersection(set(CostCloud.cost_cloud_data_columns),
                                                    set(OffCycleCredits.offcycle_credit_names)))

        cls.other_values = list(set(CostCloud.cost_cloud_data_columns).
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
            vehicle (Vehicle or CompositeVehicle):
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

        if len(cost_curve) > 1:
            interp1d = scipy.interpolate.interp1d(cost_curve[index_column],
                                                  cost_curve['%s%s' % (prefix, attribute_name)],
                                                  fill_value=(cost_curve['%s%s' % (prefix, attribute_name)].min(),
                                                          cost_curve['%s%s' % (prefix, attribute_name)].max()),
                                                  bounds_error=False)
            return interp1d(index_value)
        else:
            return cost_curve['%s%s' % (prefix, attribute_name)].item()

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


class VehicleAttributeCalculations(OMEGABase):
    """
    **Performs vehicle attribute calculations, as outlined in the input file.**

    Currently used to calculate the on-road "gap" in GHG performance.  See the input file format above for more
    information.

    """
    cache = dict()

    @staticmethod
    def init_vehicle_attribute_calculations_from_file(filename, clear_cache=False, verbose=False):
        """

        Initialize class data from input file.

        Args:
            filename (str): name of input file
            clear_cache (bool): if ``True`` then clear ``VehicleAttributeCalculations.cache``
            verbose (bool): enable additional console and logfile output if ``True``

        Returns:
            List of template/input errors, else empty list on success

        """
        import numpy as np

        if clear_cache:
            VehicleAttributeCalculations.cache = dict()

        if verbose:
            omega_log.logwrite('\nInitializing from %s...' % filename)

        input_template_name = 'vehicle_attribute_calculations'
        input_template_version = 0.2
        input_template_columns = {'start_year'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version, verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                df = df.set_index('start_year')
                df = df.drop([c for c in df.columns if 'Unnamed' in c], axis='columns')

                for idx, r in df.iterrows():
                    if idx not in VehicleAttributeCalculations.cache:
                        VehicleAttributeCalculations.cache[idx] = dict()

                    VehicleAttributeCalculations.cache[idx] = r.to_dict()

                VehicleAttributeCalculations.cache['start_year'] = \
                    np.array(list(VehicleAttributeCalculations.cache.keys()))

        return template_errors

    @staticmethod
    def perform_attribute_calculations(vehicle, cost_cloud=None):
        """
        Perform attribute calculations as specified by the input file.  Calculations may be applied to the vehicle
        directly, or to values in the cost_cloud if provided.

        Args:
            vehicle (Vehicle): the vehicle to perform calculations on
            cost_cloud (DataFrame): optional dataframe to perform calculations on

        Returns:
            Nothing, If ``cost_cloud`` is not provided then attribute calculations are performed on the vehicle object
            else they are performed on the cost cloud data

        """
        start_years = VehicleAttributeCalculations.cache['start_year']
        if len(start_years[start_years <= vehicle.model_year]) > 0:
            cache_key = max(start_years[start_years <= vehicle.model_year])

            if cache_key in VehicleAttributeCalculations.cache:
                calcs = VehicleAttributeCalculations.cache[cache_key]
                for calc, value in calcs.items():
                    select_attribute, select_value, operator, action = calc.split(':')
                    if vehicle.__getattribute__(select_attribute) == select_value:
                        attribute_source, attribute_target = action.split('->')
                        # print('vehicle.%s = vehicle.%s %s %s' % (attribute_target, attribute_source, operator, value))
                        if cost_cloud is not None:
                            cost_cloud[attribute_target] = \
                                eval("cost_cloud['%s'] %s %s" % (attribute_source, operator, value))
                        else:
                            vehicle.__setattr__(attribute_target,
                                                eval('vehicle.%s %s %s' % (attribute_source, operator, value)))
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
    def __init__(self, vehicle_list, vehicle_id, verbose=False, calc_composite_cost_curve=True,
                 weight_by='initial_registered_count'):
        """
        Create composite vehicle from list of Vehicle objects.

        Args:
            vehicle_list ([Vehicle, ...]: list of one or more ``Vehicle`` objects
            verbose (bool): enable additional console and logfile output if ``True``
            calc_composite_cost_curve (bool): if ``True`` then calculate the composite cost curve
            weight_by (str): name of the ``Vehicle`` attribute to weight by, e.g. 'initial_registered_count' or
            'base_year_market_share'

        """
        from common.omega_functions import weighted_value

        self.vehicle_list = vehicle_list  # copy.deepcopy(vehicle_list)
        self.name = 'composite vehicle (%s.%s)' % (self.vehicle_list[0].market_class_id, self.vehicle_list[0].reg_class_id)

        self.vehicle_id = vehicle_id
        self.weight_by = weight_by

        self.model_year = self.vehicle_list[0].model_year  # calendar_year?
        self.reg_class_id = self.vehicle_list[0].reg_class_id
        self.fueling_class = self.vehicle_list[0].fueling_class
        self.market_class_id = self.vehicle_list[0].market_class_id

        self.weighted_values = ['cert_co2e_grams_per_mile',
                                'cert_direct_co2e_grams_per_mile',
                                'cert_direct_kwh_per_mile',
                                'onroad_direct_co2e_grams_per_mile',
                                'onroad_direct_kwh_per_mile',
                                'new_vehicle_mfr_cost_dollars',
                                'new_vehicle_mfr_generalized_cost_dollars',
                                ]

        # calc weighted values
        for wv in self.weighted_values:
            self.__setattr__(wv, weighted_value(self.vehicle_list, weight_by, wv))

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
            plot_cost_curve = ((omega_globals.options.log_producer_iteration_years == 'all') or
                              (self.model_year in omega_globals.options.log_producer_iteration_years)) and \
                              any([v.name in omega_globals.options.log_vehicles for v in self.vehicle_list])
            self.cost_curve = self.calc_composite_cost_curve(plot=plot_cost_curve)

        self.tech_option_iteration_num = 0

        self.normalized_target_co2e_Mg = weighted_value(self.vehicle_list, self.weight_by,
                                                        'normalized_target_co2e_Mg')

        self.normalized_cert_co2e_Mg = omega_globals.options.VehicleTargets.calc_cert_co2e_Mg(self, 1, 1)

    def retail_fuel_price_dollars_per_unit(self, calendar_year=None):
        """
        Calculate the weighted retail fuel price in dollars per unit from the Vehicles in the ``vehicle_list``.

        Args:
            calendar_year (int): the year to perform calculations in

        Returns:
            Weighted Vehicle ``retail_fuel_price_dollars_per_unit``

        """
        from common.omega_functions import weighted_value

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
        plot_cost_curve = ((omega_globals.options.log_producer_iteration_years == 'all') or
                           (self.model_year in omega_globals.options.log_producer_iteration_years)) and \
                          any([v.name in omega_globals.options.log_vehicles for v in self.vehicle_list])

        if plot_cost_curve:
            from common.omega_plot import figure, label_xyt

            fig, ax1 = figure()
            label_xyt(ax1, 'CO2e [g/mi]', 'Generalized Cost [$]', '%s' % self.name)

        for v in self.vehicle_list:
            if 'cost_curve' in self.__dict__:
                for ccv in DecompositionAttributes.values:
                    v.__setattr__(ccv, DecompositionAttributes.interp1d(v, self.cost_curve, 'cert_co2e_grams_per_mile',
                                                                        self.cert_co2e_grams_per_mile, ccv))
            v.initial_registered_count = self.initial_registered_count * v.composite_vehicle_share_frac
            v.set_target_co2e_Mg()  # varies by model year and initial_registered_count
            v.set_cert_co2e_Mg()  # varies by model year and initial_registered_count

            if plot_cost_curve:
                if v.name in omega_globals.options.log_vehicles:
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
        if plot_cost_curve:
            ax1.relim()
            ax1.autoscale()

            ax1.plot(self.cost_curve['cert_co2e_grams_per_mile'],
                     self.cost_curve['new_vehicle_mfr_generalized_cost_dollars'], '-', linewidth=3,
                     label='Composite Vehicle')

            ax1.plot(self.cert_co2e_grams_per_mile, self.new_vehicle_mfr_generalized_cost_dollars, '*', markersize=25,
                     color=ax1.get_lines()[-1].get_color())

            ax1.legend(fontsize='medium', bbox_to_anchor=(1.04, 0), loc="lower left",
                       borderaxespad=0)

            figname = '%s%s_%s_cost_curve_decomposition.png' % (omega_globals.options.output_folder, self.model_year, ax1.get_title())
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
        from common.omega_functions import cartesian_prod, calc_frontier
        from common.omega_plot import figure, label_xyt

        if plot:
            fig, ax1 = figure()
            label_xyt(ax1, 'CO2e [g/mi]', 'Generalized Cost [$]', '%s' % self.name)

        composite_frontier_df = pd.DataFrame()
        composite_frontier_df['market_share_frac'] = [0]

        # calc weighted values
        for wv in self.weighted_values:
            composite_frontier_df[wv] = [0]

        for v in self.vehicle_list:
            vehicle_frontier = v.cost_curve
            vehicle_frontier['veh_%s_market_share' % v.vehicle_id] = v.composite_vehicle_share_frac

            composite_frontier_df = cartesian_prod(composite_frontier_df, vehicle_frontier)

            prior_market_share_frac = composite_frontier_df['market_share_frac']
            veh_market_share_frac = composite_frontier_df['veh_%s_market_share' % v.vehicle_id]

            for wv in self.weighted_values:
                composite_frontier_df[wv] = \
                    (composite_frontier_df[wv] * prior_market_share_frac +
                     composite_frontier_df['veh_%s_%s' % (v.vehicle_id, wv)] * veh_market_share_frac) / \
                    (prior_market_share_frac + veh_market_share_frac)

            # update running total market share
            composite_frontier_df['market_share_frac'] = prior_market_share_frac + veh_market_share_frac

            drop_columns = [c for c in composite_frontier_df.columns if c.endswith('_y') or c.endswith('_x') or
                            c.endswith('_market_share')] + ['_']

            composite_frontier_df = composite_frontier_df.drop(drop_columns, axis=1, errors='ignore')

            # calculate new sales-weighted frontier
            composite_frontier_df = calc_frontier(composite_frontier_df, 'cert_co2e_grams_per_mile',
                                                  'new_vehicle_mfr_generalized_cost_dollars',
                                                  allow_upslope=True)

            composite_frontier_df = composite_frontier_df.drop(['frontier_factor'], axis=1, errors='ignore')

            if plot:
                if v.name in omega_globals.options.log_vehicles:
                    ax1.plot(vehicle_frontier['veh_%s_cert_co2e_grams_per_mile' % v.vehicle_id],
                             vehicle_frontier['veh_%s_new_vehicle_mfr_generalized_cost_dollars' % v.vehicle_id], 's-',
                             color='black',
                             label='veh %s %s' % (v.vehicle_id, v.name))
                else:
                    ax1.plot(vehicle_frontier['veh_%s_cert_co2e_grams_per_mile' % v.vehicle_id],
                             vehicle_frontier['veh_%s_new_vehicle_mfr_generalized_cost_dollars' % v.vehicle_id], '.--',
                             linewidth=1, label='veh %s %s' % (v.vehicle_id, v.name))

        if plot:
            ax1.plot(composite_frontier_df['cert_co2e_grams_per_mile'],
                     composite_frontier_df['new_vehicle_mfr_generalized_cost_dollars'], '-', linewidth=3,
                     label='Composite Vehicle')

            ax1.legend(fontsize='medium', bbox_to_anchor=(1.04, 0), loc="lower left", borderaxespad=0)

            figname = '%s%s_%s_cost_curve_composition.png' % (omega_globals.options.output_folder, self.model_year, ax1.get_title())
            figname = figname.replace('(', '_').replace(')', '_').replace('.', '_').replace(' ', '_')\
                .replace('__', '_').replace('_png', '.png')
            fig.savefig(figname, bbox_inches='tight')

        return composite_frontier_df

    def get_new_vehicle_mfr_cost_from_cost_curve(self, query_co2e_gpmi):
        """
        Get new vehicle manufacturer cost from the composite cost curve for the provided cert CO2e g/mi value(s).

        Args:
            query_co2e_gpmi (numeric list or Array): the cert CO2e g/mi values at which to query the cost curve

        Returns:
            A float or numeric Array of new vehicle manufacturer costs

        """
        if len(self.cost_curve) > 1:
            cost_dollars = scipy.interpolate.interp1d(self.cost_curve['cert_co2e_grams_per_mile'],
                                                      self.cost_curve['new_vehicle_mfr_cost_dollars'],
                                                      fill_value=(self.cost_curve['new_vehicle_mfr_cost_dollars'].min(),
                                                                  self.cost_curve['new_vehicle_mfr_cost_dollars'].max()),
                                                      bounds_error=False)
            return cost_dollars(query_co2e_gpmi)
        else:
            return self.cost_curve['new_vehicle_mfr_cost_dollars'].item()

    def get_cert_direct_kwh_pmi_from_cost_curve(self, query_co2e_gpmi):
        """
        Get kWh/mi from the composite cost curve for the provided cert CO2e g/mi value(s).

        Args:
            query_co2e_gpmi (numeric list or Array): the cert CO2e g/mi value(s) at which to query the cost curve

        Returns:
            A float or numeric Array of kWh/mi values

        """
        return DecompositionAttributes.interp1d(self, self.cost_curve, 'cert_co2e_grams_per_mile', query_co2e_gpmi,
                                                'cert_direct_kwh_per_mile')

    def get_new_vehicle_mfr_generalized_cost_from_cost_curve(self, query_co2e_gpmi):
        """
        Get new vehicle manufacturer generalzied cost from the composite cost curve for the provided cert CO2e g/mi
        value(s).

        Args:
            query_co2e_gpmi (numeric list or Array): the cert CO2e value(s) at which to query the cost curve

        Returns:
            A float or numeric Array of new vehicle manufacturer generalized costs

        """
        return DecompositionAttributes.interp1d(self, self.cost_curve, 'cert_co2e_grams_per_mile', query_co2e_gpmi,
                                                'new_vehicle_mfr_generalized_cost_dollars')

    def get_max_cert_co2e_gpmi(self):
        """
        Get maximum cert CO2e g/mi from the cost curve.

        Returns:
            A float, max cert CO2e g/mi from the cost curve

        """
        return self.cost_curve['cert_co2e_grams_per_mile'].max()

    def get_min_cert_co2e_gpmi(self):
        """
        Get minimum cert CO2e g/mi from the cost curve.

        Returns:
            A float, min cert CO2e g/mi from the cost curve

        """
        return self.cost_curve['cert_co2e_grams_per_mile'].min()

    def get_weighted_attribute(self, attribute_name):
        from common.omega_functions import weighted_value
        return weighted_value(self.vehicle_list, self.weight_by, attribute_name)


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
    base_properties = {'name', 'manufacturer_id', 'compliance_id', 'model_year', 'fueling_class',
                       'cost_curve_class', 'base_year_reg_class_id', 'reg_class_id', 'in_use_fuel_id',
                       'cert_fuel_id', 'market_class_id', 'epa_size_class', 'lifetime_VMT',
                       'context_size_class', 'base_year_market_share', 'electrification_class'}

    # transfer base properties
    for attr in base_properties:
        to_vehicle.__setattr__(attr, from_vehicle.__getattribute__(attr))

    if model_year:
        to_vehicle.model_year = model_year

    # transfer dynamic attributes
    for attr in VehicleFinal.dynamic_attributes:
        to_vehicle.__setattr__(attr, from_vehicle.__getattribute__(attr))

    to_vehicle.set_target_co2e_grams_per_mile()  # varies by model year

    if type(from_vehicle) == VehicleFinal:
        # finish transfer from VehicleFinal to Vehicle
        from context.cost_clouds import CostCloud

        if omega_globals.options.flat_context:
            to_vehicle.cost_cloud = CostCloud.get_cloud(omega_globals.options.flat_context_year, to_vehicle.cost_curve_class)
        else:
            to_vehicle.cost_cloud = CostCloud.get_cloud(to_vehicle.model_year, to_vehicle.cost_curve_class)
        to_vehicle.cost_curve = to_vehicle.create_frontier_df()  # create frontier, inc. generalized cost and policy effects

        to_vehicle.normalized_target_co2e_Mg = \
            omega_globals.options.VehicleTargets.calc_target_co2e_Mg(to_vehicle, sales_variants=1)

        VehicleAttributeCalculations.perform_attribute_calculations(to_vehicle)
    else:  # type(from_vehicle == Vehicle)
        # finish transfer from Vehicle to VehicleFinal
        to_vehicle.initial_registered_count = from_vehicle.initial_registered_count

        # set dynamic attributes
        for attr in DecompositionAttributes.values:
            to_vehicle.__setattr__(attr, from_vehicle.__getattribute__(attr))

        to_vehicle.target_co2e_Mg = from_vehicle.target_co2e_Mg
        to_vehicle.cert_co2e_Mg = from_vehicle.cert_co2e_Mg


class Vehicle(OMEGABase):
    """
    **Implements "candidate" or "working" vehicles for use during the producer compliance search.**

    ``Vehicle`` objects are initialized from ``VehicleFinal`` objects and then appropriate attributes are transferred from
    ``Vehicle`` objects to ``VehicleFinal`` objects at the conclusion of the producer search and producer-consumer
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
        self.base_year_reg_class_id = None
        self.reg_class_id = None
        self.epa_size_class = None
        self.context_size_class = None
        self.base_year_market_share = 0
        self.electrification_class = None
        self.target_co2e_grams_per_mile = 0
        self.lifetime_VMT = 0
        self.cert_co2e_Mg = 0
        self.target_co2e_Mg = 0
        self.normalized_target_co2e_Mg = 0
        self.in_use_fuel_id = None
        self.cert_fuel_id = None
        self.market_class_id = None
        self.initial_registered_count = 0
        self.cost_cloud = None
        self.cost_curve = None

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
        from context.fuel_prices import FuelPrice
        if calendar_year is None:
            calendar_year = self.model_year

        price = 0
        fuel_dict = eval(self.in_use_fuel_id, {'__builtins__': None}, {})
        for fuel, fuel_share in fuel_dict.items():
            price += FuelPrice.get_fuel_prices(calendar_year, 'retail_dollars_per_unit', fuel) * fuel_share

        return price

    def onroad_co2e_emissions_grams_per_unit(self):
        """
        Calculate the onroad (in-use) CO2e emission in grams per unit of onroad fuel, including refuel efficiency.
        Used to calculate producer generalized cost.

        Returns:
            The onroad CO2e emission in grams per unit of onroad fuel, including refuel efficiency.

        """
        from context.onroad_fuels import OnroadFuel

        co2_emissions_grams_per_unit = 0
        fuel_dict = eval(self.in_use_fuel_id, {'__builtins__': None}, {})
        for fuel, fuel_share in fuel_dict.items():
            co2_emissions_grams_per_unit += \
                (OnroadFuel.get_fuel_attribute(self.model_year, fuel, 'direct_co2e_grams_per_unit') /
                 OnroadFuel.get_fuel_attribute(self.model_year, fuel, 'refuel_efficiency') * fuel_share)

        return co2_emissions_grams_per_unit

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

    def create_frontier_df(self):
        """
        Create a frontier ("cost curve") from a vehicle's cloud of simulated vehicle points ("cost cloud") based
        on the current policy and vehicle attributes.  The cost values are a function of the producer generalized cost
        and the CO2e values are a function of the simulated vehicle data and the policy.

        Policy factors that modify the cost cloud and may modify the frontier from year to year include off cycle
        credit values, drive cycle weightings, upstream values, etc.  This method is also where costs could be
        updated dynamically before calculating the frontier (for example, cost reductions due to learning may
        aready be present in the cost cloud, or could be implemented here instead).

        Additionally, each point in the frontier contains the values as determined by ``DecompositionAttributes``.

        Returns:
            The vehicle frontier / cost curve as a DataFrame.

        """
        from common.omega_functions import calc_frontier
        from policy.upstream_methods import UpstreamMethods
        from policy.drive_cycle_weights import DriveCycleWeights
        from policy.offcycle_credits import OffCycleCredits

        self.cost_cloud['cert_direct_oncycle_co2e_grams_per_mile'] = \
            DriveCycleWeights.calc_cert_direct_oncycle_co2e_grams_per_mile(self.model_year, self.fueling_class, self.cost_cloud)

        self.cost_cloud['cert_direct_oncycle_kwh_per_mile'] = \
            DriveCycleWeights.calc_cert_direct_oncycle_kwh_per_mile(self.model_year, self.fueling_class, self.cost_cloud)

        # initialize onroad values
        self.cost_cloud['onroad_direct_co2e_grams_per_mile'] = 0
        self.cost_cloud['onroad_direct_kwh_per_mile'] = 0

        # drop extraneous columns
        self.cost_cloud = self.cost_cloud.drop(columns=['cost_curve_class', 'model_year'])

        # TODO: update dynamic costs, if any

        # calculate off cycle credits before calculating upstream and onroad
        self.cost_cloud = OffCycleCredits.calc_off_cycle_credits(self)

        self.cost_cloud['cert_direct_co2e_grams_per_mile'] = \
            self.cost_cloud['cert_direct_oncycle_co2e_grams_per_mile'] - \
            self.cost_cloud['cert_direct_offcycle_co2e_grams_per_mile']

        self.cost_cloud['cert_direct_kwh_per_mile'] = \
            self.cost_cloud['cert_direct_oncycle_kwh_per_mile'] -\
            self.cost_cloud['cert_direct_offcycle_kwh_per_mile']

        # calc onroad gap, etc...
        VehicleAttributeCalculations.perform_attribute_calculations(self, self.cost_cloud)

        # add upstream calcs
        upstream_method = UpstreamMethods.get_upstream_method(self.model_year)

        self.cost_cloud['cert_indirect_co2e_grams_per_mile'] = \
            upstream_method(self, self.cost_cloud['cert_direct_co2e_grams_per_mile'],
                            self.cost_cloud['cert_direct_kwh_per_mile'])

        self.cost_cloud['cert_co2e_grams_per_mile'] = \
            self.cost_cloud['cert_direct_co2e_grams_per_mile'] + \
            self.cost_cloud['cert_indirect_co2e_grams_per_mile'] - \
            self.cost_cloud['cert_indirect_offcycle_co2e_grams_per_mile']

        # calculate producer generalized cost
        self.cost_cloud = omega_globals.options.ProducerGeneralizedCost.\
            calc_generalized_cost(self, 'onroad_direct_co2e_grams_per_mile',
                                  'onroad_direct_kwh_per_mile', 'new_vehicle_mfr_cost_dollars')

        # cull cost_cloud points here, based on producer constraints or whatever #

        # calculate frontier from updated cloud
        allow_upslope = True
        cost_curve = calc_frontier(self.cost_cloud, 'cert_co2e_grams_per_mile',
                                   'new_vehicle_mfr_cost_dollars', allow_upslope=allow_upslope)

        # CostCloud.plot_frontier(self.cost_cloud, self.cost_curve_class + '\nallow_upslope=%s, frontier_affinity_factor=%s' % (allow_upslope, o2.options.cost_curve_frontier_affinity_factor), cost_curve, 'cert_co2e_grams_per_mile', 'new_vehicle_mfr_cost_dollars')

        # rename generic columns to vehicle-specific columns
        cost_curve = DecompositionAttributes.rename_decomposition_columns(self, cost_curve)

        # drop frontier factor
        cost_curve = cost_curve.drop(columns=['frontier_factor'])

        if ((omega_globals.options.log_producer_iteration_years == 'all') or
            (self.model_year in omega_globals.options.log_producer_iteration_years)) and \
                (self.name in omega_globals.options.log_vehicles):

            logfile_name = '%s%d_%s_cost_cloud.csv' % (omega_globals.options.output_folder, self.model_year, self.name)
            self.cost_cloud['frontier'] = False
            self.cost_cloud.loc[cost_curve.index, 'frontier'] = True
            self.cost_cloud.to_csv(logfile_name)
            logfile_name = '%s%d_%s_cost_curve.csv' % (omega_globals.options.output_folder, self.model_year, self.name)
            cost_curve.to_csv(logfile_name)

            from common.omega_plot import figure, label_xyt

            fig, ax1 = figure()
            label_xyt(ax1, 'CO2e [g/mi]', 'Cost [$]', 'veh %s %s' % (self.vehicle_id, self.name))

            ax1.plot(self.cost_cloud['cert_co2e_grams_per_mile'],
                     self.cost_cloud['new_vehicle_mfr_cost_dollars'], '.',
                     label='Production Cost')

            ax1.plot(self.cost_cloud['cert_co2e_grams_per_mile'],
                     self.cost_cloud['new_vehicle_mfr_generalized_cost_dollars'], '.',
                     label='Generalized Cost')

            ax1.plot(cost_curve['veh_%s_cert_co2e_grams_per_mile' % self.vehicle_id],
                     cost_curve['veh_%s_new_vehicle_mfr_generalized_cost_dollars' % self.vehicle_id], 's-',
                     color='black',
                     label='Cost Curve')

            ax1.legend(fontsize='medium', bbox_to_anchor=(0, 1.07), loc="lower left", borderaxespad=0)

            figname = '%s%d_%s_cost_curve.png' % (omega_globals.options.output_folder, self.model_year, self.name)
            fig.savefig(figname.replace(' ', '_'), bbox_inches='tight')

        return cost_curve


class VehicleFinal(SQABase, Vehicle):
    """
    **Loads the base year vehicle data and stores finalized vehicles in the database.**

    Finalized vehicles are those ultimately produced by the manufacturer and are the basis for the effect and cost
    calculations performed after the compliance modeling.

    """
    # --- database table properties ---
    __tablename__ = 'vehicles'
    vehicle_id = Column(Integer, primary_key=True)  #: unique vehicle ID, database table primary key
    name = Column('name', String)  #: vehicle name
    manufacturer_id = Column(String, ForeignKey('manufacturers.manufacturer_id'))  #: vehicle manufacturer ID
    compliance_id = Column(String)  #: compliance ID, may be the manufacturer ID or 'consolidated_OEM'
    manufacturer = relationship('Manufacturer', back_populates='vehicles')  #: SQLAlchemy relationship link to manufacturer table
    annual_data = relationship('VehicleAnnualData', cascade='delete, delete-orphan')  #: SQLAlchemy relationship link to vehicle annual data table

    model_year = Column(Numeric)  #: vehicle model year
    fueling_class = Column(Enum(*fueling_classes, validate_strings=True))  #: fueling class, e.g. 'BEV', 'ICE'
    cost_curve_class = Column(String)  #: ALPHA modeling result class
    base_year_reg_class_id = Column(Enum(*legacy_reg_classes, validate_strings=True))  #: base year regulatory class, historical data
    reg_class_id = Column(String)  #: regulatory class assigned according the active policy
    epa_size_class = Column(String)  #: EPA size class
    context_size_class = Column(String)  #: context size class, used to project future vehicle sales based on the context
    base_year_market_share = Column(Float)  #: base year market share, used to maintain market share relationships within context size classes
    electrification_class = Column(String)  #: electrification class, used to determine ``fueling_class`` at this time
    target_co2e_grams_per_mile = Column('target_co2e_grams_per_mile', Float)  #: cert target CO2e g/mi, as determined by the active policy
    lifetime_VMT = Column('lifetime_vmt', Float) #: lifetime VMT, used to calculate CO2e Mg
    cert_co2e_Mg = Column('cert_co2e_megagrams', Float)  #: cert CO2e Mg, as determined by the active policy
    target_co2e_Mg = Column('target_co2e_megagrams', Float)  #: cert CO2e Mg, as determined by the active policy
    in_use_fuel_id = Column('in_use_fuel_id', String)  #: in-use / onroad fuel ID
    cert_fuel_id = Column('cert_fuel_id', String)  #: cert fuel ID
    market_class_id = Column('market_class_id', String, ForeignKey('market_classes.market_class_id'))  #: market class ID, as determined by the consumer subpackage

    _initial_registered_count = Column('_initial_registered_count', Float)

    # --- static properties ---
    compliance_ids = set()  #: the set of compliance IDs (manufacturer IDs or 'consolidated_OEM')
    mfr_base_year_size_class_share = dict()  #: dict of base year context size class market share by compliance ID and size class, used to project future vehicle sales based on the context

    base_input_template_columns = {'vehicle_name', 'manufacturer_id', 'model_year', 'reg_class_id', 'epa_size_class',
                                   'context_size_class', 'electrification_class', 'cost_curve_class', 'in_use_fuel_id',
                                   'cert_fuel_id', 'sales'}  #: mandatory input file columns, the rest can be optional numeric columns
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
        from producer.vehicle_annual_data import VehicleAnnualData
        self._initial_registered_count = initial_registered_count

        omega_globals.session.add(self)  # update database so vehicle_annual_data foreign key succeeds...

        VehicleAnnualData.update_registered_count(self,
                                                  calendar_year=self.model_year,
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
        inherit_properties = ['name', 'manufacturer_id', 'compliance_id', 'base_year_reg_class_id',
                              'reg_class_id', 'epa_size_class', 'context_size_class',
                              'base_year_market_share'] + \
                             VehicleFinal.dynamic_attributes

        # model year and registered count are required to make a full-blown VehicleFinal object
        veh = VehicleFinal(model_year=vehicle.model_year, initial_registered_count=1)

        # get the rest of the attributes from the list
        for p in inherit_properties:
            veh.__setattr__(p, vehicle.__getattribute__(p))

        return veh

    @staticmethod
    def init_vehicles_from_file(filename, verbose=False):
        """

        Load data from the base year vehicle file

        Args:
            filename (str): name of input file
            verbose (bool): enable additional console and logfile output if True

        Returns:
            List of template/input errors, else empty list on success

        """
        from context.new_vehicle_market import NewVehicleMarket

        vehicle_shares_dict = {'total': 0}

        VehicleFinal.compliance_ids = set()
        vehicles_list = []

        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_name = 'vehicles'
        input_template_version = 0.43
        input_template_columns = VehicleFinal.base_input_template_columns

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version, verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                # load data into database
                for i in df.index:
                    veh = VehicleFinal(
                        name=df.loc[i, 'vehicle_name'],
                        manufacturer_id=df.loc[i, 'manufacturer_id'],
                        model_year=df.loc[i, 'model_year'],
                        base_year_reg_class_id=df.loc[i, 'reg_class_id'],
                        epa_size_class=df.loc[i, 'epa_size_class'],
                        context_size_class=df.loc[i, 'context_size_class'],
                        electrification_class=df.loc[i, 'electrification_class'],
                        cost_curve_class=df.loc[i, 'cost_curve_class'],
                        in_use_fuel_id=df.loc[i, 'in_use_fuel_id'],
                        cert_fuel_id=df.loc[i, 'cert_fuel_id'],
                        initial_registered_count=df.loc[i, 'sales'],
                    )

                    for attr, dc in zip(VehicleFinal.dynamic_attributes, VehicleFinal.dynamic_columns):
                        veh.__setattr__(attr, df.loc[i, dc])

                    if omega_globals.options.consolidate_manufacturers:
                        veh.compliance_id = 'consolidated_OEM'
                    else:
                        veh.compliance_id = veh.manufacturer_id

                    VehicleFinal.compliance_ids.add(veh.compliance_id)

                    if veh.electrification_class == 'EV':
                        veh.fueling_class = 'BEV'
                    else:
                        veh.fueling_class = 'ICE'

                    veh.reg_class_id = omega_globals.options.RegulatoryClasses.get_vehicle_reg_class(veh)
                    veh.market_class_id = omega_globals.options.MarketClass.get_vehicle_market_class(veh)
                    veh.cert_direct_oncycle_co2e_grams_per_mile = df.loc[i, 'cert_direct_oncycle_co2e_grams_per_mile']
                    veh.cert_direct_co2e_grams_per_mile = veh.cert_direct_oncycle_co2e_grams_per_mile  # TODO: minus any credits??

                    veh.cert_co2e_grams_per_mile = None
                    veh.cert_direct_kwh_per_mile = df.loc[i, 'cert_direct_oncycle_kwh_per_mile']  # TODO: veh.cert_direct_oncycle_kwh_per_mile?
                    veh.onroad_direct_co2e_grams_per_mile = 0
                    veh.onroad_direct_kwh_per_mile = 0

                    vehicle_shares_dict['total'] += veh.initial_registered_count

                    if veh.context_size_class not in vehicle_shares_dict:
                        vehicle_shares_dict[veh.context_size_class] = 0

                    vehicle_shares_dict[veh.context_size_class] += veh.initial_registered_count

                    vehicles_list.append(veh)

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

                    if veh.context_size_class not in NewVehicleMarket.context_size_classes:
                        NewVehicleMarket.context_size_classes[veh.context_size_class] = veh.initial_registered_count
                    else:
                        NewVehicleMarket.context_size_classes[veh.context_size_class] += veh.initial_registered_count

                    size_key = veh.compliance_id + '_' + veh.context_size_class
                    if size_key not in NewVehicleMarket.manufacturer_context_size_classes:
                        NewVehicleMarket.manufacturer_context_size_classes[size_key] = veh.initial_registered_count
                    else:
                        NewVehicleMarket.manufacturer_context_size_classes[size_key] += veh.initial_registered_count

                    if verbose:
                        print(veh)

                # Update market share and create alternative vehicles (a BEV equivalent for every ICE vehicle, etc).
                # Alternative vehicles maintain fleet utility mix across model years and prevent all future vehicles
                # from becoming midsize car BEVs, for example, just because that's the dominant BEV in the base year
                # fleet
                for v in vehicles_list:
                    v.base_year_market_share = v.initial_registered_count / vehicle_shares_dict['total']

                    alt_veh = v.clone_vehicle(v)  # create alternative powertrain clone of vehicle
                    if v.fueling_class == 'ICE':
                        alt_veh.fueling_class = 'BEV'
                        alt_veh.name = 'BEV of ' + v.name
                        alt_veh.cost_curve_class = v.cost_curve_class.replace('ice_', 'bev_')
                        alt_veh.in_use_fuel_id = "{'US electricity':1.0}"
                        alt_veh.cert_fuel_id = "{'electricity':1.0}"
                        alt_veh.market_class_id = v.market_class_id.replace('ICE', 'BEV')
                    else:
                        alt_veh.fueling_class = 'ICE'
                        alt_veh.name = 'ICE of ' + v.name
                        alt_veh.cost_curve_class = v.cost_curve_class.replace('bev_', 'ice_')
                        alt_veh.in_use_fuel_id = "{'pump gasoline':1.0}"
                        alt_veh.cert_fuel_id = "{'gasoline':1.0}"
                        alt_veh.market_class_id = v.market_class_id.replace('BEV', 'ICE')
                    alt_veh.cert_direct_oncycle_co2e_grams_per_mile = 0
                    alt_veh.cert_direct_co2e_grams_per_mile = 0
                    alt_veh.cert_direct_kwh_per_mile = 0

                for nrmc in NewVehicleMarket.context_size_class_info_by_nrmc:
                    for csc in NewVehicleMarket.context_size_class_info_by_nrmc[nrmc]:
                        NewVehicleMarket.context_size_class_info_by_nrmc[nrmc][csc]['share'] = \
                            NewVehicleMarket.context_size_class_info_by_nrmc[nrmc][csc]['total'] / vehicle_shares_dict[csc]

                # calculate manufacturer base year context size class shares
                from producer.manufacturers import Manufacturer

                VehicleFinal.compliance_ids = sorted(list(VehicleFinal.compliance_ids))

                VehicleFinal.mfr_base_year_size_class_share = dict()
                for compliance_id in VehicleFinal.compliance_ids:
                    for size_class in NewVehicleMarket.context_size_classes:
                        if compliance_id not in VehicleFinal.mfr_base_year_size_class_share:
                            VehicleFinal.mfr_base_year_size_class_share[compliance_id] = dict()

                        size_key = compliance_id + '_' + size_class

                        if size_key not in NewVehicleMarket.manufacturer_context_size_classes:
                            NewVehicleMarket.manufacturer_context_size_classes[size_key] = 0

                        if verbose:
                            print('%s: %s / %s: %.2f' % (size_key,
                                                     NewVehicleMarket.manufacturer_context_size_classes[size_key],
                                                     NewVehicleMarket.context_size_classes[size_class],
                                                     NewVehicleMarket.manufacturer_context_size_classes[size_key] /
                                                     NewVehicleMarket.context_size_classes[size_class]))

                        VehicleFinal.mfr_base_year_size_class_share[compliance_id][size_class] = \
                            NewVehicleMarket.manufacturer_context_size_classes[size_key] / \
                            NewVehicleMarket.context_size_classes[size_class]

        return template_errors

    @staticmethod
    def init_database_from_file(vehicles_file, vehicle_onroad_calculations_file, verbose=False):
        """
        Init vehicle database from the base year vehicles file and set up the onroad / vehicle attribute calculations.
        Also initializes decomposition attributes.

        Args:
            vehicles_file (str): the name of the base year vehicles file
            vehicle_onroad_calculations_file (str): the name of the vehicle onroad calculations (vehicle attribute calculations) file
            verbose (bool): enable additional console and logfile output if True

        Returns:
            List of template/input errors, else empty list on success

        See Also:
            ``VehicleAttributeCalculations``, ``DecompositionAttributes``

        """
        init_fail = []

        DecompositionAttributes.init()   # offcycle_credits must be initalized first

        init_fail += VehicleFinal.init_vehicles_from_file(vehicles_file, verbose=verbose)

        init_fail += VehicleAttributeCalculations.init_vehicle_attribute_calculations_from_file(
            vehicle_onroad_calculations_file, clear_cache=True, verbose=verbose)

        return init_fail


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        import importlib
        from omega import init_user_definable_submodules

        omega_globals.options = OMEGASessionSettings()

        init_fail = []
        init_fail += init_user_definable_submodules()

        # set up global variables:
        init_omega_db(omega_globals.options.verbose)
        omega_log.init_logfile()

        from common.omega_functions import weighted_value

        from producer.manufacturers import Manufacturer  # needed for manufacturers table
        from context.onroad_fuels import OnroadFuel  # needed for showroom fuel ID
        from context.fuel_prices import FuelPrice  # needed for retail fuel price
        from context.new_vehicle_market import NewVehicleMarket  # needed for context size class hauling info
        from producer.vehicle_annual_data import VehicleAnnualData

        module_name = get_template_name(omega_globals.options.policy_targets_file)
        omega_globals.options.VehicleTargets = importlib.import_module(module_name).VehicleTargets

        module_name = get_template_name(omega_globals.options.market_classes_file)
        omega_globals.options.MarketClass = importlib.import_module(module_name).MarketClass

        from policy.policy_fuels import PolicyFuel

        from context.cost_clouds import CostCloud

        # setup up dynamic attributes before metadata.create_all()
        vehicle_columns = get_template_columns(omega_globals.options.vehicles_file)
        VehicleFinal.dynamic_columns = list(
            set.difference(set(vehicle_columns), VehicleFinal.base_input_template_columns))
        for dc in VehicleFinal.dynamic_columns:
            VehicleFinal.dynamic_attributes.append(make_valid_python_identifier(dc))

        for attr in VehicleFinal.dynamic_attributes:
            if attr not in VehicleFinal.__dict__:
                if int(sqlalchemy.__version__.split('.')[1]) > 3:
                    sqlalchemy.ext.declarative.DeclarativeMeta.__setattr__(VehicleFinal, attr, Column(attr, Float))
                else:
                    sqlalchemy.ext.declarative.api.DeclarativeMeta.__setattr__(VehicleFinal, attr, Column(attr, Float))

        SQABase.metadata.create_all(omega_globals.engine)

        init_fail += Manufacturer.init_database_from_file(omega_globals.options.manufacturers_file,
                                                          verbose=omega_globals.options.verbose)

        init_fail += omega_globals.options.MarketClass.init_from_file(omega_globals.options.market_classes_file,
                                                verbose=omega_globals.options.verbose)

        init_fail += OnroadFuel.init_from_file(omega_globals.options.onroad_fuels_file,
                                               verbose=omega_globals.options.verbose)

        init_fail += FuelPrice.init_database_from_file(omega_globals.options.context_fuel_prices_file,
                                                       verbose=omega_globals.options.verbose)

        init_fail += CostCloud.init_cost_clouds_from_file(omega_globals.options.vehicle_simulation_results_and_costs_file,
                                                          verbose=omega_globals.options.verbose)

        init_fail += omega_globals.options.VehicleTargets.init_from_file(omega_globals.options.policy_targets_file,
                                                                         verbose=omega_globals.options.verbose)

        init_fail += PolicyFuel.init_from_file(omega_globals.options.policy_fuels_file,
                                               verbose=omega_globals.options.verbose)

        init_fail += VehicleFinal.init_database_from_file(omega_globals.options.vehicles_file,
                                                          omega_globals.options.onroad_vehicle_calculations_file,
                                                          verbose=omega_globals.options.verbose)

        if not init_fail:

            vehicles_list = VehicleFinal.get_compliance_vehicles(2019, 'OEM_A')

            # update vehicle annual data, registered count must be update first:
            VehicleAnnualData.update_registered_count(vehicles_list[0], 2020, 54321)

            # dump database with updated vehicle annual data
            dump_omega_db_to_csv(omega_globals.options.database_dump_folder)

            weighted_footprint = weighted_value(vehicles_list, 'initial_registered_count', 'footprint_ft2')

            # v = vehicles_list[0]
            # v.model_year = 2020
            # VehicleAttributeCalculations.perform_attribute_calculations(v)

        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)

    except:
        dump_omega_db_to_csv(omega_globals.options.database_dump_folder)
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)

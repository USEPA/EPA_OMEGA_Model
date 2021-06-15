"""
vehicles.py
===========


"""

print('importing %s' % __file__)

from usepa_omega2 import *


class DecompositionAttributes(OMEGABase):
    """
    **Stores vehicle-specific attributes that will be tracked at each point of a vehicle or composite vehicle frontier**

    Decomposition Attributes are interpolated from the composite vehicle frontier during decomposition, using
    composite vehicle cert_co2_grams_per_mile

    """

    values = []

    @classmethod
    def init(cls):
        from offcycle_credits import OffCycleCredits

        cls.values = ['cert_co2_grams_per_mile',
                      'new_vehicle_mfr_generalized_cost_dollars',

                      'new_vehicle_mfr_cost_dollars',

                      'upstream_co2_grams_per_mile',

                      'cert_direct_co2_grams_per_mile',
                      'cert_direct_kwh_per_mile',

                      'onroad_direct_co2_grams_per_mile',
                      'onroad_direct_kwh_per_mile',

                      'cert_direct_oncycle_kwh_per_mile',
                      'cert_direct_offcycle_kwh_per_mile',

                      'cert_direct_oncycle_co2_grams_per_mile',
                      'cert_direct_offcycle_co2_grams_per_mile',

                      'cert_indirect_offcycle_co2_grams_per_mile',
                      ] + OffCycleCredits.offcycle_credit_names

    @staticmethod
    def interp1d(cost_curve, index_column, index, vehicle, attribute):
        """

        Args:
            cost_curve:
            index_column:
            index:
            vehicle:
            attribute:

        Returns:

        """

        if type(vehicle) != CompositeVehicle:
            prefix = 'veh_%s_' % vehicle.vehicle_ID
        else:
            prefix = ''

        if len(cost_curve) > 1:
            interp1d = scipy.interpolate.interp1d(cost_curve[index_column],
                                              cost_curve['%s%s' % (prefix, attribute)],
                                              fill_value=(cost_curve['%s%s' % (prefix, attribute)].min(),
                                                          cost_curve['%s%s' % (prefix, attribute)].max()),
                                              bounds_error=False)
            return interp1d(index)
        else:
            return cost_curve['%s%s' % (prefix, attribute)].item()

    @classmethod
    def rename_decomposition_columns(cls, vehicle, cost_cloud):
        """

        Args:
            vehicle:
            cost_cloud:

        Returns:

        """
        rename_dict = dict()

        for ccv in cls.values:
            rename_dict[ccv] = 'veh_%s_%s' % (vehicle.vehicle_ID, ccv)

        return cost_cloud.rename(columns=rename_dict)


class VehicleAttributeCalculations(OMEGABase):
    """
    ****
    """
    cache = dict()

    @staticmethod
    def init_vehicle_attribute_calculations_from_file(filename, clear_cache=False, verbose=False):
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
        ****
        Args:
            vehicle:
            cost_cloud:

        Returns:

        """
        start_years = VehicleAttributeCalculations.cache['start_year']
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


class CompositeVehicle(OMEGABase):
    """
    ****
    """
    next_vehicle_ID = -1

    def __init__(self, vehicle_list, calendar_year, verbose=False, calc_composite_cost_curve=True,
                 weight_by='initial_registered_count'):
        """
        Build composite vehicle from list of vehicles
        :param vehicle_list: list of vehicles (must be of same reg_class, market class, fueling_class)
        """

        from omega_functions import weighted_value

        self.vehicle_list = vehicle_list  # copy.deepcopy(vehicle_list)
        self.name = 'composite vehicle (%s.%s)' % (self.vehicle_list[0].market_class_ID, self.vehicle_list[0].reg_class_ID)

        self.vehicle_ID = CompositeVehicle.next_vehicle_ID
        CompositeVehicle.set_next_vehicle_ID()

        self.weight_by = weight_by

        self.model_year = self.vehicle_list[0].model_year # calendar_year?
        self.reg_class_ID = self.vehicle_list[0].reg_class_ID
        self.fueling_class = self.vehicle_list[0].fueling_class
        self.market_class_ID = self.vehicle_list[0].market_class_ID

        self.weighted_values = ['cert_co2_grams_per_mile',
                                'cert_direct_co2_grams_per_mile',
                                'cert_direct_kwh_per_mile',
                                'onroad_direct_co2_grams_per_mile',
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
            v.set_cert_target_co2_Mg()

        for v in self.vehicle_list:
            if self.total_weight != 0:
                v.composite_vehicle_share_frac = v.__getattribute__(self.weight_by) / self.total_weight
            else:
                v.composite_vehicle_share_frac = 0

        if calc_composite_cost_curve:
            self.cost_curve = self.calc_composite_cost_curve(plot=verbose)

        self.tech_option_iteration_num = 0

        self.normalized_cert_target_co2_Mg = weighted_value(self.vehicle_list, self.weight_by,
                                                            'normalized_cert_target_co2_Mg')

        self.normalized_cert_co2_Mg = o2.options.GHG_standard.calc_cert_co2_Mg(self, 1, 1)

    @staticmethod
    def reset_vehicle_IDs():
        """

        Returns:

        """
        CompositeVehicle.next_vehicle_ID = -1

    @staticmethod
    def set_next_vehicle_ID():
        """

        Returns:

        """
        CompositeVehicle.next_vehicle_ID = CompositeVehicle.next_vehicle_ID - 1

    def retail_fuel_price_dollars_per_unit(self, calendar_year=None):
        """

        Args:
            calendar_year:

        Returns:

        """
        from omega_functions import weighted_value

        if calendar_year is None:
            calendar_year = self.model_year

        return weighted_value(self.vehicle_list, self.weight_by, 'retail_fuel_price_dollars_per_unit',
                              calendar_year)

    def decompose(self):
        """

        Returns:

        """
        for v in self.vehicle_list:
            if 'cost_curve' in self.__dict__:
                for ccv in DecompositionAttributes.values:
                    v.__setattr__(ccv, DecompositionAttributes.interp1d(self.cost_curve,
                                                                        'cert_co2_grams_per_mile',
                                                                        self.cert_co2_grams_per_mile,
                                                                        v, ccv))
            v.initial_registered_count = self.initial_registered_count * v.composite_vehicle_share_frac
            v.set_cert_target_co2_Mg()  # varies by model year and initial_registered_count
            v.set_cert_co2_Mg()  # varies by model year and initial_registered_count

    def calc_composite_cost_curve(self, plot=False):
        """

        Args:
            plot:

        Returns:

        """
        from cost_clouds import CostCloud
        from omega_functions import cartesian_prod
        from omega_plot import figure, label_xy

        if plot:
            fig, ax1 = figure()
            label_xy(ax1, 'CO2 g/mi', '$')

        composite_frontier_df = pd.DataFrame()
        composite_frontier_df['market_share_frac'] = [0]

        # calc weighted values
        for wv in self.weighted_values:
            composite_frontier_df[wv] = [0]

        for v in self.vehicle_list:
            vehicle_frontier = v.cost_curve
            vehicle_frontier['veh_%s_market_share' % v.vehicle_ID] = v.composite_vehicle_share_frac

            composite_frontier_df = cartesian_prod(composite_frontier_df, vehicle_frontier, drop=False)

            prior_market_share_frac = composite_frontier_df['market_share_frac']
            veh_market_share_frac = composite_frontier_df['veh_%s_market_share' % v.vehicle_ID]

            for wv in self.weighted_values:
                composite_frontier_df[wv] = \
                    (composite_frontier_df[wv] * prior_market_share_frac +
                     composite_frontier_df['veh_%s_%s' % (v.vehicle_ID, wv)] * veh_market_share_frac) / \
                    (prior_market_share_frac + veh_market_share_frac)

            # update running total market share
            composite_frontier_df['market_share_frac'] = prior_market_share_frac + veh_market_share_frac

            drop_columns = [c for c in composite_frontier_df.columns if c.endswith('_y') or c.endswith('_x') or
                            c.endswith('_market_share')] + ['_']

            composite_frontier_df = composite_frontier_df.drop(drop_columns, axis=1, errors='ignore')

            # calculate new sales-weighted frontier
            composite_frontier_df = CostCloud.calc_frontier(composite_frontier_df, 'cert_co2_grams_per_mile',
                                                                 'new_vehicle_mfr_generalized_cost_dollars',
                                                                 allow_upslope=True)

            composite_frontier_df = composite_frontier_df.drop(['frontier_factor'], axis=1, errors='ignore')

        if plot:
            ax1.plot(composite_frontier_df['cert_co2_grams_per_mile'],
                     composite_frontier_df['new_vehicle_mfr_cost_dollars'], 'x-')
            ax1.plot(composite_frontier_df['cert_co2_grams_per_mile'],
                     composite_frontier_df['new_vehicle_mfr_generalized_cost_dollars'], 'x--')

        return composite_frontier_df

    def get_cost_from_cost_curve(self, target_co2_gpmi):
        """

        Args:
            target_co2_gpmi:

        Returns:

        """
        # get cost from cost curve for target_co2_gpmi(s)
        if len(self.cost_curve) > 1:
            cost_dollars = scipy.interpolate.interp1d(self.cost_curve['cert_co2_grams_per_mile'],
                                                      self.cost_curve['new_vehicle_mfr_cost_dollars'],
                                                      fill_value=(self.cost_curve['new_vehicle_mfr_cost_dollars'].min(),
                                                                  self.cost_curve['new_vehicle_mfr_cost_dollars'].max()), bounds_error=False)
            return cost_dollars(target_co2_gpmi).tolist()
        else:
            return self.cost_curve['new_vehicle_mfr_cost_dollars']

    def get_kwh_pmi(self, target_co2_gpmi):
        """

        Args:
            target_co2_gpmi:

        Returns:

        """
        return DecompositionAttributes.interp1d(self.cost_curve,
                                                'cert_co2_grams_per_mile',
                                                target_co2_gpmi,
                                                self, 'cert_direct_kwh_per_mile')

    def get_generalized_cost_from_cost_curve(self, target_co2_gpmi):
        """

        Args:
            target_co2_gpmi:

        Returns:

        """
        return DecompositionAttributes.interp1d(self.cost_curve,
                                                'cert_co2_grams_per_mile',
                                                target_co2_gpmi,
                                                self, 'new_vehicle_mfr_generalized_cost_dollars')

    def get_max_co2_gpmi(self):
        """

        Returns:

        """
        # get max co2_gpmi from self.cost_curve
        return self.cost_curve['cert_co2_grams_per_mile'].max()

    def get_min_co2_gpmi(self):
        """

        Returns:

        """
        # get min co2_gpmi from self.cost_curve
        return self.cost_curve['cert_co2_grams_per_mile'].min()

    def set_new_vehicle_mfr_cost_dollars(self):
        """

        Returns:

        """
        from omega_functions import weighted_value
        self.new_vehicle_mfr_cost_dollars = weighted_value(self.vehicle_list, self.weight_by,
                                                           'new_vehicle_mfr_cost_dollars')

    # def set_new_vehicle_mfr_generalized_cost_dollars(self):
    #     """
    #
    #     Returns:
    #
    #     """
    #     from omega_functions import weighted_value
    #     self.new_vehicle_mfr_generalized_cost_dollars = weighted_value(self.vehicle_list, self.weight_by,
    #                                                        'new_vehicle_mfr_generalized_cost_dollars')

    def set_cert_target_co2_Mg(self):
        """

        Returns:

        """
        from omega_functions import weighted_value
        self.cert_target_co2_Mg = weighted_value(self.vehicle_list, self.weight_by, 'cert_target_co2_Mg')
        return self.cert_target_co2_Mg

    def set_cert_co2_Mg(self):
        """

        Returns:

        """
        from omega_functions import weighted_value
        self.cert_co2_Mg = weighted_value(self.vehicle_list, self.weight_by, 'cert_co2_Mg')
        return self.cert_co2_Mg


class Vehicle(OMEGABase):
    """
    ****
    """
    next_vehicle_ID = 0

    def __init__(self):
        self.vehicle_ID = Vehicle.next_vehicle_ID
        self.name = ''
        self.manufacturer_ID = None
        self.model_year = None
        self.fueling_class = None
        self.hauling_class = None
        self.cost_curve_class = None
        self.legacy_reg_class_ID = None
        self.reg_class_ID = None
        self.reg_class_market_share_frac = 1.0
        self.epa_size_class = None
        self.context_size_class = None
        self.market_share = 0
        self.non_responsive_market_group = None
        self.electrification_class = None
        self.cert_target_co2_grams_per_mile = 0
        self.cert_co2_Mg = 0
        self.cert_target_co2_Mg = 0
        self.in_use_fuel_ID = None
        self.cert_fuel_ID = None
        self.market_class_ID = None
        self.footprint_ft2 = 0
        self._initial_registered_count = 0
        Vehicle.set_next_vehicle_ID()
        self.cost_cloud = None
        self.cost_curve = None

        # additional attriutes are added dynamically and may vary based on user inputs (such as off-cycle credits)
        for ccv in DecompositionAttributes.values:
            self.__setattr__(ccv, 0)

    @staticmethod
    def reset_vehicle_IDs():
        """

        Returns:

        """
        Vehicle.next_vehicle_ID = 0

    @staticmethod
    def set_next_vehicle_ID():
        """

        Returns:

        """
        Vehicle.next_vehicle_ID = Vehicle.next_vehicle_ID + 1

    @property
    def initial_registered_count(self):
        """

        Returns:

        """
        return self._initial_registered_count

    def retail_fuel_price_dollars_per_unit(self, calendar_year=None):
        """

        Args:
            calendar_year:

        Returns:

        """
        from context_fuel_prices import ContextFuelPrices
        if calendar_year is None:
            calendar_year = self.model_year

        price = 0
        fuel_dict = eval(self.in_use_fuel_ID, {'__builtins__': None}, {})
        for fuel, fuel_share in fuel_dict.items():
            price += ContextFuelPrices.get_fuel_prices(calendar_year, 'retail_dollars_per_unit', fuel) * fuel_share

        return price

    def pretax_fuel_price_dollars_per_unit(self, calendar_year=None):
        """

        Args:
            calendar_year:

        Returns:

        """
        from context_fuel_prices import ContextFuelPrices
        if calendar_year is None:
            calendar_year = self.model_year

        price = 0
        fuel_dict = eval(self.in_use_fuel_ID, {'__builtins__': None}, {})
        for fuel, fuel_share in fuel_dict.items():
            price += ContextFuelPrices.get_fuel_prices(calendar_year, 'pretax_dollars_per_unit', fuel) * fuel_share

        return price

    def fuel_tailpipe_co2_emissions_grams_per_unit(self):
        """

        Returns:

        """
        from fuels import Fuel

        co2_emissions_grams_per_unit = 0
        fuel_dict = eval(self.in_use_fuel_ID, {'__builtins__': None}, {})
        for fuel, fuel_share in fuel_dict.items():
            co2_emissions_grams_per_unit += \
                Fuel.get_fuel_attributes(fuel, 'co2_tailpipe_emissions_grams_per_unit') * fuel_share

        return co2_emissions_grams_per_unit


    @initial_registered_count.setter
    def initial_registered_count(self, initial_registered_count):
        """

        Args:
            initial_registered_count:

        Returns:

        """
        self._initial_registered_count = initial_registered_count

    def set_cert_target_co2_grams_per_mile(self):
        """

        Returns:

        """
        self.cert_target_co2_grams_per_mile = o2.options.GHG_standard.calc_target_co2_gpmi(self)

    def set_cert_target_co2_Mg(self):
        """

        Returns:

        """
        self.cert_target_co2_Mg = o2.options.GHG_standard.calc_target_co2_Mg(self)

    def set_new_vehicle_mfr_cost_dollars_from_cost_curve(self):
        """

        Returns:

        """
        self.new_vehicle_mfr_cost_dollars = self.get_cost_from_cost_curve(self.cert_co2_grams_per_mile)

    def set_new_vehicle_mfr_generalized_cost_dollars_from_cost_curve(self):
        """

        Returns:

        """
        self.new_vehicle_mfr_generalized_cost_dollars = self.get_generalized_cost_from_cost_curve(self.cert_co2_grams_per_mile)

    def get_cost_from_cost_curve(self, target_co2_gpmi):
        """

        Args:
            target_co2_gpmi:

        Returns:

        """
        # get cost from cost curve for target_co2_gpmi(s)
        return DecompositionAttributes.interp1d(self.cost_curve,
                                                'veh_%s_cert_co2_grams_per_mile' % self.vehicle_ID,
                                                target_co2_gpmi,
                                                self, 'new_vehicle_mfr_cost_dollars')

    def get_generalized_cost_from_cost_curve(self, target_co2_gpmi):
        """

        Args:
            target_co2_gpmi:

        Returns:

        """
        # get cost from cost curve for target_co2_gpmi(s)
        return DecompositionAttributes.interp1d(self.cost_curve,
                                                'veh_%s_cert_co2_grams_per_mile' % self.vehicle_ID,
                                                target_co2_gpmi,
                                                self, 'new_vehicle_mfr_generalized_cost_dollars')


    def set_cert_co2_Mg(self):
        """

        Returns:

        """
        self.cert_co2_Mg = o2.options.GHG_standard.calc_cert_co2_Mg(self)

    def inherit_vehicle(self, vehicle, model_year=None):
        """

        Args:
            vehicle:
            model_year:

        Returns:

        """
        base_properties = {'name', 'manufacturer_ID', 'model_year',
                           'fueling_class', 'hauling_class',
                           'cost_curve_class', 'legacy_reg_class_ID', 'reg_class_ID', 'in_use_fuel_ID',
                           'cert_fuel_ID', 'market_class_ID', 'footprint_ft2', 'epa_size_class',
                           'context_size_class', 'market_share', 'non_responsive_market_group',
                           'electrification_class'}

        for attr in base_properties:
            self.__setattr__(attr, vehicle.__getattribute__(attr))

        if model_year:
            self.model_year = model_year

        self.set_cert_target_co2_grams_per_mile()  # varies by model year
        self.initial_registered_count = vehicle.initial_registered_count

        if type(self) == Vehicle and type(vehicle) == VehicleFinal:
            from policy_fuel_upstream_methods import PolicyFuelUpstreamMethods
            from cost_clouds import CostCloud

            # need to add upstream to direct co2 g/mi and calculate this year's frontier
            self.cert_direct_co2_grams_per_mile = vehicle.cert_direct_co2_grams_per_mile

            # calculate cert co2 g/mi
            upstream = PolicyFuelUpstreamMethods.get_upstream_method(self.model_year)
            self.cert_direct_kwh_per_mile = vehicle.cert_direct_kwh_per_mile
            self.upstream_co2_grams_per_mile = upstream(self, self.cert_direct_co2_grams_per_mile, self.cert_direct_kwh_per_mile)
            self.cert_co2_grams_per_mile = self.cert_direct_co2_grams_per_mile + self.upstream_co2_grams_per_mile

            if o2.options.flat_context:
                self.cost_cloud = CostCloud.get_cloud(o2.options.flat_context_year, self.cost_curve_class)
            else:
                self.cost_cloud = CostCloud.get_cloud(self.model_year, self.cost_curve_class)
            self.cost_curve = self.create_frontier_df()  # create frontier, including generalized cost
            self.set_new_vehicle_mfr_cost_dollars_from_cost_curve()  # varies by model_year and cert_co2_grams_per_mile
            self.set_new_vehicle_mfr_generalized_cost_dollars_from_cost_curve()  # varies by model_year and cert_co2_grams_per_mile
            self.set_cert_target_co2_Mg()  # varies by model year and initial_registered_count
            self.set_cert_co2_Mg()  # varies by model year and initial_registered_count
            VehicleAttributeCalculations.perform_attribute_calculations(self)
        else:  # type(self) == VehicleFinal and type(vehicle == Vehicle)
            # set dynamic attributes
            for attr in DecompositionAttributes.values:
                self.__setattr__(attr, vehicle.__getattribute__(attr))
            self.cert_direct_co2_grams_per_mile = vehicle.cert_co2_grams_per_mile - vehicle.upstream_co2_grams_per_mile
            self.cert_target_co2_Mg = vehicle.cert_target_co2_Mg
            self.cert_co2_Mg = vehicle.cert_co2_Mg

        self.normalized_cert_target_co2_Mg = self.cert_target_co2_Mg / self.initial_registered_count

    def create_frontier_df(self):
        """

        Returns:

        """
        from cost_clouds import CostCloud
        from policy_fuel_upstream_methods import PolicyFuelUpstreamMethods
        from drive_cycle_weights import DriveCycleWeights
        from offcycle_credits import OffCycleCredits

        self.cost_cloud['cert_direct_oncycle_co2_grams_per_mile'] = \
            DriveCycleWeights.calc_cert_direct_oncycle_co2_grams_per_mile(self.model_year, self.fueling_class, self.cost_cloud)

        self.cost_cloud['cert_direct_oncycle_kwh_per_mile'] = \
            DriveCycleWeights.calc_cert_direct_oncycle_kwh_per_mile(self.model_year, self.fueling_class, self.cost_cloud)

        # initialize onroad values
        self.cost_cloud['onroad_direct_co2_grams_per_mile'] = 0
        self.cost_cloud['onroad_direct_kwh_per_mile'] = 0

        # drop extraneous columns
        self.cost_cloud = self.cost_cloud.drop(columns=['cost_curve_class', 'model_year'])

        # TODO: update dynamic costs, if any

        # calculate off cycle credits before calculating upstream and onroad
        self.cost_cloud = OffCycleCredits.calc_off_cycle_credits(self)

        self.cost_cloud['cert_direct_co2_grams_per_mile'] = self.cost_cloud['cert_direct_oncycle_co2_grams_per_mile'] -\
                                                            self.cost_cloud['cert_direct_offcycle_co2_grams_per_mile']

        self.cost_cloud['cert_direct_kwh_per_mile'] = self.cost_cloud['cert_direct_oncycle_kwh_per_mile'] -\
                                                      self.cost_cloud['cert_direct_offcycle_kwh_per_mile']

        # calc onroad gap, etc...
        VehicleAttributeCalculations.perform_attribute_calculations(self, self.cost_cloud)

        # add upstream calcs
        upstream_method = PolicyFuelUpstreamMethods.get_upstream_method(self.model_year)

        self.cost_cloud['upstream_co2_grams_per_mile'] = \
            upstream_method(self, self.cost_cloud['cert_direct_co2_grams_per_mile'],
                            self.cost_cloud['cert_direct_kwh_per_mile'])

        self.cost_cloud['cert_co2_grams_per_mile'] = self.cost_cloud['cert_direct_co2_grams_per_mile'] + \
                                                     self.cost_cloud['upstream_co2_grams_per_mile'] - \
                                                     self.cost_cloud['cert_indirect_offcycle_co2_grams_per_mile']

        # calculate producer generalized cost
        self.cost_cloud = o2.options.producer_calc_generalized_cost(self, 'onroad_direct_co2_grams_per_mile',
                                                                    'onroad_direct_kwh_per_mile',
                                                                    'new_vehicle_mfr_cost_dollars')

        # calculate frontier from updated cloud
        allow_upslope = True
        cost_curve = CostCloud.calc_frontier(self.cost_cloud, 'cert_co2_grams_per_mile',
                                             'new_vehicle_mfr_cost_dollars', allow_upslope=allow_upslope)

        # CostCloud.plot_frontier(self.cost_cloud, self.cost_curve_class + '\nallow_upslope=%s, frontier_affinity_factor=%s' % (allow_upslope, o2.options.cost_curve_frontier_affinity_factor), cost_curve, 'cert_co2_grams_per_mile', 'new_vehicle_mfr_cost_dollars')

        # rename generic columns to vehicle-specific columns
        cost_curve = DecompositionAttributes.rename_decomposition_columns(self, cost_curve)

        # drop frontier factor
        cost_curve = cost_curve.drop(columns=['frontier_factor'])

        return cost_curve


class VehicleFinal(SQABase, Vehicle):
    """
    ****
    """
    # --- database table properties ---
    __tablename__ = 'vehicles'
    vehicle_ID = Column('vehicle_id', Integer, primary_key=True)
    name = Column('name', String)
    manufacturer_ID = Column('manufacturer_id', String, ForeignKey('manufacturers.manufacturer_id'))
    manufacturer = relationship('Manufacturer', back_populates='vehicles')
    annual_data = relationship('VehicleAnnualData', cascade='delete, delete-orphan')

    # --- static properties ---
    # vehicle_nameplate = Column(String, default='USALDV')
    model_year = Column(Numeric)
    fueling_class = Column(Enum(*fueling_classes, validate_strings=True))
    hauling_class = Column(Enum(*hauling_classes, validate_strings=True))
    cost_curve_class = Column(String)  # for now, could be Enum of cost_curve_classes, but those classes would have to be identified and enumerated in the __init.py__...
    legacy_reg_class_ID = Column('legacy_reg_class_id', Enum(*reg_classes, validate_strings=True))
    reg_class_ID = Column('reg_class_id', Enum(*reg_classes, validate_strings=True))
    epa_size_class = Column(String)  # TODO: validate with enum?
    context_size_class = Column(String)  # TODO: validate with enum?
    market_share = Column(Float)
    non_responsive_market_group = Column(String)
    electrification_class = Column(String)  # TODO: validate with enum?
    cert_target_co2_grams_per_mile = Column('cert_target_co2_grams_per_mile', Float)
    cert_co2_Mg = Column('cert_co2_megagrams', Float)
    cert_target_co2_Mg = Column('cert_target_co2_megagrams', Float)
    in_use_fuel_ID = Column('in_use_fuel_id', String) # , ForeignKey('fuels.fuel_id'))
    cert_fuel_ID = Column('cert_fuel_id', String) # , ForeignKey('fuels.fuel_id'))
    market_class_ID = Column('market_class_id', String, ForeignKey('market_classes.market_class_id'))
    footprint_ft2 = Column(Float)

    _initial_registered_count = Column('_initial_registered_count', Float)

    #: **additional attributes are dynamically added from DecompositionAttributes.values during omega2.init_omega()**


    @property
    def initial_registered_count(self):
        """

        Returns:

        """
        return self._initial_registered_count

    @initial_registered_count.setter
    def initial_registered_count(self, initial_registered_count):
        """

        Args:
            initial_registered_count:

        Returns:

        """
        from vehicle_annual_data import VehicleAnnualData
        self._initial_registered_count = initial_registered_count

        o2.session.add(self)  # update database so vehicle_annual_data foreign key succeeds...
        # o2.session.flush()

        VehicleAnnualData.update_registered_count(self,
                                                  calendar_year=self.model_year,
                                                  registered_count=initial_registered_count)

    @staticmethod
    def get_max_model_year():
        """

        Returns:

        """
        return o2.session.query(func.max(VehicleFinal.model_year)).scalar()

    @staticmethod
    def get_manufacturer_vehicles(calendar_year, manufacturer_id):
        """

        Args:
            calendar_year:
            manufacturer_id:

        Returns:

        """
        return o2.session.query(VehicleFinal). \
            filter(VehicleFinal.manufacturer_ID == manufacturer_id). \
            filter(VehicleFinal.model_year == calendar_year).all()

    @staticmethod
    def get_vehicle_attributes(vehicle_id, attributes):
        """

        Args:
            vehicle_id:
            attributes:

        Returns:

        """
        if type(attributes) is not list:
            attributes = [attributes]
        attrs = VehicleFinal.get_class_attributes(attributes)
        return o2.session.query(*attrs).filter(VehicleFinal.vehicle_ID == vehicle_id).one()

    @staticmethod
    def calc_cert_target_co2_Mg(model_year, manufacturer_id):
        """

        Args:
            model_year:
            manufacturer_id:

        Returns:

        """
        return o2.session.query(func.sum(VehicleFinal.cert_target_co2_Mg)). \
            filter(VehicleFinal.manufacturer_ID == manufacturer_id). \
            filter(VehicleFinal.model_year == model_year).scalar()

    @staticmethod
    def calc_cert_co2_Mg(model_year, manufacturer_id):
        """

        Args:
            model_year:
            manufacturer_id:

        Returns:

        """
        return o2.session.query(func.sum(VehicleFinal.cert_co2_Mg)). \
            filter(VehicleFinal.manufacturer_ID == manufacturer_id). \
            filter(VehicleFinal.model_year == model_year).scalar()

    @staticmethod
    def clone_vehicle(vehicle):
        """

        Args:
            vehicle:

        Returns:

        """
        inherit_properties = {'name', 'manufacturer_ID', 'hauling_class', 'legacy_reg_class_ID',
                              'reg_class_ID', 'epa_size_class', 'context_size_class',
                              'market_share', 'non_responsive_market_group', 'footprint_ft2'}

        # model year and registered count are required to make a full-blown VehicleFinal object
        veh = VehicleFinal(model_year=vehicle.model_year, initial_registered_count=1)

        # get the rest of the attributes from the list
        for p in inherit_properties:
            veh.__setattr__(p, vehicle.__getattribute__(p))

        return veh

    @staticmethod
    def init_vehicles_from_file(filename, verbose=False):
        """

        Args:
            filename:
            verbose:

        Returns:

        """
        from context_new_vehicle_market import ContextNewVehicleMarket
        from consumer.market_classes import MarketClass

        vehicle_shares_dict = {'total': 0}

        vehicles_list = []

        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_name = 'vehicles'
        input_template_version = 0.4
        input_template_columns = {'vehicle_id', 'manufacturer_id', 'model_year', 'reg_class_id',
                                  'epa_size_class', 'context_size_class', 'electrification_class', 'hauling_class',
                                  'cost_curve_class', 'in_use_fuel_id', 'cert_fuel_id',
                                  'sales', 'cert_co2_grams_per_mile', 'cert_direct_kwh_per_mile', 'footprint_ft2',
                                  'eng_rated_hp', 'tot_road_load_hp', 'etw_lbs', 'length_in', 'width_in', 'height_in',
                                  'ground_clearance_in', 'wheelbase_in', 'interior_volume_cuft', 'msrp_dollars',
                                  'passenger_capacity', 'payload_capacity_lbs', 'towing_capacity_lbs'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version, verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                # load data into database
                for i in df.index:
                    veh = VehicleFinal(
                        name=df.loc[i, 'vehicle_id'],
                        manufacturer_ID=df.loc[i, 'manufacturer_id'],
                        model_year=df.loc[i, 'model_year'],
                        legacy_reg_class_ID=df.loc[i, 'reg_class_id'],
                        reg_class_ID=df.loc[i, 'reg_class_id'],
                        epa_size_class=df.loc[i, 'epa_size_class'],
                        context_size_class=df.loc[i, 'context_size_class'],
                        electrification_class=df.loc[i, 'electrification_class'],
                        hauling_class=df.loc[i, 'hauling_class'],
                        cost_curve_class=df.loc[i, 'cost_curve_class'],
                        in_use_fuel_ID=df.loc[i, 'in_use_fuel_id'],
                        cert_fuel_ID=df.loc[i, 'cert_fuel_id'],
                        footprint_ft2=df.loc[i, 'footprint_ft2'],
                    )

                    if veh.electrification_class == 'EV':
                        veh.fueling_class = 'BEV'
                    else:
                        veh.fueling_class = 'ICE'

                    veh.reg_class_ID = o2.options.GHG_standard.get_vehicle_reg_class(veh)
                    veh.market_class_ID, veh.non_responsive_market_group = MarketClass.get_vehicle_market_class(veh)
                    veh.cert_direct_oncycle_co2_grams_per_mile = df.loc[i, 'cert_co2_grams_per_mile']
                    veh.cert_direct_co2_grams_per_mile = veh.cert_direct_oncycle_co2_grams_per_mile  # TODO: minus any credits??

                    veh.cert_co2_grams_per_mile = None
                    veh.cert_direct_kwh_per_mile = df.loc[i, 'cert_direct_kwh_per_mile']
                    veh.onroad_direct_co2_grams_per_mile = 0
                    veh.onroad_direct_kwh_per_mile = 0

                    veh.initial_registered_count = df.loc[i, 'sales']

                    vehicle_shares_dict['total'] += veh.initial_registered_count

                    if veh.context_size_class not in vehicle_shares_dict:
                        vehicle_shares_dict[veh.context_size_class] = 0

                    vehicle_shares_dict[veh.context_size_class] += veh.initial_registered_count

                    vehicles_list.append(veh)

                    if veh.hauling_class == 'hauling':
                        if veh.context_size_class not in ContextNewVehicleMarket.hauling_context_size_class_info:
                            ContextNewVehicleMarket.hauling_context_size_class_info[veh.context_size_class] = \
                                {'total': veh.initial_registered_count, 'hauling_share': 0}
                        else:
                            ContextNewVehicleMarket.hauling_context_size_class_info[veh.context_size_class]['total'] = \
                                ContextNewVehicleMarket.hauling_context_size_class_info[veh.context_size_class][
                                    'total'] + veh.initial_registered_count

                    if veh.context_size_class not in ContextNewVehicleMarket.context_size_classes:
                        ContextNewVehicleMarket.context_size_classes[veh.context_size_class] = []

                    if verbose:
                        print(veh)

                # Update market share and create alternative vehicles (a BEV equivalent for every ICE vehicle, etc).
                # Alternative vehicles maintain fleet utility mix across model years and prevent all future vehicles
                # from becoming midsize car BEVs, for example, just because that's the dominant BEV in the base year
                # fleet
                for v in vehicles_list:
                    v.market_share = v.initial_registered_count / vehicle_shares_dict['total']

                    alt_veh = v.clone_vehicle(v)  # create alternative powertrain clone of vehicle
                    if v.fueling_class == 'ICE':
                        alt_veh.fueling_class = 'BEV'
                        alt_veh.name = 'BEV of ' + v.name
                        alt_veh.cost_curve_class = v.cost_curve_class.replace('ice_', 'bev_')
                        alt_veh.in_use_fuel_ID = "{'US electricity':1.0}"
                        alt_veh.cert_fuel_ID = "{'MTE US electricity':1.0}"
                        alt_veh.market_class_ID = v.market_class_ID.replace('ICE', 'BEV')
                    else:
                        alt_veh.fueling_class = 'ICE'
                        alt_veh.name = 'ICE of ' + v.name
                        alt_veh.cost_curve_class = v.cost_curve_class.replace('bev_', 'ice_')
                        alt_veh.in_use_fuel_ID = "{'pump gasoline':1.0}"
                        alt_veh.cert_fuel_ID = "{'MTE Gasoline':1.0}"
                        alt_veh.market_class_ID = v.market_class_ID.replace('BEV', 'ICE')
                    alt_veh.cert_direct_oncycle_co2_grams_per_mile = 0
                    alt_veh.cert_direct_co2_grams_per_mile = 0
                    alt_veh.cert_direct_kwh_per_mile = 0

                for hsc in ContextNewVehicleMarket.hauling_context_size_class_info:
                    ContextNewVehicleMarket.hauling_context_size_class_info[hsc]['hauling_share'] = \
                        ContextNewVehicleMarket.hauling_context_size_class_info[hsc]['total'] / \
                        vehicle_shares_dict[hsc]

        return template_errors

    @staticmethod
    def init_database_from_file(vehicles_file, vehicle_onroad_calculations_file, verbose=False):
        """

        Args:
            vehicles_file:
            vehicle_onroad_calculations_file:
            verbose:

        Returns:

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
            print(fileio.get_filenameext(__file__))

        # set up global variables:
        o2.options = OMEGARuntimeOptions()
        init_omega_db()
        o2.engine.echo = True
        omega_log.init_logfile()

        init_fail = []

        from omega_functions import weighted_value, unweighted_value

        from manufacturers import Manufacturer  # needed for manufacturers table
        from consumer.market_classes import MarketClass  # needed for market class ID
        from fuels import Fuel  # needed for showroom fuel ID
        from context_fuel_prices import ContextFuelPrices # needed for retail fuel price
        from context_new_vehicle_market import ContextNewVehicleMarket # needed for context size class hauling info
        # from vehicles import Vehicle
        from vehicle_annual_data import VehicleAnnualData

        from GHG_standards_flat import input_template_name as flat_template_name
        from GHG_standards_footprint import input_template_name as footprint_template_name
        ghg_template_name = get_template_name(o2.options.ghg_standards_file)

        if ghg_template_name == flat_template_name:
            from GHG_standards_flat import GHGStandardFlat

            o2.options.GHG_standard = GHGStandardFlat
        elif ghg_template_name == footprint_template_name:
            from GHG_standards_footprint import GHGStandardFootprint

            o2.options.GHG_standard = GHGStandardFootprint
        else:
            init_fail.append('UNKNOWN GHG STANDARD "%s"' % ghg_template_name)

        from GHG_standards_fuels import GHGStandardFuels

        from cost_clouds import CostCloud

        SQABase.metadata.create_all(o2.engine)

        init_fail += Manufacturer.init_database_from_file(o2.options.manufacturers_file,
                                                                     verbose=o2.options.verbose)
        init_fail += MarketClass.init_database_from_file(o2.options.market_classes_file,
                                                                    verbose=o2.options.verbose)
        init_fail += Fuel.init_database_from_file(o2.options.fuels_file, verbose=o2.options.verbose)

        init_fail += ContextFuelPrices.init_database_from_file(o2.options.context_fuel_prices_file,
                                                                          verbose=o2.options.verbose)

        init_fail += CostCloud.init_cost_clouds_from_file(o2.options.cost_file, verbose=o2.options.verbose)

        init_fail += o2.options.GHG_standard.init_database_from_file(o2.options.ghg_standards_file,
                                                                             verbose=o2.options.verbose)

        init_fail += GHGStandardFuels.init_database_from_file(o2.options.ghg_standards_fuels_file,
                                                                         verbose=o2.options.verbose)

        init_fail += VehicleFinal.init_database_from_file(o2.options.vehicles_file,
                                                                     o2.options.vehicle_onroad_calculations_file,
                                                                     verbose=o2.options.verbose)

        if not init_fail:

            vehicles_list = VehicleFinal.get_manufacturer_vehicles(2019, 'USA Motors')

            # update vehicle annual data, registered count must be update first:
            VehicleAnnualData.update_registered_count(vehicles_list[0], 2020, 54321)
            VehicleAnnualData.update_vehicle_annual_data(vehicles_list[0], 2020, 'vmt', 12345)
            VehicleAnnualData.update_vehicle_annual_data(vehicles_list[0], 2020, 'annual_vmt', 15000)

            # dump database with updated vehicle annual data
            dump_omega_db_to_csv(o2.options.database_dump_folder)

            weighted_footprint = weighted_value(vehicles_list, 'initial_registered_count', 'footprint_ft2')

            print(vehicles_list[0].retail_fuel_price_dollars_per_unit())
            print(vehicles_list[1].retail_fuel_price_dollars_per_unit())
            print(vehicles_list[0].retail_fuel_price_dollars_per_unit(2030))
            print(vehicles_list[1].retail_fuel_price_dollars_per_unit(2030))

            # v = vehicles_list[0]
            # v.model_year = 2020
            # VehicleAttributeCalculations.perform_attribute_calculations(v)

        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)

    except:
        dump_omega_db_to_csv(o2.options.database_dump_folder)
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)

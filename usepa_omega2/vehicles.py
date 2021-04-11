"""
vehicles.py
===========


"""

print('importing %s' % __file__)

import o2  # import global variables
from usepa_omega2 import *


class CompositeVehicle(OMEGABase):
    next_vehicle_ID = -1

    def __init__(self, vehicle_list, calendar_year, verbose=False):
        """
        Build composite vehicle from list of vehicles
        :param vehicle_list: list of vehicles (must be of same reg_class, market class, fueling_class)
        """
        import copy
        from omega_functions import weighted_value

        self.vehicle_list = vehicle_list  # copy.deepcopy(vehicle_list)
        self.name = 'composite vehicle (%s.%s)' % (self.vehicle_list[0].market_class_ID, self.vehicle_list[0].reg_class_ID)

        self.vehicle_ID = CompositeVehicle.next_vehicle_ID
        CompositeVehicle.set_next_vehicle_ID()

        self.model_year = self.vehicle_list[0].model_year
        self.reg_class_ID = self.vehicle_list[0].reg_class_ID
        self.fueling_class = self.vehicle_list[0].fueling_class
        self.market_class_ID = self.vehicle_list[0].market_class_ID
        self.cert_target_CO2_Mg = self.set_cert_target_CO2_Mg()
        self.cert_CO2_Mg = self.set_cert_CO2_Mg()

        # calc sales-weighted values
        self.cert_CO2_grams_per_mile = weighted_value(self.vehicle_list, 'initial_registered_count',
                                                      'cert_CO2_grams_per_mile')

        self.cert_kWh_per_mile = weighted_value(self.vehicle_list, 'initial_registered_count',
                                                      'cert_kWh_per_mile')

        self.footprint_ft2 = weighted_value(self.vehicle_list, 'initial_registered_count', 'footprint_ft2')

        self.new_vehicle_mfr_cost_dollars = self.set_new_vehicle_mfr_cost_dollars()
        self.new_vehicle_mfr_generalized_cost_dollars = self.set_new_vehicle_mfr_generalized_cost_dollars()

        self.initial_registered_count = 0
        for v in self.vehicle_list:
            self.initial_registered_count = self.initial_registered_count + v.initial_registered_count

        for v in self.vehicle_list:
            v.reg_class_market_share_frac = v.initial_registered_count / self.initial_registered_count

        self.cost_curve = self.calc_composite_cost_curve(plot=verbose)

    @staticmethod
    def reset_vehicle_IDs():
        CompositeVehicle.next_vehicle_ID = -1

    @staticmethod
    def set_next_vehicle_ID():
        CompositeVehicle.next_vehicle_ID = CompositeVehicle.next_vehicle_ID - 1

    def retail_fuel_price_dollars_per_unit(self, calendar_year=None):
        from omega_functions import weighted_value

        if calendar_year is None:
            calendar_year = self.model_year

        return weighted_value(self.vehicle_list, 'initial_registered_count', 'retail_fuel_price_dollars_per_unit', calendar_year)

    def decompose(self):
        # for v in self.vehicle_list:
        #     print('%s= %f' % (v.vehicle_ID, v.cert_CO2_grams_per_mile))

        for v in self.vehicle_list:
            if len(self.cost_curve) > 1:
                vehicle_co2_curve = scipy.interpolate.interp1d(self.cost_curve['cert_co2_grams_per_mile'],
                                                                self.cost_curve['veh_%s_cert_co2_grams_per_mile' % v.vehicle_ID],
                                                                fill_value=(self.cost_curve['veh_%s_cert_co2_grams_per_mile' % v.vehicle_ID].min(),
                                                                            self.cost_curve['veh_%s_cert_co2_grams_per_mile' % v.vehicle_ID].max()), bounds_error=False)

                vehicle_kWh_curve = scipy.interpolate.interp1d(self.cost_curve['cert_co2_grams_per_mile'],
                                                                self.cost_curve['veh_%s_cert_kWh_per_mile' % v.vehicle_ID],
                                                                fill_value=(self.cost_curve['veh_%s_cert_kWh_per_mile' % v.vehicle_ID].min(),
                                                                            self.cost_curve['veh_%s_cert_kWh_per_mile' % v.vehicle_ID].max()), bounds_error=False)
                v.cert_CO2_grams_per_mile = vehicle_co2_curve(self.cert_CO2_grams_per_mile)
                v.cert_kWh_per_mile = vehicle_kWh_curve(self.cert_CO2_grams_per_mile)
            else:
                v.cert_CO2_grams_per_mile = self.cost_curve['veh_%s_cert_co2_grams_per_mile' % v.vehicle_ID].item()
                v.cert_kWh_per_mile = self.cost_curve['veh_%s_cert_kWh_per_mile' % v.vehicle_ID].item()

            v.initial_registered_count = self.initial_registered_count * v.reg_class_market_share_frac
            v.set_new_vehicle_mfr_cost_dollars_from_cost_curve()  # varies by model_year and cert_CO2_grams_per_mile
            v.set_new_vehicle_mfr_generalized_cost_dollars_from_cost_curve()  # varies by model_year and cert_CO2_grams_per_mile
            v.set_cert_target_CO2_Mg()  # varies by model year and initial_registered_count
            v.set_cert_CO2_Mg()  # varies by model year and initial_registered_count

            # print('%s: %f' % (v.vehicle_ID, v.cert_CO2_grams_per_mile))

    def calc_composite_cost_curve(self, plot=False):
        from cost_clouds import CostCloud
        from omega_functions import cartesian_prod
        from omega_plot import figure, label_xy

        if plot:
            fig, ax1 = figure()
            label_xy(ax1, 'CO2 g/mi', '$')

        composite_frontier_df = pd.DataFrame()
        composite_frontier_df['cert_co2_grams_per_mile'] = [0]
        # composite_frontier_df['tailpipe_co2_grams_per_mile'] = [0]
        composite_frontier_df['cert_kWh_per_mile'] = [0]
        composite_frontier_df['new_vehicle_mfr_cost_dollars'] = [0]
        composite_frontier_df['new_vehicle_mfr_generalized_cost_dollars'] = [0]
        composite_frontier_df['market_share_frac'] = [0]

        for v in self.vehicle_list:
            vehicle_frontier = v.cost_curve
            vehicle_frontier['veh_%s_market_share' % v.vehicle_ID] = v.reg_class_market_share_frac

            composite_frontier_df = cartesian_prod(composite_frontier_df, vehicle_frontier, drop=False)

            prior_market_share_frac = composite_frontier_df['market_share_frac']
            veh_market_share_frac = composite_frontier_df['veh_%s_market_share' % v.vehicle_ID]

            # calculate weighted co2 g/mi
            composite_frontier_df['cert_co2_grams_per_mile'] = \
                (composite_frontier_df['cert_co2_grams_per_mile'] * prior_market_share_frac +
                 composite_frontier_df['veh_%s_cert_co2_grams_per_mile' % v.vehicle_ID] * veh_market_share_frac) / \
                (prior_market_share_frac + veh_market_share_frac)

            # composite_frontier_df['tailpipe_co2_grams_per_mile'] = \
            #     (composite_frontier_df['tailpipe_co2_grams_per_mile'] * prior_market_share_frac +
            #      composite_frontier_df['veh_%s_tailpipe_co2_grams_per_mile' % v.vehicle_ID] * veh_market_share_frac) / \
            #     (prior_market_share_frac + veh_market_share_frac)

            # calculate weighted kWh/mi
            composite_frontier_df['cert_kWh_per_mile'] = \
                (composite_frontier_df['cert_kWh_per_mile'] * prior_market_share_frac +
                 composite_frontier_df['veh_%s_cert_kWh_per_mile' % v.vehicle_ID] * veh_market_share_frac) / \
                (prior_market_share_frac + veh_market_share_frac)

            # calculate weighted cost
            composite_frontier_df['new_vehicle_mfr_cost_dollars'] = \
                (composite_frontier_df['new_vehicle_mfr_cost_dollars'] * prior_market_share_frac +
                 composite_frontier_df['veh_%s_mfr_cost_dollars' % v.vehicle_ID] * veh_market_share_frac) / \
                (prior_market_share_frac + veh_market_share_frac)

            composite_frontier_df['new_vehicle_mfr_generalized_cost_dollars'] = \
                (composite_frontier_df['new_vehicle_mfr_generalized_cost_dollars'] * prior_market_share_frac +
                 composite_frontier_df['veh_%s_mfr_generalized_cost_dollars' % v.vehicle_ID] * veh_market_share_frac) / \
                (prior_market_share_frac + veh_market_share_frac)

            # update running total market share
            composite_frontier_df['market_share_frac'] = prior_market_share_frac + veh_market_share_frac

            # if plot:
            #     ax1.plot(composite_frontier_df['cert_co2_grams_per_mile'],
            #              composite_frontier_df['new_vehicle_mfr_cost_dollars'], '.')
            #     ax1.plot(composite_frontier_df['cert_co2_grams_per_mile'],
            #              composite_frontier_df['new_vehicle_mfr_generalized_cost_dollars'], '.')

            # calculate new sales-weighted frontier
            composite_frontier_df = CostCloud.calculate_frontier(composite_frontier_df, 'cert_co2_grams_per_mile',
                                                                 'new_vehicle_mfr_generalized_cost_dollars')

            # if plot:
            #     ax1.plot(composite_frontier_df['cert_co2_grams_per_mile'],
            #              composite_frontier_df['new_vehicle_mfr_cost_dollars'], '.-')
            #     ax1.plot(composite_frontier_df['cert_co2_grams_per_mile'],
            #              composite_frontier_df['new_vehicle_mfr_generalized_cost_dollars'], '.--')

        if plot:
            ax1.plot(composite_frontier_df['cert_co2_grams_per_mile'],
                     composite_frontier_df['new_vehicle_mfr_cost_dollars'], 'x-')
            ax1.plot(composite_frontier_df['cert_co2_grams_per_mile'],
                     composite_frontier_df['new_vehicle_mfr_generalized_cost_dollars'], 'x--')

        return composite_frontier_df

    def get_cost_from_cost_curve(self, target_co2_gpmi):
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
        import numpy as np
        # get kwh/mi from cost curve for target_co2_gpmi(s)
        if len(self.cost_curve) > 1:
            kWh_pmi = scipy.interpolate.interp1d(self.cost_curve['cert_co2_grams_per_mile'],
                                                      self.cost_curve['cert_kWh_per_mile'],
                                                      fill_value=(self.cost_curve['cert_kWh_per_mile'].min(),
                                                                  self.cost_curve['cert_kWh_per_mile'].max()), bounds_error=False)
            return kWh_pmi(target_co2_gpmi).tolist()
        else:
            return self.cost_curve['cert_kWh_per_mile']

    def get_generalized_cost_from_cost_curve(self, target_co2_gpmi):
        import numpy as np
        # get cost from cost curve for target_co2_gpmi(s)
        if len(self.cost_curve) > 1:
            cost_dollars = scipy.interpolate.interp1d(self.cost_curve['cert_co2_grams_per_mile'],
                                                      self.cost_curve['new_vehicle_mfr_generalized_cost_dollars'],
                                                      fill_value=(self.cost_curve['new_vehicle_mfr_generalized_cost_dollars'].min(),
                                                                  self.cost_curve['new_vehicle_mfr_generalized_cost_dollars'].max()), bounds_error=False)
            return cost_dollars(target_co2_gpmi).tolist()
        else:
            return self.cost_curve['new_vehicle_mfr_generalized_cost_dollars']

    def get_max_co2_gpmi(self):
        # get max co2_gpmi from self.cost_curve
        return self.cost_curve['cert_co2_grams_per_mile'].max()

    def get_min_co2_gpmi(self):
        # get min co2_gpmi from self.cost_curve
        return self.cost_curve['cert_co2_grams_per_mile'].min()

    def set_new_vehicle_mfr_cost_dollars(self):
        from omega_functions import weighted_value
        self.new_vehicle_mfr_cost_dollars = weighted_value(self.vehicle_list, 'initial_registered_count',
                                                           'new_vehicle_mfr_cost_dollars')
        return self.new_vehicle_mfr_cost_dollars

    def set_new_vehicle_mfr_generalized_cost_dollars(self):
        from omega_functions import weighted_value
        self.new_vehicle_mfr_cost_dollars = weighted_value(self.vehicle_list, 'initial_registered_count',
                                                           'new_vehicle_mfr_generalized_cost_dollars')
        return self.new_vehicle_mfr_cost_dollars

    def set_cert_target_CO2_Mg(self):
        from omega_functions import weighted_value
        self.cert_target_CO2_Mg = weighted_value(self.vehicle_list, 'initial_registered_count', 'cert_target_CO2_Mg')
        return self.cert_target_CO2_Mg

    def set_cert_CO2_Mg(self):
        from omega_functions import weighted_value
        self.cert_CO2_Mg = weighted_value(self.vehicle_list, 'initial_registered_count', 'cert_CO2_Mg')
        return self.cert_CO2_Mg


class Vehicle(OMEGABase):
    next_vehicle_ID = 0

    def __init__(self):
        self.vehicle_ID = Vehicle.next_vehicle_ID
        self.name = ''
        self.manufacturer_ID = None
        self.model_year = None
        self.fueling_class = None
        self.hauling_class = None
        self.cost_curve_class = None
        self.reg_class_ID = None
        self.reg_class_market_share_frac = 1.0
        self.epa_size_class = None
        self.context_size_class = None
        self.context_size_class_share_frac = None
        self.electrification_class = None
        self.upstream_CO2_grams_per_mile = None
        self.cert_CO2_grams_per_mile = None
        self.cert_kWh_per_mile = None
        self.cert_target_CO2_grams_per_mile = None
        self.cert_CO2_Mg = None
        self.cert_target_CO2_Mg = None
        self.new_vehicle_mfr_cost_dollars = None
        self.new_vehicle_mfr_generalized_cost_dollars = None
        self.manufacturer_deemed_new_vehicle_generalized_cost_dollars = None
        self.in_use_fuel_ID = None
        self.cert_fuel_ID = None
        self.market_class_ID = None
        self.footprint_ft2 = None
        self._initial_registered_count = 0
        Vehicle.set_next_vehicle_ID()
        self.cost_cloud = None
        self.cost_curve = None

    @staticmethod
    def reset_vehicle_IDs():
        Vehicle.next_vehicle_ID = 0

    @staticmethod
    def set_next_vehicle_ID():
        Vehicle.next_vehicle_ID = Vehicle.next_vehicle_ID + 1

    @property
    def initial_registered_count(self):
        return self._initial_registered_count

    def retail_fuel_price_dollars_per_unit(self, calendar_year=None):
        from context_fuel_prices import ContextFuelPrices
        if calendar_year is None:
            calendar_year = self.model_year

        price = 0
        fuel_dict = eval(self.in_use_fuel_ID)
        for fuel, fuel_share in fuel_dict.items():
            price += ContextFuelPrices.get_fuel_prices(calendar_year, 'retail_dollars_per_unit', fuel) * fuel_share

        return price

    def pretax_fuel_price_dollars_per_unit(self, calendar_year=None):
        from context_fuel_prices import ContextFuelPrices
        if calendar_year is None:
            calendar_year = self.model_year

        price = 0
        fuel_dict = eval(self.in_use_fuel_ID)
        for fuel, fuel_share in fuel_dict.items():
            price += ContextFuelPrices.get_fuel_prices(calendar_year, 'pretax_dollars_per_unit', fuel) * fuel_share

        return price

    def fuel_tailpipe_co2_emissions_grams_per_unit(self):
        from fuels import Fuel

        co2_emissions_grams_per_unit = 0
        fuel_dict = eval(self.in_use_fuel_ID)
        for fuel, fuel_share in fuel_dict.items():
            co2_emissions_grams_per_unit += Fuel.get_fuel_attributes(fuel, 'co2_tailpipe_emissions_grams_per_unit') * fuel_share

        return co2_emissions_grams_per_unit


    @initial_registered_count.setter
    def initial_registered_count(self, initial_registered_count):
        self._initial_registered_count = initial_registered_count

    def set_cert_target_CO2_grams_per_mile(self):
        self.cert_target_CO2_grams_per_mile = o2.options.GHG_standard.calculate_target_co2_gpmi(self)

    def set_cert_target_CO2_Mg(self):
        self.cert_target_CO2_Mg = o2.options.GHG_standard.calculate_target_co2_Mg(self)

    def set_new_vehicle_mfr_cost_dollars_from_cost_curve(self):
        self.new_vehicle_mfr_cost_dollars = self.get_cost_from_cost_curve(self.cert_CO2_grams_per_mile)

    def set_new_vehicle_mfr_generalized_cost_dollars_from_cost_curve(self):
        self.new_vehicle_mfr_generalized_cost_dollars = self.get_generalized_cost_from_cost_curve(self.cert_CO2_grams_per_mile)

    def get_cost_from_cost_curve(self, target_co2_gpmi):
        # get cost from cost curve for target_co2_gpmi(s)
        if len(self.cost_curve) > 1:
            cost_dollars = scipy.interpolate.interp1d(self.cost_curve['veh_%s_cert_co2_grams_per_mile' % self.vehicle_ID],
                                                      self.cost_curve['veh_%s_mfr_cost_dollars' % self.vehicle_ID],
                                                      fill_value=(self.cost_curve['veh_%s_mfr_cost_dollars' % self.vehicle_ID].min(),
                                                                  self.cost_curve['veh_%s_mfr_cost_dollars' % self.vehicle_ID].max()), bounds_error=False)
            return cost_dollars(target_co2_gpmi).tolist()
        else:
            return self.cost_curve['veh_%s_mfr_cost_dollars' % self.vehicle_ID].item()

    def get_generalized_cost_from_cost_curve(self, target_co2_gpmi):
        # get cost from cost curve for target_co2_gpmi(s)
        if len(self.cost_curve) > 1:
            cost_dollars = scipy.interpolate.interp1d(self.cost_curve['veh_%s_cert_co2_grams_per_mile' % self.vehicle_ID],
                                                  self.cost_curve['veh_%s_mfr_generalized_cost_dollars' % self.vehicle_ID],
                                                  fill_value=(self.cost_curve['veh_%s_mfr_generalized_cost_dollars' % self.vehicle_ID].min(),
                                                              self.cost_curve['veh_%s_mfr_generalized_cost_dollars' % self.vehicle_ID].max()), bounds_error=False)
            return cost_dollars(target_co2_gpmi).tolist()
        else:
            return self.cost_curve['veh_%s_mfr_generalized_cost_dollars' % self.vehicle_ID].item()
    #
    # def get_max_co2_gpmi(self):
    #     # get max co2_gpmi from self.cost_curve
    #     return self.cost_curve['veh_%s_mfr_cost_dollars' % self.vehicle_ID].max()
    #
    # def get_min_co2_gpmi(self):
    #     # get min co2_gpmi from self.cost_curve
    #     return self.cost_curve['veh_%s_cert_co2_grams_per_mile' % self.vehicle_ID].min()

    def set_cert_CO2_Mg(self):
        self.cert_CO2_Mg = o2.options.GHG_standard.calculate_cert_co2_Mg(self)

    def inherit_vehicle(self, vehicle, model_year=None):
        inherit_properties = {'name', 'manufacturer_ID', 'model_year', 'fueling_class', 'hauling_class',
                              'cost_curve_class', 'reg_class_ID', 'in_use_fuel_ID', 'cert_fuel_ID', 'market_class_ID',
                              'footprint_ft2', 'epa_size_class', 'context_size_class', 'context_size_class_share_frac',
                              'electrification_class'}

        for p in inherit_properties:
            self.__setattr__(p, vehicle.__getattribute__(p))

        if model_year:
            self.model_year = model_year

        from policy_fuel_upstream_methods import PolicyFuelUpstreamMethods
        from cost_clouds import CostCloud

        self.set_cert_target_CO2_grams_per_mile()  # varies by model year
        self.initial_registered_count = vehicle.initial_registered_count
        self.cert_kWh_per_mile = vehicle.cert_kWh_per_mile

        if type(self) == Vehicle and type(vehicle) == VehicleFinal:
            # need to add upstream to "tailpipe" co2 g/mi and calculate this year's frontier
            self.cert_CO2_grams_per_mile = vehicle.cert_CO2_grams_per_mile  # this is really "tailpipe" g/mi

            upstream = PolicyFuelUpstreamMethods.get_upstream_method(self.model_year)
            self.upstream_CO2_grams_per_mile = upstream(self, self.cert_CO2_grams_per_mile, self.cert_kWh_per_mile)
            self.cert_CO2_grams_per_mile += self.upstream_CO2_grams_per_mile

            self.cost_cloud = CostCloud.get_cloud(self.model_year, self.cost_curve_class)
            self.cost_curve = self.create_frontier_df()  # create frontier, including generalized cost
            self.set_new_vehicle_mfr_cost_dollars_from_cost_curve()  # varies by model_year and cert_CO2_grams_per_mile
            self.set_new_vehicle_mfr_generalized_cost_dollars_from_cost_curve()  # varies by model_year and cert_CO2_grams_per_mile
            self.set_cert_target_CO2_Mg()  # varies by model year and initial_registered_count
            self.set_cert_CO2_Mg()  # varies by model year and initial_registered_count
        else:  # type(self) == VehicleFinal and type(vehicle == Vehicle)
            # cert_co2_grams_per_mile already has upstream in it, don't need to add it
            self.cert_CO2_grams_per_mile = vehicle.cert_CO2_grams_per_mile #  - vehicle.upstream_CO2_grams_per_mile
            self.new_vehicle_mfr_cost_dollars = vehicle.new_vehicle_mfr_cost_dollars
            self.new_vehicle_mfr_generalized_cost_dollars = vehicle.new_vehicle_mfr_generalized_cost_dollars
            self.cert_target_CO2_Mg = vehicle.cert_target_CO2_Mg
            self.cert_CO2_Mg = vehicle.cert_CO2_Mg

    def create_frontier_df(self):
        from cost_clouds import CostCloud
        from policy_fuel_upstream_methods import PolicyFuelUpstreamMethods
        from drive_cycle_weights import DriveCycleWeights

        co2_name = 'veh_%s_cert_co2_grams_per_mile' % self.vehicle_ID
        tailpipe_co2_name = 'veh_%s_tailpipe_co2_grams_per_mile' % self.vehicle_ID
        kwh_name = 'veh_%s_cert_kWh_per_mile' % self.vehicle_ID
        tailpipe_kWh_name = 'veh_%s_tailpipe_kWh_per_mile' % self.vehicle_ID
        cost_name = 'veh_%s_mfr_cost_dollars' % self.vehicle_ID

        # rename generic columns to vehicle-specific columns
        self.cost_cloud = self.cost_cloud.rename(
            columns={'cert_co2_grams_per_mile': co2_name, 'cert_kWh_per_mile': kwh_name,
                     'new_vehicle_mfr_cost_dollars': cost_name})

        self.cost_cloud[co2_name] = \
            DriveCycleWeights.calc_weighted_drive_cycle_co2_grams_per_mile(self.model_year, self.cost_cloud)

        self.cost_cloud[kwh_name] = \
            DriveCycleWeights.calc_weighted_drive_cycle_kWh_per_mile(self.model_year, self.cost_cloud)

        # capture pre-upstream values as "tailpipe", for now...
        self.cost_cloud[tailpipe_co2_name] = self.cost_cloud[co2_name]
        self.cost_cloud[tailpipe_kWh_name] = self.cost_cloud[kwh_name]

        # drop extraneous columns
        self.cost_cloud = self.cost_cloud.drop(columns=['cost_curve_class', 'model_year'])

        # TODO: update dynamic costs, if any

        # add upstream calcs
        upstream = PolicyFuelUpstreamMethods.get_upstream_method(self.model_year)
        self.cost_cloud['upstream_co2_grams_per_mile'] = \
            upstream(self, self.cost_cloud[co2_name], self.cost_cloud[kwh_name])
        self.cost_cloud[co2_name] += self.cost_cloud['upstream_co2_grams_per_mile']

        # calculate producer generalized cost
        self.cost_cloud = o2.options.producer_calculate_generalized_cost(self, self.cost_cloud, co2_name, cost_name)

        # calculate frontier from updated cloud
        cost_curve = CostCloud.calculate_frontier(self.cost_cloud, co2_name, cost_name, allow_upslope=False)

        # CostCloud.plot_frontier(self.cost_cloud, '', cost_curve, co2_name, cost_name)

        # drop frontier factor
        cost_curve = cost_curve.drop(columns=['frontier_factor'])

        return cost_curve


class VehicleFinal(SQABase, Vehicle):
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
    reg_class_ID = Column('reg_class_id', Enum(*reg_classes, validate_strings=True))
    epa_size_class = Column(String)  # TODO: validate with enum?
    context_size_class = Column(String)  # TODO: validate with enum?
    context_size_class_share_frac = Column(Float)
    electrification_class = Column(String)  # TODO: validate with enum?
    cert_target_CO2_grams_per_mile = Column('cert_target_co2_grams_per_mile', Float)
    cert_CO2_Mg = Column('cert_co2_megagrams', Float)
    cert_target_CO2_Mg = Column('cert_target_co2_megagrams', Float)
    new_vehicle_mfr_cost_dollars = Column(Float)
    new_vehicle_mfr_generalized_cost_dollars = Column(Float)
    manufacturer_deemed_new_vehicle_generalized_cost_dollars = Column(Float)
    in_use_fuel_ID = Column('showroom_fuel_id', String) # , ForeignKey('fuels.fuel_id'))
    cert_fuel_ID = Column('cert_fuel_id', String) # , ForeignKey('fuels.fuel_id'))
    market_class_ID = Column('market_class_id', String, ForeignKey('market_classes.market_class_id'))
    footprint_ft2 = Column(Float)
    upstream_CO2_grams_per_mile = Column('upstream_co2_grams_per_mile', Float)
    cert_CO2_grams_per_mile = Column('cert_co2_grams_per_mile', Float)
    cert_kWh_per_mile = Column('cert_kwh_per_mile', Float)
    _initial_registered_count = Column('_initial_registered_count', Float)

    @property
    def initial_registered_count(self):
        return self._initial_registered_count

    @initial_registered_count.setter
    def initial_registered_count(self, initial_registered_count):
        from vehicle_annual_data import VehicleAnnualData
        self._initial_registered_count = initial_registered_count

        o2.session.add(self)  # update database so vehicle_annual_data foreign key succeeds...
        # o2.session.flush()

        VehicleAnnualData.update_registered_count(self,
                                                  calendar_year=self.model_year,
                                                  registered_count=initial_registered_count)

    @staticmethod
    def get_max_model_year():
        return o2.session.query(func.max(VehicleFinal.model_year)).scalar()

    @staticmethod
    def get_manufacturer_vehicles(calendar_year, manufacturer_id):
        return o2.session.query(VehicleFinal). \
            filter(VehicleFinal.manufacturer_ID == manufacturer_id). \
            filter(VehicleFinal.model_year == calendar_year).all()

    @staticmethod
    def get_vehicle_attributes(vehicle_id, attributes):
        if type(attributes) is not list:
            attributes = [attributes]
        attrs = VehicleFinal.get_class_attributes(attributes)
        return o2.session.query(*attrs).filter(VehicleFinal.vehicle_ID == vehicle_id).one()

    @staticmethod
    def calc_cert_target_CO2_Mg(model_year, manufacturer_id):
        return o2.session.query(func.sum(VehicleFinal.cert_target_CO2_Mg)). \
            filter(VehicleFinal.manufacturer_ID == manufacturer_id). \
            filter(VehicleFinal.model_year == model_year).scalar()

    @staticmethod
    def init_database_from_file(filename, verbose=False):
        from context_new_vehicle_market import ContextNewVehicleMarket
        from consumer.market_classes import MarketClass

        context_size_class_dict = dict()
        vehicles_list = []

        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_name = 'vehicles'
        input_template_version = 0.3
        input_template_columns = {'vehicle_id', 'manufacturer_id', 'model_year', 'reg_class_id',
                                  'epa_size_class', 'context_size_class', 'electrification_class', 'hauling_class',
                                  'cost_curve_class', 'in_use_fuel_id', 'cert_fuel_id',
                                  'sales', 'cert_co2_grams_per_mile', 'cert_kwh_per_mile', 'footprint_ft2'}

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
                    veh.market_class_ID = MarketClass.get_vehicle_market_class(veh)
                    veh.cert_CO2_grams_per_mile = df.loc[i, 'cert_co2_grams_per_mile']
                    veh.cert_kWh_per_mile = df.loc[i, 'cert_kwh_per_mile']
                    veh.initial_registered_count = df.loc[i, 'sales']
                    # veh.set_new_vehicle_mfr_cost_dollars()
                    # veh.set_new_vehicle_mfr_generalized_cost_dollars()
                    # veh.set_cert_target_CO2_grams_per_mile()
                    # veh.set_cert_target_CO2_Mg()
                    # veh.set_cert_CO2_Mg()

                    if veh.context_size_class not in context_size_class_dict:
                        context_size_class_dict[veh.context_size_class] = veh.initial_registered_count
                    else:
                        context_size_class_dict[veh.context_size_class] = \
                            context_size_class_dict[veh.context_size_class] + veh.initial_registered_count

                    vehicles_list.append(veh)

                    if veh.hauling_class == 'hauling':
                        if veh.context_size_class not in ContextNewVehicleMarket.hauling_context_size_class_info:
                            ContextNewVehicleMarket.hauling_context_size_class_info[veh.context_size_class] = \
                                {'total': veh.initial_registered_count, 'hauling_share': 0}
                        else:
                            ContextNewVehicleMarket.hauling_context_size_class_info[veh.context_size_class]['total'] = \
                                ContextNewVehicleMarket.hauling_context_size_class_info[veh.context_size_class][
                                    'total'] + veh.initial_registered_count

                    if verbose:
                        print(veh)

                # update context size class share
                for v in vehicles_list:
                    v.context_size_class_share_frac = v.initial_registered_count / context_size_class_dict[
                        v.context_size_class]

                for hsc in ContextNewVehicleMarket.hauling_context_size_class_info:
                    ContextNewVehicleMarket.hauling_context_size_class_info[hsc]['hauling_share'] = \
                        ContextNewVehicleMarket.hauling_context_size_class_info[hsc]['total'] / \
                        context_size_class_dict[hsc]

        return template_errors


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

        init_fail = init_fail + Manufacturer.init_database_from_file(o2.options.manufacturers_file,
                                                                     verbose=o2.options.verbose)
        init_fail = init_fail + MarketClass.init_database_from_file(o2.options.market_classes_file,
                                                                    verbose=o2.options.verbose)
        init_fail = init_fail + Fuel.init_database_from_file(o2.options.fuels_file, verbose=o2.options.verbose)

        init_fail = init_fail + ContextFuelPrices.init_database_from_file(o2.options.context_fuel_prices_file,
                                                                          verbose=o2.options.verbose)

        init_fail = init_fail + CostCloud.init_cost_clouds_from_file(o2.options.cost_file, verbose=o2.options.verbose)

        init_fail = init_fail + o2.options.GHG_standard.init_database_from_file(o2.options.ghg_standards_file,
                                                                             verbose=o2.options.verbose)

        init_fail = init_fail + GHGStandardFuels.init_database_from_file(o2.options.ghg_standards_fuels_file,
                                                                         verbose=o2.options.verbose)

        init_fail = init_fail + VehicleFinal.init_database_from_file(o2.options.vehicles_file, verbose=o2.options.verbose)

        if not init_fail:

            vehicles_list = VehicleFinal.get_manufacturer_vehicles(2019, 'USA Motors')

            # update vehicle annual data, registered count must be update first:
            VehicleAnnualData.update_registered_count(vehicles_list[0], 2020, 54321)
            VehicleAnnualData.update_vehicle_annual_data(vehicles_list[0], 2020, 'vmt', 12345)
            VehicleAnnualData.update_vehicle_annual_data(vehicles_list[0], 2020, 'annual_vmt', 15000)

            # dump database with updated vehicle annual data
            dump_omega_db_to_csv(o2.options.database_dump_folder)

            weighted_mfr_cost_dollars = weighted_value(vehicles_list, 'initial_registered_count',
                                                       'new_vehicle_mfr_cost_dollars')
            weighted_co2gpmi = weighted_value(vehicles_list, 'initial_registered_count', 'cert_CO2_grams_per_mile')
            weighted_footprint = weighted_value(vehicles_list, 'initial_registered_count', 'footprint_ft2')

            print(vehicles_list[0].retail_fuel_price_dollars_per_unit())
            print(vehicles_list[1].retail_fuel_price_dollars_per_unit())
            print(vehicles_list[0].retail_fuel_price_dollars_per_unit(2030))
            print(vehicles_list[1].retail_fuel_price_dollars_per_unit(2030))

            cv = CompositeVehicle(vehicles_list[0:4], calendar_year=2020, verbose=True)
            cv.cost_curve.to_csv('composite_cost_curve.csv')

            print(cv.retail_fuel_price_dollars_per_unit(2021))
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)

    except:
        dump_omega_db_to_csv(o2.options.database_dump_folder)
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)

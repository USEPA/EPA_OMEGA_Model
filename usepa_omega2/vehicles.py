"""
vehicles.py
===========


"""

print('importing %s' % __file__)

import o2  # import global variables
from usepa_omega2 import *


class CompositeVehicle(o2.OmegaBase):
    next_vehicle_ID = -1

    def __init__(self, vehicle_list):
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

        self.footprint_ft2 = weighted_value(self.vehicle_list, 'initial_registered_count', 'footprint_ft2')

        self.new_vehicle_mfr_cost_dollars = self.set_new_vehicle_mfr_cost_dollars()

        self.initial_registered_count = 0
        for v in self.vehicle_list:
            self.initial_registered_count = self.initial_registered_count + v.initial_registered_count

        for v in self.vehicle_list:
            v.reg_class_market_share_frac = v.initial_registered_count / self.initial_registered_count

        self.cost_curve = self.calc_composite_cost_curve(plot=False)

    @staticmethod
    def reset_vehicle_IDs():
        CompositeVehicle.next_vehicle_ID = -1

    @staticmethod
    def set_next_vehicle_ID():
        CompositeVehicle.next_vehicle_ID = CompositeVehicle.next_vehicle_ID - 1

    def decompose(self):
        # for v in self.vehicle_list:
        #     print('%s= %f' % (v.vehicle_ID, v.cert_CO2_grams_per_mile))

        for v in self.vehicle_list:
            vehicle_cost_curve = scipy.interpolate.interp1d(self.cost_curve['cert_co2_grams_per_mile'],
                                                            self.cost_curve[
                                                                'veh_%s_cert_co2_grams_per_mile' % v.vehicle_ID],
                                                            fill_value='extrapolate')

            v.cert_CO2_grams_per_mile = vehicle_cost_curve(self.cert_CO2_grams_per_mile)
            v.initial_registered_count = self.initial_registered_count * v.reg_class_market_share_frac
            v.set_new_vehicle_mfr_cost_dollars()  # varies by model_year and cert_CO2_grams_per_mile
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

        composite_cloud_df = pd.DataFrame()
        composite_cloud_df['cert_co2_grams_per_mile'] = [0]
        composite_cloud_df['new_vehicle_mfr_cost_dollars'] = [0]
        for v in self.vehicle_list:
            vehicle_frontier = v.create_frontier_df()

            if plot:
                ax1.plot(vehicle_frontier.iloc[:, 0], vehicle_frontier.iloc[:, 1], '.-')

            vehicle_frontier['veh_%d_market_share' % v.vehicle_ID] = v.reg_class_market_share_frac
            composite_cloud_df = cartesian_prod(composite_cloud_df, vehicle_frontier, drop=False)

            composite_cloud_df['cert_co2_grams_per_mile'] = composite_cloud_df['cert_co2_grams_per_mile'] + \
                                                      composite_cloud_df['veh_%d_cert_co2_grams_per_mile' % v.vehicle_ID] * \
                                                      composite_cloud_df['veh_%d_market_share' % v.vehicle_ID]

            composite_cloud_df['new_vehicle_mfr_cost_dollars'] = composite_cloud_df['new_vehicle_mfr_cost_dollars'] + \
                                                          composite_cloud_df[
                                                              'veh_%s_mfr_cost_dollars' % v.vehicle_ID] * \
                                                          composite_cloud_df['veh_%s_market_share' % v.vehicle_ID]

        cost_curve = CostCloud.calculate_frontier(composite_cloud_df, 'cert_co2_grams_per_mile',
                                            'new_vehicle_mfr_cost_dollars')

        if plot:
            ax1.plot(cost_curve['cert_co2_grams_per_mile'], cost_curve['new_vehicle_mfr_cost_dollars'], '.-')

        return cost_curve

    def get_cost(self, target_co2_gpmi):
        # get cost from cost curve for target_co2_gpmi(s)
        cost_dollars = scipy.interpolate.interp1d(self.cost_curve['cert_co2_grams_per_mile'],
                                                  self.cost_curve['new_vehicle_mfr_cost_dollars'],
                                                  fill_value='extrapolate')

        return cost_dollars(target_co2_gpmi).tolist()

    def get_max_co2_gpmi(self):
        # get max co2_gpmi from self.cost_curve
        return self.cost_curve['cert_co2_grams_per_mile'].max()

    def get_min_co2_gpmi(self):
        # get min co2_gpmi from self.cost_curve
        return self.cost_curve['cert_co2_grams_per_mile'].min()

    def set_new_vehicle_mfr_cost_dollars(self):
        from omega_functions import weighted_value
        self.new_vehicle_mfr_cost_dollars = weighted_value(self.vehicle_list, 'initial_registered_count', 'new_vehicle_mfr_cost_dollars')
        return self.new_vehicle_mfr_cost_dollars

    def set_cert_target_CO2_Mg(self):
        from omega_functions import weighted_value
        self.cert_target_CO2_Mg = weighted_value(self.vehicle_list, 'initial_registered_count', 'cert_target_CO2_Mg')
        return self.cert_target_CO2_Mg

    def set_cert_CO2_Mg(self):
        from omega_functions import weighted_value
        self.cert_CO2_Mg = weighted_value(self.vehicle_list, 'initial_registered_count', 'cert_CO2_Mg')
        return self.cert_CO2_Mg


class VehicleBase(o2.OmegaBase):
    next_vehicle_ID = 0

    name = ''
    manufacturer_ID = None

    model_year = None
    fueling_class = None
    hauling_class = None
    cost_curve_class = None
    reg_class_ID = None
    cert_CO2_grams_per_mile = None
    cert_target_CO2_grams_per_mile = None
    cert_CO2_Mg = None
    cert_target_CO2_Mg = None
    new_vehicle_mfr_cost_dollars = None
    manufacturer_deemed_new_vehicle_generalized_cost_dollars = None
    in_use_fuel_ID = None
    # TODO: cert_fuel_ID = Column('cert_fuel_id', String, ForeignKey('ghg_standard_fuels.fuel_id'))
    market_class_ID = None
    footprint_ft2 = None
    reg_class_market_share_frac = 1.0
    _initial_registered_count = 0

    def __init__(self):
        self.vehicle_ID = VehicleBase.next_vehicle_ID
        VehicleBase.set_next_vehicle_ID()

    @staticmethod
    def reset_vehicle_IDs():
        VehicleBase.next_vehicle_ID = 0

    @staticmethod
    def set_next_vehicle_ID():
        VehicleBase.next_vehicle_ID = VehicleBase.next_vehicle_ID + 1

    @property
    def initial_registered_count(self):
        return self._initial_registered_count

    @initial_registered_count.setter
    def initial_registered_count(self, initial_registered_count):
        self._initial_registered_count = initial_registered_count

    def set_cert_target_CO2_grams_per_mile(self):
        self.cert_target_CO2_grams_per_mile = o2.options.GHG_standard.calculate_target_co2_gpmi(self)

    def set_cert_target_CO2_Mg(self):
        self.cert_target_CO2_Mg = o2.options.GHG_standard.calculate_target_co2_Mg(self)

    def set_new_vehicle_mfr_cost_dollars(self):
        from cost_curves import CostCurve
        self.new_vehicle_mfr_cost_dollars = CostCurve.get_cost(cost_curve_class=self.cost_curve_class,
                                                               model_year=self.model_year,
                                                               target_co2_gpmi=self.cert_CO2_grams_per_mile)

    def get_cost(self, target_co2_gpmi):
        from cost_curves import CostCurve
        # get cost from cost curve for target_co2_gpmi(s)
        cost_dollars = CostCurve.get_cost(cost_curve_class=self.cost_curve_class,
                                          model_year=self.model_year,
                                          target_co2_gpmi=target_co2_gpmi)

        return cost_dollars

    def get_max_co2_gpmi(self):
        from cost_curves import CostCurve
        # get max co2_gpmi from self.cost_curve
        return CostCurve.get_max_co2_gpmi(self.cost_curve_class, self.model_year)

    def get_min_co2_gpmi(self):
        from cost_curves import CostCurve
        # get min co2_gpmi from self.cost_curve
        return CostCurve.get_min_co2_gpmi(self.cost_curve_class, self.model_year)

    def set_cert_CO2_Mg(self):
        self.cert_CO2_Mg = o2.options.GHG_standard.calculate_cert_co2_Mg(self)

    def inherit_vehicle(self, vehicle, model_year=None):
        inherit_properties = {'name', 'manufacturer_ID', 'model_year', 'fueling_class', 'hauling_class',
                              'cost_curve_class', 'reg_class_ID', 'in_use_fuel_ID', 'market_class_ID',
                              'footprint_ft2'}

        for p in inherit_properties:
            self.__setattr__(p, vehicle.__getattribute__(p))

        if model_year:
            self.model_year = model_year

        self.set_cert_target_CO2_grams_per_mile()  # varies by model year
        self.initial_registered_count = vehicle.initial_registered_count
        self.cert_CO2_grams_per_mile = vehicle.cert_CO2_grams_per_mile
        self.set_new_vehicle_mfr_cost_dollars()  # varies by model_year and cert_CO2_grams_per_mile
        self.set_cert_target_CO2_Mg()  # varies by model year and initial_registered_count
        self.set_cert_CO2_Mg()  # varies by model year and initial_registered_count

    def create_frontier_df(self):
        from cost_curves import CostCurve
        df = pd.DataFrame()

        df['veh_%s_cert_co2_grams_per_mile' % self.vehicle_ID] = \
            CostCurve.get_co2_gpmi(self.cost_curve_class, self.model_year)

        df['veh_%s_mfr_cost_dollars' % self.vehicle_ID] = \
            CostCurve.get_cost(self.cost_curve_class, self.model_year, df['veh_%s_cert_co2_grams_per_mile' % self.vehicle_ID])

        return df


class Vehicle(SQABase, VehicleBase):
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
    cert_target_CO2_grams_per_mile = Column('cert_target_co2_grams_per_mile', Float)
    cert_CO2_Mg = Column('cert_co2_megagrams', Float)
    cert_target_CO2_Mg = Column('cert_target_co2_megagrams', Float)
    new_vehicle_mfr_cost_dollars = Column(Float)
    manufacturer_deemed_new_vehicle_generalized_cost_dollars = Column(Float)
    in_use_fuel_ID = Column('showroom_fuel_id', String, ForeignKey('fuels.fuel_id'))
    # TODO: cert_fuel_ID = Column('cert_fuel_id', String, ForeignKey('ghg_standard_fuels.fuel_id'))
    market_class_ID = Column('market_class_id', String, ForeignKey('market_classes.market_class_id'))
    footprint_ft2 = Column(Float)
    cert_CO2_grams_per_mile = Column('cert_co2_grams_per_mile', Float)

    @property
    def initial_registered_count(self):
        from vehicle_annual_data import VehicleAnnualData
        return VehicleAnnualData.get_registered_count(vehicle_ID=self.vehicle_ID, age=0)

    @initial_registered_count.setter
    def initial_registered_count(self, initial_registered_count):
        from vehicle_annual_data import VehicleAnnualData

        o2.session.add(self)  # update database so vehicle_annual_data foreign key succeeds...
        o2.session.flush()

        VehicleAnnualData.update_registered_count(self,
                                                  calendar_year=self.model_year,
                                                  registered_count=initial_registered_count)

    @staticmethod
    def init_database_from_file(filename, verbose=False):
        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_name = 'vehicles'
        input_template_version = 0.0005
        input_template_columns = {'vehicle_id', 'manufacturer_id', 'model_year', 'reg_class_id', 'hauling_class',
                                  'cost_curve_class', 'in_use_fuel_id', 'cert_fuel_id', 'market_class_id',
                                  'sales', 'cert_co2_grams_per_mile', 'footprint_ft2'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version, verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                # load data into database
                for i in df.index:
                    veh = Vehicle(
                        name=df.loc[i, 'vehicle_id'],
                        manufacturer_ID=df.loc[i, 'manufacturer_id'],
                        model_year=df.loc[i, 'model_year'],
                        reg_class_ID=df.loc[i, 'reg_class_id'],
                        hauling_class=df.loc[i, 'hauling_class'],
                        cost_curve_class=df.loc[i, 'cost_curve_class'],
                        in_use_fuel_ID=df.loc[i, 'in_use_fuel_id'],
                        market_class_ID=df.loc[i, 'market_class_id'],
                        footprint_ft2=df.loc[i, 'footprint_ft2'],
                    )

                    if 'BEV' in veh.market_class_ID:
                        veh.fueling_class = 'BEV'
                    else:
                        veh.fueling_class = 'ICE'

                    veh.cert_CO2_grams_per_mile = df.loc[i, 'cert_co2_grams_per_mile']
                    veh.initial_registered_count = df.loc[i, 'sales']
                    veh.set_new_vehicle_mfr_cost_dollars()
                    veh.set_cert_target_CO2_grams_per_mile()
                    veh.set_cert_target_CO2_Mg()
                    veh.set_cert_CO2_Mg()

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

        from omega_functions import weighted_value, unweighted_value

        from manufacturers import Manufacturer  # needed for manufacturers table
        from market_classes import MarketClass  # needed for market class ID
        from fuels import Fuel  # needed for showroom fuel ID
        # from vehicles import Vehicle
        from vehicle_annual_data import VehicleAnnualData

        if o2.options.GHG_standard == 'flat':
            from GHG_standards_flat import GHGStandardFlat
        else:
            from GHG_standards_footprint import GHGStandardFootprint

        if o2.options.cost_file_type == 'curves':
            from cost_curves import CostCurve  # needed for vehicle cost from CO2
        else:
            from cost_clouds import CostCloud  # needed for vehicle cost from CO2

        SQABase.metadata.create_all(o2.engine)

        init_fail = []
        init_fail = init_fail + Manufacturer.init_database_from_file(o2.options.manufacturers_file,
                                                                     verbose=o2.options.verbose)
        init_fail = init_fail + MarketClass.init_database_from_file(o2.options.market_classes_file,
                                                                    verbose=o2.options.verbose)
        init_fail = init_fail + Fuel.init_database_from_file(o2.options.fuels_file, verbose=o2.options.verbose)

        if o2.options.cost_file_type == 'curves':
            init_fail = init_fail + CostCurve.init_database_from_file(o2.options.cost_file, verbose=o2.options.verbose)
        else:
            init_fail = init_fail + CostCloud.init_database_from_file(o2.options.cost_file, verbose=o2.options.verbose)

        if o2.options.GHG_standard == 'flat':
            init_fail = init_fail + GHGStandardFlat.init_database_from_file(o2.options.ghg_standards_file,
                                                                            verbose=o2.options.verbose)
            o2.options.GHG_standard = GHGStandardFlat
        else:
            init_fail = init_fail + GHGStandardFootprint.init_database_from_file(o2.options.ghg_standards_file,
                                                                                 verbose=o2.options.verbose)
            o2.options.GHG_standard = GHGStandardFootprint

        init_fail = init_fail + Vehicle.init_database_from_file(o2.options.vehicles_file, verbose=o2.options.verbose)

        if not init_fail:
            dump_omega_db_to_csv(o2.options.database_dump_folder)

            vehicles_list = o2.session.query(Vehicle). \
                filter(Vehicle.manufacturer_ID == 'USA Motors'). \
                filter(Vehicle.model_year == 2020). \
                all()

            weighted_mfr_cost_dollars = weighted_value(vehicles_list, 'initial_registered_count',
                                                       'new_vehicle_mfr_cost_dollars')
            weighted_co2gpmi = weighted_value(vehicles_list, 'initial_registered_count', 'cert_CO2_grams_per_mile')
            weighted_footprint = weighted_value(vehicles_list, 'initial_registered_count', 'footprint_ft2')

            print(vehicles_list[0].new_vehicle_mfr_cost_dollars - unweighted_value(vehicles_list[0],
                                                                                   weighted_mfr_cost_dollars,
                                                                                   vehicles_list,
                                                                                   'initial_registered_count',
                                                                                   'new_vehicle_mfr_cost_dollars'))
            print(vehicles_list[1].new_vehicle_mfr_cost_dollars - unweighted_value(vehicles_list[1],
                                                                                   weighted_mfr_cost_dollars,
                                                                                   vehicles_list,
                                                                                   'initial_registered_count',
                                                                                   'new_vehicle_mfr_cost_dollars'))

            print(vehicles_list[0].cert_CO2_grams_per_mile == unweighted_value(vehicles_list[0], weighted_co2gpmi,
                                                                               vehicles_list,
                                                                               'initial_registered_count',
                                                                               'cert_CO2_grams_per_mile'))
            print(vehicles_list[1].cert_CO2_grams_per_mile == unweighted_value(vehicles_list[1], weighted_co2gpmi,
                                                                               vehicles_list,
                                                                               'initial_registered_count',
                                                                               'cert_CO2_grams_per_mile'))

            print(
                vehicles_list[2].footprint_ft2 == unweighted_value(vehicles_list[2], weighted_footprint, vehicles_list,
                                                                   'initial_registered_count', 'footprint_ft2'))
            print(
                vehicles_list[3].footprint_ft2 == unweighted_value(vehicles_list[3], weighted_footprint, vehicles_list,
                                                                   'initial_registered_count', 'footprint_ft2'))

            base_vehicles_list = []
            for v in vehicles_list:
                vb = VehicleBase()
                vb.inherit_vehicle(v)
                base_vehicles_list.append(vb)

            cv = CompositeVehicle(base_vehicles_list)
            print(cv)

            cv.cost_curve.to_csv('combined_frontier.csv', index=False)

            cv.decompose()  # update cv.vehicle_list vehicles

            cv2 = CompositeVehicle(cv.vehicle_list)
            cv2.decompose()
            print(cv2)

            cv3 = CompositeVehicle(cv2.vehicle_list)
            cv3.decompose()
            print(cv3)

        else:
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)

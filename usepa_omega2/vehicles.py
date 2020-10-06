"""
vehicles.py
===========


"""

print('importing %s' % __file__)

import o2  # import global variables
from usepa_omega2 import *


def sales_weight(vehicle_list, attribute_name):
    """

    :param vehicle_list:
    :param attribute_name:
    :return:
    """
    weighted_sum = 0
    total_sales = 0
    for v in vehicle_list:
        sales = v.get_initial_registered_count()
        total_sales = total_sales + sales
        weighted_sum = weighted_sum + v.__getattribute__(attribute_name) * sales

    return weighted_sum / total_sales


def sales_unweight(veh, vehicle_list, attribute_name, weighted_value):
    """

    :param veh:
    :param vehicle_list:
    :param attribute_name:
    :param weighted_value:
    :return:
    """
    total_sales = 0
    weighted_sum = 0
    for v in vehicle_list:
        sales = v.get_initial_registered_count()
        total_sales = total_sales + sales
        if v is not veh:
            weighted_sum = weighted_sum + v.__getattribute__(attribute_name) * sales

    return (weighted_value * total_sales - weighted_sum) / veh.get_initial_registered_count()


class CompositeVehicle:
    composite_vehicle_num = 0

    def __init__(self, vehicle_list):
        """
        Build composite vehicle from list of vehicles
        :param vehicle_list: list of vehicles (must be of same reg_class, market class, fueling_class)
        """
        self.vehicle_list = vehicle_list
        self.name = 'composite vehicle (%s.%s)' % (self.vehicle_list[0].market_class_ID, self.vehicle_list[0].reg_class_ID)

        self.vehicle_ID = 'CV%d' % CompositeVehicle.composite_vehicle_num
        CompositeVehicle.composite_vehicle_num = CompositeVehicle.composite_vehicle_num + 1

        self.model_year = self.vehicle_list[0].model_year
        self.reg_class_ID = self.vehicle_list[0].reg_class_ID
        self.fueling_class = self.vehicle_list[0].fueling_class

        # calc sales-weighted values
        self.cert_CO2_grams_per_mile = sales_weight(self.vehicle_list, 'cert_CO2_grams_per_mile')
        self.footprint_ft2 = sales_weight(self.vehicle_list, 'footprint_ft2')
        self.new_vehicle_mfr_cost_dollars = sales_weight(self.vehicle_list, 'new_vehicle_mfr_cost_dollars')
        self.cost_curve = None  # TODO: calc sales weighted cost curve here, based on cost_curve classes and model_year

        total_sales = 0
        for v in self.vehicle_list:
            total_sales = total_sales = v.get_initial_registered_count()

        for v in self.vehicle_list:
            v.reg_class_market_share_frac = v.get_initial_registered_count() / total_sales

    def __repr__(self):
        return "<OMEGA2 %s object at 0x%x>" % (type(self).__name__,  id(self))

    def __str__(self):
        s = ''
        for k in self.__dict__:
            s = s + k + ' = ' + str(self.__dict__[k]) + '\n'
        return s

    def get_cost(self, target_co2_gpmi):
        # get cost from cost curve for target_co2_gpmi(s)
        pass

    def get_max_co2_gpmi(self):
        # get max co2_gpmi from self.cost_curve
        pass

    def get_min_co2_gpmi(self):
        # get min co2_gpmi from self.cost_curve
        pass


class Vehicle(SQABase):
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
    cert_CO2_grams_per_mile = Column('cert_co2_grams_per_mile', Float)
    cert_target_CO2_grams_per_mile = Column('cert_target_co2_grams_per_mile', Float)
    cert_CO2_Mg = Column('cert_co2_megagrams', Float)
    cert_target_CO2_Mg = Column('cert_target_co2_megagrams', Float)
    new_vehicle_mfr_cost_dollars = Column(Float)
    manufacturer_deemed_new_vehicle_generalized_cost_dollars = Column(Float)
    in_use_fuel_ID = Column('showroom_fuel_id', String, ForeignKey('fuels.fuel_id'))
    # TODO: cert_fuel_ID = Column('cert_fuel_id', String, ForeignKey('ghg_standard_fuels.fuel_id'))
    market_class_ID = Column('market_class_id', String, ForeignKey('market_classes.market_class_id'))
    footprint_ft2 = Column(Float)
    reg_class_market_share_frac = 1.0

    def __repr__(self):
        return "<OMEGA2 %s object at 0x%x>" % (type(self).__name__,  id(self))

    def __str__(self):
        s = ''
        for k in self.__dict__:
            s = s + k + ' = ' + str(self.__dict__[k]) + '\n'
        return s

    def set_cert_target_CO2_grams_per_mile(self):
        self.cert_target_CO2_grams_per_mile = o2.options.GHG_standard.calculate_target_co2_gpmi(self)

    def set_cert_target_CO2_Mg(self):
        self.cert_target_CO2_Mg = o2.options.GHG_standard.calculate_target_co2_Mg(self)

    def set_cert_co2_grams_per_mile(self, cert_co2_grams_per_mile):
        from cost_curves import CostCurve
        self.cert_CO2_grams_per_mile = cert_co2_grams_per_mile
        self.new_vehicle_mfr_cost_dollars = CostCurve.get_cost(cost_curve_class=self.cost_curve_class,
                                                              model_year=self.model_year,
                                                              target_co2_gpmi=self.cert_CO2_grams_per_mile)

    def set_cert_CO2_Mg(self):
        self.cert_CO2_Mg = o2.options.GHG_standard.calculate_cert_co2_Mg(self)

    def set_initial_registered_count(self, sales):
        from vehicle_annual_data import VehicleAnnualData

        o2.session.add(self)  # update database so vehicle_annual_data foreign key succeeds...
        o2.session.flush()

        VehicleAnnualData.update_registered_count(self,
                                                  calendar_year=self.model_year,
                                                  registered_count=sales)

    def get_initial_registered_count(self):
        from vehicle_annual_data import VehicleAnnualData

        return VehicleAnnualData.get_registered_count(vehicle_ID=self.vehicle_ID, age=0)

    def inherit_vehicle(self, vehicle):
        inherit_properties = {'name', 'manufacturer', 'manufacturer_ID', 'model_year', 'fueling_class', 'hauling_class',
                              'cost_curve_class', 'reg_class_ID', 'in_use_fuel_ID', 'market_class_ID',
                              'cert_CO2_grams_per_mile', 'footprint_ft2'}
        for p in inherit_properties:
            self.__setattr__(p, vehicle.__getattribute__(p))

    @staticmethod
    def init_database_from_file(filename, verbose=False):
        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_name = 'vehicles'
        input_template_version = 0.0005
        input_template_columns = {'vehicle_id', 'manufacturer_id', 'model_year', 'reg_class_id', 'hauling_class',
                                  'cost_curve_class', 'in_use_fuel_id', 'cert_fuel_id', 'market_class_id', 'sales',
                                  'cert_co2_grams_per_mile', 'footprint_ft2'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version, verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                # obj_list = []
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

                    veh.set_cert_co2_grams_per_mile(df.loc[i, 'cert_co2_grams_per_mile'])
                    # veh.new_vehicle_mfr_cost_dollars = CostCurve.get_cost(cost_curve_class=veh.cost_curve_class,
                    #                                                       model_year=veh.model_year,
                    #                                                       target_co2_gpmi=veh.cert_CO2_grams_per_mile)

                    veh.set_initial_registered_count(df.loc[i, 'sales'])
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
        init_fail = init_fail + Manufacturer.init_database_from_file(o2.options.manufacturers_file, verbose=o2.options.verbose)
        init_fail = init_fail + MarketClass.init_database_from_file(o2.options.market_classes_file, verbose=o2.options.verbose)
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

            weighted_mfr_cost_dollars = sales_weight(vehicles_list, 'new_vehicle_mfr_cost_dollars')
            weighted_co2gpmi = sales_weight(vehicles_list, 'cert_CO2_grams_per_mile')
            weighted_footprint = sales_weight(vehicles_list, 'footprint_ft2')

            print(vehicles_list[0].new_vehicle_mfr_cost_dollars - sales_unweight(vehicles_list[0], vehicles_list,
                                                                             'new_vehicle_mfr_cost_dollars',
                                                                             weighted_mfr_cost_dollars))
            print(vehicles_list[1].new_vehicle_mfr_cost_dollars - sales_unweight(vehicles_list[1], vehicles_list,
                                                                             'new_vehicle_mfr_cost_dollars',
                                                                             weighted_mfr_cost_dollars))

            print(vehicles_list[0].cert_CO2_grams_per_mile == sales_unweight(vehicles_list[0], vehicles_list,
                                                                             'cert_CO2_grams_per_mile',
                                                                             weighted_co2gpmi))
            print(vehicles_list[1].cert_CO2_grams_per_mile == sales_unweight(vehicles_list[1], vehicles_list,
                                                                             'cert_CO2_grams_per_mile',
                                                                             weighted_co2gpmi))

            print(vehicles_list[2].footprint_ft2 == sales_unweight(vehicles_list[2], vehicles_list, 'footprint_ft2',
                                                                   weighted_footprint))
            print(vehicles_list[3].footprint_ft2 == sales_unweight(vehicles_list[3], vehicles_list, 'footprint_ft2',
                                                                   weighted_footprint))
        else:
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)

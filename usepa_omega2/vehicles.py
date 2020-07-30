"""
vehicles.py
===========


"""

from usepa_omega2 import *


class Vehicle(SQABase):
    # --- database table properties ---
    __tablename__ = 'vehicles'
    vehicle_ID = Column('vehicle_id', Integer, primary_key=True)
    name = Column('name', String)
    manufacturer_ID = Column('manufacturer_id', String, ForeignKey('manufacturers.manufacturer_id'))
    manufacturer = relationship('Manufacturer', back_populates='vehicles')

    # --- static properties ---
    # vehicle_nameplate = Column(String, default='USALDV')
    model_year = Column(Numeric)
    fueling_class = Column(Enum(*fueling_classes, validate_strings=True))
    hauling_class = Column(Enum(*hauling_classes, validate_strings=True))
    cost_curve_class = Column(String)  # for now, could be Enum of cost_curve_classes, but those classes would have to be identified and enumerated in the __init.py__...
    # reg_class_ID = Column('reg_class_id', Enum(*reg_classes, validate_strings=True))
    reg_class_ID = Column('reg_class_id', Enum(*list(RegClass.__members__), validate_strings=True))
    cert_CO2_grams_per_mile = Column('cert_co2_grams_per_mile', Float)
    cert_target_CO2_grams_per_mile = Column('cert_target_co2_grams_per_mile', Float)
    cert_CO2_Mg = Column('cert_co2_megagrams', Float)
    cert_target_CO2_Mg = Column('cert_target_co2_megagrams', Float)
    new_vehicle_cost_dollars = Column(Float)
    showroom_fuel_ID = Column('showroom_fuel_id', String, ForeignKey('fuels.fuel_id'))
    market_class_ID = Column('market_class_id', String, ForeignKey('market_classes.market_class_id'))
    footprint_ft2 = Column(Float)

    def __repr__(self):
        return "<OMEGA2 %s object at 0x%x>" % (type(self).__name__,  id(self))

    def __str__(self):
        s = ''  # '"<OMEGA2 %s object at 0x%x>" % (type(self).__name__,  id(self))
        for k in self.__dict__:
            s = s + k + ' = ' + str(self.__dict__[k]) + '\n'
        return s

    def set_cert_target_CO2_grams_per_mile(self):
        self.cert_target_CO2_grams_per_mile = o2_options.GHG_standard.calculate_target_co2_gpmi(self)

    def set_cert_target_CO2_Mg(self):
        self.cert_target_CO2_Mg = o2_options.GHG_standard.calculate_target_co2_Mg(self)

    def set_cert_CO2_Mg(self):
        self.cert_CO2_Mg = o2_options.GHG_standard.calculate_cert_co2_Mg(self)

    def set_initial_registered_count(self, sales):
        from vehicle_annual_data import VehicleAnnualData

        session.add(self)  # update database so vehicle_annual_data foreign key succeeds...
        session.flush()

        VehicleAnnualData.update_registered_count(session, vehicle_ID=self.vehicle_ID,
                                                  calendar_year=self.model_year,
                                                  registered_count=sales)

    def get_initial_registered_count(self):
        from vehicle_annual_data import VehicleAnnualData

        return VehicleAnnualData.get_registered_count(session, vehicle_ID=self.vehicle_ID, age=0)

    def inherit_vehicle(self, vehicle):
        inherit_properties = {'name', 'manufacturer', 'manufacturer_ID', 'model_year', 'fueling_class', 'hauling_class',
                              'cost_curve_class', 'reg_class_ID', 'showroom_fuel_ID', 'market_class_ID',
                              'footprint_ft2'}
        for p in inherit_properties:
            self.__setattr__(p, vehicle.__getattribute__(p))

    @staticmethod
    def init_database_from_file(filename, session, verbose=False):
        from cost_curves import CostCurve


        omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_name = 'vehicles'
        input_template_version = 0.0004
        input_template_columns = {'vehicle_id', 'manufacturer_id', 'model_year', 'reg_class_id', 'hauling_class',
                                  'cost_curve_class', 'showroom_fuel_id', 'market_class_id', 'sales',
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
                        showroom_fuel_ID=df.loc[i, 'showroom_fuel_id'],
                        market_class_ID=df.loc[i, 'market_class_id'],
                        cert_CO2_grams_per_mile=df.loc[i, 'cert_co2_grams_per_mile'],
                        footprint_ft2=df.loc[i, 'footprint_ft2'],
                    )

                    if 'BEV' in veh.market_class_ID:
                        veh.fueling_class = 'BEV'
                    else:
                        veh.fueling_class = 'ICE'

                    veh.new_vehicle_cost_dollars = CostCurve.get_cost(session,
                                                                        cost_curve_class=veh.cost_curve_class,
                                                                        model_year=veh.model_year,
                                                                        target_co2_gpmi=veh.cert_CO2_grams_per_mile)

                    veh.set_initial_registered_count(df.loc[i, 'sales'])
                    veh.set_cert_target_CO2_grams_per_mile()
                    veh.set_cert_target_CO2_Mg()
                    veh.set_cert_CO2_Mg()

        return template_errors


if __name__ == '__main__':
    if '__file__' in locals():
        print(fileio.get_filenameext(__file__))

    from manufacturers import Manufacturer  # needed for manufacturers table
    from market_classes import MarketClass  # needed for market class ID
    from fuels import Fuel  # needed for showroom fuel ID
    from cost_curves import CostCurve  # needed for vehicle cost from CO2
    from cost_clouds import CostCloud  # needed for vehicle cost from CO2

    SQABase.metadata.create_all(engine)

    init_fail = []
    init_fail = init_fail + Manufacturer.init_database_from_file(o2_options.manufacturers_file, session, verbose=o2_options.verbose)
    init_fail = init_fail + MarketClass.init_database_from_file(o2_options.market_classes_file, session, verbose=o2_options.verbose)
    init_fail = init_fail + Fuel.init_database_from_file(o2_options.fuels_file, session, verbose=o2_options.verbose)
    # init_fail = init_fail + CostCloud.init_database_from_file(o2_options.cost_clouds_file, session, verbose=o2_options.verbose)
    init_fail = init_fail + CostCurve.init_database_from_file(o2_options.cost_curves_file, session, verbose=o2_options.verbose)

    init_fail = init_fail + Vehicle.init_database_from_file(o2_options.vehicles_file, session, verbose=o2_options.verbose)

    if not init_fail:
        dump_database_to_csv(engine, o2_options.database_dump_folder, verbose=o2_options.verbose)

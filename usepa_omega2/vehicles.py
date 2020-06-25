"""
vehicles.py
==========


"""

from usepa_omega2 import *


class Vehicle(SQABase):
    # --- database table properties ---
    __tablename__ = 'vehicles'
    index = Column('index', Integer, primary_key=True)
    vehicle_ID = Column('vehicle_id', String)
    manufacturer_ID = Column('manufacturer_id', String, ForeignKey('manufacturers.manufacturer_id'))
    manufacturer = relationship('Manufacturer', back_populates='vehicles')

    # --- static properties ---
    # vehicle_nameplate = Column(String, default='USALDV')
    model_year = Column(Numeric)
    # fueling_class = Column(Enum(*fueling_classes, validate_strings=True))
    hauling_class = Column(Enum(*hauling_classes, validate_strings=True))
    cost_curve_class = Column(String)  # for now, could be Enum of cost_curve_classes, but those classes would have to be identified and enumerated in the __init.py__...
    reg_class_ID = Column('reg_class_id', Enum(*reg_classes, validate_strings=True))
    cert_CO2_grams_per_mile = Column('cert_co2_grams_per_mile', Float)
    cost_dollars = Column(Float)
    showroom_fuel_ID = Column('showroom_fuel_id', String, ForeignKey('fuels.fuel_id'))
    market_class_ID = Column('market_class_id', String, ForeignKey('market_classes.market_class_id'))

    def __repr__(self):
        return "<OMEGA2 %s object at 0x%x>" % (type(self).__name__,  id(self))

    def __str__(self):
        s = ''  # '"<OMEGA2 %s object at 0x%x>" % (type(self).__name__,  id(self))
        for k in self.__dict__:
            s = s + k + ' = ' + str(self.__dict__[k]) + '\n'
        return s

    def init_database(filename, session, verbose=False):
        print('\nInitializing database from %s...' % filename)

        input_template_name = 'vehicles'
        input_template_version = 0.0002
        input_template_columns = {'vehicle_id', 'manufacturer_id', 'model_year', 'reg_class_id', 'hauling_class',
                                  'cost_curve_class', 'showroom_fuel_id', 'market_class_id', 'sales'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version, verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                obj_list = []
                # load data into database
                for i in df.index:
                    obj_list.append(Vehicle(
                        vehicle_ID=df.loc[i, 'vehicle_id'],
                        manufacturer_ID=df.loc[i, 'manufacturer_id'],
                        model_year=df.loc[i, 'model_year'],
                        reg_class_ID=df.loc[i, 'reg_class_id'],
                        hauling_class=df.loc[i, 'hauling_class'],
                        cost_curve_class=df.loc[i, 'cost_curve_class'],
                        showroom_fuel_ID=df.loc[i, 'showroom_fuel_id'],
                        market_class_ID=df.loc[i, 'market_class_id'],
                    ))
                    # TODO: fueling_class??
                    # TODO: cost_dollars = lookup from cost curve based on CO2 and cost_curve class...
                    # TODO: vehicle_ID=df.loc[i, 'sales'], # need to create age 0 entry in vehicle annual data...
                session.add_all(obj_list)
                session.flush()

        return template_errors


if __name__ == '__main__':
    if '__file__' in locals():
        print(fileio.get_filenameext(__file__))

    from manufacturers import *  # needed for manufacturers table
    from market_classes import *  # needed for market class ID
    from fuels import *  # needed for showroom fuel ID

    SQABase.metadata.create_all(engine)

    init_fail = []
    init_fail = init_fail + Manufacturer.init_database(o2_options.manufacturers_file, session, verbose=o2_options.verbose)
    init_fail = init_fail + MarketClass.init_database(o2_options.market_classes_file, session, verbose=o2_options.verbose)
    init_fail = init_fail + Fuel.init_database(o2_options.fuels_file, session, verbose=o2_options.verbose)

    init_fail = init_fail + Vehicle.init_database(o2_options.vehicles_file, session, verbose=o2_options.verbose)

    if not init_fail:
        dump_database_to_csv(engine, o2_options.database_dump_folder, verbose=o2_options.verbose)

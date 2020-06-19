"""
vehicles.py
==========


"""

from usepa_omega2 import *


class Vehicle(SQABase):
    # --- database table properties ---
    __tablename__ = 'vehicles'
    vehicle_ID = Column('vehicle_id', Integer, primary_key=True)
    manufacturer_ID = Column('manufacturer_id', Integer, ForeignKey('manufacturers.manufacturer_id'))

    # --- static properties ---
    vehicle_nameplate = Column(String, default='USALDV')
    model_year = Column(Integer)
    fueling_class = Column(Enum(*fueling_classes, validate_strings=True))
    hauling_class = Column(Enum(*hauling_classes, validate_strings=True))
    cost_curve_class = Column(String)  # for now, could be Enum of cost_curve_classes, but those classes would have to be identified and enumerated in the __init.py__...
    reg_class_ID = Column('reg_class_id', Enum(*reg_classes, validate_strings=True))
    cert_CO2_grams_per_mile = Column('cert_co2_grams_per_mile', Float)
    cost_dollars = Column(Float)
    showroom_fuel_ID = Column('showroom_fuel_id', Integer, ForeignKey('fuels.fuel_id'))
    market_class_ID = Column('market_class_id', Integer, ForeignKey('market_classes.market_class_id'))

    def __repr__(self):
        s = '\n<vehicle.Vehicle object at %#x>' % id(self)
        for k in ['VIN', 'nameplate', 'powertrain_efficiency_norm']:
            s = s + ', '
            s = s + k + ' = ' + str(self.__dict__[k])
        return s

    def __str__(self):
        s = '\n<vehicle.Vehicle object at %#x>\n' % id(self)
        for k in self.__dict__:
            s = s + k + ' = ' + str(self.__dict__[k]) + '\n'
        return s


if __name__ == '__main__':
    print(fileio.get_filenameext(__file__))

    from manufacturers import *  # needed for manufacturers table
    from market_classes import *  # needed for market class ID
    from fuels import *  # needed for showroom fuel ID

    session = Session(bind=engine)
    SQABase.metadata.create_all(engine)

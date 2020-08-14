"""
vehicle_annual_data.py
======================


"""

import o2  # import global variables
from usepa_omega2 import *


class VehicleAnnualData(SQABase):
    # --- database table properties ---
    __tablename__ = 'vehicle_annual_data'
    index = Column('index', Integer, primary_key=True)
    vehicle_ID = Column('vehicle_id', Integer, ForeignKey('vehicles.vehicle_id'))
    calendar_year = Column(Numeric)
    registered_count = Column(Numeric)
    annual_vmt = Column(Numeric)
    vmt = Column(Numeric)
    age = Column(Numeric)

    def update_registered_count(vehicle_ID, calendar_year, registered_count):
        from vehicles import Vehicle

        age = calendar_year - o2.session.query(Vehicle.model_year).filter(Vehicle.vehicle_ID == vehicle_ID).scalar()

        o2.session.add(VehicleAnnualData(vehicle_ID=vehicle_ID,
                                      calendar_year=calendar_year,
                                      registered_count=registered_count,
                                      age=age))
        o2.session.flush()

    def get_registered_count(vehicle_ID, age):
        return float(o2.session.query(VehicleAnnualData.registered_count). \
            filter(VehicleAnnualData.vehicle_ID==vehicle_ID). \
            filter(VehicleAnnualData.age==age).scalar())

    def insert_vmt(vehicle_ID, calendar_year, annual_vmt):
        vmt = o2.session.query(VehicleAnnualData.registered_count).\
            filter(VehicleAnnualData.vehicle_ID==vehicle_ID).\
            filter(VehicleAnnualData.calendar_year==calendar_year).scalar() * annual_vmt
        veh = o2.session.query(VehicleAnnualData).\
            filter(VehicleAnnualData.vehicle_ID==vehicle_ID).\
            filter(VehicleAnnualData.calendar_year==calendar_year).all()
        veh[0].annual_vmt = annual_vmt
        veh[0].vmt = vmt


if __name__ == '__main__':
    if '__file__' in locals():
        print(fileio.get_filenameext(__file__))

    # set up global variables:
    o2.options = OMEGARuntimeOptions()
    (o2.engine, o2.session) = init_db()

    from manufacturers import Manufacturer  # required by vehicles
    from fuels import Fuel  # required by vehicles
    from market_classes import MarketClass  # required by vehicles
    from vehicles import Vehicle  # for foreign key vehicle_ID

    SQABase.metadata.create_all(o2.engine)

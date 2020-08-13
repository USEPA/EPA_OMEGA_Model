"""
vehicle_annual_data.py
======================


"""

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

    def update_registered_count(session, vehicle_ID, calendar_year, registered_count):
        from vehicles import Vehicle

        age = calendar_year - session.query(Vehicle.model_year).filter(Vehicle.vehicle_ID == vehicle_ID).scalar()

        session.add(VehicleAnnualData(vehicle_ID=vehicle_ID,
                                      calendar_year=calendar_year,
                                      registered_count=registered_count,
                                      age=age))
        session.flush()

    def get_registered_count(session, vehicle_ID, age):
        from vehicles import Vehicle

        return float(session.query(VehicleAnnualData.registered_count).\
            filter(VehicleAnnualData.vehicle_ID==vehicle_ID).\
            filter(VehicleAnnualData.age==age).scalar())

    def insert_vmt(session, vehicle_ID, calendar_year, annual_vmt):
        vmt = session.query(VehicleAnnualData.registered_count).\
            filter(VehicleAnnualData.vehicle_ID==vehicle_ID).\
            filter(VehicleAnnualData.calendar_year==calendar_year).scalar() * annual_vmt
        veh = session.query(VehicleAnnualData).\
            filter(VehicleAnnualData.vehicle_ID==vehicle_ID).\
            filter(VehicleAnnualData.calendar_year==calendar_year).all()
        veh[0].annual_vmt = annual_vmt
        veh[0].vmt = vmt


if __name__ == '__main__':
    if '__file__' in locals():
        print(fileio.get_filenameext(__file__))

    from manufacturers import Manufacturer  # required by vehicles
    from fuels import Fuel  # required by vehicles
    from market_classes import MarketClass  # required by vehicles
    from vehicles import Vehicle  # for foreign key vehicle_ID

    session = Session(bind=engine)
    SQABase.metadata.create_all(engine)

"""
vehicle_annual_data.py
======================


"""

print('importing %s' % __file__)

import o2  # import global variables
from usepa_omega2 import *


class VehicleAnnualData(SQABase, OmegaBase):
    # --- database table properties ---
    __tablename__ = 'vehicle_annual_data'
    index = Column('index', Integer, primary_key=True)
    vehicle_ID = Column('vehicle_id', Integer, ForeignKey('vehicles.vehicle_id'))
    calendar_year = Column(Numeric)
    registered_count = Column(Numeric)
    annual_vmt = Column(Numeric)
    vmt = Column(Numeric)
    age = Column(Numeric)


    @staticmethod
    def update_registered_count(vehicle, calendar_year, registered_count):
        """
        Update vehicle registered count and / or create initial vehicle annual data table entry
        :param vehicle:  VehicleFinal object
        :param calendar_year: calendar year
        :param registered_count: number of vehicle that are still in service (registered)
        :return: updates vehicle annual data table
        """
        age = calendar_year - vehicle.model_year

        vad = o2.session.query(VehicleAnnualData). \
            filter(VehicleAnnualData.vehicle_ID == vehicle.vehicle_ID). \
            filter(VehicleAnnualData.calendar_year == calendar_year). \
            filter(VehicleAnnualData.age == age).one_or_none()

        if vad:
            vad.registered_count=registered_count
        else:
            o2.session.add(VehicleAnnualData(vehicle_ID=vehicle.vehicle_ID,
                                         calendar_year=calendar_year,
                                         registered_count=registered_count,
                                         age=age))

        o2.session.flush()

    @staticmethod
    def update_vehicle_annual_data(vehicle, calendar_year, attribute, attribute_value):

        age = calendar_year - vehicle.model_year

        vad = o2.session.query(VehicleAnnualData). \
            filter(VehicleAnnualData.vehicle_ID == vehicle.vehicle_ID). \
            filter(VehicleAnnualData.calendar_year == calendar_year). \
            filter(VehicleAnnualData.age == age).one()

        vad.__setattr__(attribute, attribute_value)

        o2.session.flush()

    @staticmethod
    def get_registered_count(vehicle_ID, age):
        return float(o2.session.query(VehicleAnnualData.registered_count). \
            filter(VehicleAnnualData.vehicle_ID==vehicle_ID). \
            filter(VehicleAnnualData.age==age).scalar())

    @staticmethod
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
    try:
        if '__file__' in locals():
            print(fileio.get_filenameext(__file__))

        # set up global variables:
        o2.options = OMEGARuntimeOptions()
        init_omega_db()

        from manufacturers import Manufacturer  # required by vehicles
        from fuels import Fuel  # required by vehicles
        from market_classes import MarketClass  # required by vehicles
        from vehicles import VehicleFinal  # for foreign key vehicle_ID

        SQABase.metadata.create_all(o2.engine)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)

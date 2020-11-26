"""
vehicle_annual_data.py
======================


"""

print('importing %s' % __file__)

import o2  # import global variables
from usepa_omega2 import *


class VehicleAnnualData(SQABase, OMEGABase):
    # --- database table properties ---
    __tablename__ = 'vehicle_annual_data'
    index = Column('index', Integer, primary_key=True)
    vehicle_ID = Column('vehicle_id', Integer, ForeignKey('vehicles.vehicle_id'))
    calendar_year = Column(Numeric)
    registered_count = Column(Numeric)
    annual_vmt = Column(Float)
    vmt = Column(Float)
    age = Column(Numeric)
    onroad_co2_grams_per_mile = Column(Float)
    onroad_fuel_consumption_rate = Column(Float)
    fuel_consumption = Column(Float)
    voc_vehicle_ustons = Column(Float)
    co_vehicle_ustons = Column(Float)
    nox_vehicle_ustons = Column(Float)
    pm25_vehicle_ustons = Column(Float)
    sox_vehicle_ustons = Column(Float)
    benzene_vehicle_ustons = Column(Float)
    butadiene13_vehicle_ustons = Column(Float)
    formaldehyde_vehicle_ustons = Column(Float)
    acetaldehyde_vehicle_ustons = Column(Float)
    acrolein_vehicle_ustons = Column(Float)
    ch4_vehicle_metrictons = Column(Float)
    n2o_vehicle_metrictons = Column(Float)
    co2_vehicle_metrictons = Column(Float)
    voc_upstream_ustons = Column(Float)
    co_upstream_ustons = Column(Float)
    nox_upstream_ustons = Column(Float)
    pm25_upstream_ustons = Column(Float)
    sox_upstream_ustons = Column(Float)
    benzene_upstream_ustons = Column(Float)
    butadiene13_upstream_ustons = Column(Float)
    formaldehyde_upstream_ustons = Column(Float)
    acetaldehyde_upstream_ustons = Column(Float)
    acrolein_upstream_ustons = Column(Float)
    naphthalene_upstream_ustons = Column(Float)
    ch4_upstream_metrictons = Column(Float)
    n2o_upstream_metrictons = Column(Float)
    co2_upstream_metrictons = Column(Float)


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
        vad = o2.session.query(VehicleAnnualData).\
            filter(VehicleAnnualData.vehicle_ID==vehicle_ID).\
            filter(VehicleAnnualData.calendar_year==calendar_year).all()
        vad[0].annual_vmt = annual_vmt
        vad[0].vmt = vmt


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

"""
manufacturer_annual_data.py
===========================


"""

from usepa_omega2 import *


class ManufacturerAnnualData(SQABase):
    # --- database table properties ---
    __tablename__ = 'manufacturer_annual_data'
    index = Column('index', Integer, primary_key=True)
    manufacturer_ID = Column('manufacturer_id', Integer, ForeignKey('manufacturers.manufacturer_id'))
    calendar_year = Column(Numeric)
    cert_co2_Mg = Column('cert_co2_megagrams', Numeric)
    cert_target_co2_Mg = Column('cert_target_co2_megagrams', Numeric)
    manufacturer_vehicle_cost_dollars = Column('manufacturer_vehicle_cost_dollars', Numeric)

    @staticmethod
    def update_manufacturer_annual_data(calendar_year, manufacturer_ID, cert_target_co2_Mg,
                                        cert_co2_Mg, manufacturer_vehicle_cost_dollars):
        session.add(ManufacturerAnnualData(manufacturer_ID=manufacturer_ID,
                                           calendar_year=calendar_year,
                                           cert_target_co2_Mg=cert_target_co2_Mg,
                                           cert_co2_Mg=cert_co2_Mg,
                                           manufacturer_vehicle_cost_dollars=manufacturer_vehicle_cost_dollars
                                           ))
        session.flush()

    # @staticmethod
    # def update_cert_target_co2_Mg(calendar_year, manufacturer_ID, cert_target_co2_Mg):
    #     session.add(ManufacturerAnnualData(manufacturer_ID=manufacturer_ID,
    #                                   calendar_year=calendar_year,
    #                                   cert_target_co2_Mg=cert_target_co2_Mg,
    #                                   ))
    #     session.flush()

    # @staticmethod
    # def update_cert_co2_Mg(calendar_year, manufacturer_ID, cert_co2_Mg):
    #     mad = session.query(ManufacturerAnnualData)\
    #         .filter(manufacturer_ID==manufacturer_ID)\
    #         .filter(calendar_year==calendar_year).scalar()
    #     mad.cert_co2_Mg = cert_co2_Mg
    #     session.flush()


if __name__ == '__main__':
    if '__file__' in locals():
        print(fileio.get_filenameext(__file__))

    from manufacturers import Manufacturer  # required by vehicles

    session = Session(bind=engine)
    SQABase.metadata.create_all(engine)

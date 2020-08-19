"""
manufacturer_annual_data.py
===========================


"""

import o2  # import global variables
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
    bev_non_hauling_share_frac = Column('bev_non_hauling_share_frac', Numeric)
    ice_non_hauling_share_frac = Column('ice_non_hauling_share_frac', Numeric)
    bev_hauling_share_frac = Column('bev_hauling_share_frac', Numeric)
    ice_hauling_share_frac = Column('ice_hauling_share_frac', Numeric)

    @staticmethod
    def create_manufacturer_annual_data(calendar_year, manufacturer_ID, cert_target_co2_Mg,
                                        cert_co2_Mg, manufacturer_vehicle_cost_dollars,
                                        bev_non_hauling_share_frac, ice_non_hauling_share_frac,
                                        bev_hauling_share_frac, ice_hauling_share_frac):
        o2.session.add(ManufacturerAnnualData(manufacturer_ID=manufacturer_ID,
                                              calendar_year=calendar_year,
                                              cert_target_co2_Mg=cert_target_co2_Mg,
                                              cert_co2_Mg=cert_co2_Mg,
                                              manufacturer_vehicle_cost_dollars=manufacturer_vehicle_cost_dollars,
                                              bev_non_hauling_share_frac=bev_non_hauling_share_frac,
                                              ice_non_hauling_share_frac=ice_non_hauling_share_frac,
                                              bev_hauling_share_frac=bev_hauling_share_frac,
                                              ice_hauling_share_frac=ice_hauling_share_frac,
                                              ))
        o2.session.flush()


if __name__ == '__main__':
    if '__file__' in locals():
        print(fileio.get_filenameext(__file__))

    # set up global variables:
    o2.options = OMEGARuntimeOptions()
    init_omega_db()

    from manufacturers import Manufacturer  # required by vehicles

    SQABase.metadata.create_all(o2.engine)

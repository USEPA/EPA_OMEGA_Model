"""


----

**CODE**

"""

print('importing %s' % __file__)

from usepa_omega2 import *


class ManufacturerAnnualData(SQABase):
    # --- database table properties ---
    __tablename__ = 'manufacturer_annual_data'
    index = Column('index', Integer, primary_key=True)
    manufacturer_ID = Column('manufacturer_id', Integer, ForeignKey('manufacturers.manufacturer_id'))
    calendar_year = Column(Numeric)
    calendar_year_cert_co2_Mg = Column('calendar_year_cert_co2_megagrams', Float)
    model_year_cert_co2_Mg = Column('model_year_cert_co2_megagrams', Float)
    cert_target_co2_Mg = Column('cert_target_co2_megagrams', Float)
    manufacturer_vehicle_cost_dollars = Column('manufacturer_vehicle_cost_dollars', Float)

    @staticmethod
    def create_manufacturer_annual_data(calendar_year, manufacturer_ID, cert_target_co2_Mg,
                                        calendar_year_cert_co2_Mg, manufacturer_vehicle_cost_dollars):
        o2.session.add(ManufacturerAnnualData(manufacturer_ID=manufacturer_ID,
                                              calendar_year=calendar_year,
                                              cert_target_co2_Mg=cert_target_co2_Mg,
                                              calendar_year_cert_co2_Mg=calendar_year_cert_co2_Mg,
                                              model_year_cert_co2_Mg=calendar_year_cert_co2_Mg,  # to start with
                                              manufacturer_vehicle_cost_dollars=manufacturer_vehicle_cost_dollars,
                                              ))
        o2.session.flush()

    @staticmethod
    def get_calendar_years():
        return sql_unpack_result(o2.session.query(ManufacturerAnnualData.calendar_year).all())

    @staticmethod
    def get_cert_target_co2_Mg():
        return sql_unpack_result(o2.session.query(ManufacturerAnnualData.cert_target_co2_Mg).all())

    @staticmethod
    def get_calendar_year_cert_co2_Mg():
        return sql_unpack_result(o2.session.query(ManufacturerAnnualData.calendar_year_cert_co2_Mg).all())

    @staticmethod
    def get_model_year_cert_co2_Mg():
        return sql_unpack_result(o2.session.query(ManufacturerAnnualData.model_year_cert_co2_Mg).all())

    @staticmethod
    def get_total_cost_billions():
        return float(
            o2.session.query(func.sum(ManufacturerAnnualData.manufacturer_vehicle_cost_dollars)).scalar()) / 1e9

    @staticmethod
    def update_model_year_cert_co2_Mg(model_year, manufacturer_ID, transaction_amount_Mg):
        mad = o2.session.query(ManufacturerAnnualData)\
            .filter(ManufacturerAnnualData.calendar_year==model_year)\
            .filter(ManufacturerAnnualData.manufacturer_ID==manufacturer_ID).one_or_none()

        if mad is not None:
            mad.model_year_cert_co2_Mg += transaction_amount_Mg


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(fileio.get_filenameext(__file__))

        # set up global variables:
        o2.options = OMEGARuntimeOptions()
        init_omega_db()

        from manufacturers import Manufacturer  # required by vehicles

        SQABase.metadata.create_all(o2.engine)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
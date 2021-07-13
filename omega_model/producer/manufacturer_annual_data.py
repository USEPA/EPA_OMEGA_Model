"""

**Routines to create and update yearly manufacturer compliance data.**

Manufacturer annual data is created for each compliance model year as a result of vehicle sales and certification
performance.  Compliance of a model year may be achieve retroactively through the use of credits created by future
model years.

See Also:
    The ``GHG_credits`` module, and ``postproc_session.plot_manufacturer_compliance()`` for credit plotting routines.

----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *


class ManufacturerAnnualData(SQABase):
    # --- database table properties ---
    __tablename__ = 'manufacturer_annual_data'  # database table name
    index = Column('index', Integer, primary_key=True)  #: database table index
    manufacturer_ID = Column('manufacturer_id', Integer, ForeignKey('manufacturers.manufacturer_id'))  #: manufacturer id, e..g 'USA Motors'
    model_year = Column(Numeric)  #: model year of the data
    calendar_year_cert_co2e_Mg = Column('calendar_year_cert_co2e_megagrams', Float)  #: certification CO2 (Mg) achieved in the given calendar year (initial compliance state)
    model_year_cert_co2e_Mg = Column('model_year_cert_co2e_megagrams', Float)  #: certificaiton CO2 (Mg) achieved, including credits transferred to/from other model years
    cert_target_co2e_Mg = Column('cert_target_co2e_megagrams', Float)  #: certification target CO2 (Mg) for the calendar year
    manufacturer_vehicle_cost_dollars = Column('manufacturer_vehicle_cost_dollars', Float)  #: total manufacturer vehicle cost for the model year (sum of vehicle sales X vehicle cost)

    @staticmethod
    def create_manufacturer_annual_data(model_year, manufacturer_ID, cert_target_co2e_Mg,
                                        calendar_year_cert_co2e_Mg, manufacturer_vehicle_cost_dollars):
        """
        Create initial manufacturer compliance database entry for the given year.
        Final compliance state may depend on future years via credit banking.

        Args:
            model_year (numeric): the compliance model year
            manufacturer_ID (str): manufacturer id, e.g. 'USA Motors'
            cert_target_co2e_Mg (numeric): target CO2 Mg for the model year
            calendar_year_cert_co2e_Mg (numeric): initial compliance state (CO2 Mg) of the vehicles produced in the model year
            manufacturer_vehicle_cost_dollars (numeric): total manufacturer vehicle cost (sum of vehicle sales X vehicle cost)

        """
        omega_globals.session.add(ManufacturerAnnualData(manufacturer_ID=manufacturer_ID,
                                                         model_year=model_year,
                                                         cert_target_co2e_Mg=cert_target_co2e_Mg,
                                                         calendar_year_cert_co2e_Mg=calendar_year_cert_co2e_Mg,
                                                         model_year_cert_co2e_Mg=calendar_year_cert_co2e_Mg,  # to start with
                                                         manufacturer_vehicle_cost_dollars=manufacturer_vehicle_cost_dollars,
                                                         ))
        omega_globals.session.flush()

    @staticmethod
    def get_model_years():
        """

        Returns: A list of model years of manufacturer compliance data

        """

        return sql_unpack_result(omega_globals.session.query(ManufacturerAnnualData.model_year).all())

    @staticmethod
    def get_cert_target_co2e_Mg():
        """

        Returns: A list of target CO2 Mg for each model year

        """
        return sql_unpack_result(omega_globals.session.query(ManufacturerAnnualData.cert_target_co2e_Mg).all())

    @staticmethod
    def get_calendar_year_cert_co2e_Mg():
        """

        Returns: A list of initial compliance state data (CO2 Mg) of the vehicles produced by model year

        """
        return sql_unpack_result(omega_globals.session.query(ManufacturerAnnualData.calendar_year_cert_co2e_Mg).all())

    @staticmethod
    def get_model_year_cert_co2e_Mg():
        """

        Returns: A list of final achieved certification CO2 Mg for each model year, including credits transferred
        to/from other model years

        """
        return sql_unpack_result(omega_globals.session.query(ManufacturerAnnualData.model_year_cert_co2e_Mg).all())

    @staticmethod
    def get_total_cost_billions():
        """

        Returns: A list of total manufacturer vehicle costs by model year, in billions of dollars

        """
        return float(
            omega_globals.session.query(func.sum(ManufacturerAnnualData.manufacturer_vehicle_cost_dollars)).scalar()) / 1e9

    @staticmethod
    def update_model_year_cert_co2e_Mg(model_year, manufacturer_id, transaction_amount_Mg):
        """
        Update model year certification CO2 Mg based on the given transaction amount.  Used for credit banking.

        Args:
            model_year (numeric): the model year of the transaction
            manufacturer_id (str): manufacturer name, e.g. 'USA Motors'
            transaction_amount_Mg (numeric): the transaction amount, may be positive (receiving credits) or negative (transferring credits)

        """
        mad = omega_globals.session.query(ManufacturerAnnualData)\
            .filter(ManufacturerAnnualData.model_year == model_year)\
            .filter(ManufacturerAnnualData.manufacturer_ID == manufacturer_id).one_or_none()

        if mad is not None:
            mad.model_year_cert_co2e_Mg += transaction_amount_Mg


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        # set up global variables:
        omega_globals.options = OMEGARuntimeOptions()
        init_omega_db(omega_globals.options.verbose)

        from manufacturers import Manufacturer  # required by vehicles

        SQABase.metadata.create_all(omega_globals.engine)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
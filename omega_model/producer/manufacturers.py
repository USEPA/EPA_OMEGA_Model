"""


----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *

initial_credit_bank = dict()

class Manufacturer(SQABase, OMEGABase):
    # --- database table properties ---
    __tablename__ = 'manufacturers'
    manufacturer_ID = Column('manufacturer_id', String, primary_key=True)
    vehicles = relationship('VehicleFinal', back_populates='manufacturer')

    # --- static properties ---
    @staticmethod
    def init_database_from_file(filename, verbose=False):
        from policy.credit_banking import CreditBank
        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_name = 'manufacturers'
        input_template_version = 0.0003
        input_template_columns = {'manufacturer_id'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version, verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                obj_list = []
                # load data into database
                for i in df.index:
                    manufacturer_ID = df.loc[i, 'manufacturer_id']
                    obj_list.append(Manufacturer(
                        manufacturer_ID=manufacturer_ID,
                    ))
                omega_globals.session.add_all(obj_list)
                omega_globals.session.flush()

                template_errors = CreditBank.validate_ghg_credits_template(omega_globals.options.ghg_credits_file, verbose)

                if not template_errors:
                    initial_credit_bank[manufacturer_ID] = CreditBank(omega_globals.options.ghg_credits_file, manufacturer_ID)

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        # set up global variables:
        omega_globals.options = OMEGARuntimeOptions()
        init_omega_db(omega_globals.options.verbose)
        omega_log.init_logfile()

        from context.onroad_fuels import OnroadFuel
        from consumer.market_classes import MarketClass
        from producer.vehicles import VehicleFinal
        from producer.vehicle_annual_data import VehicleAnnualData

        SQABase.metadata.create_all(omega_globals.engine)

        init_fail = []
        init_fail += Manufacturer.init_database_from_file(omega_globals.options.manufacturers_file, verbose=omega_globals.options.verbose)

        if not init_fail:
            dump_omega_db_to_csv(omega_globals.options.database_dump_folder)
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)

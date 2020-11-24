"""
context_fuel_prices.py
======================


"""

print('importing %s' % __file__)

import o2  # import global variables
from usepa_omega2 import *


class ContextFuelPrices(SQABase, OMEGABase):
    # --- database table properties ---
    __tablename__ = 'context_fuels'
    index = Column('index', Integer, primary_key=True)
    context_ID = Column('context_id', String)
    case_ID = Column('case_id', String)
    fuel_ID = Column('fuel_id', String)
    calendar_year = Column(Numeric)
    retail_dollars_per_unit = Column(Float)
    pretax_dollars_per_unit = Column(Float)

    @staticmethod
    def get_retail_fuel_price(calendar_year, fuel_ID):
        if o2.options.flat_context:
            calendar_year = o2.options.flat_context_year

        return o2.session.query(ContextFuelPrices.retail_dollars_per_unit).\
            filter(ContextFuelPrices.context_ID == o2.options.context_id).\
            filter(ContextFuelPrices.case_ID == o2.options.context_case_id).\
            filter(ContextFuelPrices.calendar_year == calendar_year).\
            filter(ContextFuelPrices.fuel_ID == fuel_ID).one()[0]

    @staticmethod
    def get_pretax_fuel_price(calendar_year, fuel_ID):
        if o2.options.flat_context:
            calendar_year = o2.options.flat_context_year

        return o2.session.query(ContextFuelPrices.pretax_dollars_per_unit).\
            filter(ContextFuelPrices.context_ID == o2.options.context_id).\
            filter(ContextFuelPrices.case_ID == o2.options.context_case_id).\
            filter(ContextFuelPrices.calendar_year == calendar_year).\
            filter(ContextFuelPrices.fuel_ID == fuel_ID).one()[0]

    @staticmethod
    def init_database_from_file(filename, verbose=False):
        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_name = 'context_fuel_prices'
        input_template_version = 0.1
        input_template_columns = {'context_id', 'case_id', 'fuel_id', 'calendar_year', 'retail_dollars_per_unit',
                                  'pretax_dollars_per_unit'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            # TODO: do we need to validate no missing years, years in sequential order?

            if not template_errors:
                obj_list = []
                # load data into database
                for i in df.index:
                    obj_list.append(ContextFuelPrices(
                        context_ID=df.loc[i, 'context_id'],
                        case_ID=df.loc[i, 'case_id'],
                        fuel_ID=df.loc[i, 'fuel_id'],
                        calendar_year=df.loc[i, 'calendar_year'],
                        retail_dollars_per_unit=df.loc[i, 'retail_dollars_per_unit'],
                        pretax_dollars_per_unit=df.loc[i, 'pretax_dollars_per_unit'],
                    ))
                o2.session.add_all(obj_list)
                o2.session.flush()

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(fileio.get_filenameext(__file__))

        # set up global variables:
        o2.options = OMEGARuntimeOptions()
        init_omega_db()
        omega_log.init_logfile()

        SQABase.metadata.create_all(o2.engine)

        init_fail = []
        init_fail = init_fail + ContextFuelPrices.init_database_from_file(o2.options.context_fuel_prices_file,
                                                                          verbose=o2.options.verbose)

        if not init_fail:
            dump_omega_db_to_csv(o2.options.database_dump_folder)

            print(ContextFuelPrices.get_retail_fuel_price(2020, 'pump gasoline'))
            print(ContextFuelPrices.get_pretax_fuel_price(2020, 'pump gasoline'))
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)

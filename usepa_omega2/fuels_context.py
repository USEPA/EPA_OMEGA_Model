"""
fuels_context.py
================


"""

print('importing %s' % __file__)

import o2  # import global variables
from usepa_omega2 import *


class FuelsContext(SQABase, OMEGABase):
    # --- database table properties ---
    __tablename__ = 'fuels_context'
    index = Column('index', Integer, primary_key=True)
    context_ID = Column('context_id', String)
    case_ID = Column('case_id', String)
    fuel_ID = Column('fuel_id', String)
    calendar_year = Column(Numeric)
    retail_dollars_per_unit = Column(Float)
    pretax_dollars_per_unit = Column(Float)
    fuels_context_ID = 'AEO2020'  # TODO: should come from batch definition context specification
    fuels_case_ID = 'Reference case'  # TODO: should come from batch definition context specification

    @staticmethod
    def get_retail_fuel_price(calendar_year, fuel_ID):
        return o2.session.query(FuelsContext.retail_dollars_per_unit).\
            filter(FuelsContext.context_ID == FuelsContext.fuels_context_ID).\
            filter(FuelsContext.case_ID == FuelsContext.fuels_case_ID).\
            filter(FuelsContext.calendar_year == calendar_year).\
            filter(FuelsContext.fuel_ID == fuel_ID).one()[0]

    @staticmethod
    def get_pretax_fuel_price(calendar_year, fuel_ID):
        return o2.session.query(FuelsContext.pretax_dollars_per_unit).\
            filter(FuelsContext.context_ID == FuelsContext.fuels_context_ID).\
            filter(FuelsContext.case_ID == FuelsContext.fuels_case_ID).\
            filter(FuelsContext.calendar_year == calendar_year).\
            filter(FuelsContext.fuel_ID == fuel_ID).one()[0]

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
                    obj_list.append(FuelsContext(
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
        init_fail = init_fail + FuelsContext.init_database_from_file(o2.options.fuels_context_file,
                                                                     verbose=o2.options.verbose)

        if not init_fail:
            dump_omega_db_to_csv(o2.options.database_dump_folder)

            print(FuelsContext.get_retail_fuel_price(2020, 'pump gasoline'))
            print(FuelsContext.get_pretax_fuel_price(2020, 'pump gasoline'))
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)

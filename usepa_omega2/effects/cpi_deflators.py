"""
cpi_deflators.py
================


"""

import o2  # import global variables
from usepa_omega2 import *


class CPIPriceDeflators(SQABase):
    # --- database table properties ---
    __tablename__ = 'context_cpi_price_deflators'
    index = Column('index', Integer, primary_key=True)

    calendar_year = Column('calendar_year', Numeric)
    price_deflator = Column('price_deflator', Numeric)
    adjustment_factor = Column('adjustment_factor', Numeric)

    def __repr__(self):
        return f"<OMEGA2 {type(self).__name__} object at 0x{id(self)}>"

    @staticmethod
    def init_database_from_file(filename, verbose=False):
        if verbose:
            omega_log.logwrite(f'\nInitializing database from {filename}...')

        input_template_name = 'context_cpi_price_deflators'
        input_template_version = 0.1
        input_template_columns = {'calendar_year', 'price_deflator', 'adjustment_factor'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                obj_list = []
                # load data into database
                for i in df.index:
                    obj_list.append(CPIPriceDeflators(
                        calendar_year=df.loc[i, 'calendar_year'],
                        price_deflator=df.loc[i, 'price_deflator'],
                        adjustment_factor=df.loc[i, 'adjustment_factor'],
                    ))
                o2.session.add_all(obj_list)
                o2.session.flush()

        return template_errors

    def df_from_table(self, arg):
        df_return = pd.read_sql(f'SELECT * FROM {self.__tablename__}', con=o2.engine)
        df_return.set_index(arg, inplace=True)
        return df_return


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

        init_fail = init_fail + CPIPriceDeflators.init_database_from_file(o2.options.cpi_deflators_file,
                                                                          verbose=o2.options.verbose)

        if not init_fail:
            dump_omega_db_to_csv(o2.options.database_dump_folder)
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)

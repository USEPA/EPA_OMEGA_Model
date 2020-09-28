"""
GHG_standards_fuels.py
======================


"""

print('importing %s' % __file__)

import o2  # import global variables
from usepa_omega2 import *


class GHGStandardFuels(SQABase):
    # --- database table properties ---
    __tablename__ = 'ghg_standards_fuels'
    index = Column('index', Integer, primary_key=True)
    fuel_ID = Column('fuel_id', String)
    calendar_year = Column(Numeric)
    cert_CO2_grams_per_unit = Column('cert_co2_grams_per_unit', Float)

    def __repr__(self):
        return "<OMEGA2 %s object at 0x%x>" % (type(self).__name__, id(self))

    def __str__(self):
        s = ''  # '"<OMEGA2 %s object at 0x%x>" % (type(self).__name__,  id(self))
        for k in self.__dict__:
            s = s + k + ' = ' + str(self.__dict__[k]) + '\n'
        return s

    @staticmethod
    def init_database_from_file(filename, verbose=False):
        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_name = 'ghg_standards-fuels'
        input_template_version = 0.0001
        input_template_columns = {'fuel_id', 'calendar_year', 'cert_co2_grams_per_unit'}

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
                    obj_list.append(GHGStandardFuels(
                        fuel_ID=df.loc[i, 'fuel_id'],
                        calendar_year=df.loc[i, 'calendar_year'],
                        cert_CO2_grams_per_unit=df.loc[i, 'cert_co2_grams_per_unit'],
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
        init_fail = init_fail + GHGStandardFuels.init_database_from_file(o2.options.ghg_standards_fuels_file,
                                                                         verbose=o2.options.verbose)

        if not init_fail:
            dump_omega_db_to_csv(o2.options.database_dump_folder)
        else:
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)

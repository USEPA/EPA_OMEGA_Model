"""
fuel_scenario_data.py
=====================


"""

import o2  # import global variables
from usepa_omega2 import *


class FuelScenarioAnnualData(SQABase):
    # --- database table properties ---
    __tablename__ = 'fuel_scenario_annual_data'
    index = Column('index', Integer, primary_key=True)
    fuel_ID = Column('fuel_id', String)
    fuel_scenario_ID = Column('fuel_scenario_id', String)
    calendar_year = Column(Numeric)
    cost_dollars_per_unit = Column(Float)
    upstream_CO2_per_unit = Column('upstream_co2_per_unit', Float)

    def __repr__(self):
        return "<OMEGA2 %s object at 0x%x>" % (type(self).__name__, id(self))

    def __str__(self):
        s = ''  # '"<OMEGA2 %s object at 0x%x>" % (type(self).__name__,  id(self))
        for k in self.__dict__:
            s = s + k + ' = ' + str(self.__dict__[k]) + '\n'
        return s

    @staticmethod
    def init_database_from_file(filename, verbose=False):
        omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_name = 'fuel_scenario_annual_data'
        input_template_version = 0.0002
        input_template_columns = {'fuel_id', 'fuel_scenario_id', 'calendar_year', 'cost_dollars_per_unit',
                                  'upstream_co2_grams_per_unit'}

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
                    obj_list.append(FuelScenarioAnnualData(
                        fuel_ID=df.loc[i, 'fuel_id'],
                        fuel_scenario_ID=df.loc[i, 'fuel_scenario_id'],
                        calendar_year=df.loc[i, 'calendar_year'],
                        cost_dollars_per_unit=df.loc[i, 'cost_dollars_per_unit'],
                        upstream_CO2_per_unit=df.loc[i, 'upstream_co2_grams_per_unit'],
                    ))
                o2.session.add_all(obj_list)
                o2.session.flush()

        return template_errors


if __name__ == '__main__':
    if '__file__' in locals():
        print(fileio.get_filenameext(__file__))

    # set up global variables:
    o2.options = OMEGARuntimeOptions()
    (o2.engine, o2.session) = init_db()

    SQABase.metadata.create_all(o2.engine)

    init_fail = []
    init_fail = init_fail + FuelScenarioAnnualData.init_database_from_file(o2.options.fuel_scenario_annual_data_file,
                                                                           verbose=o2.options.verbose)

    if not init_fail:
        dump_database_to_csv(o2.engine, o2.options.database_dump_folder, verbose=o2.options.verbose)

"""
fuel_scenarios.py
=================


"""

from usepa_omega2 import *


class FuelScenario(SQABase):
    # --- database table properties ---
    __tablename__ = 'fuel_scenarios'
    fuel_scenario_ID = Column('fuel_scenario_id', String, primary_key=True)
    dollar_year = Column('dollar_year', Numeric)

    def __repr__(self):
        return "<OMEGA2 %s object at 0x%x>" % (type(self).__name__,  id(self))

    def __str__(self):
        return "<Fuel('%s', %f MJ/%s)>" % (self.name, self.energy_density_MJ_per_unit, self.unit)

    @staticmethod
    def init_database_from_file(filename, session, verbose=False):
        omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_name = 'fuel_scenarios'
        input_template_version = 0.0002
        input_template_columns = {'fuel_scenario_id', 'dollar_year'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version, verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                obj_list = []
                # load data into database
                for i in df.index:
                    obj_list.append(FuelScenario(
                        fuel_scenario_ID=df.loc[i, 'fuel_scenario_id'],
                        dollar_year=df.loc[i, 'dollar_year'],
                    ))
                session.add_all(obj_list)
                session.flush()

        return template_errors


if __name__ == '__main__':
    if '__file__' in locals():
        print(fileio.get_filenameext(__file__))

    SQABase.metadata.create_all(engine)

    init_fail = []
    init_fail = init_fail + FuelScenario.init_database_from_file(o2_options.fuel_scenarios_file, session, verbose=o2_options.verbose)

    if not init_fail:
        dump_database_to_csv(engine, o2_options.database_dump_folder, verbose=o2_options.verbose)

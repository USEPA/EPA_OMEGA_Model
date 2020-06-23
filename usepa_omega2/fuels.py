"""
fuels.py
========


"""

from usepa_omega2 import *

input_template_name = 'fuels'
input_template_version = 0.0002
input_template_columns = {'fuel_id', 'unit', 'energy_density_megajoules_per_unit'}


class Fuel(SQABase):
    # --- database table properties ---
    __tablename__ = 'fuels'
    fuel_ID = Column('fuel_id', Integer, primary_key=True)
    name = Column('name', String)
    unit = Column(Enum(*fuel_units, validate_strings=True))
    energy_density_MJ_per_unit = Column('energy_density_megajoules_per_unit', Float)

    def init_database(filename, session, verbose=False):
        print('\nInitializing database from %s...' % filename)

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version, verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                fuels = []
                # load data into database
                for i in df.index:
                    fuels.append(Fuel(
                        name=df.loc[i, 'fuel_id'],
                        unit=df.loc[i, 'unit'],
                        energy_density_MJ_per_unit=df.loc[i, 'energy_density_megajoules_per_unit'])
                    )
                session.add_all(fuels)
                session.flush()

        return template_errors


if __name__ == '__main__':
    print(fileio.get_filenameext(__file__))

    session = Session(bind=engine)
    SQABase.metadata.create_all(engine)

    init_fail = Fuel.init_database('input_templates/fuels.csv', session, verbose=True)

    if not init_fail:
        dump_database_to_csv(engine, '__dump_fuel')

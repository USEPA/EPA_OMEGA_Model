"""
cost_curves.py
==============


"""

from usepa_omega2 import *


class CostCurvePoint(SQABase):
    # --- database table properties ---
    __tablename__ = 'cost_curves'
    index = Column('index', Integer, primary_key=True)

    cost_curve_class = Column(String)
    calendar_year = Column(Numeric)
    cost_dollars = Column(Float)  # TODO:should this be a pickled list or array or just a single point??
    CO2_grams_per_mile = Column('co2_grams_per_mile', Float)  # TODO:should this be a pickled list or array or just a single point??

    def __repr__(self):
        return "<OMEGA2 %s object at 0x%x>" % (type(self).__name__,  id(self))

    def __str__(self):
        s = ''  # '"<OMEGA2 %s object at 0x%x>" % (type(self).__name__,  id(self))
        for k in self.__dict__:
            s = s + k + ' = ' + str(self.__dict__[k]) + '\n'
        return s

    # noinspection PyMethodParameters
    def init_database_from_file(filename, session, verbose=False):
        print('\nInitializing database from %s...' % filename)

        input_template_name = 'cost_curves'
        input_template_version = 0.0001
        input_template_columns = {'cost_curve_class', 'model_year', 'cert_co2_grams_per_mile', 'new_vehicle_cost'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version, verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                obj_list = []
                # load data into database TODO: need to calculate frontier first...
                for i in df.index:
                    obj_list.append(CostCurvePoint(
                        cost_curve_class=df.loc[i, 'cost_curve_class'],
                        calendar_year=df.loc[i, 'model_year'],
                        cost_dollars=df.loc[i, 'new_vehicle_cost'],
                        CO2_grams_per_mile= df.loc[i, 'cert_co2_grams_per_mile'],
                    ))
                session.add_all(obj_list)
                session.flush()

        return template_errors

    def init_database_from_lists(cost_curve_class, model_year, frontier_co2_gpmi, frontier_cost, session, verbose=False):
        print('\nInitializing database from %s frontier...' % cost_curve_class)

        obj_list = []
        for cost, co2_gpmi in zip(frontier_cost, frontier_co2_gpmi):
            obj_list.append(CostCurvePoint(
                cost_curve_class=cost_curve_class,
                calendar_year=model_year,
                cost_dollars=cost,
                CO2_grams_per_mile=co2_gpmi,
            ))
        session.add_all(obj_list)
        session.flush()

    def calculate_generalized_cost(self, market_class_ID):
        print(market_class_ID)


if __name__ == '__main__':
    if '__file__' in locals():
        print(fileio.get_filenameext(__file__))

    SQABase.metadata.create_all(engine)

    init_fail = []
    init_fail = init_fail + CostCurvePoint.init_database_from_file(o2_options.cost_curves_file, session, verbose=o2_options.verbose)

    if not init_fail:
        dump_database_to_csv(engine, o2_options.database_dump_folder, verbose=o2_options.verbose)

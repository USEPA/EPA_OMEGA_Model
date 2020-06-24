"""
cost_curves.py
==========


"""

from usepa_omega2 import *

input_template_name = 'cost_clouds'
input_template_version = 0.0001
input_template_columns = {'cost_curve_class', 'model_year', 'cert_co2_grams_per_mile', 'new_vehicle_cost'}


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
    def init_database(filename, session, verbose=False):
        print('\nInitializing database from %s...' % filename)

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

    def calculate_generalized_cost(self, market_class_ID):
        print(market_class_ID)


if __name__ == '__main__':
    print(fileio.get_filenameext(__file__))

    session = Session(bind=engine)
    SQABase.metadata.create_all(engine)

    init_fail = CostCurvePoint.init_database('input_templates/%s.csv' % input_template_name, session, verbose=True)

    if not init_fail:
        dump_database_to_csv(engine, '__dump')

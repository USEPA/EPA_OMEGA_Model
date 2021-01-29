"""
cost_curves.py
==============


"""

print('importing %s' % __file__)

import o2  # import global variables
from usepa_omega2 import *

input_template_name = 'cost_curves'

class CostCurve(SQABase, OMEGABase):
    # --- database table properties ---
    __tablename__ = 'cost_curves'
    index = Column('index', Integer, primary_key=True)

    cost_curve_class = Column(String)
    model_year = Column(Numeric)
    cost_dollars = Column(Float)
    cert_CO2_grams_per_mile = Column(Float)

    @staticmethod
    def init_database_from_file(filename, verbose=False):
        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_version = 0.0002
        input_template_columns = {'cost_curve_class', 'model_year', 'cert_co2_grams_per_mile', 'cost_dollars'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                obj_list = []

                for i in df.index:
                    obj_list.append(CostCurve(
                        cost_curve_class=df.loc[i, 'cost_curve_class'],
                        model_year=df.loc[i, 'model_year'],
                        cost_dollars=df.loc[i, 'cost_dollars'],
                        cert_CO2_grams_per_mile=df.loc[i, 'cert_co2_grams_per_mile'],
                    ))
                o2.session.add_all(obj_list)
                o2.session.flush()

        return template_errors

    @staticmethod
    def init_database_from_lists(cost_curve_class, model_year, frontier_co2_gpmi, frontier_cost, verbose=False):
        if verbose:
            omega_log.logwrite('\nInitializing database from %s frontier...' % cost_curve_class)

        obj_list = []
        for cost, co2_gpmi in zip(frontier_cost, frontier_co2_gpmi):
            obj_list.append(CostCurve(
                cost_curve_class=cost_curve_class,
                model_year=model_year,
                cost_dollars=cost,
                cert_CO2_grams_per_mile=co2_gpmi,
            ))
        o2.session.add_all(obj_list)
        o2.session.flush()

    @staticmethod
    def get_cost(cost_curve_class, model_year, target_co2_gpmi):
        if o2.options.flat_context:
            model_year = o2.options.flat_context_year

        min_cost_curve_year = o2.session.query(func.min(CostCurve.model_year)).scalar()
        max_cost_curve_year = o2.session.query(func.max(CostCurve.model_year)).scalar()

        if model_year < min_cost_curve_year:
            omega_log.logwrite(
                "\n### WARNING: Attempt to access %s cost curve for year (%d) below minimum (%d) ###\n" % (
                    cost_curve_class, model_year, min_cost_curve_year))
            model_year = min_cost_curve_year

        if model_year > max_cost_curve_year:
            omega_log.logwrite(
                "\n### WARNING: Attempt to access %s cost curve for year (%d) above maximum (%d) ###\n" % (
                    cost_curve_class, model_year, max_cost_curve_year))
            model_year = min_cost_curve_year

        result = o2.session.query(CostCurve.cost_dollars, CostCurve.cert_CO2_grams_per_mile).filter(
            CostCurve.model_year == model_year).filter(CostCurve.cost_curve_class == cost_curve_class)
        curve_cost_dollars = [r[0] for r in result]
        curve_co2_gpmi = [r[1] for r in result]

        cost_dollars = scipy.interpolate.interp1d(curve_co2_gpmi, curve_cost_dollars, fill_value='extrapolate')

        return cost_dollars(target_co2_gpmi)

    @staticmethod
    def get_min_co2_gpmi(cost_curve_class, model_year):
        if o2.options.flat_context:
            model_year = o2.options.flat_context_year

        return o2.session.query(func.min(CostCurve.cert_CO2_grams_per_mile)). \
            filter(CostCurve.cost_curve_class == cost_curve_class). \
            filter(CostCurve.model_year == model_year).scalar()

    @staticmethod
    def get_max_co2_gpmi(cost_curve_class, model_year):
        if o2.options.flat_context:
            model_year = o2.options.flat_context_year

        return o2.session.query(func.max(CostCurve.cert_CO2_grams_per_mile)). \
            filter(CostCurve.cost_curve_class == cost_curve_class). \
            filter(CostCurve.model_year == model_year).scalar()

    @staticmethod
    def get_co2_gpmi(cost_curve_class, model_year):
        if o2.options.flat_context:
            model_year = o2.options.flat_context_year

        return sql_unpack_result(o2.session.query(CostCurve.cert_CO2_grams_per_mile).
                                 filter(CostCurve.cost_curve_class == cost_curve_class).
                                 filter(CostCurve.model_year == model_year).all())


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(fileio.get_filenameext(__file__))

        # set up global variables:
        o2.options = OMEGARuntimeOptions()
        init_omega_db()
        omega_log.init_logfile()
        o2.options.cost_file = 'test_inputs/cost_curves.csv'

        SQABase.metadata.create_all(o2.engine)

        init_fail = []
        init_fail = init_fail + CostCurve.init_database_from_file(o2.options.cost_file, verbose=o2.options.verbose)

        if not init_fail:
            from omega_plot import *
            import numpy as np

            dump_omega_db_to_csv(o2.options.database_dump_folder)

            print(CostCurve.get_cost('ice_MPW_LRL', 2020, 100))
            print(CostCurve.get_cost('ice_MPW_LRL', 2020, [0, 100, 200, 300, 400, 500, 1000]))

            # plot cost curves
            ice_Truck_co2gpmi = CostCurve.get_co2_gpmi('ice_Truck', 2020)
            ice_Truck_cost = CostCurve.get_cost('ice_Truck', 2020, ice_Truck_co2gpmi)

            ice_MPW_LRL_co2gpmi = CostCurve.get_co2_gpmi('ice_MPW_LRL', 2020)
            ice_MPW_LRL_cost = CostCurve.get_cost('ice_MPW_LRL', 2020, ice_MPW_LRL_co2gpmi)

            fig, ax1 = fplothg(ice_Truck_co2gpmi, ice_Truck_cost,'o-')
            ax1.plot(ice_MPW_LRL_co2gpmi, ice_MPW_LRL_cost, 'o-')

            # create weighted cost curves and plot
            co2gpmi = list(set([*ice_Truck_co2gpmi, *ice_MPW_LRL_co2gpmi]))
            co2gpmi.sort()
            c1 = CostCurve.get_cost('ice_Truck', 2020, co2gpmi)
            c2 = CostCurve.get_cost('ice_MPW_LRL', 2020, co2gpmi)
            ax1.plot(co2gpmi, c1, '.--')
            ax1.plot(co2gpmi, c2, '.--')
            r1 = 0.75
            c3 = np.array(c1) * r1 + np.array(c2) * (1-r1)
            ax1.plot(co2gpmi, c3, '*--')
            r1 = 0.25
            c3 = np.array(c1) * r1 + np.array(c2) * (1-r1)
            ax1.plot(co2gpmi, c3, '*--')
            label_xyt(ax1, 'co2 [g/mi]', 'cost [$]', 'Cost Curves and weighted Cost Curves')

        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)

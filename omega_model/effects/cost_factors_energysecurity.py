"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents $/gallon cost estimates associated with energy security.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,context_cost_factors-energysecurity,input_template_version:,0.2

Sample Data Columns
    .. csv-table::
        :widths: auto

        calendar_year,dollar_basis,dollars_per_gallon,foreign_oil_fraction
        2020,2018,0.081357143,0.9

Data Column Name and Description
    :calendar_year:
        The calendar year for which $/gallon values are applicable.

    :dollar_basis:
        The dollar basis of values within the table. Values are converted in code to the dollar basis to be used in the analysis.

    :dollars_per_gallon:
        The cost (in US dollars) per gallon of liquid fuel associated with energy security.

    :foreign_oil_fraction:
        A legacy parameter that is not used currently.

----

**CODE**

"""

from omega_model import *
import omega_model.effects.general_functions as gen_fxns

cache = dict()


class CostFactorsEnergySecurity(SQABase, OMEGABase):
    # --- database table properties ---
    __tablename__ = 'cost_factors_energysecurity'
    index = Column(Integer, primary_key=True)
    calendar_year = Column(Numeric)
    dollar_basis = Column(Float)
    dollars_per_gallon = Column(Float)
    foreign_oil_fraction = Column(Float)

    @staticmethod
    def get_cost_factors(calendar_year, cost_factors):
        """

        Args:
            calendar_year: calendar year to get cost factors for
            cost_factors: name of cost factor or list of cost factor attributes to get

        Returns: cost factor or list of cost factors

        """
        cache_key = '%s_%s' % (calendar_year, cost_factors)

        if cache_key not in cache:
            if type(cost_factors) is not list:
                cost_factors = [cost_factors]
            attrs = CostFactorsEnergySecurity.get_class_attributes(cost_factors)

            result = omega_globals.session.query(*attrs).filter(CostFactorsEnergySecurity.calendar_year == calendar_year).all()[0]

            if len(cost_factors) == 1:
                cache[cache_key] = result[0]
            else:
                cache[cache_key] = result

        return cache[cache_key]


    @staticmethod
    def init_database_from_file(filename, verbose=False):
        cache.clear()

        if verbose:
            omega_log.logwrite(f'\nInitializing database from {filename}...')

        input_template_name = 'context_cost_factors-energysecurity'
        input_template_version = 0.2
        input_template_columns = {'calendar_year',
                                  'dollar_basis',
                                  'dollars_per_gallon',
                                  'foreign_oil_fraction',
                                  }

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)
            df = df.loc[df['dollar_basis'] != 0, :]

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            deflators = pd.read_csv(omega_globals.options.ip_deflators_file, skiprows=1, index_col=0).to_dict('index')
            df = gen_fxns.adjust_dollars(df, deflators, omega_globals.options.analysis_dollar_basis,
                                         'dollars_per_gallon')

            if not template_errors:
                obj_list = []
                # load data into database
                for i in df.index:
                    obj_list.append(CostFactorsEnergySecurity(
                        calendar_year = df.loc[i, 'calendar_year'],
                        dollar_basis = df.loc[i, 'dollar_basis'],
                        dollars_per_gallon = df.loc[i, 'dollars_per_gallon'],
                        foreign_oil_fraction = df.loc[i, 'foreign_oil_fraction'],
                    ))
                omega_globals.session.add_all(obj_list)
                omega_globals.session.flush()

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        init_omega_db(omega_globals.options.verbose)
        omega_log.init_logfile()

        SQABase.metadata.create_all(omega_globals.engine)

        init_fail = []

        init_fail += CostFactorsEnergySecurity.init_database_from_file(omega_globals.options.energysecurity_cost_factors_file,
                                                                       verbose=omega_globals.options.verbose)

        if not init_fail:
            dump_omega_db_to_csv(omega_globals.options.database_dump_folder)
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)

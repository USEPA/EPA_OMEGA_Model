"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents $/mile cost estimates associated with congestion and noise associated with road travel.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,context_cost_factors-congestion-noise,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        reg_class_id,dollar_basis,congestion_cost_dollars_per_mile,noise_cost_dollars_per_mile
        car,2018,0.063390239,0.000940863
        truck,2018,0.056598428,0.000940863

Data Column Name and Description
    :reg_class_id:
        Vehicle regulatory class at the time of certification, e.g. 'car','truck'.  Reg class definitions may differ
        across years within the simulation based on policy changes. ``reg_class_id`` can be considered a 'historical'
        or 'legacy' reg class.

    :dollar_basis:
        The dollar basis of values within the table. Values are converted in-code to 'analysis_dollar_basis' using the
        implicit_price_deflators input file.

    :congestion_cost_dollars_per_mile:
        The cost per vehicle mile traveled associated with congestion.

    :noise_cost_dollars_per_mile:
        The cost per vehicle mile traveled associated with noise.


----

**CODE**

"""

from omega_model import *
import omega_model.effects.general_functions as gen_fxns

_cache = dict()


class CostFactorsCongestionNoise(SQABase, OMEGABase):
    # --- database table properties ---
    __tablename__ = 'cost_factors_congestion_noise'
    index = Column('index', Integer, primary_key=True)
    reg_class_id = Column(String)
    dollar_basis = Column(Float)
    congestion_cost_dollars_per_mile = Column(Float)
    noise_cost_dollars_per_mile = Column(Float)

    @staticmethod
    def get_cost_factors(reg_class_id, cost_factors):
        """

        Args:
            reg_class_id: reg class to get cost factors for
            cost_factors: name of cost factor or list of cost factor attributes to get

        Returns: cost factor or list of cost factors

        """
        cache_key = '%s_%s' % (reg_class_id, cost_factors)

        if cache_key not in _cache:
            if type(cost_factors) is not list:
                cost_factors = [cost_factors]
            attrs = CostFactorsCongestionNoise.get_class_attributes(cost_factors)

            result = omega_globals.session.query(*attrs).filter(CostFactorsCongestionNoise.reg_class_id == reg_class_id).all()[0]

            if len(cost_factors) == 1:
                _cache[cache_key] = result[0]
            else:
                _cache[cache_key] = result

        return _cache[cache_key]

    @staticmethod
    def init_database_from_file(filename, verbose=False):
        _cache.clear()

        if verbose:
            omega_log.logwrite(f'\nInitializing database from {filename}...')

        input_template_name = 'context_cost_factors-congestion-noise'
        input_template_version = 0.1
        input_template_columns = {'reg_class_id',
                                  'dollar_basis',
                                  'congestion_cost_dollars_per_mile',
                                  'noise_cost_dollars_per_mile',
                                  }

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)
            df = df.loc[df['dollar_basis'] != 0, :]

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            cols_to_convert = [col for col in df.columns if 'dollars_per_mile' in col]

            df = gen_fxns.adjust_dollars(df, 'ip_deflators', omega_globals.options.analysis_dollar_basis, *cols_to_convert)

            if not template_errors:
                obj_list = []
                # load data into database
                for i in df.index:
                    obj_list.append(CostFactorsCongestionNoise(
                        reg_class_id = df.loc[i, 'reg_class_id'],
                        dollar_basis = df.loc[i, 'dollar_basis'],
                        congestion_cost_dollars_per_mile = df.loc[i, 'congestion_cost_dollars_per_mile'],
                        noise_cost_dollars_per_mile = df.loc[i, 'noise_cost_dollars_per_mile'],
                    ))
                omega_globals.session.add_all(obj_list)
                omega_globals.session.flush()

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        from effects.ip_deflators import ImplictPriceDeflators

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        init_omega_db(omega_globals.options.verbose)
        omega_log.init_logfile()

        SQABase.metadata.create_all(omega_globals.engine)

        init_fail = []

        init_fail += ImplictPriceDeflators.init_from_file(omega_globals.options.ip_deflators_file,
                                                          verbose=omega_globals.options.verbose)

        init_fail += CostFactorsCongestionNoise.init_database_from_file(omega_globals.options.congestion_noise_cost_factors_file,
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

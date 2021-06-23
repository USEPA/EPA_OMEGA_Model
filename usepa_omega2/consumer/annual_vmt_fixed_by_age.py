"""


----

**CODE**

"""

from usepa_omega2 import *

cache = dict()


class AnnualVMTFixedByAge(SQABase, OMEGABase):
    # --- database table properties ---
    __tablename__ = 'annual_vmt_fixed_by_age'
    index = Column('index', Integer, primary_key=True)

    age = Column('age', Numeric)
    market_class_ID = Column('market_class_id', String, ForeignKey('market_classes.market_class_id'))
    annual_vmt = Column('annual_vmt', Numeric)

    @staticmethod
    def get_vmt(market_class_id, age):
        cache_key = '%s_%s' % (market_class_id, age)

        if cache_key not in cache:
            cache[cache_key] = float(globals.session.query(AnnualVMTFixedByAge.annual_vmt).
                                     filter(AnnualVMTFixedByAge.market_class_ID == market_class_id).
                                     filter(AnnualVMTFixedByAge.age == age).scalar())

        return cache[cache_key]

    @staticmethod
    def init_database_from_file(filename, verbose=False):
        cache.clear()

        if verbose:
            omega_log.logwrite(f'\nInitializing database from {filename}...')

        input_template_name = 'annual_vmt_fixed_by_age'
        input_template_version = 0.0001
        input_template_columns = {'age', 'market_class_id', 'annual_vmt'}

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
                    obj_list.append(AnnualVMTFixedByAge(
                        age=df.loc[i, 'age'],
                        market_class_ID=df.loc[i, 'market_class_id'],
                        annual_vmt=df.loc[i, 'annual_vmt'],
                    ))
                globals.session.add_all(obj_list)
                globals.session.flush()

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        # set up global variables:
        globals.options = OMEGARuntimeOptions()
        init_omega_db()
        omega_log.init_logfile()

        from consumer.market_classes import MarketClass  # needed for market class ID

        SQABase.metadata.create_all(globals.engine)

        init_fail = []
        init_fail += MarketClass.init_database_from_file(globals.options.market_classes_file,
                                                         verbose=globals.options.verbose)

        init_fail += AnnualVMTFixedByAge.init_database_from_file(globals.options.annual_vmt_fixed_by_age_file,
                                                                 verbose=globals.options.verbose)

        if not init_fail:
            dump_omega_db_to_csv(globals.options.database_dump_folder)
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)

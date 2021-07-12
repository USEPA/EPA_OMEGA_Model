"""

**Routines to load and provide access to annual vehicle miles travelled (VMT) by market class and age.**

The data represents a fixed VMT schedule by age.

----

**CODE**

"""

from omega_model import *

cache = dict()


class AnnualVMTFixedByAge(SQABase, OMEGABase):
    """
    Loads and provides access to VMT by market class and age.

    """
    # --- database table properties ---
    __tablename__ = 'annual_vmt_fixed_by_age'
    index = Column(Integer, primary_key=True)  #: database table index

    age = Column(Numeric)  #: vehicle age
    market_class_ID = Column('market_class_id', String, ForeignKey('market_classes.market_class_id'))  #: vehicle market class
    annual_vmt = Column(Numeric)  #: vehicle miles travelled

    @staticmethod
    def get_vmt(market_class_id, age):
        """
        Get vehicle miles travelled by market class and age.

        Args:
            market_class_id (str): market class id, e.g. 'hauling.ICE'
            age (int): vehicle age in years

        Returns:
            (float) Vehicle miles travelled.

        """
        cache_key = '%s_%s' % (market_class_id, age)

        if cache_key not in cache:
            cache[cache_key] = float(omega_globals.session.query(AnnualVMTFixedByAge.annual_vmt).
                                     filter(AnnualVMTFixedByAge.market_class_ID == market_class_id).
                                     filter(AnnualVMTFixedByAge.age == age).scalar())

        return cache[cache_key]

    @staticmethod
    def init_database_from_file(filename, verbose=False):
        """

        Initialize class data from input file.

        Args:
            filename (str): name of input file
            verbose (bool): enable additional console and logfile output if True

        Returns:
            List of template/input errors, else empty list on success

        """
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
                omega_globals.session.add_all(obj_list)
                omega_globals.session.flush()

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        # set up global variables:
        omega_globals.options = OMEGARuntimeOptions()
        init_omega_db(omega_globals.options.verbose)
        omega_log.init_logfile()

        from consumer.market_classes import MarketClass  # needed for market class ID

        SQABase.metadata.create_all(omega_globals.engine)

        init_fail = []
        init_fail += MarketClass.init_database_from_file(omega_globals.options.market_classes_file,
                                                         verbose=omega_globals.options.verbose)

        init_fail += AnnualVMTFixedByAge.init_database_from_file(omega_globals.options.annual_vmt_fixed_by_age_file,
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

"""

**Routines to load and provide access to annual vehicle miles travelled (VMT) by market class and age.**

The data represents a fixed VMT schedule by age.

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.  The header uses a dynamic format.

The data represents the re-registered proportion of vehicles by age and market class.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,``[module_name]``,input_template_version:,0.1

Sample Header
    .. csv-table::

       input_template_name:, consumer.annual_vmt_fixed_by_age, input_template_version:, 0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        age,market_class_id,annual_vmt
        0,non_hauling.BEV,14699.55515
        1,non_hauling.BEV,14251.70373
        2,non_hauling.BEV,14025.35397

:age:
    Vehicle age, in years

:market_class_id:
    Vehicle market class ID, e.g. 'hauling.ICE'

:annual_vmt:
    Vehicle miles travelled per year at the given age

----

**CODE**

"""

from omega_model import *

cache = dict()


class AnnualVMT(OMEGABase, SQABase, AnnualVMTBase):
    """
    Loads and provides access to VMT by market class and age.

    """
    # --- database table properties ---
    __tablename__ = 'annual_vmt_fixed_by_age'
    index = Column(Integer, primary_key=True)  #: database table index

    age = Column(Numeric)  #: vehicle age
    market_class_id = Column('market_class_id', String, ForeignKey('market_classes.market_class_id'))  #: vehicle market class
    annual_vmt = Column(Numeric)  #: vehicle miles travelled

    @staticmethod
    def get_vmt(market_class_id, age, **kwargs):
        """
        Get vehicle miles travelled by market class and age.

        Args:
            **kwargs:
            market_class_id (str): market class id, e.g. 'hauling.ICE'
            age (int): vehicle age in years

        Returns:
            (float) Vehicle miles travelled.

        """
        cache_key = '%s_%s' % (market_class_id, age)

        if cache_key not in cache:
            cache[cache_key] = float(omega_globals.session.query(AnnualVMT.annual_vmt).
                                     filter(AnnualVMT.market_class_id == market_class_id).
                                     filter(AnnualVMT.age == age).scalar())

        return cache[cache_key]

    @staticmethod
    def init_from_file(filename, verbose=False):
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

        input_template_name = __name__
        input_template_version = 0.1
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
                    obj_list.append(AnnualVMT(
                        age=df.loc[i, 'age'],
                        market_class_id=df.loc[i, 'market_class_id'],
                        annual_vmt=df.loc[i, 'annual_vmt'],
                    ))
                omega_globals.session.add_all(obj_list)
                omega_globals.session.flush()

        return template_errors


if __name__ == '__main__':

    __name__ = '%s.%s' % (file_io.get_parent_foldername(__file__), file_io.get_filename(__file__))

    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        import importlib

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()

        init_fail = []

        # pull in reg classes before building database tables (declaring classes) that check reg class validity
        module_name = get_template_name(omega_globals.options.policy_reg_classes_file)
        omega_globals.options.RegulatoryClasses = importlib.import_module(module_name).RegulatoryClasses
        init_fail += omega_globals.options.RegulatoryClasses.init_from_file(
            omega_globals.options.policy_reg_classes_file)

        init_omega_db(omega_globals.options.verbose)
        omega_log.init_logfile()

        from consumer.market_classes import MarketClass  # needed for market class ID

        SQABase.metadata.create_all(omega_globals.engine)

        init_fail += MarketClass.init_database_from_file(omega_globals.options.market_classes_file,
                                                         verbose=omega_globals.options.verbose)

        init_fail += AnnualVMT.init_from_file(omega_globals.options.annual_vmt_file,
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

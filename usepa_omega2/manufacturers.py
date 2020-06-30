"""
manufacturers.py
================


"""

from usepa_omega2 import *


class Manufacturer(SQABase):
    # --- database table properties ---
    __tablename__ = 'manufacturers'
    manufacturer_ID = Column('manufacturer_id', String, primary_key=True)
    vehicles = relationship('Vehicle', back_populates='manufacturer')

    # --- static properties ---
    # name = Column(String, default='USA Motors')

    def __repr__(self):
        return "<OMEGA2 %s object at 0x%x>" % (type(self).__name__,  id(self))

    def __str__(self):
        s = '\n<manufacturer.Manufacturer object at %#x>\n' % id(self)
        for k in self.__dict__:
            s = s + k + ' = ' + str(self.__dict__[k]) + '\n'
        return s

    def init_database_from_file(filename, session, verbose=False):
        print('\nInitializing database from %s...' % filename)

        input_template_name = 'manufacturers'
        input_template_version = 0.0003
        input_template_columns = {'manufacturer_id'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version, verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                obj_list = []
                # load data into database
                for i in df.index:
                    obj_list.append(Manufacturer(
                        manufacturer_ID=df.loc[i, 'manufacturer_id'],
                        # name=df.loc[i, 'name'],
                    ))
                session.add_all(obj_list)
                session.flush()

        return template_errors


if __name__ == '__main__':
    if '__file__' in locals():
        print(fileio.get_filenameext(__file__))

    from fuels import *
    from market_classes import *
    from vehicles import *

    SQABase.metadata.create_all(engine)

    init_fail = []
    init_fail = init_fail + Manufacturer.init_database_from_file(o2_options.manufacturers_file, session, verbose=o2_options.verbose)

    if not init_fail:
        dump_database_to_csv(engine, o2_options.database_dump_folder, verbose=o2_options.verbose)

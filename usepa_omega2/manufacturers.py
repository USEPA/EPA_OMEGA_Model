"""
manufacturers.py
===============


"""

from usepa_omega2 import *


class Manufacturer(SQABase):
    # --- database table properties ---
    __tablename__ = 'manufacturers'
    manufacturer_ID = Column('manufacturer_id', Integer, primary_key=True)

    # --- static properties ---
    name = Column(String, default='USAMotors')

    def __repr__(self):
        return "<OMEGA2 %s object at 0x%x>" % (type(self).__name__,  id(self))

    def __str__(self):
        s = '\n<manufacturer.Manufacturer object at %#x>\n' % id(self)
        for k in self.__dict__:
            s = s + k + ' = ' + str(self.__dict__[k]) + '\n'
        return s

    # def init_database(filename, session, verbose=False):
    #     print('\nInitializing database from %s...' % filename)
    #
    #     template_errors = validate_template_version_info(filename, input_template_name, input_template_version, verbose=verbose)
    #
    #     if not template_errors:
    #         # read in the data portion of the input file
    #         df = pd.read_csv(filename, skiprows=1)
    #
    #         template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)
    #
    #         if not template_errors:
    #             pass
    #
    #     return template_errors


if __name__ == '__main__':
    print(fileio.get_filenameext(__file__))

    session = Session(bind=engine)
    SQABase.metadata.create_all(engine)

"""
fuels.py
==========


"""

from usepa_omega2 import *


class Fuel(SQABase):
    # --- database table properties ---
    __tablename__ = 'fuels'
    fuel_ID = Column('fuel_id', Integer, primary_key=True)
    unit = Column('unit', Enum(*fuel_units, validate_strings=True))
    energy_density_MJ_per_unit = Column('energy_density_megajoules_per_unit', Float)


if __name__ == '__main__':
    print(fileio.get_filenameext(__file__))

    session = Session(bind=engine)
    SQABase.metadata.create_all(engine)

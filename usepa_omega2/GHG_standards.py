"""
GHG_standards.py
==========


"""

from usepa_omega2 import *


class GHGStandard(SQABase):
    # --- database table properties ---
    __tablename__ = 'ghg_standards'
    model_year = Column(Integer, primary_key=True)
    reg_class_ID = Column('reg_class_id', Enum(*reg_classes, validate_strings=True), primary_key=True)
    GHG_target_CO2_grams_per_mile = Column('ghg_target_co2_grams_per_mile', Float)
    lifetime_VMT = Column('lifetime_vmt', Float)


if __name__ == '__main__':
    print(fileio.get_filenameext(__file__))

    session = Session(bind=engine)
    SQABase.metadata.create_all(engine)

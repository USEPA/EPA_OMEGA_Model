"""
showroom_annual_data.py
==========


"""

from usepa_omega2 import *


class ShowroomData(SQABase):
    # --- database table properties ---
    __tablename__ = 'showroom_annual_data'
    market_class_ID = Column('market_class_id', Integer, primary_key=True)

    annual_VMT = Column('annual_vmt', Integer)
    calendar_year = Column(Float)
    demanded_sales_count = Column(Integer)


if __name__ == '__main__':
    print(fileio.get_filenameext(__file__))

    session = Session(bind=engine)
    SQABase.metadata.create_all(engine)

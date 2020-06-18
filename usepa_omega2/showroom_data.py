"""
showroom_data.py
==========


"""

from usepa_omega2 import *


class ShowroomData(SQABase):
    # --- database table properties ---
    __tablename__ = 'showroom_data'
    market_class_ID = Column('market_class_id', Integer, primary_key=True)

    annual_VMT = Column('annual_vmt', Integer)
    payback_years = Column(Float)
    price_amortization_period = Column(Float)
    discount_rate = Column(Float)
    share_weight = Column(Float)


if __name__ == '__main__':
    print(fileio.get_filenameext(__file__))

    session = Session(bind=engine)
    SQABase.metadata.create_all(engine)

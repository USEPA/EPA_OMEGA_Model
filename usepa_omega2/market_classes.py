"""
market_classes.py
==========


"""

from usepa_omega2 import *


class MarketClass(SQABase):
    # --- database table properties ---
    __tablename__ = 'market_classes'
    market_class_ID = Column('market_class_id', Integer, primary_key=True)
    fueling_class = Column(Enum(*fueling_classes, validate_strings=True))
    hauling_class = Column(Enum(*hauling_classes, validate_strings=True))
    ownership_class = Column(Enum(*ownership_classes, validate_strings=True))


if __name__ == '__main__':
    print(fileio.get_filenameext(__file__))

    session = Session(bind=engine)
    SQABase.metadata.create_all(engine)

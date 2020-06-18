"""
cost_curves.py
==========


"""

from usepa_omega2 import *


class CostCurve(SQABase):
    # --- database table properties ---
    __tablename__ = 'cost_curves'
    index = Column('index', Integer, primary_key=True)

    cost_curve_class = Column(String)
    calendar_year = Column(Integer)
    cost_dollars = Column(Float)
    CO2_grams_per_mile = Column('co2_grams_per_mile', Float)

    def calculate_generalized_cost(self, market_class_ID):
        print(market_class_ID)


if __name__ == '__main__':
    print(fileio.get_filenameext(__file__))

    session = Session(bind=engine)
    SQABase.metadata.create_all(engine)

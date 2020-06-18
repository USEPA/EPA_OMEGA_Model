"""
fuel_scenario_data.py
==========


"""

from usepa_omega2 import *


class FuelScenarioAnnualData(SQABase):
    # --- database table properties ---
    __tablename__ = 'fuel_scenario_annual_data'
    fuel_ID = Column('fuel_id', Integer, primary_key=True)
    scenario_ID = Column('scenario_id', String)
    calendar_year = Column(Integer)
    cost_dollars_per_unit = Column(Float)
    upstream_CO2_per_unit = Column('upstream_co2_per_unit', Float)


if __name__ == '__main__':
    print(fileio.get_filenameext(__file__))

    session = Session(bind=engine)
    SQABase.metadata.create_all(engine)

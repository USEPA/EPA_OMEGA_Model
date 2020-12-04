"""

monetized_effects_data.py
=========================
"""
import pandas as pd

import o2
from usepa_omega2 import *


class MonetizedEffectsData(SQABase, OMEGABase):
    # --- database table properties ---
    __tablename__ = 'monetized_effects_data'
    index = Column('index', Integer, primary_key=True)
    vehicle_ID = Column('vehicle_id', Integer, ForeignKey('vehicles.vehicle_id'))
    calendar_year = Column(Numeric)
    age = Column(Numeric)
    discount_status = Column(String)
    fuel_30_social_cost_dollars = Column(Float)
    fuel_70_social_cost_dollars = Column(Float)
    congestion_30_social_cost_dollars = Column(Float)
    congestion_70_social_cost_dollars = Column(Float)
    maintenance_30_social_cost_dollars = Column(Float)
    maintenance_70_social_cost_dollars = Column(Float)
    refueling_30_social_cost_dollars = Column(Float)
    refueling_70_social_cost_dollars = Column(Float)
    driving_30_social_cost_dollars = Column(Float)
    driving_70_social_cost_dollars = Column(Float)
    co2_domestic_25_social_cost_dollars = Column(Float)
    co2_domestic_30_social_cost_dollars = Column(Float)
    co2_domestic_70_social_cost_dollars = Column(Float)
    ch4_domestic_25_social_cost_dollars = Column(Float)
    ch4_domestic_30_social_cost_dollars = Column(Float)
    ch4_domestic_70_social_cost_dollars = Column(Float)
    n2o_domestic_25_social_cost_dollars = Column(Float)
    n2o_domestic_30_social_cost_dollars = Column(Float)
    n2o_domestic_70_social_cost_dollars = Column(Float)
    co2_global_25_social_cost_dollars = Column(Float)
    co2_global_30_social_cost_dollars = Column(Float)
    co2_global_70_social_cost_dollars = Column(Float)
    ch4_global_25_social_cost_dollars = Column(Float)
    ch4_global_30_social_cost_dollars = Column(Float)
    ch4_global_70_social_cost_dollars = Column(Float)
    n2o_global_25_social_cost_dollars = Column(Float)
    n2o_global_30_social_cost_dollars = Column(Float)
    n2o_global_70_social_cost_dollars = Column(Float)
    pm25_low_mortality_30_social_cost_dollars = Column(Float)
    pm25_high_mortality_30_social_cost_dollars = Column(Float)
    nox_low_mortality_30_social_cost_dollars = Column(Float)
    nox_high_mortality_30_social_cost_dollars = Column(Float)
    sox_low_mortality_30_social_cost_dollars = Column(Float)
    sox_high_mortality_30_social_cost_dollars = Column(Float)
    pm25_low_mortality_70_social_cost_dollars = Column(Float)
    pm25_high_mortality_70_social_cost_dollars = Column(Float)
    nox_low_mortality_70_social_cost_dollars = Column(Float)
    nox_high_mortality_70_social_cost_dollars = Column(Float)
    sox_low_mortality_70_social_cost_dollars = Column(Float)
    sox_high_mortality_70_social_cost_dollars = Column(Float)


    @staticmethod
    def update_undiscounted_monetized_effects_data(vehicle):

        med = o2.session.query(MonetizedEffectsData).\
            filter(MonetizedEffectsData.vehicle_ID == vehicle.vehicle_ID).\
            filter(MonetizedEffectsData.calendar_year == vehicle.calendar_year).\
            filter(MonetizedEffectsData.age == vehicle.age).\
            filter(MonetizedEffectsData.discount_status == 'undiscounted').one_or_none()

        if med:
            pass
        else:
            o2.session.add(MonetizedEffectsData(vehicle_ID=vehicle.vehicle_ID,
                                                calendar_year=vehicle.calendar_year,
                                                age=vehicle.age,
                                                discount_status='undiscounted'))

        med = o2.session.query(MonetizedEffectsData). \
            filter(MonetizedEffectsData.vehicle_ID == vehicle.vehicle_ID). \
            filter(MonetizedEffectsData.calendar_year == vehicle.calendar_year). \
            filter(MonetizedEffectsData.age == vehicle.age).\
            filter(MonetizedEffectsData.discount_status == 'undiscounted').one()

        return med

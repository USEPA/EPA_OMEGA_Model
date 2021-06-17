"""


----

**CODE**

"""

# import pandas as pd

from usepa_omega2 import *


class CostEffectsNonEmissions(SQABase, OMEGABase):
    # --- database table properties ---
    __tablename__ = 'cost_effects_non_emissions'
    index = Column('index', Integer, primary_key=True)
    vehicle_ID = Column('vehicle_id', Integer, ForeignKey('vehicles.vehicle_id'))
    calendar_year = Column(Numeric)
    age = Column(Numeric)
    discount_status = Column(String)
    fuel_30_retail_cost_dollars = Column(Float)
    fuel_70_retail_cost_dollars = Column(Float)
    fuel_30_social_cost_dollars = Column(Float)
    fuel_70_social_cost_dollars = Column(Float)
    energy_security_30_social_cost_dollars = Column(Float)
    energy_security_70_social_cost_dollars = Column(Float)
    congestion_30_social_cost_dollars = Column(Float)
    congestion_70_social_cost_dollars = Column(Float)
    noise_30_social_cost_dollars = Column(Float)
    noise_70_social_cost_dollars = Column(Float)
    maintenance_30_social_cost_dollars = Column(Float)
    maintenance_70_social_cost_dollars = Column(Float)
    refueling_30_social_cost_dollars = Column(Float)
    refueling_70_social_cost_dollars = Column(Float)
    driving_30_social_cost_dollars = Column(Float)
    driving_70_social_cost_dollars = Column(Float)

"""


----

**CODE**

"""

from omega_model import *


class CostEffectsSCC(SQABase, OMEGABase):
    # --- database table properties ---
    __tablename__ = 'cost_effects_scc'
    index = Column('index', Integer, primary_key=True)
    vehicle_ID = Column('vehicle_id', Integer, ForeignKey('vehicles.vehicle_id'))
    calendar_year = Column(Numeric)
    age = Column(Numeric)
    discount_status = Column(String)
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


    @staticmethod
    def update_undiscounted_monetized_effects_data(med_veh, med_dict):

        for k, v in med_dict.items():
            med_veh.__setattr__(k, v)

        omega_globals.session.flush()

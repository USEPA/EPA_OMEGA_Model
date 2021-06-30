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
    discount_rate = Column(Float)
    co2_global_5_cost_dollars = Column(Float)
    co2_global_3_cost_dollars = Column(Float)
    co2_global_25_cost_dollars = Column(Float)
    co2_global_395_cost_dollars = Column(Float)
    ch4_global_5_cost_dollars = Column(Float)
    ch4_global_3_cost_dollars = Column(Float)
    ch4_global_25_cost_dollars = Column(Float)
    ch4_global_395_cost_dollars = Column(Float)
    n2o_global_5_cost_dollars = Column(Float)
    n2o_global_3_cost_dollars = Column(Float)
    n2o_global_25_cost_dollars = Column(Float)
    n2o_global_395_cost_dollars = Column(Float)


    @staticmethod
    def update_undiscounted_monetized_effects_data(med_veh, med_dict):

        for k, v in med_dict.items():
            med_veh.__setattr__(k, v)

        common.omega_globals.session.flush()

"""

----

**CODE**

"""


from omega_model import *


class CostEffectsCriteria(SQABase, OMEGABase):
    # --- database table properties ---
    __tablename__ = 'cost_effects_criteria'
    index = Column(Integer, primary_key=True)
    vehicle_ID = Column('vehicle_id', Integer, ForeignKey('vehicles.vehicle_id'))
    calendar_year = Column(Numeric)
    age = Column(Numeric)
    discount_rate = Column(Float)
    pm25_tailpipe_3_cost_dollars = Column(Float)
    pm25_upstream_3_cost_dollars = Column(Float)
    nox_tailpipe_3_cost_dollars = Column(Float)
    nox_upstream_3_cost_dollars = Column(Float)
    so2_tailpipe_3_cost_dollars = Column(Float)
    so2_upstream_3_cost_dollars = Column(Float)
    pm25_tailpipe_7_cost_dollars = Column(Float)
    pm25_upstream_7_cost_dollars = Column(Float)
    nox_tailpipe_7_cost_dollars = Column(Float)
    nox_upstream_7_cost_dollars = Column(Float)
    so2_tailpipe_7_cost_dollars = Column(Float)
    so2_upstream_7_cost_dollars = Column(Float)
    criteria_tailpipe_3_cost_dollars = Column(Float)
    criteria_upstream_3_cost_dollars = Column(Float)
    criteria_tailpipe_7_cost_dollars = Column(Float)
    criteria_upstream_7_cost_dollars = Column(Float)
    criteria_3_cost_dollars = Column(Float)
    criteria_7_cost_dollars = Column(Float)

    @staticmethod
    def update_undiscounted_cost_effects_criteria(med_veh, med_dict):

        for k, v in med_dict.items():
            med_veh.__setattr__(k, v)

        common.omega_globals.session.flush()

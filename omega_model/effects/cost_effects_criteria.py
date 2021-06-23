"""


----

**CODE**

"""


from omega_model import *


class CostEffectsCriteria(SQABase, OMEGABase):
    # --- database table properties ---
    __tablename__ = 'cost_effects_criteria'
    index = Column('index', Integer, primary_key=True)
    vehicle_ID = Column('vehicle_id', Integer, ForeignKey('vehicles.vehicle_id'))
    calendar_year = Column(Numeric)
    age = Column(Numeric)
    discount_status = Column(String)
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
    def update_undiscounted_cost_effects_criteria(med_veh, med_dict):

        for k, v in med_dict.items():
            med_veh.__setattr__(k, v)

        omega_globals.session.flush()

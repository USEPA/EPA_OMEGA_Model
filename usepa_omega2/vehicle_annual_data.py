"""
vehicle_annual_data.py
==========


"""

from usepa_omega2 import *


class VehicleAnnualData(SQABase):
    # --- database table properties ---
    __tablename__ = 'vehicle_annual_data'
    vehicle_ID = Column('vehicle_id', Integer, ForeignKey('vehicles.vehicle_id'), primary_key=True)
    calendar_year = Column(Integer)
    registered_count = Column(Integer)


if __name__ == '__main__':
    if '__file__' in locals():
        print(fileio.get_filenameext(__file__))

    from manufacturers import *  # required by vehicles
    from fuels import *  # required by vehicles
    from market_classes import *  # required by vehicles
    from vehicles import *  # for foreign key vehicle_ID

    session = Session(bind=engine)
    SQABase.metadata.create_all(engine)

    # dump_database_to_csv(engine, o2_options.database_dump_folder, verbose=o2_options.verbose)

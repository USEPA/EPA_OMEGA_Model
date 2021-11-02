"""


----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *

_cache = dict()


class VehicleAnnualData(SQABase, OMEGABase):
    """
    **Stores and retrieves vehicle annual data, which includes age, registered count, vehicle miles travelled, etc.**

    """
    # --- database table properties ---
    __tablename__ = 'vehicle_annual_data'
    index = Column('index', Integer, primary_key=True)  #: database table index
    vehicle_id = Column('vehicle_id', Integer, ForeignKey('vehicles.vehicle_id'))  #: vehicle ID, e.g. ``1``
    calendar_year = Column(Numeric)  #: calendar year, e.g. ``2030``
    age = Column(Numeric)  #: vehicle age, new vehicles have age ``0``
    registered_count = Column(Float)  #: count of vehicles remaining in service (registered)
    annual_vmt = Column(Float)  #: vehicle miles travelled in the given year
    vmt = Column(Float)  #: annual vehicle miles travelled times registered count


    @staticmethod
    def update_registered_count(vehicle, calendar_year, registered_count):
        """
        Update vehicle registered count and / or create initial vehicle annual data table entry.

        Args:
            vehicle (VehicleFinal): the vehicle whose count is being updated
            calendar_year (int): the calendar year to update registered count it
            registered_count (float): number of vehicle that are still in service (registered)

        Returns:
            Nothing, updates vehicle annual data table

        """
        age = calendar_year - vehicle.model_year

        vad = omega_globals.session.query(VehicleAnnualData). \
            filter(VehicleAnnualData.vehicle_id == vehicle.vehicle_id). \
            filter(VehicleAnnualData.calendar_year == calendar_year). \
            filter(VehicleAnnualData.age == age).one_or_none()

        if vad:
            vad.registered_count = registered_count
        else:
            omega_globals.session.add(VehicleAnnualData(vehicle_id=vehicle.vehicle_id,
                                                        calendar_year=calendar_year,
                                                        registered_count=registered_count,
                                                        age=age))

    @staticmethod
    def get_calendar_years():
        """
        Get the calendar years that have vehicle annual data.

        Returns:
            List of calendar years that have vehicle annual data.

        """
        return sql_unpack_result(omega_globals.session.query(VehicleAnnualData.calendar_year).all())

    @staticmethod
    def get_vehicle_annual_data(calendar_year, compliance_id=None, attributes=None):
        """
        Get vehicle annual data for the given calendar year.

        Args:
            calendar_year (int): calendar to get data for
            attributes (str, [strs]): optional name of attribute(s) to retrieve instead of all data

        Returns:
            A list of VehicleAnnualData objects, or a list of n-tuples of the requested attribute(s) value(s), e.g.
            ``[(1,), (2,), (3,), ...`` which can be conveniently unpacked by ``omega_db.sql_unpack_result()``

        """
        from producer.vehicles import VehicleFinal

        if attributes is None and compliance_id is None:
            result = omega_globals.session.query(VehicleAnnualData)\
                .filter(VehicleAnnualData.calendar_year == calendar_year).all()
        elif attributes is None and compliance_id is not None:
            result = omega_globals.session.query(VehicleAnnualData)\
                .filter(VehicleAnnualData.calendar_year == calendar_year)\
                .filter(VehicleFinal.compliance_id == compliance_id)\
                .all()
        else:
            if type(attributes) is not list:
                attributes = [attributes]
            attrs = VehicleAnnualData.get_class_attributes(attributes)

            if compliance_id is None:
                result = omega_globals.session.query(*attrs)\
                    .filter(VehicleAnnualData.calendar_year == calendar_year).all()
            else:
                result = omega_globals.session.query(*attrs)\
                    .filter(VehicleAnnualData.calendar_year == calendar_year) \
                    .filter(VehicleFinal.compliance_id == compliance_id) \
                    .filter(VehicleFinal.vehicle_id == VehicleAnnualData.vehicle_id) \
                    .all()

        return result


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        import importlib

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()

        init_fail = []

        # pull in reg classes before building database tables (declaring classes) that check reg class validity
        module_name = get_template_name(omega_globals.options.policy_reg_classes_file)
        omega_globals.options.RegulatoryClasses = importlib.import_module(module_name).RegulatoryClasses
        init_fail += omega_globals.options.RegulatoryClasses.init_from_file(
            omega_globals.options.policy_reg_classes_file)

        module_name = get_template_name(omega_globals.options.market_classes_file)
        omega_globals.options.MarketClass = importlib.import_module(module_name).MarketClass

        init_omega_db(omega_globals.options.verbose)

        from producer.manufacturers import Manufacturer  # required by vehicles
        from context.onroad_fuels import OnroadFuel  # required by vehicles
        from producer.vehicles import VehicleFinal  # for foreign key vehicle_id

        SQABase.metadata.create_all(omega_globals.engine)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)

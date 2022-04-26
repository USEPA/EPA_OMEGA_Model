"""


----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *

_cache = dict()

class VehicleAnnualData(OMEGABase):
    """
    **Stores and retrieves vehicle annual data, which includes age, registered count, vehicle miles travelled, etc.**

    """

    _data = pd.DataFrame()

    def __init__(self, calendar_year, vehicle_id, compliance_id, age, registered_count=0, annual_vmt=0, odometer=0, vmt=0):
        self.calendar_year = calendar_year  #: calendar year, e.g. ``2030``
        self.vehicle_id = vehicle_id  #: vehicle ID, e.g. ``1``
        self.age = age  #: vehicle age, new vehicles have age ``0``
        self.registered_count = registered_count  #: count of vehicles remaining in service (registered)
        self.annual_vmt = annual_vmt  #: vehicle miles travelled in the given year
        self.odometer = odometer  #: the cumulative annual_vmt or odometer reading
        self.vmt = vmt  #: annual vehicle miles travelled times registered count

    @staticmethod
    def create(calendar_year, vehicle_id, compliance_id, age, registered_count=0, annual_vmt=0, odometer=0, vmt=0):
        vad = VehicleAnnualData(calendar_year, vehicle_id, compliance_id, age,
                                registered_count, annual_vmt, odometer, vmt)

        return {'calendar_year': calendar_year, 'compliance_id': compliance_id, 'vehicle_id': vehicle_id,
                'age': age, 'data': vad}

    @staticmethod
    def add_all(vad_list):
        VehicleAnnualData._data = VehicleAnnualData._data.append(vad_list, ignore_index=True)

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

        vad = VehicleAnnualData._data[(VehicleAnnualData._data['calendar_year'] == calendar_year) &
                                      (VehicleAnnualData._data['vehicle_id'] == vehicle.vehicle_id)]

        if vad.empty:
            vad = VehicleAnnualData.create(calendar_year, vehicle.vehicle_id, vehicle.compliance_id, age, registered_count)
            VehicleAnnualData.add_all(vad)
        else:
            vad['data'].item().registered_count = registered_count

    @staticmethod
    def get_calendar_years():
        """
        Get the calendar years that have vehicle annual data.

        Returns:
            List of calendar years that have vehicle annual data.

        """
        return VehicleAnnualData._data['calendar_year'].values

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
            result = VehicleAnnualData._data[VehicleAnnualData._data['calendar_year'] == calendar_year]['data']
        elif attributes is None and compliance_id is not None:
            result = VehicleAnnualData._data[(VehicleAnnualData._data['calendar_year'] == calendar_year) &
                                             (VehicleAnnualData._data['compliance_id'] == compliance_id)]['data']

        return result

    @staticmethod
    def get_odometers(calendar_year):
        data = omega_globals.session.query(VehicleAnnualData.vehicle_id, VehicleAnnualData.odometer).\
            filter(VehicleAnnualData.calendar_year == calendar_year).all()
        return pd.DataFrame(data, columns=['vehicle_id', 'odometer'])

    @staticmethod
    def init_vehicle_annual_data():
        global _data

        _cache.clear()
        VehicleAnnualData._data = pd.DataFrame(columns=('calendar_year', 'compliance_id', 'vehicle_id', 'age', 'data'))

        return []


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

        if not init_fail:
            pass
        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)

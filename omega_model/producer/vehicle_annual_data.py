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

    _data = []

    @staticmethod
    def create(calendar_year, vehicle_id, compliance_id, age, registered_count=0, annual_vmt=0, odometer=0, vmt=0):
        return {'calendar_year': calendar_year, 'compliance_id': compliance_id, 'vehicle_id': vehicle_id,
                'age': age, 'registered_count': registered_count, 'annual_vmt': annual_vmt, 'odometer': odometer,
                'vmt': vmt}

    @staticmethod
    def add_all(vad_list):
        if type(vad_list) == list:
            for vad in vad_list:
                VehicleAnnualData._data.append(vad)
        else:
            VehicleAnnualData._data.append(vad_list)  # , ignore_index=True)

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
        age = int(calendar_year - vehicle.model_year)

        vad = [v for v in VehicleAnnualData._data
               if v['calendar_year'] == calendar_year and v['vehicle_id'] == vehicle.vehicle_id]

        if not vad:
            vad = VehicleAnnualData.create(int(calendar_year), vehicle.vehicle_id, vehicle.compliance_id, age,
                                           registered_count)
            VehicleAnnualData.add_all(vad)
        else:
            vad['registered_count'] = registered_count

    @staticmethod
    def get_calendar_years():
        """
        Get the calendar years that have vehicle annual data.

        Returns:
            List of calendar years that have vehicle annual data.

        """
        return [v['calendar_year'] for v in VehicleAnnualData._data]

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
            result = [v for v in VehicleAnnualData._data
                      if v['calendar_year'] == calendar_year]
        elif attributes is None and compliance_id is not None:
            result = [v for v in VehicleAnnualData._data
                      if v['calendar_year'] == calendar_year and v['compliance_id'] == compliance_id]

        return result

    @staticmethod
    def init_vehicle_annual_data():

        _cache.clear()

        VehicleAnnualData._data = []

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

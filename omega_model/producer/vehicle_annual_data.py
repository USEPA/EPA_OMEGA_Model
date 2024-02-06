"""

**Vehicle annual data module.**

Routines to store and retrieve vehicle annual data, which includes age, registered count, vehicle miles travelled, etc.

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
    def create(calendar_year, vehicle_id, compliance_id, age, reg_class_id, registered_count=0, annual_vmt=0, odometer=0, vmt=0):
        """
        Create a dict of the given values.

        Args:
            calendar_year (int): the calendar year
            vehicle_id (str): the vehicle id
            compliance_id (str): manufacturer name, or 'consolidated_OEM'
            age (int): vehicle age in years
            reg_class_id (str): reg class id, e.g. 'car', 'truck', etc
            registered_count (float): the registered count of the given vehicle
            annual_vmt (float): annual vehicle miles travelled
            odometer (float): the accumulate vehicle miles travelled of the given vehicle
            vmt (float): vehicle miles travelled

        Returns:
            A dict of the given values.

        """
        return {'calendar_year': calendar_year, 'compliance_id': compliance_id, 'vehicle_id': vehicle_id,
                'age': age, 'reg_class_id': reg_class_id, 'registered_count': registered_count,
                'annual_vmt': annual_vmt, 'odometer': odometer, 'vmt': vmt}

    @staticmethod
    def add_all(vad_list):
        """
        Add all vehicle annual data records to the class data set.

        Args:
            vad_list (dict | list): dict or list of vehicle annual data dicts

        Returns:
            Nothing, updates ``VehicleAnnualData._data``

        """
        if type(vad_list) is list:
            for vad in vad_list:
                VehicleAnnualData._data.append(vad)
        else:
            VehicleAnnualData._data.append(vad_list)  # , ignore_index=True)

    @staticmethod
    def update_registered_count(vehicle, calendar_year, registered_count):
        """
        Update vehicle registered count and / or create initial vehicle annual data table entry.

        Args:
            vehicle (Vehicle): the vehicle whose count is being updated
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
                                           vehicle.reg_class_id, registered_count)
            VehicleAnnualData.add_all(vad)
        else:
            vad[0]['registered_count'] = registered_count

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
        Get vehicle annual data for the given calendar year and compliance id, if applicable.

        Args:
            calendar_year (int): calendar to get data for
            compliance_id (str): name of manufacturer, e.g. 'consolidated_OEM'
            attributes (str, [strs]): optional name of attribute(s) to retrieve instead of all data

        Returns:
            A list of VehicleAnnualData dictionaries``

        """
        # from producer.vehicles import Vehicle

        if attributes is None and compliance_id is None:
            result = [v for v in VehicleAnnualData._data
                      if v['calendar_year'] == calendar_year]
        elif attributes is None and compliance_id is not None:
            result = [v for v in VehicleAnnualData._data
                      if v['calendar_year'] == calendar_year and v['compliance_id'] == compliance_id]

        return result

    @staticmethod
    def get_vehicle_annual_data_by_vehicle_id(calendar_year, vehicle_id, attribute_name):
        """
        Get vehicle annual data for the given calendar year.

        Args:
            calendar_year (int): calendar to get data for
            vehicle_id (str): the vehicle_id
            attribute_name (str): the attribute_name for which a value is sought

        Returns:
            The attribute_value for the given attribute_name

        """
        result = [v[attribute_name] for v in VehicleAnnualData._data
                  if v['calendar_year'] == calendar_year and v['vehicle_id'] == vehicle_id]

        return result[0]

    @staticmethod
    def init_vehicle_annual_data():
        """
        Initialize the module by clear caches.

        Returns:
            Nothing, clears cached data.

        """
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

        module_name = get_template_name(omega_globals.options.policy_reg_classes_file)
        omega_globals.options.RegulatoryClasses = importlib.import_module(module_name).RegulatoryClasses
        init_fail += omega_globals.options.RegulatoryClasses.init_from_file(
            omega_globals.options.policy_reg_classes_file)

        module_name = get_template_name(omega_globals.options.market_classes_file)
        omega_globals.options.MarketClass = importlib.import_module(module_name).MarketClass

        from producer.manufacturers import Manufacturer  # required by vehicles
        from context.onroad_fuels import OnroadFuel  # required by vehicles
        from producer.vehicles import Vehicle  # for vehicle_id

        if not init_fail:
            pass
        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            sys.exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)

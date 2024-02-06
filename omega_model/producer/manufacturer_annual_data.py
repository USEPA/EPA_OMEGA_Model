"""

**Routines to create and update yearly manufacturer compliance data.**

Manufacturer annual data is created for each compliance model year as a result of vehicle sales and certification
performance.  Compliance of a model year may be achieve retroactively through the use of credits created by future
model years.

See Also:
    The ``GHG_credits`` module, and ``postproc_session.plot_manufacturer_compliance()`` for credit plotting routines.

----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *


class ManufacturerAnnualData(OMEGABase):
    """
    Stores manufacturer annual target / achieved CO2e Mg and total cost data.

    """
    _data = []

    @staticmethod
    def create_manufacturer_annual_data(model_year, compliance_id, target_co2e_Mg,
                                        calendar_year_cert_co2e_Mg, manufacturer_vehicle_cost_dollars,
                                        model_year_cert_co2e_megagrams=None):
        """
        Create initial manufacturer compliance entry for the given year.
        Final compliance state may depend on future years via credit banking.

        Args:
            model_year (numeric): the compliance model year
            compliance_id (str): manufacturer name, or 'consolidated_OEM'
            target_co2e_Mg (numeric): target CO2e Mg for the model year
            calendar_year_cert_co2e_Mg (numeric): initial compliance state (CO2e Mg) of the vehicles
                produced in the model year
            manufacturer_vehicle_cost_dollars (numeric): total manufacturer vehicle cost
                (sum of vehicle sales X vehicle cost)
            model_year_cert_co2e_megagrams (numeric): manufacturer model year cert CO2e Mg, if known, else ``None``

        Returns:
            Nothing, updates class data

        """
        if not model_year_cert_co2e_megagrams:
            model_year_cert_co2e_megagrams = calendar_year_cert_co2e_Mg

        ManufacturerAnnualData._data.append({'compliance_id': compliance_id, 'model_year': model_year,
                                             'target_co2e_megagrams': target_co2e_Mg,
                                             'calendar_year_cert_co2e_megagrams': calendar_year_cert_co2e_Mg,
                                             'model_year_cert_co2e_megagrams': model_year_cert_co2e_megagrams,
                                             'manufacturer_vehicle_cost_dollars': manufacturer_vehicle_cost_dollars})

    @staticmethod
    def get_target_co2e_Mg(compliance_id):
        """
        Get cert target CO2e in megagrams for each model year.

        Args:
            compliance_id (str): manufacturer name, or 'consolidated_OEM'

        Returns: A list of target CO2e Mg for each model year

        """
        return [mad['target_co2e_megagrams'] for mad in ManufacturerAnnualData._data
                if mad['compliance_id'] == compliance_id]

    @staticmethod
    def get_calendar_year_cert_co2e_Mg(compliance_id):
        """
        Get the initial cert CO2e in megagrams for each calendar year, final certification may be higher or lower
        depending on credit transfers.

        Args:
            compliance_id (str): manufacturer name, or 'consolidated_OEM'

        Returns: A list of initial compliance state data (CO2e Mg) of the vehicles produced by model year

        """
        return [mad['calendar_year_cert_co2e_megagrams'] for mad in ManufacturerAnnualData._data
                if mad['compliance_id'] == compliance_id]

    @staticmethod
    def get_model_year_cert_co2e_Mg(compliance_id):
        """
        Get the final cert CO2e in megagrams for each model year, including the effect of credit transfers.

        Args:
            compliance_id (str): manufacturer name, or 'consolidated_OEM'

        Returns: A list of final achieved certification CO2e Mg for each model year, including credits transferred
        to/from other model years

        """
        return [mad['model_year_cert_co2e_megagrams'] for mad in ManufacturerAnnualData._data
                if mad['compliance_id'] == compliance_id]

    @staticmethod
    def get_total_cost_billions(compliance_id):
        """
        Get total manufacturer new vehicle cost (sum of vehicle prices times vehicle sales) for each model year, in
        billions of dollars.

        Args:
            compliance_id (str): manufacturer name, or 'consolidated_OEM'

        Returns: A list of total manufacturer vehicle costs by model year, in billions of dollars

        """
        return sum([mad['manufacturer_vehicle_cost_dollars'] / 1e9 for mad in ManufacturerAnnualData._data
                if mad['compliance_id'] == compliance_id])

    @staticmethod
    def update_model_year_cert_co2e_Mg(model_year, compliance_id, transaction_amount_Mg):
        """
        Update model year certification CO2e Mg based on the given transaction amount.  Used for credit banking.

        Args:
            model_year (numeric): the model year of the transaction
            compliance_id (str): manufacturer name, or 'consolidated_OEM'
            transaction_amount_Mg (numeric): the transaction amount, may be positive (receiving credits) or negative
                (transferring credits)

        """
        mad = [mad for mad in ManufacturerAnnualData._data
               if mad['model_year'] == model_year and mad['compliance_id'] == compliance_id]

        if mad:
            mad[0]['model_year_cert_co2e_megagrams'] += transaction_amount_Mg

    @staticmethod
    def init_manufacturer_annual_data():
        """
        Initialize the module by clear caches.

        Returns:
            Nothing, clears cached data.

        """
        ManufacturerAnnualData._data = []

        return []


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()

        from manufacturers import Manufacturer  # required by vehicles

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)

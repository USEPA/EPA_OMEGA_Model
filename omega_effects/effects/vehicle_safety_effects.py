

class VehicleSafetyEffects:
    """

    The VehicleSafetyEffects class creates objects containing identifying information and safety effects calculation
    results for a given vehicle.

    """
    def __init__(self):

        self.session_policy = None
        self.session_name = None
        self.vehicle_id = None
        self.base_year_vehicle_id = None
        self.manufacturer_id = None
        self.name = None
        self.calendar_year = None
        self.model_year = None
        self.age = None
        self.base_year_reg_class_id = None
        self.reg_class_id = None
        self.context_size_class = None
        self.in_use_fuel_id = None
        self.market_class_id = None
        self.fueling_class = None
        self.base_year_powertrain_type = None
        self.registered_count = None
        self.context_vmt_adjustment = None
        self.annual_vmt = None
        self.odometer = None
        self.vmt = None
        self.annual_vmt_rebound = None
        self.vmt_rebound = None
        self.body_style = None
        self.footprint_ft2 = None
        self.workfactor = None
        self.change_per_100lbs_below = None
        self.change_per_100lbs_above = None
        self.threshold_lbs = None
        self.base_year_curbweight_lbs = None
        self.curbweight_lbs = None
        self.lbs_changed = None
        self.lbs_changed_below_threshold = None
        self.lbs_changed_above_threshold = None
        self.check_for_0 = None
        self.base_fatality_rate = None
        self.fatality_rate_change_below_threshold = None
        self.fatality_rate_change_above_threshold = None
        self.session_fatality_rate = None
        self.base_fatalities = None
        self.session_fatalities = None

    def update_value(self, update_dict):
        """

        Args:
            update_dict (dict): the class instance attributes as keys along with their values.

        Returns:
            Nothing, but it sets class instance attributes to the values contained in update_dict.

        """
        for k, v in update_dict.items():
            self.__setattr__(k, v)

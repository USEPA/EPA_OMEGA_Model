"""

Functions to adjust vehicle miles traveled to ensure consistency with projections included in the context_stock_vmt.csv
file.

----

**CODE**

"""
from omega_model import *


class AdjustmentsVMT:

    def __init__(self):
        self.dict = dict()

    def calc_vmt_adjustments(self, calendar_years):
        """

        Args:
            calendar_years: The years for which VMT adjustments are to be made.

        Returns:
            Nothing, but it creates a dictionary of adjusted VMT values by calendar year for use in effects calculations.

        """
        from producer.vehicle_annual_data import VehicleAnnualData
        from effects.legacy_fleet import LegacyFleet
        from context.context_stock_vmt import ContextStockVMT


        for calendar_year in calendar_years:
            vads = VehicleAnnualData.get_vehicle_annual_data(calendar_year)

            # first a loop to determine vmt for this calendar year's non-legacy fleet
            calendar_year_vmt = sum(vad['vmt'] for vad in vads if (vad['calendar_year'] - vad['age']) >= calendar_years[0])

            # next sum the vmt for this calendar year's legacy fleet
            calendar_year_legacy_fleet = [v for k, v in LegacyFleet._legacy_fleet.items() if k[1] == calendar_year]
            calendar_year_legacy_fleet_vmt = sum(v['vmt'] for v in calendar_year_legacy_fleet)

            # sum the two to get the fleet vmt
            calendar_year_vmt += calendar_year_legacy_fleet_vmt

            # get projected stock vmt
            context_stock, context_vmt = ContextStockVMT.get_context_stock_vmt(calendar_year)

            # calc the vmt adjustment for this calendar year
            calendar_year_vmt_adj = context_vmt / calendar_year_vmt

            self.dict[calendar_year] = calendar_year_vmt_adj

    def get_vmt_adjustment(self, calendar_year):
        """

        Args:
            calendar_year: int; the calendar year for which the adjustment factor is sought.

        Returns:
            The vmt adjustment factor for the passed calendar year.

        """
        return self.dict[calendar_year]

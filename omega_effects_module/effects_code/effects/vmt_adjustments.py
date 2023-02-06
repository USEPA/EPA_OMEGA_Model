"""

Functions to adjust vehicle miles traveled to ensure consistency with projections included in the context_stock_vmt.csv
file.

----

**CODE**

"""


class AdjustmentsVMT:

    def __init__(self):
        self.dict = dict()

    def calc_vmt_adjustments(self, batch_settings, session_settings):
        """

        Args:
            batch_settings: an instance of the BatchSettings class.
            session_settings: an instance of the SessionSettings class.

        Returns:
            Nothing, but it creates a dictionary of adjusted VMT values by calendar year for use in effects calculations.

        """
        calendar_years = batch_settings.calendar_years

        for calendar_year in calendar_years:

            vads = session_settings.vehicle_annual_data.get_vehicle_annual_data_by_calendar_year(calendar_year)

            # first a loop to determine vmt and registered count for this calendar year's non-legacy fleet
            calendar_year_vmt \
                = sum(vad['vmt'] for vad in vads if (vad['calendar_year'] - vad['age']) >= calendar_years[0])
            calendar_year_stock \
                = sum(vad['registered_count'] for vad in vads if (vad['calendar_year'] - vad['age']) >= calendar_years[0])

            # next sum the vmt and registered count for this calendar year's legacy fleet
            calendar_year_legacy_fleet =\
                [v for k, v in batch_settings.legacy_fleet._legacy_fleet.items() if k[1] == calendar_year]
            calendar_year_legacy_fleet_vmt = sum(v['vmt'] for v in calendar_year_legacy_fleet)
            calendar_year_legacy_fleet_stock = sum(v['registered_count'] for v in calendar_year_legacy_fleet)

            # sum the two to get the fleet vmt
            calendar_year_vmt += calendar_year_legacy_fleet_vmt

            # get projected stock vmt
            context_stock, context_vmt = batch_settings.context_stock_and_vmt.get_context_stock_vmt(calendar_year)

            # calc the vmt adjustment for this calendar year
            calendar_year_vmt_adj = context_vmt / calendar_year_vmt
            calendar_year_legacy_fleet_stock_adj = \
                (context_stock - calendar_year_stock) / calendar_year_legacy_fleet_stock

            self.dict[calendar_year] = {'vmt_adj': calendar_year_vmt_adj,
                                        'legacy_stock_adj': calendar_year_legacy_fleet_stock_adj}

    def get_vmt_adjustment(self, calendar_year):
        """

        Args:
            calendar_year (int): the calendar year for which the adjustment factor is sought.

        Returns:
            The vmt adjustment factor for the passed calendar year.

        """
        return self.dict[calendar_year]['vmt_adj']

    def get_stock_adjustment(self, calendar_year):
        """

        Args:
            calendar_year (int): the calendar year for which the adjustment factor is sought.

        Returns:
            The stock or registered count adjustment factor for the passed calendar year.

        """
        return self.dict[calendar_year]['legacy_stock_adj']

import pandas as pd


class LegacyVsAnalysisFleet:

    """

    """
    def __init__(self):
        self.physical_pivot = pd.DataFrame()
        self.safety_pivot = pd.DataFrame()
        self.index_cols = ['calendar_year', 'fueling_class', 'in_use_fuel_id']
        self.physical_value_cols = [
            'registered_count',
            'vmt',
            'vmt_rebound',
            'fuel_consumption_kwh',
            'fuel_consumption_gallons',
            'co2_vehicle_metrictons',
            'session_fatalities',
        ]
        self.safety_value_cols = [
            'registered_count',
            'base_fatalities',
            'session_fatalities',
            'vmt',
            'vmt_rebound',
        ]

    def create_physical_pivot(self, session_settings, df, fleet):
        """

        Args:
            session_settings: an instance of the SessionSettings class.
            df (DataFrame): physical effects in full detail for a given session.
            fleet (str): e.g., 'ld' or 'md'

        Returns:
            Nothing, but it builds a pivot table DataFrame for inclusion as an output file.

        """
        session_pivot = self.create_pivot(session_settings, df, self.physical_value_cols, fleet)

        self.physical_pivot = pd.concat([self.physical_pivot, session_pivot], axis=0)

    def create_safety_pivot(self, session_settings, df, fleet):
        """

        Args:
            session_settings: an instance of the SessionSettings class.
            df (DataFrame): safety effects in full detail for a given session.
            fleet (str): e.g., 'ld' or 'md'

        Returns:
            Nothing, but it builds a pivot table DataFrame for inclusion as an output file.

        """
        session_pivot = self.create_pivot(session_settings, df, self.safety_value_cols, fleet)

        self.safety_pivot = pd.concat([self.safety_pivot, session_pivot], axis=0)

    def create_pivot(self, session_settings, df, value_cols, fleet):
        """

        Args:
            session_settings: an instance of the SessionSettings class.
            df (DataFrame): safety effects in full detail for a given session.
            value_cols (list): list of attributes to include in the pivot results.
            fleet (str): e.g., 'ld' or 'md'

        Returns:
            A pivot table based on the passed DataFrame.

        """
        p_leg_bev = pd.pivot_table(
            df.loc[(df['manufacturer_id'] == 'legacy_fleet') & (df['fueling_class'] == 'BEV'), :],
            index=self.index_cols,
            values=value_cols, aggfunc='sum'
        )
        p_leg_ice = pd.pivot_table(
            df.loc[(df['manufacturer_id'] == 'legacy_fleet') & (df['fueling_class'] != 'BEV'), :],
            index=self.index_cols,
            values=value_cols, aggfunc='sum'
        )
        p_bev = pd.pivot_table(
            df.loc[(df['manufacturer_id'] != 'legacy_fleet') & (df['fueling_class'] == 'BEV'), :],
            index=self.index_cols,
            values=value_cols, aggfunc='sum'
        )
        p_ice = pd.pivot_table(
            df.loc[(df['manufacturer_id'] != 'legacy_fleet') & (df['fueling_class'] != 'BEV'), :],
            index=self.index_cols,
            values=value_cols, aggfunc='sum'
        )

        p_leg_bev.insert(0, 'type', 'legacy_fleet')
        p_leg_ice.insert(0, 'type', 'legacy_fleet')
        p_bev.insert(0, 'type', 'analysis_fleet')
        p_ice.insert(0, 'type', 'analysis_fleet')

        p_leg_bev.insert(0, 'fleet', f'{fleet}')
        p_leg_ice.insert(0, 'fleet', f'{fleet}')
        p_bev.insert(0, 'fleet', f'{fleet}')
        p_ice.insert(0, 'fleet', f'{fleet}')

        p = pd.concat([p_bev, p_ice, p_leg_bev, p_leg_ice], axis=0)
        p.insert(0, 'session_name', f'{session_settings.session_name}')
        p.insert(0, 'session_policy', f'{session_settings.session_policy}')

        return p

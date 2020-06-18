import pandas as pd
from usepa_omega2.fleet_metrics import FleetMetrics


# this dict would be passed to the module from the producer module? obviously it won't be hardcoded; elasticity will be set via an input file?
price_fuelsavings_dict = {('Petroleum', 'Hauling', 'Private'): {'TechCost': 500, 'FuelSavings': 375},
                          ('Petroleum', 'Hauling', 'Shared'): {'TechCost': 500, 'FuelSavings': 750},
                          ('Petroleum', 'NonHauling', 'Private'): {'TechCost': 250, 'FuelSavings': 375},
                          ('Petroleum', 'NonHauling', 'Shared'): {'TechCost': 250, 'FuelSavings': 750},
                          ('Electricity', 'Hauling', 'Private'): {'TechCost': 100, 'FuelSavings': 100},
                          ('Electricity', 'Hauling', 'Shared'): {'TechCost': 100, 'FuelSavings': 200},
                          ('Electricity', 'NonHauling', 'Private'): {'TechCost': 200, 'FuelSavings': 300},
                          ('Electricity', 'NonHauling', 'Shared'): {'TechCost': 200, 'FuelSavings': 400},
                          }
elasticity = -1


class RegistrationMetrics:

    def __init__(self, calendar_year, economic_parameters_dict):
        self.calendar_year = calendar_year
        self.economic_parameters_dict = economic_parameters_dict

    def calc_vehs_per_household(self, shared_vs_private_dict, vehicle_disposition_factor):
        vehs_per_hh = self.economic_parameters_dict[self.calendar_year]['VehiclesPerHousehold'] \
                     * (1 - shared_vs_private_dict[self.calendar_year] * vehicle_disposition_factor)
        return vehs_per_hh

    def calc_fleet_stock(self, vehs_per_household):
        fleet_stock = vehs_per_household * self.economic_parameters_dict[self.calendar_year]['NumberOfHouseholds']
        return fleet_stock

    def calc_new_sales(self, fleet_df, price_fuelsavings_dict, elasticity):
        fleet_age1 = pd.DataFrame(fleet_df.loc[fleet_df['ModelYear'] == self.calendar_year - 1, :])
        fleet_age1.reset_index(drop=True, inplace=True)
        fleet_age1.set_index('FC_HC_OC', inplace=True)
        fleet_age1_sales = FleetMetrics(fleet_age1).fleet_metric_sum('Volume')
        fleet_age1_dict = fleet_age1.to_dict('index')
        increased_sales = 0
        for fuel_class in ['Petroleum', 'Electricity']:
            for hauling_class in ['Hauling', 'NonHauling']:
                for ownership_class in ['Private', 'Shared']:
                    increased_sales += (fleet_age1_dict[(fuel_class, hauling_class, ownership_class)]['TransactionPrice']
                                        + price_fuelsavings_dict[(fuel_class, hauling_class, ownership_class)]['TechCost']
                                        - price_fuelsavings_dict[(fuel_class, hauling_class, ownership_class)]['FuelSavings']) \
                                       * (1 + elasticity / 100)
        sales_new = fleet_age1_sales + increased_sales
        return sales_new

    def vehicles_disposed(self):
        pass


# registration_metrics = RegistrationMetrics(2018, economic_parameters_dict)
# vehs_per_hh = registration_metrics.calc_vehs_per_household(shared_vs_private_dict, .25)
# stock = registration_metrics.calc_fleet_stock(vehs_per_hh)
# sales = registration_metrics.calc_new_sales(fleet_initial, price_fuelsavings_dict, elasticity)
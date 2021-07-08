"""

**Functions to get vehicle data based on vehicle ID, vehicle emission factors for the given vehicle model year and reg-class, refinery and power section emission factors for the given calendar year,
and then to calculate from them the pollutant inventories, including fuel consumed, for each year in the analysis.**



----

**CODE**

"""

grams_per_us_ton = 907185
grams_per_metric_ton = 1_000_000

# create some empty dicts in which to store VehicleFinal objects and vehicle/refinery/powersector emission factors
vehicles_dict = dict()
fuel_attribute_dict = dict()


def get_vehicle_info(vehicle_id):
    """

    """
    from producer.vehicles import VehicleFinal

    # add kwh_per_mile_cycle here when available in VehicleFinal
    attribute_list = ['model_year', 'reg_class_ID', 'in_use_fuel_ID', 'onroad_direct_co2_grams_per_mile', 'onroad_direct_kwh_per_mile']

    if vehicle_id not in vehicles_dict:
        vehicles_dict[vehicle_id] = VehicleFinal.get_vehicle_attributes(vehicle_id, attribute_list)

    return vehicles_dict[vehicle_id]


def get_vehicle_ef(calendar_year, model_year, reg_class_id, fuel):
    from effects.emission_factors_vehicles import EmissionFactorsVehicles

    emission_factors = ['voc_grams_per_mile',
                        'co_grams_per_mile',
                        'nox_grams_per_mile',
                        'pm25_grams_per_mile',
                        'sox_grams_per_gallon',
                        'benzene_grams_per_mile',
                        'butadiene13_grams_per_mile',
                        'formaldehyde_grams_per_mile',
                        'acetaldehyde_grams_per_mile',
                        'acrolein_grams_per_mile',
                        'ch4_grams_per_mile',
                        'n2o_grams_per_mile',
                        ]

    age = calendar_year - model_year

    return EmissionFactorsVehicles.get_emission_factors(model_year, age, reg_class_id, fuel, emission_factors)


def get_powersector_ef(calendar_year):
    from effects.emission_factors_powersector import EmissionFactorsPowersector

    emission_factors = ['voc_grams_per_kwh',
                        'co_grams_per_kwh',
                        'nox_grams_per_kwh',
                        'pm25_grams_per_kwh',
                        'sox_grams_per_kwh',
                        'benzene_grams_per_kwh',
                        'butadiene13_grams_per_kwh',
                        'formaldehyde_grams_per_kwh',
                        'acetaldehyde_grams_per_kwh',
                        'acrolein_grams_per_kwh',
                        'co2_grams_per_kwh',
                        'ch4_grams_per_kwh',
                        'n2o_grams_per_kwh',
                        ]

    return EmissionFactorsPowersector.get_emission_factors(calendar_year, emission_factors)


def get_refinery_ef(calendar_year, fuel):
    from effects.emission_factors_refinery import EmissionFactorsRefinery

    emission_factors = ['voc_grams_per_gallon',
                        'co_grams_per_gallon',
                        'nox_grams_per_gallon',
                        'pm25_grams_per_gallon',
                        'sox_grams_per_gallon',
                        'benzene_grams_per_gallon',
                        'butadiene13_grams_per_gallon',
                        'formaldehyde_grams_per_gallon',
                        'acetaldehyde_grams_per_gallon',
                        'acrolein_grams_per_gallon',
                        'co2_grams_per_gallon',
                        'ch4_grams_per_gallon',
                        'n2o_grams_per_gallon',
                        ]

    return EmissionFactorsRefinery.get_emission_factors(calendar_year, fuel, emission_factors)


# TODO when calculating refinery inventory, we need to consider where fuel is refined so we'll need a new input file for that
# TODO add vmt_liquid and vmt_electric to vehicle_annual_data
def calc_inventory(calendar_year):
    """
    Calculate onroad CO2 grams/mile, kWh/mile, fuel consumption, vehicle and upstream emission inventories
    by calendar year for vehicles in the vehicle_annual_data table.
    :param calendar_year: calendar year
    :return: Fills data in the vehicle_annual_data table that has not been filled to this point.
    """
    from producer.vehicle_annual_data import VehicleAnnualData
    from context.onroad_fuels import OnroadFuel

    vads = VehicleAnnualData.get_vehicle_annual_data(calendar_year)

    # UPDATE vehicle annual data related to effects
    for vad in vads:
        model_year, reg_class_ID, in_use_fuel_ID, onroad_direct_co2_grams_per_mile, onroad_direct_kwh_per_mile = get_vehicle_info(vad.vehicle_ID)

        fuel_dict = eval(in_use_fuel_ID, {'__builtins__': None}, {})
        liquid_fuel = None
        electric_fuel = None

        vmt_liquid_fuel = 0
        vmt_electricity = 0
        onroad_gallons_per_mile = 0
        fuel_consumption_gallons = 0
        fuel_consumption_kWh = 0

        voc_vehicle_ustons = 0
        co_vehicle_ustons = 0
        nox_vehicle_ustons = 0
        pm25_vehicle_ustons = 0
        so2_vehicle_ustons = 0
        benzene_vehicle_ustons = 0
        butadiene13_vehicle_ustons = 0
        formaldehyde_vehicle_ustons = 0
        acetaldehyde_vehicle_ustons = 0
        acrolein_vehicle_ustons = 0

        ch4_vehicle_metrictons = 0
        n2o_vehicle_metrictons = 0
        co2_vehicle_metrictons = 0

        voc_ps, co_ps, nox_ps, pm25_ps, sox_ps, benzene_ps, butadiene13_ps, formaldehyde_ps, acetaldehyde_ps, acrolein_ps, co2_ps, ch4_ps, n2o_ps, \
        voc_ref, co_ref, nox_ref, pm25_ref, sox_ref, benzene_ref, butadiene13_ref, formaldehyde_ref, acetaldehyde_ref, acrolein_ref, co2_ref, ch4_ref, n2o_ref \
            = 26 * [0]

        for fuel, fuel_share in fuel_dict.items():
            refuel_efficiency = OnroadFuel.get_fuel_attribute(calendar_year, fuel, 'refuel_efficiency')
            transmission_efficiency = OnroadFuel.get_fuel_attribute(calendar_year, fuel, 'transmission_efficiency')
            co2_emissions_grams_per_unit = OnroadFuel.get_fuel_attribute(calendar_year, fuel, 'direct_co2_grams_per_unit') / refuel_efficiency

            # fuel consumption
            if fuel == 'US electricity' and onroad_direct_kwh_per_mile:
                electric_fuel = fuel
                vmt_electricity = vad.vmt * fuel_share
                fuel_consumption_kWh += vmt_electricity * onroad_direct_kwh_per_mile / transmission_efficiency
            elif fuel != 'US electricity' and onroad_direct_co2_grams_per_mile:
                liquid_fuel = fuel
                vmt_liquid_fuel = vad.vmt * fuel_share
                onroad_gallons_per_mile += fuel_share * onroad_direct_co2_grams_per_mile / co2_emissions_grams_per_unit
                fuel_consumption_gallons = vad.vmt * onroad_gallons_per_mile / transmission_efficiency
                
                # vehicle tailpipe emissions for liquid fuel operation
                voc, co, nox, pm25, sox, benzene, butadiene13, formaldehyde, acetaldehyde, acrolein, ch4, n2o \
                    = get_vehicle_ef(calendar_year, model_year, reg_class_ID, liquid_fuel)

                voc_vehicle_ustons += vmt_liquid_fuel * voc / grams_per_us_ton
                co_vehicle_ustons += vmt_liquid_fuel * co / grams_per_us_ton
                nox_vehicle_ustons += vmt_liquid_fuel * nox / grams_per_us_ton
                pm25_vehicle_ustons += vmt_liquid_fuel * pm25 / grams_per_us_ton
                benzene_vehicle_ustons += vmt_liquid_fuel * benzene / grams_per_us_ton
                butadiene13_vehicle_ustons += vmt_liquid_fuel * butadiene13 / grams_per_us_ton
                formaldehyde_vehicle_ustons += vmt_liquid_fuel * formaldehyde / grams_per_us_ton
                acetaldehyde_vehicle_ustons += vmt_liquid_fuel * acetaldehyde / grams_per_us_ton
                acrolein_vehicle_ustons += vmt_liquid_fuel * acrolein / grams_per_us_ton

                so2_vehicle_ustons += fuel_consumption_gallons * sox / grams_per_us_ton

                ch4_vehicle_metrictons += vmt_liquid_fuel * ch4 / grams_per_metric_ton
                n2o_vehicle_metrictons += vmt_liquid_fuel * n2o / grams_per_metric_ton
                co2_vehicle_metrictons += vmt_liquid_fuel * onroad_direct_co2_grams_per_mile / grams_per_metric_ton

        vad.vmt_liquid_fuel = vmt_liquid_fuel
        vad.vmt_electricity = vmt_electricity
        vad.onroad_direct_co2_grams_per_mile = onroad_direct_co2_grams_per_mile
        vad.onroad_direct_kwh_per_mile = onroad_direct_kwh_per_mile
        vad.onroad_gallons_per_mile = onroad_gallons_per_mile
        vad.fuel_consumption_gallons = fuel_consumption_gallons
        vad.fuel_consumption_kWh = fuel_consumption_kWh

        vad.voc_vehicle_ustons = voc_vehicle_ustons
        vad.co_vehicle_ustons = co_vehicle_ustons
        vad.nox_vehicle_ustons = nox_vehicle_ustons
        vad.pm25_vehicle_ustons = pm25_vehicle_ustons
        vad.so2_vehicle_ustons = so2_vehicle_ustons
        vad.benzene_vehicle_ustons = benzene_vehicle_ustons
        vad.butadiene13_vehicle_ustons = butadiene13_vehicle_ustons
        vad.formaldehyde_vehicle_ustons = formaldehyde_vehicle_ustons
        vad.acetaldehyde_vehicle_ustons = acetaldehyde_vehicle_ustons
        vad.acrolein_vehicle_ustons = acrolein_vehicle_ustons

        vad.ch4_vehicle_metrictons = ch4_vehicle_metrictons
        vad.n2o_vehicle_metrictons = n2o_vehicle_metrictons
        vad.co2_vehicle_metrictons = co2_vehicle_metrictons

        # upstream inventory
        if electric_fuel:
            voc_ps, co_ps, nox_ps, pm25_ps, sox_ps, benzene_ps, butadiene13_ps, formaldehyde_ps, acetaldehyde_ps, acrolein_ps, co2_ps, ch4_ps, n2o_ps \
                = get_powersector_ef(calendar_year)
        if liquid_fuel:
            voc_ref, co_ref, nox_ref, pm25_ref, sox_ref, benzene_ref, butadiene13_ref, formaldehyde_ref, acetaldehyde_ref, acrolein_ref, co2_ref, ch4_ref, n2o_ref \
                = get_refinery_ef(calendar_year, liquid_fuel)

        vad.voc_upstream_ustons = (fuel_consumption_kWh * voc_ps + fuel_consumption_gallons * voc_ref) / grams_per_us_ton
        vad.co_upstream_ustons = (fuel_consumption_kWh * co_ps + fuel_consumption_gallons * co_ref) / grams_per_us_ton
        vad.nox_upstream_ustons = (fuel_consumption_kWh * nox_ps + fuel_consumption_gallons * nox_ref) / grams_per_us_ton
        vad.pm25_upstream_ustons = (fuel_consumption_kWh * pm25_ps + fuel_consumption_gallons * pm25_ref) / grams_per_us_ton
        vad.so2_upstream_ustons = (fuel_consumption_kWh * sox_ps + fuel_consumption_gallons * sox_ref) / grams_per_us_ton
        vad.benzene_upstream_ustons = (fuel_consumption_kWh * benzene_ps + fuel_consumption_gallons * benzene_ref) / grams_per_us_ton
        vad.butadiene13_upstream_ustons = (fuel_consumption_kWh * butadiene13_ps + fuel_consumption_gallons * butadiene13_ref) / grams_per_us_ton
        vad.formaldehyde_upstream_ustons = (fuel_consumption_kWh * formaldehyde_ps + fuel_consumption_gallons * formaldehyde_ref) / grams_per_us_ton
        vad.acetaldehyde_upstream_ustons = (fuel_consumption_kWh * acetaldehyde_ps + fuel_consumption_gallons * acetaldehyde_ref) / grams_per_us_ton
        vad.acrolein_upstream_ustons = (fuel_consumption_kWh * acrolein_ps + fuel_consumption_gallons * acrolein_ref) / grams_per_us_ton

        vad.co2_upstream_metrictons = (fuel_consumption_kWh * co2_ps + fuel_consumption_gallons * co2_ref) / grams_per_metric_ton
        vad.ch4_upstream_metrictons = (fuel_consumption_kWh * ch4_ps + fuel_consumption_gallons * ch4_ref) / grams_per_metric_ton
        vad.n2o_upstream_metrictons = (fuel_consumption_kWh * n2o_ps + fuel_consumption_gallons * n2o_ref) / grams_per_metric_ton

        # sum vehicle and upstream into totals
        vad.voc_total_ustons = vad.voc_vehicle_ustons + vad.voc_upstream_ustons
        vad.co_total_ustons = vad.co_vehicle_ustons + vad.co_upstream_ustons
        vad.nox_total_ustons = vad.nox_vehicle_ustons + vad.nox_upstream_ustons
        vad.pm25_total_ustons = vad.pm25_vehicle_ustons + vad.pm25_upstream_ustons
        vad.so2_total_ustons = vad.so2_vehicle_ustons + vad.so2_upstream_ustons
        vad.benzene_total_ustons = vad.benzene_vehicle_ustons + vad.benzene_upstream_ustons
        vad.butadiene13_total_ustons = vad.butadiene13_vehicle_ustons + vad.butadiene13_upstream_ustons
        vad.formaldehyde_total_ustons = vad.formaldehyde_vehicle_ustons + vad.formaldehyde_upstream_ustons
        vad.acetaldehyde_total_ustons = vad.acetaldehyde_vehicle_ustons + vad.acetaldehyde_upstream_ustons
        vad.acrolein_total_ustons = vad.acrolein_vehicle_ustons + vad.acrolein_upstream_ustons
        vad.co2_total_metrictons = vad.co2_vehicle_metrictons + vad.co2_upstream_metrictons
        vad.ch4_total_metrictons = vad.ch4_vehicle_metrictons + vad.ch4_upstream_metrictons
        vad.n2o_total_metrictons = vad.n2o_vehicle_metrictons + vad.n2o_upstream_metrictons

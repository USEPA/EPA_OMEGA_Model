"""

inventory.py
============
"""
import pandas as pd
import o2
from usepa_omega2 import *


grams_per_us_ton = 907185
grams_per_metric_ton = 1000000
transloss = 0.07
gap_ice = 0.8
gap_bev = 0.7
co2_indolene = 8887
kwh_per_mile_cycle = 0.2 # TODO Placeholder - what are we doing about calculating energy consumption on vehicles?


vehicles_dict = dict()
vef_dict = dict()
ref_dict = dict()
pef_dict = dict()


def get_vehicle_info(vehicle_ID, query=False):
    from vehicles import VehicleFinal

    if vehicle_ID in vehicles_dict and not query:
        model_year, reg_class_ID, in_use_fuel_ID, cert_CO2_grams_per_mile = vehicles_dict[vehicle_ID] # add kwh_per_mile_cycle here when available in VehicleFinal
    else:
        model_year, reg_class_ID, in_use_fuel_ID, cert_CO2_grams_per_mile = \
            o2.session.query(VehicleFinal.model_year, VehicleFinal.reg_class_ID,
                             VehicleFinal.in_use_fuel_ID, VehicleFinal.cert_CO2_grams_per_mile).\
                filter(VehicleFinal.vehicle_ID == vehicle_ID).one()
        vehicles_dict[vehicle_ID] = model_year, reg_class_ID, in_use_fuel_ID, cert_CO2_grams_per_mile

    return model_year, reg_class_ID, in_use_fuel_ID, cert_CO2_grams_per_mile


def get_vehicle_ef(calendar_year, model_year, reg_class_ID, query=False):
    from effects.emission_factors_vehicles import EmissionFactorsVehicles

    age = calendar_year - model_year
    vef_dict_id = f'{model_year}_{age}_{reg_class_ID}'

    if vef_dict_id in vef_dict and not query:
        voc, co, nox, pm25, sox, benzene, butadiene13, formaldehyde, acetaldehyde, acrolein, ch4, n2o = vef_dict[vef_dict_id]
    else:
        voc, co, nox, pm25, sox, benzene, butadiene13, formaldehyde, acetaldehyde, acrolein, ch4, n2o \
            = o2.session.query(EmissionFactorsVehicles.voc_grams_per_mile,
                               EmissionFactorsVehicles.co_grams_per_mile,
                               EmissionFactorsVehicles.nox_grams_per_mile,
                               EmissionFactorsVehicles.pm25_grams_per_mile,
                               EmissionFactorsVehicles.sox_grams_per_gallon,
                               EmissionFactorsVehicles.benzene_grams_per_mile,
                               EmissionFactorsVehicles.butadiene13_grams_per_mile,
                               EmissionFactorsVehicles.formaldehyde_grams_per_mile,
                               EmissionFactorsVehicles.acetaldehyde_grams_per_mile,
                               EmissionFactorsVehicles.acrolein_grams_per_mile,
                               EmissionFactorsVehicles.ch4_grams_per_mile,
                               EmissionFactorsVehicles.n2o_grams_per_mile,).\
            filter(EmissionFactorsVehicles.model_year == model_year).\
            filter(EmissionFactorsVehicles.age == age).\
            filter(EmissionFactorsVehicles.reg_class_id == reg_class_ID).one()

        vef_dict[vef_dict_id] = voc, co, nox, pm25, sox, benzene, butadiene13, formaldehyde, acetaldehyde, acrolein, ch4, n2o

    return voc, co, nox, pm25, sox, benzene, butadiene13, formaldehyde, acetaldehyde, acrolein, ch4, n2o


def get_powersector_ef(calendar_year, query=False):
    from effects.emission_factors_powersector import EmissionFactorsPowersector

    pef_dict_id = f'{calendar_year}'

    if pef_dict_id in pef_dict and not query:
        voc, co, nox, pm25, sox, benzene, butadiene13, formaldehyde, acetaldehyde, acrolein, co2, ch4, n2o = pef_dict[pef_dict_id]
    else:
        voc, co, nox, pm25, sox, benzene, butadiene13, formaldehyde, acetaldehyde, acrolein, co2, ch4, n2o \
            = o2.session.query(EmissionFactorsPowersector.voc_grams_per_kWh,
                               EmissionFactorsPowersector.co_grams_per_kWh,
                               EmissionFactorsPowersector.nox_grams_per_kWh,
                               EmissionFactorsPowersector.pm25_grams_per_kWh,
                               EmissionFactorsPowersector.sox_grams_per_kWh,
                               EmissionFactorsPowersector.benzene_grams_per_kWh,
                               EmissionFactorsPowersector.butadiene13_grams_per_kWh,
                               EmissionFactorsPowersector.formaldehyde_grams_per_kWh,
                               EmissionFactorsPowersector.acetaldehyde_grams_per_kWh,
                               EmissionFactorsPowersector.acrolein_grams_per_kWh,
                               EmissionFactorsPowersector.co2_grams_per_kWh,
                               EmissionFactorsPowersector.ch4_grams_per_kWh,
                               EmissionFactorsPowersector.n2o_grams_per_kWh,).\
            filter(EmissionFactorsPowersector.calendar_year == calendar_year).one()

        pef_dict[pef_dict_id] = voc, co, nox, pm25, sox, benzene, butadiene13, formaldehyde, acetaldehyde, acrolein, co2, ch4, n2o

    return voc, co, nox, pm25, sox, benzene, butadiene13, formaldehyde, acetaldehyde, acrolein, co2, ch4, n2o


def get_refinery_ef(calendar_year, query=False):
    from effects.emission_factors_refinery import EmissionFactorsRefinery

    ref_dict_id = f'{calendar_year}'

    if ref_dict_id in ref_dict and not query:
        voc, co, nox, pm25, sox, benzene, butadiene13, formaldehyde, acetaldehyde, acrolein, naphthalene, co2, ch4, n2o = ref_dict[ref_dict_id]
    else:
        voc, co, nox, pm25, sox, benzene, butadiene13, formaldehyde, acetaldehyde, acrolein, naphthalene, co2, ch4, n2o \
            = o2.session.query(EmissionFactorsRefinery.voc_grams_per_gallon,
                               EmissionFactorsRefinery.co_grams_per_gallon,
                               EmissionFactorsRefinery.nox_grams_per_gallon,
                               EmissionFactorsRefinery.pm25_grams_per_gallon,
                               EmissionFactorsRefinery.sox_grams_per_gallon,
                               EmissionFactorsRefinery.benzene_grams_per_gallon,
                               EmissionFactorsRefinery.butadiene13_grams_per_gallon,
                               EmissionFactorsRefinery.formaldehyde_grams_per_gallon,
                               EmissionFactorsRefinery.acetaldehyde_grams_per_gallon,
                               EmissionFactorsRefinery.acrolein_grams_per_gallon,
                               EmissionFactorsRefinery.naphthalene_grams_per_gallon,
                               EmissionFactorsRefinery.co2_grams_per_gallon,
                               EmissionFactorsRefinery.ch4_grams_per_gallon,
                               EmissionFactorsRefinery.n2o_grams_per_gallon,).\
            filter(EmissionFactorsRefinery.calendar_year == calendar_year).one()

        ref_dict[ref_dict_id] = voc, co, nox, pm25, sox, benzene, butadiene13, formaldehyde, acetaldehyde, acrolein, naphthalene, co2, ch4, n2o

    return voc, co, nox, pm25, sox, benzene, butadiene13, formaldehyde, acetaldehyde, acrolein, naphthalene, co2, ch4, n2o


def calc_inventory(calendar_year):
    from vehicle_annual_data import VehicleAnnualData

    query = False

    vad_vehs = o2.session.query(VehicleAnnualData).filter(VehicleAnnualData.calendar_year == calendar_year).all()

    # UPDATE vehicle annual data related to effects
    for vad_veh in vad_vehs:
        model_year, reg_class_ID, in_use_fuel_ID, cert_CO2_grams_per_mile = get_vehicle_info(vad_veh.vehicle_ID, query=query) # add kwh_per_mile_cycle here

        if in_use_fuel_ID == 'US electricity':
            # co2 and fuel consumption for electric
            vad_veh.onroad_co2_grams_per_mile = 0
            vad_veh.onroad_fuel_consumption_rate = kwh_per_mile_cycle / gap_bev # TODO placeholder for now
            vad_veh.fuel_consumption = vad_veh.vmt * vad_veh.onroad_fuel_consumption_rate

            # upstream inventory for electric
            voc, co, nox, pm25, sox, benzene, butadiene13, formaldehyde, acetaldehyde, acrolein, co2, ch4, n2o \
                = get_powersector_ef(calendar_year, query=query)

            vad_veh.voc_upstream_ustons = vad_veh.fuel_consumption * voc / grams_per_us_ton
            vad_veh.co_upstream_ustons = vad_veh.fuel_consumption * co / grams_per_us_ton
            vad_veh.nox_upstream_ustons = vad_veh.fuel_consumption * nox / grams_per_us_ton
            vad_veh.pm25_upstream_ustons = vad_veh.fuel_consumption * pm25 / grams_per_us_ton
            vad_veh.benzene_upstream_ustons = vad_veh.fuel_consumption * benzene / grams_per_us_ton
            vad_veh.butadiene13_upstream_ustons = vad_veh.fuel_consumption * butadiene13 / grams_per_us_ton
            vad_veh.formaldehyde_upstream_ustons = vad_veh.fuel_consumption * formaldehyde / grams_per_us_ton
            vad_veh.acetaldehyde_upstream_ustons = vad_veh.fuel_consumption * acetaldehyde / grams_per_us_ton
            vad_veh.acrolein_upstream_ustons = vad_veh.fuel_consumption * acrolein / grams_per_us_ton

            vad_veh.sox_upstream_ustons = vad_veh.fuel_consumption * sox / grams_per_us_ton

            vad_veh.ch4_upstream_metrictons = vad_veh.fuel_consumption * ch4 / grams_per_metric_ton
            vad_veh.n2o_upstream_metrictons = vad_veh.fuel_consumption * n2o / grams_per_metric_ton
            vad_veh.co2_upstream_metrictons = vad_veh.fuel_consumption * co2 / grams_per_metric_ton

        else:
            # co2 and fuel consumption for petrol
            vad_veh.onroad_co2_grams_per_mile = cert_CO2_grams_per_mile / gap_ice  # TODO how are we doing this - simply gap? what about AC, off-cycle, etc.?
            vad_veh.onroad_fuel_consumption_rate = vad_veh.onroad_co2_grams_per_mile / co2_indolene  # TODO is this how we're doing this?
            vad_veh.fuel_consumption = vad_veh.vmt * vad_veh.onroad_fuel_consumption_rate

            # vehicle inventory for petrol
            voc, co, nox, pm25, sox, benzene, butadiene13, formaldehyde, acetaldehyde, acrolein, ch4, n2o \
                = get_vehicle_ef(calendar_year, model_year, reg_class_ID, query=query)

            # it seems like the below dicts and loops should work, but the inv_attr isn't working with vad_veh.inv_attr
            # criteria = {'voc': voc,
            #             'co': co,
            #             'nox': nox,
            #             'pm25': pm25,
            #             'sox': sox,
            #             'benzene': benzene,
            #             'butadiene13': butadiene13,
            #             'formaldehyde': formaldehyde,
            #             'acetaldehyde': acetaldehyde,
            #             'acrolein': acrolein,
            #             }
            # ghg = {'ch4': ch4,
            #        'n2o': n2o,
            #        }

            # for k, v in criteria.items():
            #     # inv_attr = f'{k}_vehicle_ustons'
            #     # vad_veh.inv_attr = vad_veh.vmt * v / grams_per_us_ton
            #
            # for k, v in ghg.items():
            #     inv_attr = f'{k}_vehicle_metrictons'
            #     vad_veh.inv_attr = vad_veh.vmt * v / grams_per_metric_ton
            #
            # inv_attr = 'sox_vehicle_ustons'
            # vad_veh.inv_attr = vad_veh.fuel_consumption * v / grams_per_us_ton

            vad_veh.voc_vehicle_ustons = vad_veh.vmt * voc / grams_per_us_ton
            vad_veh.co_vehicle_ustons = vad_veh.vmt * co / grams_per_us_ton
            vad_veh.nox_vehicle_ustons = vad_veh.vmt * nox / grams_per_us_ton
            vad_veh.pm25_vehicle_ustons = vad_veh.vmt * pm25 / grams_per_us_ton
            vad_veh.benzene_vehicle_ustons = vad_veh.vmt * benzene / grams_per_us_ton
            vad_veh.butadiene13_vehicle_ustons = vad_veh.vmt * butadiene13 / grams_per_us_ton
            vad_veh.formaldehyde_vehicle_ustons = vad_veh.vmt * formaldehyde / grams_per_us_ton
            vad_veh.acetaldehyde_vehicle_ustons = vad_veh.vmt * acetaldehyde / grams_per_us_ton
            vad_veh.acrolein_vehicle_ustons = vad_veh.vmt * acrolein / grams_per_us_ton

            vad_veh.sox_vehicle_ustons = vad_veh.fuel_consumption * sox / grams_per_us_ton

            vad_veh.ch4_vehicle_metrictons = vad_veh.vmt * ch4 / grams_per_metric_ton
            vad_veh.n2o_vehicle_metrictons = vad_veh.vmt * n2o / grams_per_metric_ton
            vad_veh.co2_vehicle_metrictons = vad_veh.vmt * vad_veh.onroad_co2_grams_per_mile / grams_per_metric_ton

            # upstream inventory for petrol
            voc, co, nox, pm25, sox, benzene, butadiene13, formaldehyde, acetaldehyde, acrolein, naphthalene, co2, ch4, n2o \
                = get_refinery_ef(calendar_year, query=query)

            vad_veh.voc_upstream_ustons = vad_veh.fuel_consumption * voc / grams_per_us_ton
            vad_veh.co_upstream_ustons = vad_veh.fuel_consumption * co / grams_per_us_ton
            vad_veh.nox_upstream_ustons = vad_veh.fuel_consumption * nox / grams_per_us_ton
            vad_veh.pm25_upstream_ustons = vad_veh.fuel_consumption * pm25 / grams_per_us_ton
            vad_veh.benzene_upstream_ustons = vad_veh.fuel_consumption * benzene / grams_per_us_ton
            vad_veh.butadiene13_upstream_ustons = vad_veh.fuel_consumption * butadiene13 / grams_per_us_ton
            vad_veh.formaldehyde_upstream_ustons = vad_veh.fuel_consumption * formaldehyde / grams_per_us_ton
            vad_veh.acetaldehyde_upstream_ustons = vad_veh.fuel_consumption * acetaldehyde / grams_per_us_ton
            vad_veh.acrolein_upstream_ustons = vad_veh.fuel_consumption * acrolein / grams_per_us_ton
            vad_veh.naphthalene_upstream_ustons = vad_veh.fuel_consumption * naphthalene / grams_per_us_ton

            vad_veh.sox_upstream_ustons = vad_veh.fuel_consumption * sox / grams_per_us_ton

            vad_veh.ch4_upstream_metrictons = vad_veh.fuel_consumption * ch4 / grams_per_metric_ton
            vad_veh.n2o_upstream_metrictons = vad_veh.fuel_consumption * n2o / grams_per_metric_ton
            vad_veh.co2_upstream_metrictons = vad_veh.fuel_consumption * co2 / grams_per_metric_ton


def calc_vehicle_co2_gallons(vf_df, vad_df):
    print('calc_vehicle_co2_gallons')

    df_return = vf_df[['vehicle_id', 'model_year', 'showroom_fuel_id', 'cert_co2_grams_per_mile']]
    df_return = vad_df.merge(df_return, on='vehicle_id', how='left')
    df_return['onroad_co2_grams_per_mile'] = df_return['cert_co2_grams_per_mile'] / gap_ice
    # the following structure would be needed if vehicle_annual_data doesn't already include the needed columns
    # df_return.insert(len(df_return.columns),
    #                  'onroad_co2_grams_per_mile',
    #                  df_return['cert_co2_grams_per_mile'] / gap_ice)
    df_return.loc[df_return['showroom_fuel_id'] != 'US electricity', 'onroad_fuel_consumption_rate'] \
        = co2_indolene / df_return['onroad_co2_grams_per_mile']

    df_return.loc[df_return['showroom_fuel_id'] != 'US electricity', 'co2_vehicle_metrictons'] \
        = df_return[['vmt', 'onroad_co2_grams_per_mile']].product(axis=1) / grams_per_metric_ton

    df_return.loc[df_return['showroom_fuel_id'] != 'US electricity', 'fuel_consumption'] \
        = df_return['vmt'] / df_return['onroad_fuel_consumption_rate']

    return df_return


def calc_vehicle_inventory(df_effects, vf_df, vef_df, *args):
    print('calc_vehicle_inventory')

    df_return = df_effects.merge(vf_df[['vehicle_id', 'reg_class_id']], on='vehicle_id', how='left')
    temp = df_return[['model_year', 'age', 'reg_class_id']].merge(vef_df, on=['model_year', 'age', 'reg_class_id'], how='left')

    for arg in args:
        if arg == 'sox':
            df_return.loc[df_return['showroom_fuel_id'] != 'US electricity', f'{arg}_vehicle_ustons'] \
                = df_return['fuel_consumption'] * temp[f'{arg}_grams_per_gallon'] / grams_per_us_ton
        elif arg == 'ch4' or arg == 'n2o':
            df_return.loc[df_return['showroom_fuel_id'] != 'US electricity', f'{arg}_vehicle_metrictons'] \
                = df_return['vmt'] * temp[f'{arg}_grams_per_mile'] / grams_per_metric_ton
        else:
            df_return.loc[df_return['showroom_fuel_id'] != 'US electricity', f'{arg}_vehicle_ustons'] \
                = df_return['vmt'] * temp[f'{arg}_grams_per_mile'] / grams_per_us_ton

    return df_return


def calc_refinery_inventory(df_effects, ref_df, *args):
    print('calc_refinery_inventory')

    df_return = df_effects.copy()
    temp = df_return[['calendar_year']].merge(ref_df, on=['calendar_year'], how='left')

    for arg in args:
        if arg == 'ch4' or arg == 'n2o' or arg == 'co2':
            df_return.loc[df_return['showroom_fuel_id'] != 'US electricity', f'{arg}_upstream_metrictons'] \
                = df_return['fuel_consumption'] * temp[f'{arg}_grams_per_gallon'] / grams_per_metric_ton
        else:
            df_return.loc[df_return['showroom_fuel_id'] != 'US electricity', f'{arg}_upstream_ustons'] \
                = df_return['fuel_consumption'] * temp[f'{arg}_grams_per_gallon'] / grams_per_us_ton

    return df_return


def calc_powersector_inventory(df_effects, pef_df, *args):
    print('calc_powersector_inventory')

    df_return = df_effects.copy()
    temp = df_return[['calendar_year']].merge(pef_df, on=['calendar_year'], how='left')
    cert_kwh_per_mile = kwh_per_mile_cycle

    df_return.loc[df_return['showroom_fuel_id'] == 'US electricity', 'onroad_fuel_consumption_rate'] \
        = cert_kwh_per_mile / gap_bev / (1 - transloss)  # TODO how are we doing this - simply gap? what about AC, off-cycle, etc.?

    df_return.loc[df_return['showroom_fuel_id'] == 'US electricity', 'fuel_consumption'] \
        = df_return[['vmt', 'onroad_fuel_consumption_rate']].product(axis=1)

    for arg in args:
            if arg == 'ch4' or arg == 'n2o' or arg == 'co2':
                df_return.loc[df_return['showroom_fuel_id'] == 'US electricity', f'{arg}_upstream_metrictons'] \
                    = df_return['fuel_consumption'] * temp[f'{arg}_grams_per_kWh'] / grams_per_metric_ton
            else:
                df_return.loc[df_return['showroom_fuel_id'] == 'US electricity', f'{arg}_upstream_ustons'] \
                    = df_return['fuel_consumption'] * temp[f'{arg}_grams_per_kWh'] / grams_per_us_ton

    return df_return

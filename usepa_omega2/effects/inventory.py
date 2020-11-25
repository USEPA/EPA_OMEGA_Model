"""

inventory.py
============
"""
import pandas as pd
import o2
from usepa_omega2 import *


grams_per_us_ton	= 907185
grams_per_metric_ton = 1000000
transloss = 0.07
gap_ice = 0.8
gap_bev = 0.7
co2_indolene = 8887
kwh_per_mile_cycle = 0.2 # TODO Placeholder - what are we doing about calculating energy consumption on vehicles?

#
# def calc_vehicle_co2_gallons():
#     print('calc_vehicle_co2_gallons')
#     from vehicles import VehicleFinal
#     from vehicle_annual_data import VehicleAnnualData
#
#     vehicles = o2.session.query(VehicleFinal).filter(VehicleFinal.in_use_fuel_ID != 'US electricity').all()
#     vehicle_IDs = []
#     for idx, value in enumerate(vehicles):
#         vehicle_IDs.append(vehicles[idx].vehicle_ID)
#
#     for idx, vehicle_ID in enumerate(vehicle_IDs):
#         veh_ages = o2.session.query(VehicleAnnualData.age).filter(VehicleAnnualData.vehicle_ID == vehicle_ID).all()
#         veh_my = o2.session.query(VehicleFinal.model_year).filter(VehicleFinal.vehicle_ID == vehicle_ID).scalar()
#
#         cert_co2 = o2.session.query(VehicleFinal.cert_CO2_grams_per_mile).filter(VehicleFinal.vehicle_ID == vehicle_ID).scalar()
#         onroad_co2 = cert_co2 / gap_ice # TODO how are we doing this - simply gap? what about AC, off-cycle, etc.?
#         mpg = co2_indolene / onroad_co2 # TODO is this how we're doing this?
#
#         for idx, veh_age in enumerate(veh_ages):
#             veh_vmt = o2.session.query(VehicleAnnualData.vmt).\
#                 filter(VehicleAnnualData.vehicle_ID == vehicle_ID).\
#                 filter(VehicleAnnualData.age == veh_age[0]).scalar()
#
#             vehicle = o2.session.query(VehicleFinal).filter(VehicleFinal.vehicle_ID == vehicle_ID)[0]
#             cy = veh_my + veh_age[0]
#             try:
#                 valu_co2 = veh_vmt * onroad_co2 / grams_per_metric_ton
#                 valu_gal = veh_vmt / mpg
#                 co2_attr = 'co2_vehicle_metrictons' # TODO metrictons and gallons probably belong in calc_vehicle_inventory, not here
#                 gal_attr = 'fuel_consumption'
#                 VehicleAnnualData.update_vehicle_annual_data(vehicle, cy, 'onroad_co2_grams_per_mile', onroad_co2)
#                 VehicleAnnualData.update_vehicle_annual_data(vehicle, cy, 'onroad_fuel_consumption_rate', mpg)
#                 VehicleAnnualData.update_vehicle_annual_data(vehicle, cy, co2_attr, valu_co2)
#                 VehicleAnnualData.update_vehicle_annual_data(vehicle, cy, gal_attr, valu_gal)
#             except:
#                 pass
#
#
# def calc_vehicle_inventory(*args):
#     print('calc_vehicle_inventory')
#     from vehicles import VehicleFinal
#     from vehicle_annual_data import VehicleAnnualData
#     from effects.emission_factors_vehicles import EmissionFactorsVehicles
#
#     vehicles = o2.session.query(VehicleFinal).filter(VehicleFinal.in_use_fuel_ID != 'US electricity').all()
#     vehicle_IDs = []
#     for idx, value in enumerate(vehicles):
#         vehicle_IDs.append(vehicles[idx].vehicle_ID)
#
#     for idx, vehicle_ID in enumerate(vehicle_IDs):
#         veh_ages = o2.session.query(VehicleAnnualData.age).filter(VehicleAnnualData.vehicle_ID == vehicle_ID).all()
#         veh_my = o2.session.query(VehicleFinal.model_year).filter(VehicleFinal.vehicle_ID == vehicle_ID).scalar()
#         veh_regclass_id = o2.session.query(VehicleFinal.reg_class_ID).filter(VehicleFinal.vehicle_ID == vehicle_ID).scalar()
#
#         for arg in args:
#             if arg == 'sox':
#                 factor_attr = f'{arg}_grams_per_gallon'
#             else:
#                 factor_attr = f'{arg}_grams_per_mile'
#             for idx, veh_age in enumerate(veh_ages):
#                 factor_object = o2.session.query(EmissionFactorsVehicles).\
#                     filter(EmissionFactorsVehicles.reg_class_id == veh_regclass_id).\
#                     filter(EmissionFactorsVehicles.model_year == veh_my).\
#                     filter(EmissionFactorsVehicles.age == veh_age[0]).all()
#
#                 factor = factor_object[0].__getattribute__(factor_attr)
#                 veh_vmt = o2.session.query(VehicleAnnualData.vmt).\
#                     filter(VehicleAnnualData.vehicle_ID == vehicle_ID).\
#                     filter(VehicleAnnualData.age == veh_age[0]).scalar()
#                 veh_gallons = o2.session.query(VehicleAnnualData.fuel_consumption).\
#                     filter(VehicleAnnualData.vehicle_ID == vehicle_ID).\
#                     filter(VehicleAnnualData.age == veh_age[0]).scalar()
#
#                 vehicle = o2.session.query(VehicleFinal).filter(VehicleFinal.vehicle_ID == vehicle_ID)[0]
#                 cy = veh_my + veh_age[0]
#                 if arg == 'sox':
#                     try:
#                         valu = veh_gallons * factor / grams_per_us_ton
#                         inv_attr = f'{arg}_vehicle_ustons'
#                         VehicleAnnualData.update_vehicle_annual_data(vehicle, cy, inv_attr, valu)
#                     except:
#                         pass
#                 elif arg == 'ch4' or arg == 'n2o':
#                     try:
#                         valu = veh_vmt * factor / grams_per_metric_ton
#                         inv_attr = f'{arg}_vehicle_metrictons'
#                         VehicleAnnualData.update_vehicle_annual_data(vehicle, cy, inv_attr, valu)
#                     except:
#                         pass
#                 else:
#                     try:
#                         valu = veh_vmt * factor / grams_per_us_ton
#                         inv_attr = f'{arg}_vehicle_ustons'
#                         VehicleAnnualData.update_vehicle_annual_data(vehicle, cy, inv_attr, valu)
#                     except:
#                         pass
#
#
# def calc_refinery_inventory(*args):
#     print('calc_refinery_inventory')
#     from vehicles import VehicleFinal
#     from vehicle_annual_data import VehicleAnnualData
#     from effects.emission_factors_refinery import EmissionFactorsRefinery
#
#     vehicles = o2.session.query(VehicleFinal).filter(VehicleFinal.in_use_fuel_ID != 'US electricity').all()
#     vehicle_IDs = []
#     for idx, value in enumerate(vehicles):
#         vehicle_IDs.append(vehicles[idx].vehicle_ID)
#
#     for idx, vehicle_ID in enumerate(vehicle_IDs):
#         veh_cyears = o2.session.query(VehicleAnnualData.calendar_year).filter(VehicleAnnualData.vehicle_ID == vehicle_ID).all()
#
#         for arg in args:
#             factor_attr = f'{arg}_grams_per_gallon'
#             for idx, veh_cyear in enumerate(veh_cyears):
#                 factor_object = o2.session.query(EmissionFactorsRefinery).\
#                     filter(EmissionFactorsRefinery.calendar_year == veh_cyear[0]).all()
#
#                 factor = factor_object[0].__getattribute__(factor_attr)
#                 veh_gallons = o2.session.query(VehicleAnnualData.fuel_consumption).\
#                     filter(VehicleAnnualData.vehicle_ID == vehicle_ID).\
#                     filter(VehicleAnnualData.calendar_year == veh_cyear[0]).scalar()
#
#                 vehicle = o2.session.query(VehicleFinal).filter(VehicleFinal.vehicle_ID == vehicle_ID)[0]
#                 cy = veh_cyear[0]
#                 if arg == 'ch4' or arg == 'n2o' or arg == 'co2':
#                     try:
#                         valu = veh_gallons * factor / grams_per_metric_ton
#                         inv_attr = f'{arg}_upstream_metrictons'
#                         VehicleAnnualData.update_vehicle_annual_data(vehicle, cy, inv_attr, valu)
#                     except:
#                         pass
#                 else:
#                     try:
#                         valu = veh_gallons * factor / grams_per_us_ton
#                         inv_attr = f'{arg}_upstream_ustons'
#                         VehicleAnnualData.update_vehicle_annual_data(vehicle, cy, inv_attr, valu)
#                     except:
#                         pass
#
#
# def calc_powersector_inventory(*args):
#     print('calc_powersector_inventory')
#     from vehicles import VehicleFinal
#     from vehicle_annual_data import VehicleAnnualData
#     from effects.emission_factors_powersector import EmissionFactorsPowersector
#
#     vehicles = o2.session.query(VehicleFinal).filter(VehicleFinal.in_use_fuel_ID == 'US electricity').all()
#     vehicle_IDs = []
#     for idx, value in enumerate(vehicles):
#         vehicle_IDs.append(vehicles[idx].vehicle_ID)
#
#     for idx, vehicle_ID in enumerate(vehicle_IDs):
#         veh_cyears = o2.session.query(VehicleAnnualData.calendar_year).filter(VehicleAnnualData.vehicle_ID == vehicle_ID).all()
#
#         # cert_kwh_per_mile = o2.session.query(VehicleFinal.cert_kWh_per_mile).filter(VehicleFinal.vehicle_ID == vehicle_ID).scalar()
#         cert_kwh_per_mile = kwh_per_mile_cycle
#         onroad_kwh_per_mile = cert_kwh_per_mile / gap_bev / (1 - transloss)  # TODO how are we doing this - simply gap? what about AC, off-cycle, etc.?
#
#         for arg in args:
#             factor_attr = f'{arg}_grams_per_kWh'
#             for idx, veh_cyear in enumerate(veh_cyears):
#                 factor_object = o2.session.query(EmissionFactorsPowersector).\
#                     filter(EmissionFactorsPowersector.calendar_year == veh_cyear[0]).all()
#
#                 factor = factor_object[0].__getattribute__(factor_attr)
#                 veh_vmt = o2.session.query(VehicleAnnualData.vmt).\
#                     filter(VehicleAnnualData.vehicle_ID == vehicle_ID).\
#                     filter(VehicleAnnualData.calendar_year == veh_cyear[0]).scalar()
#                 try:
#                     veh_kWh = veh_vmt * onroad_kwh_per_mile
#                 except:
#                     pass
#
#                 vehicle = o2.session.query(VehicleFinal).filter(VehicleFinal.vehicle_ID == vehicle_ID)[0]
#                 cy = veh_cyear[0]
#                 if arg == 'ch4' or arg == 'n2o' or arg == 'co2':
#                     try:
#                         valu = veh_kWh * factor / grams_per_metric_ton
#                         inv_attr = f'{arg}_upstream_metrictons'
#                         VehicleAnnualData.update_vehicle_annual_data(vehicle, cy, inv_attr, valu)
#                     except:
#                         pass
#                 else:
#                     try:
#                         valu = veh_kWh * factor / grams_per_us_ton
#                         inv_attr = f'{arg}_upstream_ustons'
#                         VehicleAnnualData.update_vehicle_annual_data(vehicle, cy, inv_attr, valu)
#                     except:
#                         pass
#                 try:
#                     veh_kWh = veh_vmt * onroad_kwh_per_mile
#                     VehicleAnnualData.update_vehicle_annual_data(vehicle, cy, 'onroad_fuel_consumption_rate', onroad_kwh_per_mile)
#                     VehicleAnnualData.update_vehicle_annual_data(vehicle, cy, 'fuel_consumption', veh_kWh)
#                 except:
#                     pass


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

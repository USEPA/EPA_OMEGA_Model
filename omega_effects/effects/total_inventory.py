

def calc_total_inventory(physical_effects_dict):

    for v in physical_effects_dict.values():

        v['voc_upstream_ustons'] = v['voc_refinery_ustons'] + v['voc_egu_ustons']
        v['co_upstream_ustons'] = v['co_refinery_ustons'] + v['co_egu_ustons']
        v['nox_upstream_ustons'] = v['nox_refinery_ustons'] + v['nox_egu_ustons']
        v['pm25_upstream_ustons'] = v['pm25_refinery_ustons'] + v['pm25_egu_ustons']
        v['sox_upstream_ustons'] = v['sox_refinery_ustons'] + v['sox_egu_ustons']

        v['co2_upstream_metrictons'] = v['co2_refinery_metrictons'] + v['co2_egu_metrictons']
        v['ch4_upstream_metrictons'] = v['ch4_refinery_metrictons'] + v['ch4_egu_metrictons']
        v['n2o_upstream_metrictons'] = v['n2o_refinery_metrictons'] + v['n2o_egu_metrictons']

        # sum vehicle and upstream into totals
        v['nmog_and_voc_total_ustons'] = v['nmog_vehicle_ustons'] + v['voc_upstream_ustons']
        v['co_total_ustons'] = v['co_vehicle_ustons'] + v['co_upstream_ustons']
        v['nox_total_ustons'] = v['nox_vehicle_ustons'] + v['nox_upstream_ustons']
        v['pm25_total_ustons'] = v['pm25_vehicle_ustons'] + v['pm25_upstream_ustons']
        v['sox_total_ustons'] = v['sox_vehicle_ustons'] + v['sox_upstream_ustons']
        v['acetaldehyde_total_ustons'] = v['acetaldehyde_vehicle_ustons']  # + acetaldehyde_upstream_ustons
        v['acrolein_total_ustons'] = v['acrolein_vehicle_ustons']  # + acrolein_upstream_ustons
        v['benzene_total_ustons'] = v['benzene_vehicle_ustons']  # + benzene_upstream_ustons
        v['ethylbenzene_total_ustons'] = v['ethylbenzene_vehicle_ustons']  # + ethylbenzene_upstream_ustons
        v['formaldehyde_total_ustons'] = v['formaldehyde_vehicle_ustons']  # + formaldehyde_upstream_ustons
        v['naphthalene_total_ustons'] = v['naphthalene_vehicle_ustons']  # + naphlathene_upstream_ustons
        v['13_butadiene_total_ustons'] = v['13_butadiene_vehicle_ustons']  # + butadiene13_upstream_ustons
        v['15pah_total_ustons'] = v['15pah_vehicle_ustons']  # + pah15_upstream_ustons

        v['co2_total_metrictons'] = v['co2_vehicle_metrictons'] + v['co2_upstream_metrictons']
        v['ch4_total_metrictons'] = v['ch4_vehicle_metrictons'] + v['ch4_upstream_metrictons']
        v['n2o_total_metrictons'] = v['n2o_vehicle_metrictons'] + v['n2o_upstream_metrictons']

    return physical_effects_dict

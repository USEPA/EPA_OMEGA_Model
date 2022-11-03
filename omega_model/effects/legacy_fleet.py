from omega_model import *
# import omega_model.effects.general_functions as gen_fxns


class LegacyFleet(OMEGABase):
    """
    Loads and provides access to legacy fleet data by model year and age.

    """

    _data = dict()  # private dict, the legacy_fleet_file data
    _legacy_fleet = dict() # the built legacy fleet for the analysis

    @staticmethod
    def get_legacy_fleet_data(key, *args):
        """

        Args:
            key (tuple): the LegacyFleet._legacy_fleet key
            args (str, strs): name of attributes for which attribute values are sought

        Returns:
            A list of values associated with the key for each arg passed

        """
        return_values = list()
        for arg in args:
            return_values.append(LegacyFleet._legacy_fleet[key][arg])

        return return_values

    @staticmethod
    def update_legacy_fleet(key, update_dict):
        """

        Parameters:
            key: tuple; the LegacyFleet._legacy_fleet dict key
            update_dict: Dictionary; represents the attribute-value pairs to be updated

        Returns:
            Nothing, but updates the object dictionary with update_dict

        """
        if key in LegacyFleet._legacy_fleet:
            for attribute_name, attribute_value in update_dict.items():
                LegacyFleet._legacy_fleet[key][attribute_name] = attribute_value

        else:
            LegacyFleet._legacy_fleet.update({key: {}})
            for attribute_name, attribute_value in update_dict.items():
                LegacyFleet._legacy_fleet[key].update({attribute_name: attribute_value})

    @staticmethod
    def init_from_file(filename, verbose=False):
        """

        Initialize class data from input file.

        Args:
            filename (str): name of input file
            verbose (bool): enable additional console and logfile output if True

        Returns:
            List of template/input errors, else empty list on success

        """
        LegacyFleet._data.clear()

        if verbose:
            omega_log.logwrite(f'\nInitializing database from {filename}...')

        input_template_name = 'legacy_fleet'
        input_template_version = 0.1
        input_template_columns = {'model_year',
                                  'age',
                                  'calendar_year',
                                  'reg_class_id',
                                  'body_style',
                                  'market_class_id',
                                  'in_use_fuel_id',
                                  'registered_count',
                                  'miles_per_gallon',
                                  'horsepower',
                                  'curbweight_lbs',
                                  'fuel_capacity_gallons',
                                  'kwh_per_mile',
                                  'range_miles',
                                  'transaction_price_dollars',
                                  }

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            df.fillna(0, inplace=True)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                key = pd.Series(zip(
                    df['age'],
                    df['calendar_year'],
                    df['reg_class_id'],
                    df['market_class_id'],
                    df['in_use_fuel_id'],
                ))
                # add attributes that are populated in build_legacy_fleet_for_analysis
                df.insert(0, 'vehicle_id', pow(10, 6))
                df.insert(len(df.columns), 'annual_vmt', 0)
                df.insert(len(df.columns), 'odometer', 0)
                LegacyFleet._data = df.set_index(key).to_dict(orient='index')

        return template_errors

    @staticmethod
    def build_legacy_fleet_for_analysis(calendar_years):

        from consumer.reregistration_fixed_by_age import Reregistration
        from consumer.annual_vmt_fixed_by_age import OnroadVMT

        vehicle_id_increment = 0
        for calendar_year in calendar_years:

            for key, nested_dict in LegacyFleet._data.items():

                last_age, last_calendar_year, reg_class_id, market_class_id, fuel_id = key
                model_year = nested_dict['model_year']
                new_age = calendar_year - model_year

                reregistered_proportion = Reregistration.get_reregistered_proportion(model_year, market_class_id, new_age)
                new_registered_count = nested_dict['registered_count'] * reregistered_proportion
                if new_registered_count == 0:
                    pass

                else:
                    vehicle_id_increment += 1
                    annual_vmt = OnroadVMT.get_vmt(calendar_year, market_class_id, new_age)
                    new_key = new_age, calendar_year, reg_class_id, market_class_id, fuel_id
                    update_dict = nested_dict.copy()
                    update_dict['age'] = new_age
                    update_dict['calendar_year'] = calendar_year
                    update_dict['registered_count'] = new_registered_count
                    update_dict['annual_vmt'] = annual_vmt
                    update_dict['odometer'] = OnroadVMT.get_cumulative_vmt(market_class_id, new_age)
                    if nested_dict['vehicle_id'] == pow(10, 6):
                        update_dict['vehicle_id'] += vehicle_id_increment
                    LegacyFleet.update_legacy_fleet(new_key, update_dict)

        return LegacyFleet._legacy_fleet

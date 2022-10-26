from omega_model import *
# import omega_model.effects.general_functions as gen_fxns


class LegacyFleet(OMEGABase):
    """
    Loads and provides access to legacy fleet data by model year and age.

    """

    _data = dict()  # private dict, cost factors social cost of carbon by calendar year

    @staticmethod
    def get_legacy_fleet_data(key, *args):
        """

        Args:
            key (tuple): the LegacyFleet._data key
            args (str, strs): name of attributes for which attribute values are sought

        Returns:
            A list of values associated with the key for each arg passed

        """
        return_values = list()
        for arg in args:
            return_values.append(LegacyFleet._data[key][arg])

        return return_values

    @staticmethod
    def update_legacy_fleet(key, update_dict):
        """

        Parameters:
            key: tuple; the LegacyFleet._data dict key
            update_dict: Dictionary; represents the attribute-value pairs to be updated

        Returns:
            Nothing, but updates the object dictionary with update_dict

        """
        if key in LegacyFleet._data:
            for attribute_name, attribute_value in update_dict.items():
                LegacyFleet._data[key][attribute_name] = attribute_value

        else:
            LegacyFleet._data.update({key: {}})
            for attribute_name, attribute_value in update_dict.items():
                LegacyFleet._data[key].update({attribute_name: attribute_value})

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
            # df = df.loc[df['dollar_basis'] != 0, :]

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns, verbose=verbose)

            # cols_to_convert = [col for col in df.columns if 'USD_per_metricton' in col]

            # df = gen_fxns.adjust_dollars(df, 'ip_deflators', omega_globals.options.analysis_dollar_basis, *cols_to_convert)

            if not template_errors:
                key = pd.Series(zip(
                    df['age'],
                    df['calendar_year'],
                    df['reg_class_id'],
                    df['market_class_id'],
                    df['in_use_fuel_id'],
                ))
                LegacyFleet._data = df.set_index(key).to_dict(orient='index')

        return template_errors

    @staticmethod
    def build_legacy_fleet_for_analysis(calendar_years):

        from consumer.reregistration_fixed_by_age import Reregistration
        from consumer.annual_vmt_fixed_by_age import OnroadVMT

        _dict = LegacyFleet._data.copy()
        for calendar_year in calendar_years:

            # _dict = LegacyFleet._data.copy()
            for key, value in _dict.items():

                last_age, last_calendar_year, reg_class_id, market_class_id, fuel_id = key
                model_year = value['model_year']
                new_age = calendar_year - model_year

                reregistered_proportion = Reregistration.get_reregistered_proportion(model_year, market_class_id, new_age)
                new_registered_count = value['registered_count'] * reregistered_proportion
                if new_registered_count == 0:
                    pass

                else:
                    update_dict = dict()
                    annual_vmt = OnroadVMT.get_vmt(calendar_year, market_class_id, new_age)
                    new_key = new_age, calendar_year, reg_class_id, market_class_id, fuel_id
                    # update_dict.update({new_key: value})
                    update_dict[new_key]['age'] = new_age
                    update_dict[new_key]['calendar_year'] = calendar_year
                    update_dict[new_key]['registered_count'] = new_registered_count
                    update_dict[new_key]['annual_vmt'] = annual_vmt
                    update_dict[new_key]['odometer'] = OnroadVMT.get_cumulative_vmt(market_class_id, new_age)
                    LegacyFleet.update_legacy_fleet(new_key, update_dict)

        return LegacyFleet._data

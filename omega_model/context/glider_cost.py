"""

**Routines to glider cost.

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.  The template header uses a dynamic format.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,glider_cost,input_template_version:,0.1,``{optional_source_data_comment}``

Sample Data Columns
    .. csv-table::
        :widths: auto

        body_style,item,material,value,dollar_basis,notes
        sedan,unibody_structure,aluminum,(2.55) * structure_mass_lbs * MARKUP,2020,
        sedan,unibody_structure,steel,(1.8) * structure_mass_lbs * MARKUP,2020,
        cuv_suv,unibody_structure,aluminum,(2.65) * structure_mass_lbs * MARKUP,2020,

----

**CODE**

"""
import pandas as pd

print('importing %s' % __file__)

from omega_model import *
from effects.general_functions import dollar_adjustment_factor

_cache = dict()


class GliderCost(OMEGABase):
    """
    **Loads and provides access to glider cost data, provides methods to calculate glider costs.**

    """

    @staticmethod
    def calc_cost(vehicle, pkg_df):
        """
        Calculate the value of the response surface equation for the given powertrain type, cost curve class (tech
        package) for the full factorial combination of the iterable terms.

        Args:
            vehicle (Vehicle): the vehicle to calc costs for
            pkg_df (DataFrame): the necessary information for developing cost estimates.

        Returns:
            A list of cost values indexed the same as pkg_df.

        """
        results = []

        base_powertrain_cost \
            = vehicle.powertrain_cost

        body_structure = 'unibody_structure'
        if vehicle.unibody_structure == 0:
            body_structure = 'ladder_structure'

        # markups and learning
        markup = eval(_cache['ALL', 'markup', 'not applicable']['value'], {}, locals())
        learning_rate = eval(_cache['ALL', 'learning_rate', 'not applicable']['value'], {}, locals())
        learning_start = eval(_cache['ALL', 'learning_start', 'not applicable']['value'], {}, locals())
        legacy_sales_scaler = eval(_cache['ALL', 'legacy_sales_learning_scaler', 'not applicable']['value'], {}, locals())
        sales_scaler = eval(_cache['ALL', 'sales_scaler', 'not applicable']['value'], {}, locals())
        cumulative_sales = sales_scaler * (vehicle.model_year - learning_start)
        learning_factor = ((cumulative_sales + legacy_sales_scaler) / legacy_sales_scaler) ** learning_rate

        # first calc base glider structure and non-structure weights
        structure_mass_lbs = vehicle.base_year_structure_mass_lbs
        adj_factor = _cache[vehicle.body_style, body_structure, vehicle.structure_material]['dollar_adjustment']
        structure_cost = eval(_cache[vehicle.body_style, body_structure, vehicle.structure_material]['value'], {}, locals()) \
                         * adj_factor * learning_factor

        base_year_glider_non_structure_cost = (vehicle.base_year_msrp_dollars / markup) - structure_cost - base_powertrain_cost

        # now calc package costs
        for idx, row in pkg_df.iterrows():
            # glider structure cost
            structure_mass_lbs = row['structure_mass_lbs']
            material = row['structure_material']
            adj_factor = _cache[vehicle.body_style, body_structure, material]['dollar_adjustment']
            pkg_structure_cost = eval(_cache[vehicle.body_style, body_structure, material]['value'], {}, locals()) \
                                        * adj_factor * learning_factor

            # glider non-structure cost
            delta_footprint = vehicle.base_year_footprint_ft2 - row['footprint_ft2']
            adj_factor = _cache[vehicle.body_style, 'non_structure', 'various']['dollar_adjustment']
            delta_glider_non_structure_cost = eval(_cache[vehicle.body_style, 'non_structure', 'various']['value'], {}, locals()) \
                                              * adj_factor * learning_factor
            pkg_glider_non_structure_cost = base_year_glider_non_structure_cost + delta_glider_non_structure_cost

            pkg_glider_cost = pkg_structure_cost + pkg_glider_non_structure_cost

            results.append((pkg_glider_cost, pkg_structure_cost, pkg_glider_non_structure_cost))

        return results

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
        _cache.clear()

        if verbose:
            omega_log.logwrite('\nInitializing GliderCost from %s...' % filename, echo_console=True)
        input_template_name = 'glider_cost'
        input_template_version = 0.11
        input_template_columns = {'body_style', 'item', 'structure_material', 'value', 'dollar_basis', 'notes'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)
        if not template_errors:

            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns,
                                                        verbose=verbose)

            if not template_errors:

                cost_keys = zip(df['body_style'], df['item'], df['structure_material'])

                for cost_key in cost_keys:

                    _cache[cost_key] = dict()
                    body_style, item, structure_material = cost_key

                    cost_info = df[(df['body_style'] == body_style)
                                   & (df['item'] == item)
                                   & (df['structure_material'] == structure_material)].iloc[0]

                    _cache[cost_key] = {'value': dict(),
                                        'dollar_adjustment': 1}

                    if cost_info['dollar_basis'] > 0:
                        adj_factor = dollar_adjustment_factor('ip_deflators', int(cost_info['dollar_basis']))
                        _cache[cost_key]['dollar_adjustment'] = adj_factor

                    _cache[cost_key]['value'] = compile(cost_info['value'], '<string>', 'eval')

        return template_errors

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

       input_template_name:,``[module_name]``,input_template_version:,0.1,``{optional_source_data_comment}``

Sample Data Columns
    .. csv-table::
        :widths: auto

        body_style,item,material,value,dollar_basis,notes
        sedan,unibody_structure,aluminum,(2.55) * GLIDER_WEIGHT * MARKUP,2020,
        sedan,unibody_structure,steel,(1.8) * GLIDER_WEIGHT * MARKUP,2020,
        cuv_suv,unibody_structure,aluminum,(2.65) * GLIDER_WEIGHT * MARKUP,2020,

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
    def calc_cost(veh, pkg_df):
        """
        Calculate the value of the response surface equation for the given powertrain type, cost curve class (tech
        package) for the full factorial combination of the iterable terms.

        Args:
            veh (object): an object of the vehicles.Vehicle class.
            pkg_df (DataFrame): the necessary information for developing cost estimates.

        Returns:
            A list of cost values indexed the same as pkg_df.

        """
        results = []

        base_footprint, model_year, base_msrp, context_size_class \
            = veh.footprint_ft2, veh.model_year, veh.msrp_dollars, veh.context_size_class
        unibody_structure, base_glider_structure_weight, material, base_powertrain_cost \
            = veh.unibody_structure, veh.glider_structure_weight, veh.material, veh.powertrain_cost
        base_height, base_ground_clearance \
            = veh.height_in, veh.ground_clearance_in
        # for testing
        # base_footprint, model_year, base_msrp, context_size_class, unibody_structure, base_glider_structure_weight, \
        # material, base_powertrain_cost, base_height, base_ground_clearance \
        #     = veh

        structure = 'unibody_structure'
        if unibody_structure == 0:
            structure = 'ladder_structure'

        body_style_dict = {'Compact': 'sedan',
                           'Large Utility': 'pickup',
                           'Large': 'sedan',
                           'Large Crossover': 'cuv_suv',
                           'Large Pickup': 'pickup',
                           'Large Van': 'cuv_suv',
                           'Midsize': 'sedan',
                           'Minicompact': 'sedan',
                           'Small Crossover': 'cuv_suv',
                           'Small Pickup': 'pickup',
                           'Small Utility': 'cuv_suv',
                           'Small Van': 'cuv_suv',
                           'Subcompact': 'sedan',
                           'Two Seater': 'sedan',
                           }

        body_style = body_style_dict[context_size_class]

        # markups and learning
        MARKUP = eval(_cache['ALL', 'markup', 'not applicable']['value'], {}, locals())

        learning_rate = eval(_cache['ALL', 'learning_rate', 'not applicable']['value'], {}, locals())
        learning_start = eval(_cache['ALL', 'learning_start', 'not applicable']['value'], {}, locals())
        legacy_sales_scaler = eval(_cache['ALL', 'legacy_sales_learning_scaler', 'not applicable']['value'], {}, locals())
        sales_scaler = eval(_cache['ALL', 'sales_scaler', 'not applicable']['value'], {}, locals())
        cumulative_sales = sales_scaler * (model_year - learning_start)
        learning_factor = ((cumulative_sales + legacy_sales_scaler) / legacy_sales_scaler) ** learning_rate

        # first calc base glider structure and non-structure weights
        GLIDER_WEIGHT = base_glider_structure_weight
        adj_factor = _cache[body_style, structure, material]['dollar_adjustment']
        base_glider_structure_cost = eval(_cache[body_style, structure, material]['value'], {}, locals()) \
                                     * adj_factor * learning_factor

        base_glider_non_structure_cost = (base_msrp / MARKUP) - base_glider_structure_cost - base_powertrain_cost

        # now calc package costs
        for idx, row in pkg_df.iterrows():

            # glider structure cost
            GLIDER_WEIGHT = row['glider_structure_weight']
            material = row['material']
            adj_factor = _cache[body_style, structure, material]['dollar_adjustment']
            pkg_glider_structure_cost = eval(_cache[body_style, structure, material]['value'], {}, locals()) \
                                        * adj_factor * learning_factor

            # glider non-structure cost
            DELTA_FOOTPRINT = base_footprint - row['footprint_ft2']
            DELTA_HEIGHT = base_height - row['height_in']
            DELTA_CLEARANCE = base_ground_clearance - row['ground_clearance_in']
            adj_factor = _cache[body_style, 'non_structure', 'various']['dollar_adjustment']
            delta_glider_non_structure_cost = eval(_cache[body_style, 'non_structure', 'various']['value'], {}, locals()) \
                                              * adj_factor * learning_factor
            pkg_glider_non_structure_cost = base_glider_non_structure_cost + delta_glider_non_structure_cost

            pkg_glider_cost = pkg_glider_structure_cost + pkg_glider_non_structure_cost

            results.append(pkg_glider_cost)

        return results

    @staticmethod
    def init_from_file(filename, verbose=False):

        _cache.clear()

        if verbose:
            omega_log.logwrite('\nInitializing GliderCost from %s...' % filename, echo_console=True)
        input_template_name = __name__
        input_template_version = 0.1
        input_template_columns = {'body_style', 'item', 'material', 'value', 'dollar_basis', 'notes'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)
        if not template_errors:

            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns,
                                                        verbose=verbose)

            if not template_errors:

                cost_keys = zip(df['body_style'], df['item'], df['material'])

                for cost_key in cost_keys:

                    _cache[cost_key] = dict()
                    body_style, item, material = cost_key

                    cost_info = df[(df['body_style'] == body_style)
                                   & (df['item'] == item)
                                   & (df['material'] == material)].iloc[0]

                    _cache[cost_key] = {'value': dict(),
                                        'dollar_adjustment': 1}

                    if cost_info['dollar_basis'] > 0:
                        adj_factor = dollar_adjustment_factor('ip_deflators', int(cost_info['dollar_basis']))
                        _cache[cost_key]['dollar_adjustment'] = adj_factor

                    _cache[cost_key]['value'] = compile(cost_info['value'], '<string>', 'eval')

        return template_errors

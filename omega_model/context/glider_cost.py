"""

**Routines to calculate glider cost.**

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.  The template header uses a dynamic format.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,glider_cost,input_template_version:,0.11,notes:,20220719 structure costs for aluminum BIW aligned with FEV Venza and Silverado teardowns

Sample Data Columns
    .. csv-table::
        :widths: auto

        body_style,item,material,value,dollar_basis
        sedan,unibody_structure,steel,(1.5 * structure_mass_lbs + 1500) * markup,2020
        sedan,unibody_structure,aluminum,(3.4 * structure_mass_lbs + 1500) * markup,2020
        cuv_suv,unibody_structure,aluminum,(3.4 * structure_mass_lbs + 1700) * markup,2020

Data Column Name and Description
    :body_style:
        Vehicle body style, e.g. 'sedan', 'ALL', etc

    :item:
        Name of the glider cost parameter, e.g. 'unibody_structure', 'learning_rate', etc

    :material:
        Parameter material type, e.g. 'steel', 'aluminum', etc

    :value:
        The parameter cost value or equation to be evaulated

    :dollar_basis:
        The dollar basis year for the cost value, e.g. ``2020``

----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *
from context.ip_deflators import ImplicitPriceDeflators

_cache = dict()


class GliderCost(OMEGABase):
    """
    **Loads and provides access to glider cost data, provides methods to calculate glider costs.**

    """

    @staticmethod
    def get_markups_and_learning(vehicle):
        """

        Args:
            vehicle:

        Returns:

        """
        # for future vectorizing if "vehicle" is not a Vehicle() ... could do this earlier in the init, too
        # body_structure = vehicle.unibody_structure.replace({0: 'ladder_structure', 1: 'unibody_structure'})

        body_structure = 'unibody_structure'
        if vehicle.unibody_structure == 0:
            body_structure = 'ladder_structure'

        locals_dict = locals()

        # markups and learning
        markup = eval(_cache['ALL', 'markup', 'not applicable']['value'], {}, locals_dict)
        learning_rate = eval(_cache['ALL', 'learning_rate', 'not applicable']['value'], {}, locals_dict)
        learning_start = eval(_cache['ALL', 'learning_start', 'not applicable']['value'], {}, locals_dict)
        legacy_sales_scaler = eval(_cache['ALL', 'legacy_sales_learning_scaler', 'not applicable']['value'], {},
                                   locals_dict)
        sales_scaler = eval(_cache['ALL', 'sales_scaler', 'not applicable']['value'], {}, locals_dict)

        cumulative_sales = abs(sales_scaler * (vehicle.model_year - learning_start))
        learning_factor = ((cumulative_sales + legacy_sales_scaler) / legacy_sales_scaler) ** learning_rate
        if vehicle.model_year < learning_start:
            learning_factor = 1 / learning_factor

        return body_structure, learning_factor, markup

    @staticmethod
    def get_base_year_glider_non_structure_cost(vehicle, structure_mass_lbs, powertrain_cost):
        """
        Calculate the base year glider non-structure cost.

        Args:
            vehicle (Vehicle): the vehicle to calculate the glider non-structure cost for
            structure_mass_lbs (float): vehicle structure mass in pounds
            powertrain_cost (float): powertrain cost in dollars

        Returns:
            Vehicle base year glider non-structure cost.

        """
        body_structure, learning_factor, markup = GliderCost.get_markups_and_learning(vehicle)

        # first calc base glider structure and non-structure weights

        # convert adj_factor and structure_cost to np.array(list comprehensions) for vectorizing...

        adj_factor = _cache[vehicle.body_style, body_structure, vehicle.structure_material]['dollar_adjustment']
        structure_cost = eval(_cache[vehicle.body_style, body_structure, vehicle.structure_material]['value'], {},
                              locals()) * adj_factor * learning_factor

        base_year_glider_non_structure_cost = \
            vehicle.base_year_msrp_dollars - structure_cost - powertrain_cost

        return base_year_glider_non_structure_cost

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

        from context.mass_scaling import MassScaling

        body_structure, learning_factor, markup = GliderCost.get_markups_and_learning(vehicle)

        structure_mass_lbs = pkg_df['structure_mass_lbs'].values
        delta_footprint = pkg_df['footprint_ft2'].values - vehicle.base_year_footprint_ft2

        locals_dict = locals()  # cache local equation terms

        # glider structure cost
        adj_factor = np.array([_cache[vehicle.body_style, body_structure, sm]['dollar_adjustment']
                               for sm in pkg_df['structure_material']])

        values = np.zeros_like(structure_mass_lbs)
        for structure_material in MassScaling.structure_materials:
            values += eval(_cache[vehicle.body_style, body_structure, structure_material]['value']) * \
                      (pkg_df['structure_material'].values == structure_material)
        structure_cost = values * adj_factor * learning_factor

        # glider non-structure cost
        adj_factor = _cache[vehicle.body_style, 'non_structure', 'various']['dollar_adjustment']
        delta_glider_non_structure_cost = eval(_cache[vehicle.body_style, 'non_structure', 'various']['value'],
                                               {}, locals_dict) * adj_factor * learning_factor

        glider_non_structure_cost = \
            vehicle.base_year_glider_non_structure_cost_dollars + delta_glider_non_structure_cost

        return structure_cost, glider_non_structure_cost

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
            omega_log.logwrite('\nInitializing GliderCost from %s...' % filename)
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
                        adj_factor = ImplicitPriceDeflators.dollar_adjustment_factor(int(cost_info['dollar_basis']))
                        _cache[cost_key]['dollar_adjustment'] = adj_factor

                    _cache[cost_key]['value'] = compile(str(cost_info['value']), '<string>', 'eval')

        return template_errors

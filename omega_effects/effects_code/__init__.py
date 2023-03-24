"""

**OMEGA effects code subpackage.**

----

**CODE**

"""
# Version number of the omega effects module, not the omega model

__version__ = '0.6.0'

# 0.6.0
# Fixes for better tracking of powertrain type for maintenance and repair costs by using tech flags rather than
# base_year_powertrain_type.

# 0.5.0
# Add MY calcs for physical effects.
# Cleanup to use pd.concat() rather than df.insert().

# MY function now uses purchase_price attribute rather than consumer_price.
# Add domestic SCC calcs.
# batch file now includes toggle for net benefits using 'global', 'domestic' or 'both'
# Refactor CAP benefit attribute names to use study names rather than low/high distinction.
# No change to results.
# Fixes to vmt adjustments and legacy fleet handling, largely for MD.
# vmt and stock adjustments now handled separate from safety calcs.

# 0.4.3
# Slight change to MY lifetime outputs and attribute names.

# 0.4.2
# Add entry (set in general_inputs_for_effects.csv) to control how many years to include in consumer view.

# 0.4.1
# Add new emission_rates_refinery.py to make use of AQM derived rates.
# Fix periods calc in consumer view function of cost_effects.py.

# 0.4.0
# Add model year lifetime cost calcs to cost_effects.py.

# 0.3.0
# Add option to save or not the large vehicle-level files.
# Add footprint and workfactor to large vehicle-level files.
# Remove possible use of a context fuel cost per mile file since that will no longer be run within OMEGA compliance model.
# New batch files.

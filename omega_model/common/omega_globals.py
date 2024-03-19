"""

**OMEGA global variables.**

Runtime options to be populated during initialization.

----

**CODE**

"""

print('importing %s' % __file__)

import sys

# globals to be populated at runtime:
options = None  #: simulation options
pass_num = 0  #: multi-pass pass number
manufacturer_aggregation = False  #: true if manufacturer-level detail in vehicle aggregation
price_modification_data = None  #: holds price modification data for the current compliance_id and calendar year
locked_price_modification_data = None  #: holds price locked modification data for the current compliance_id and calendar year
cumulative_battery_GWh = {'total': 0}  #: holds cumulative battery GWh production, by calendar year, from first pass
share_precision = int(str.split(str(sys.float_info.epsilon), 'e-')[1])-1  #: round to the Nth digit when calculating share values in constraint dicts
constraints = dict()  #: dict of constraint dicts by market category
finalized_vehicles = []  #: finalized vehicles

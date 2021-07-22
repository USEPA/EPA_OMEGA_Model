"""

**The consumer package defines market classes, their associated properties, and routines to determine consumer
desired market shares as a function of market class, relative costs, etc.  The consumer module also handles vehicle
re-registration.**

----

**CODE**

"""

market_categories = ['ICE', 'BEV', 'hauling', 'non_hauling']  #: overall market categories

responsive_market_categories = ['ICE', 'BEV']  #: market categories that have consumer response (i.e. price -> sales)

non_responsive_market_categories = ['hauling', 'non_hauling']  #: market categories that do not have consumer response

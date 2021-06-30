"""

**OMEGA global variables.**

Runtime options and database connection variables to be populated during initialization.

----

**CODE**

"""


print('importing %s' % __file__)

# globals to be populated at runtime:
options = None  #: simulation options
engine = None  #: connection to database engine
session = None  #: database session

import os
import time
from datetime import datetime
import Get_URLs_Edmunds

start_time = datetime.now()
Get_URLs_Edmunds.Get_URLs_Edmunds(2021)

time_elapsed = datetime.now() - start_time
print('Time elapsed (hh:mm:ss.ms) {}'.format(time_elapsed))

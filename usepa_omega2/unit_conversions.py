"""


----

**CODE**

"""

print('importing %s' % __file__)

import numpy as np

kW2hp = 1.341
hp2kW = 1 / 1.341

rpmftlbs2hp = 1 / 5252.19943720332  # combination of rpm2radps, ftlbs2Nm, W to kW and kW2hp...

mi2mtr = 1609.344
mtr2mi = 1 / 1609.344

kmh2mph = 1000 / 1609.344
mph2kmh = 1609.344 / 1000

kmh2mps = 1 / 3.6
mps2kmh = 3.6

mps2mph = 3600 / 1609.344
mph2mps = 1609.344 / 3600

lbm2kg = 0.453592  # NIST
kg2lbm = 1 / 0.453592

kW2hp = 1.341
hp2kW = 1 / 1.341

W2kW = 1 / 1000  # by definition
kW2W = 1000

kWs2hphr = kW2hp / 3600
hphr2kWs = 3600 / kW2hp

N2lbf = 0.224808943  # google
lbf2N = 1 / 0.224808943

rpm2radps = np.pi / 30
radps2rpm = 30 / np.pi

ton2lbm = 2000
lbm2ton = 1 / 2000

gal2lit = 3.78541178
lit2gal = 1 / 3.78541178

cc2lit = 1 / 1000
lit2cc = 1000

gal2cc = 3.78541178 * 1000
cc2gal = 1 / 3.78541178 / 1000

galdies2gCO2 = 10180
gCO22galdies = 1 / 10180

galgas2gCO2 = 8887
gCO22galgas = 1 / 8887

ftlbs2Nm = 1.355818  # NIST
Nm2ftlbs = 1 / 1.355818

kPa2MPa = 1 / 1000  # by definition
MPa2kPa = 1000

kPa2bar = 1 / 100  # by definition
bar2kPa = 100

bar2MPa = 1 / 10  # by definition
MPa2bar = 10

Pa2bar = 1e-5  # by definition
bar2Pa = 1e5

psi2kPa = 6.894757  # NIST, physics.nist.gov/Pubs/SP811/appenB9.html
kPa2psi = 1 / 6.894757

psi2bar = 6.894757 / 100
bar2psi = 100 / 6.894757

BTUplbm2MJpkg = 2.326e-3
MJpkg2BTUplbm = 1 / 2.326e-3

in2m = 2.54e-02  # NIST, http://www.nist.gov/pml/wmd/metric/upload/SP1038.pdf
m2in = 1 / 2.54e-02

in2mm = 25.4
mm2in = 1 / 25.4

in2cm = 2.54
cm2in = 1 / 2.54

water_density_nominal_gpgal_60F = 3781.8  # 0.99904 = ASTM D 4052 density of water at 60F, grams per cc, rounded
water_density_gpgal_60F = 0.99904 / cc2gal  # nominal 3781.8 % 0.99904 = ASTM D 4052 density of water at 60F, grams per cc
water_density_gpL_60F = 0.99904 / cc2lit

specific_gravity2density_kgpL_60F = water_density_gpL_60F / 1000
density_kgpL2specific_gravity_60F = 1000 / water_density_gpL_60F

#class UnitConversions(object):
#    def __init__(self):

def degF2degC(F):
    return (F-32)*5/9

def degC2degF(C):
    return C*9/5 + 32

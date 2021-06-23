#Define Unit Conversion terms
#Time
hr2s = 3600
s2hr = 1/hr2s
#Mass
slug2kg = 14.5939
kg2slug = 1/slug2kg
kg2lbm = 2.20462
lbm2kg = 1/kg2lbm
#Distance
mi2km = 1.60934
km2mi = 1 / mi2km
m2in = 39.3701
in2m = 1/m2in
m2ft = 3.28084
ft2m = 1/m2ft
mi2m = mi2km*1e3
in2mm = 25.4
ft2in = 12
in2ft = 1/ft2in
#Velocity
mps2kmph = 3.6
kmph2mps = 1 / mps2kmph
mps2mph = 2.23694
mph2mps = 1/mps2mph
ftps2kmph = 1.09728
kmph2ftps = 1/ftps2kmph
mph2ftps = 1.46667
ftps2mph = 1/mph2ftps
#Acceleration
ftps22mph2 = 2454.5454545454545
mph22ftps2 = 1/ftps22mph2
mps22mph2 = 8052.9706513958
mph22mps2 = 1/mps22mph2
mps22ftps2 = mps22mph2*mph22ftps2
#Gravity
gravity_mps2 = 9.81
#Force
lbf2n = 4.44822
n2lbf = 1/lbf2n
#Power
hp2mw = 745.7e-6
hp2w = hp2mw*1e6
w2hp = 1/hp2w
mw2hp = 1/hp2mw
hp2kw = hp2mw*1000
kw2hp= 1/hp2kw
lbfftps2hp = 0.00181818182
hp2lbfftps = 1/lbfftps2hp
hp2lbfmph = (hp2w*mps2mph)*n2lbf
lbfmph2hp = s2hr*mi2m*lbf2n*w2hp
#Energy
kwhr2mj = 3.6
mj2kwhr = 1 / kwhr2mj
j2kwhr = 1/(1000*3600)
hps2kwhr = hp2kw * s2hr
btu2mj = 1055.06*1e-6
mj2btu = 1/btu2mj
#Volume
gal2l = 3.78541
l2gal = 1/gal2l
m32ft3 =(m2ft)**3
ft32m3 = (ft2m)**3
l2in3 = 61.0237
in32l = 1/l2in3
#Volumetric Energy Content
mjpl2btupf3 = 26839.2
btupf32mjpl = 1 / mjpl2btupf3
#Density
kgpm32slugpft3 = kg2slug * ft32m3
slugpft32kgpm3 = 1/kgpm32slugpft3
#Other
lbfpmph2lbfpfps = 1/1.46667
btuplbm2mjpkg = 2326*1e-6
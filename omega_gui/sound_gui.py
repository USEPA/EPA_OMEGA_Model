"""

MP3 Sound Player

"""

from playsound import playsound

import sys

if not len(sys.argv) > 1:
    print("Sound File Missing")
else:
    try:
        playsound(sys.argv[1])
    except:
        pass

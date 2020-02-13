from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(packages = [], excludes = [])

import sys
base = 'Win32GUI' if sys.platform=='win32' else None

executables = [
    Executable('omega_gui_v8.py', base=base, targetName = 'omega1')
]

setup(name='try4',
      version = '1.0',
      description = 'try4',
      options = dict(build_exe = buildOptions),
      executables = executables)

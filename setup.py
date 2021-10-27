import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.rst").read_text()

# This call to setup() does all the work
setup(
    name="usepa-omega2",
    version="1.9.2",
    description="OMEGA Model, version 2",
    long_description=README,
    long_description_content_type="text/x-rst",
    url="https://github.com/USEPA/EPA_OMEGA_Model",
    project_urls={'OMEGA2 Documentation': 'https://omega2.readthedocs.io/en/latest/index.html',
                  'Bug Tracker': 'https://github.com/USEPA/EPA_OMEGA_Model/issues',
                  'Source Code': 'https://github.com/USEPA/EPA_OMEGA_Model',
    },
    author="US EPA",
    author_email="newman.kevin@epa.gov",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    packages=["omega_model"],                # or something like packages=find_packages(exclude=("tests",)),
    include_package_data=True,
    install_requires=["numpy", "matplotlib", 'PySide2', 'PyYAML', 'multitimer'],
    entry_points={
        "console_scripts": [
            "omega2=omega_model.__main__:main",
        ]
    },
)
# coding: utf-8

import sys
from setuptools import setup, find_packages

NAME = "composition-opc-ua-interface"
VERSION = "1.0.0"

# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = ["connexion"]

setup(
    name=NAME,
    version=VERSION,
    description="composition-opc-ua-interface",
    author_email="stichling@fortiss.org",
    url="",
    keywords=["Swagger", "composition-opc-ua-interface", "opcua"],
    install_requires=REQUIRES,
    packages=find_packages(),
    package_data={'': ['connexion_description/connexion_description.yaml']},
    include_package_data=True,
    entry_points={
        'console_scripts': ['composition-opc-ua-interface=run:main']},
    long_description="""\
    composition-service API
    """
)


# Created by Steffen Karlsson on 02-12-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

__author__ = 'Steffen Karlsson'
__version__ = '0.1-dev'
__licence__ = 'GNU LESSER GENERAL PUBLIC LICENSE Version 3'
__doc__ = ""

from sys import path
from os import getcwd
path.append(getcwd())

from Pyro4 import locateNS
NS = locateNS()


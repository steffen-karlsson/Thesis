# Created by Steffen Karlsson on 02-12-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from sys import argv
from os import path
from bdos.config import parser


class _InvalidConfigurationFile(Exception):
    def __init__(self, message):
        super(_InvalidConfigurationFile, self).__init__(message)


def validate_configuration(index, node_types):
    cfg_file = argv[2]
    if not path.exists(cfg_file) and not cfg_file.endswith(".cfg"):
        raise _InvalidConfigurationFile("Configuration file has to be .cfg format")

    return parser.parse_project_cfg(cfg_file, index, node_types)

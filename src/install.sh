#!/bin/bash

# Created by Steffen Karlsson on 02-12-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

python setup.py sdist
pip install dist/bdos-0.1.dev0.tar.gz
make html -C docs/

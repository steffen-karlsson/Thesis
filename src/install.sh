#!/bin/bash

# Created by Steffen Karlsson on 02-12-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

validate_bdos () {
    pythonlocallib='/usr/lib/python2.7/dist-packages/bdos'
    pythonlib='/usr/local/lib/python2.7/dist-packages/bdos'

    if [ -d "$pythonlocallib" ] ;
    then
        bdosdir=${pythonlocallib}
    elif [ -d "$pythonlib" ] ;
    then
        bdosdir=${pythonlib}
    else
        echo "Aborting, please try to run the install.sh script again to succesfully install bdos"
        exit 1
    fi
}

python setup.py sdist
pip install dist/bdos-0.1.dev0.tar.gz

validate_bdos
make html -C ${bdosdir}/web/docs/

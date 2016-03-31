#!/bin/bash

# Created by Steffen Karlsson on 02-12-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

validate() {
    pythonlocallib='/usr/lib/python2.7/dist-packages/sofa'
    pythonlib='/usr/local/lib/python2.7/dist-packages/sofa'

    if [ -d "$pythonlocallib" ] ;
    then
        dir=${pythonlocallib}
    elif [ -d "$pythonlib" ] ;
    then
        dir=${pythonlib}
    else
        echo "Aborting, please try to run the install.sh script again to succesfully install sofa"
        exit 1
    fi
}

python setup.py sdist
pip install dist/sofa-0.1.dev0.tar.gz

validate
make html -C ${dir}/docs/

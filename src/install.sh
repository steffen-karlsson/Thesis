#!/bin/bash

# Created by Steffen Karlsson on 02-12-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

validate_bdae () {
    pythonlocallib='/usr/lib/python2.7/dist-packages/bdae'
    pythonlib='/usr/local/lib/python2.7/dist-packages/bdae'

    if [ -d "$pythonlocallib" ] ;
    then
        bdaedir=${pythonlocallib}
    elif [ -d "$pythonlib" ] ;
    then
        bdaedir=${pythonlib}
    else
        echo "Aborting, please try to run the install.sh script again to succesfully install bdae"
        exit 1
    fi
}

python setup.py sdist
pip install dist/bdae-0.1.dev0.tar.gz

validate_bdae
make html -C ${bdaedir}/web/docs/

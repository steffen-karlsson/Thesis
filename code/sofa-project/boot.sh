#!/bin/bash

# Created by Steffen Karlsson on 02-12-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

set_bootfile () {
    if [ "${type}" = "gateway" ] || [ "${type}" = "storage" ] || [ "${type}" = "monitor" ] ;
    then bootfile="boot.py"
    else
        echo "Invalid type, supported types are: gateway, storage, monitor"
        exit 1
    fi
}

find_cfg_param_in_type () {
    find_cfg_param ${type} $1
}

find_cfg_param () {
    argument=$2
    echo $(awk '/^\['$1'\]/{f=1} f==1&&/^'${argument}'/{print $3;exit}' ${cfg_file})
}

validate_sofa () {
    pythonlocallib='/usr/lib/python2.7/dist-packages/sofa'
    pythonlib='/usr/local/lib/python2.7/dist-packages/sofa'

    if [ -d "$pythonlocallib" ] ;
    then
        sofadir=${pythonlocallib}
    elif [ -d "$pythonlib" ] ;
    then
        sofadir=${pythonlib}
    else
        echo "Aborting, please try to run the install.sh script again to succesfully install sofa"
        exit 1
    fi
}

validate_pyro () {
    OUTPUT=`pgrep pyro4-ns`
    if [ "${#OUTPUT}" -eq 0 ] ;
    then pyro4-ns &
    fi
}

start_gateway () {
    i=0
    directory=$(find_cfg_param general project-path)
    addresses=$(find_cfg_param_in_type addresses)
    echo "NOTE: Remeber to execute install.sh on" ${addresses}

    for address in $(echo $(find_cfg_param_in_type addresses) | tr ',' "\n")
    do
        ip=$(echo ${address} | awk -F ':' '{print $1}')
        echo "Booting node as: python "${sofadir}/${bootfile} ${i} ${cfg_file} ${types[@]} "at" ${address}
        nohup ssh ${ip} bash -c "'python " ${sofadir}/${bootfile} ${i} ${cfg_file} ${types[@]}"'" > /dev/null 2>&1 &
        i=$((i+1))
    done
}

if [ ! $# -ge 2 ]
then
  echo "Illegal ammount of argument, \$1: config file \$2: sections parsed from the file (first is booted)"
  echo "Supported types: gateway, storage, monitor"
  exit
fi

args=( $@ )
cfg_file=${args[0]}
types=( ${args[@]:1} )
type=${types[0]}

validate_sofa
set_bootfile
validate_pyro
start_gateway

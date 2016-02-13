#!/bin/bash

# Created by Steffen Karlsson on 02-12-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

if [ $# -ne 2 ]
then
  echo "Illegal ammount of argument, \$1: type \$2: config file"
  echo "Supported types: gateway, storage, monitor"
  exit
fi

type=$1
cfg_file=$2

set_bootfile () {
    if [ "${type}" = "gateway" ] || [ "${type}" = "storage" ] || [ "${type}" = "monitor" ] ;
    then bootfile="boot_"${type}".py"
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

validate_pyro () {
    OUTPUT=`pgrep pyro4-ns`
    if [ "${#OUTPUT}" -eq 0 ] ;
    then pyro4-ns &
    fi
}

start_gateway () {
    i=0
    set_bootfile
    validate_pyro

    directory=$(find_cfg_param general project-path)
    for address in $(echo $(find_cfg_param_in_type addresses) | tr ',' "\n")
    do
        ip=$(echo ${address} | awk -F ':' '{print $1}')
        echo "Booting node as: python "${directory}/"bdos/"${bootfile} ${cfg_file} ${i} "at" ${address}
        nohup ssh ${ip} bash -c "'python "${directory}/"bdos/"${bootfile} ${cfg_file} ${i}"'" > /dev/null 2>&1 &
        i=$((i+1))
    done
}

start_gateway
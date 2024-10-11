#!/bin/bash

CLUSTERID=$1
PROCID=$2
echo $PATH
echo "Runnin Cluster ${CLUSTERID} Job ${PROCID}"
BATCH_DIR=${PWD}
echo "Current dir: ${BATCH_DIR}"
# cd TEMPL_WORKDIR
# echo "Now in dir: ${PWD}"
#
hostname

tar xfz ntuple-tools.tar.gz
echo "======================"
ls

tar xfz puppi_iso_p2eg.tar.gz
echo "======================"
ls

# source ./setup_lxplus.sh
# source ./setVirtualEnvWrapper.sh
# workon TEMPL_VIRTUALENV
# cd ${BATCH_DIR}

source  puppi_iso_p2eg/bin/activate
echo "======================"
echo "Check the virtual environment"
echo $VIRTUAL_ENV
echo "======================"

date
python analyzeNtuples.py -f TEMPL_CFG -i TEMPL_INPUT -p TEMPL_COLL -s TEMPL_SAMPLE -n TEMPL_NEVENT -o ${BATCH_DIR} -r ${PROCID} -b 1

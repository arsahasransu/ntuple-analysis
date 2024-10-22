#!/bin/bash

PARENT_CLUSTERID=$1
CLUSTERID=$2
PROCID=$3

echo $PATH
echo "Runnin Cluster ${CLUSTERID} Job ${PROCID}"
BATCH_DIR=${PWD}
echo "Current dir: ${BATCH_DIR}"

hostname
source /cvmfs/sft.cern.ch/lcg/views/LCG_106a/x86_64-el9-gcc14-opt/setup.sh

ls
# # copy the output files from previous step to the scratch area
# cp -v /opt/ppd/scratch/asahasra/condor_scratch/Histos/histos_${PARENT_CLUSTERID}/*.root ./

# # delete the output files from their old location
# # rm -rv /opt/ppd/scratch/asahasra/condor_scratch/Histos/histos_${PARENT_CLUSTERID}/*.root

# # hadd the output files
# ONEFILE=$(ls *.root | head -n 1)
# BASENAME="${ONEFILE%_*}"
# hadd $BASENAME.root *.root

# # copy the hadded output files to the output directory
# cp -v $BASENAME.root /opt/ppd/scratch/asahasra/condor_scratch/Histos/histos_${PARENT_CLUSTERID}/
#!/bin/bash

CLUSTERID=$1
PROCID=$2

echo "Runnin Cluster ${CLUSTERID} Job ${PROCID}"
BATCH_DIR=${PWD}
echo "Current dir: ${BATCH_DIR}"
cd TEMPL_WORKDIR
echo "Now in dir: ${PWD}"

hostname

source ./setup_lxplus.sh
source ./setVirtualEnvWrapper.sh
workon TEMPL_VIRTUALENV

cd ${BATCH_DIR}
date
for filename in TEMPL_OUTDIR/TEMPL_INFILE; do
    eos cp TEMPL_EOSPROTOCOL$filename .
done
hadd -j 5 -k TEMPL_OUTFILE `ls TEMPL_INFILE`

#mv TEMPL_OUTFILE TEMPL_OUTDIR

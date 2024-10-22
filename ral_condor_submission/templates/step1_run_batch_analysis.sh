#!/bin/bash

CLUSTERID=$1
PROCID=$2
echo $PATH
echo "Runnin Cluster ${CLUSTERID} Job ${PROCID}"
BATCH_DIR=${PWD}
echo "Current dir: ${BATCH_DIR}"

hostname
source /cvmfs/sft.cern.ch/lcg/views/LCG_106a/x86_64-el9-gcc14-opt/setup.sh

tar xfz ntuple-tools.tar.gz
echo -e "\n======================\n"
ls

date

mkdir ./input_data_files
echo -e "\n======================\n"
echo "Check the new input folder creation"
ls
echo -e "\n======================\n"

TEMPL_ADD_TO_SH
# Files per job needs to be specified above
START_INDEX=$(( PROCID * FILESPERJOB + 1 ))
END_INDEX=$(( (PROCID+1) * FILESPERJOB ))

# Ensure the end index does not exceed the total number of lines in the file
TOTAL_LINES=$(wc -l < inputfiles_condorcopy.sh)
if [ $END_INDEX -ge $TOTAL_LINES ]; then
    END_INDEX=$TOTAL_LINES
fi

# Extract and execute the lines from START_INDEX to END_INDEX
sed -n "${START_INDEX},${END_INDEX}p" "inputfiles_condorcopy.sh" | bash

echo -e "\n======================\n"
echo "Check contents of input folder"
ls ./input_data_files
echo -e "\n======================\n"

cat sample_config.yaml
python3 analyzeNtuples.py -f TEMPL_CFG -i TEMPL_INPUT -p TEMPL_COLL -s TEMPL_SAMPLE -n TEMPL_NEVENT -o ${BATCH_DIR}

mkdir -p /opt/ppd/scratch/asahasra/condor_scratch/Histos/histos_${CLUSTERID}
BASE_FILE_NAME=$(basename histos*.root ".root")
NEW_FILE_NAME="${BASE_FILE_NAME}_${PROCID}.root"
cp -v histos*.root /opt/ppd/scratch/asahasra/condor_scratch/Histos/histos_${CLUSTERID}/${NEW_FILE_NAME}
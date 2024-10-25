rm dagman_file.dag*

hadd /opt/ppd/scratch/asahasra/condor_scratch/Histos/histos_$1/histos_dytoll_m50_PU0_eggens_v1.131Xv3ai.root /opt/ppd/scratch/asahasra/condor_scratch/Histos/histos_$1/histos_dytoll_m50_PU0_eggens_v1.131Xv3ai_*.root
mv /opt/ppd/scratch/asahasra/condor_scratch/Histos/histos_$1/histos_dytoll_m50_PU0_eggens_v1.131Xv3ai.root /opt/ppd/scratch/asahasra/condor_scratch/Histos/histos_dytoll_m50_PU0_eggens_v1.131Xv3ai.root
rm -rv /opt/ppd/scratch/asahasra/condor_scratch/Histos/histos_$1/

hadd /opt/ppd/scratch/asahasra/condor_scratch/Histos/histos_$2/histos_dytoll_m50_PU200_eggens_v1.131Xv3ai.root /opt/ppd/scratch/asahasra/condor_scratch/Histos/histos_$2/histos_dytoll_m50_PU200_eggens_v1.131Xv3ai_*.root
mv /opt/ppd/scratch/asahasra/condor_scratch/Histos/histos_$2/histos_dytoll_m50_PU200_eggens_v1.131Xv3ai.root /opt/ppd/scratch/asahasra/condor_scratch/Histos/histos_dytoll_m50_PU200_eggens_v1.131Xv3ai.root
rm -rv /opt/ppd/scratch/asahasra/condor_scratch/Histos/histos_$2/
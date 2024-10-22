rm dagman_file.dag*

hadd /opt/ppd/scratch/asahasra/condor_scratch/Histos/histos_$1/histos_dytoll_m50_PU0_eggens_v1.131Xv3ai.root /opt/ppd/scratch/asahasra/condor_scratch/Histos/histos_$1/histos_dytoll_m50_PU0_eggens_v1.131Xv3ai_*.root
rm /opt/ppd/scratch/asahasra/condor_scratch/Histos/histos_$1/histos_dytoll_m50_PU0_eggens_v1.131Xv3ai_*.root

hadd /opt/ppd/scratch/asahasra/condor_scratch/Histos/histos_$2/histos_dytoll_m50_PU200_eggens_v1.131Xv3ai.root /opt/ppd/scratch/asahasra/condor_scratch/Histos/histos_$2/histos_dytoll_m50_PU200_eggens_v1.131Xv3ai_*.root
rm /opt/ppd/scratch/asahasra/condor_scratch/Histos/histos_$2/histos_dytoll_m50_PU200_eggens_v1.131Xv3ai_*.root

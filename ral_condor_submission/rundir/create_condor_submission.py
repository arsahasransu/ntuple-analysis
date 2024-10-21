import argparse
import copy
import glob
import os
import shutil
import subprocess
from typing import Any, Mapping
import yaml

def check_unreplaced_keys(file):
    with open(file, 'r') as f:
        filedata = f.read()

    for line in filedata.split('\n'):
        if 'TEMP' in line:
            raise ValueError(f'Unreplaced key in file {file}: {line}')


def copy_and_replace(template_file, new_file, replacements:Mapping[str, Any]):
    shutil.copyfile(template_file, new_file)
    with open(new_file, 'r') as file:
        filedata = file.read()

    for key, value in replacements.items():
        filedata = filedata.replace(key, str(value))

    with open(new_file, 'w') as file:
        file.write(filedata)

    check_unreplaced_keys(new_file)


# Read arguments from command line
parser = argparse.ArgumentParser(description='Create HTCondor submission files.')
parser.add_argument('--config', type=str, required=True, help='Path to the condor submit config YAML file')
args = parser.parse_args()

# Read input yaml config for condor configuration
condor_submit_config = yaml.load(open(args.config), Loader=yaml.FullLoader)

input_dir = condor_submit_config['dataset']['input_dir']

datasets = list(condor_submit_config['samples'].keys())
for dataset in datasets:
    print(f'\nCreating condor submission config for dataset: {dataset}\n')
    condorDir = f"{dataset}_condorDir"
    if not os.path.exists(condorDir):
        os.mkdir(condorDir)
        os.mkdir(f"{condorDir}/logs")
        os.mkdir(f"{condorDir}/outs")
        os.mkdir(f"{condorDir}/errs")
    else:
        res = input(f"Directory {condorDir} already exists. Should it be remade? (y/n)").lower()
        if res == 'y':
            os.system(f"rm -rf {condorDir}")
            os.mkdir(condorDir)
            os.mkdir(f"{condorDir}/logs")
            os.mkdir(f"{condorDir}/outs")
            os.mkdir(f"{condorDir}/errs")
        else:
            print(f"Skipping dataset {dataset}")
            continue

    input_sample_dir = condor_submit_config['samples'][dataset]['input_sample_dir']
    events_per_file = condor_submit_config['samples'][dataset]['events_per_file']
    files_per_job = condor_submit_config['samples'][dataset]['files_per_job']
    maxjobs = condor_submit_config['samples'][dataset]['maxjobs']

    # Read the input file list - split into jobs and copy to the input_data_files directory
    input_files = glob.glob(os.path.join(input_dir, input_sample_dir, '*.root'))
    numjobs = len(input_files) // files_per_job if len(input_files) // files_per_job < maxjobs else maxjobs
    inputfiles_condorcopy = ''
    for jobnum in range(numjobs):
        start_index = jobnum * files_per_job
        end_index = start_index + files_per_job
        job_input_files = input_files[start_index:end_index]
        
        for input_file in job_input_files:
            inputfiles_condorcopy += f'cp -v {input_file} ./input_data_files/\n'
    with open(f'{condorDir}/inputfiles_condorcopy.sh', 'w') as f:
        f.write(inputfiles_condorcopy)
    
    # Copy the samples yaml file
    condor_sample_config = copy.deepcopy(condor_submit_config)
    condor_sample_config['dataset']['input_dir'] = './'
    del condor_sample_config['samples']
    condor_sample_config['samples'] = {dataset: {'input_sample_dir': 'input_data_files/'}}
    with open(f'{condorDir}/sample_config.yaml', 'w') as f:
        yaml.dump(condor_sample_config, f)

    add_to_sh = f'FILESPERJOB={files_per_job}\n'

    condor_analysis_sub_replacements = {
        'TEMP_SH_FILENAME': 'run_batch_analysis.sh',
        'TEMP_MONITORPATH': '.',
        'TEMP_JOBFLAVOUR': 'espresso',
        'TEMP_JOBNUMS': numjobs,
        'TEMP_INPUTFILES': '../ntuple-tools.tar.gz,sample_config.yaml,inputfiles_condorcopy.sh'
        }
    copy_and_replace('../templates/condor.sub', f'{condorDir}/condor_batch_analysis.sub', condor_analysis_sub_replacements)

    condor_analysis_sh_replacements = {
        'TEMPL_CFG': './cfg/egiso_puppi.yaml',
        'TEMPL_INPUT': 'sample_config.yaml',
        'TEMPL_COLL': 'gen_plots',
        'TEMPL_SAMPLE': dataset,
        'TEMPL_NEVENT': events_per_file,
        'TEMPL_ADD_TO_SH': add_to_sh
    }
    copy_and_replace('../templates/run_batch_analysis.sh', f'{condorDir}/run_batch_analysis.sh', condor_analysis_sh_replacements)

# # Create environment and code tarballs
# res = input("\nRecreate environment tarball? (y/n): ").lower()
# if res == 'y':
#     try:
#         os.chdir("../../")
#         env_tarball = "ral_condor_submission/rundir/puppi_iso_p2eg.tar.gz"
#         subprocess.run(
#             ["tar", "-czf", env_tarball, "/opt/ppd/scratch/asahasra/egiso_puppi_dir/venv4histos_puppi_iso_p2eg"],
#             check=True,
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE
#         )
#         print(f"Environment tarball created at {env_tarball}\n")
#         os.chdir('ral_condor_submission/rundir')
#     except subprocess.CalledProcessError as e:
#         print(f"An error occurred while creating the tarball: {e.stderr.decode()}")
#     except Exception as e:
#         print(f"An unexpected error occurred: {str(e)}")

res = input("\nRecreate code tarball? (y/n): ").lower()
if res == 'y':
    try:
        os.chdir("../../")
        subprocess.run(
            ["git", "archive", "--format=tar.gz", "HEAD", "-o", os.path.join("ral_condor_submission/rundir/ntuple-tools.tar.gz")],
            check=True
        )
        os.chdir('ral_condor_submission/rundir')
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while creating the tarball: {e.stderr.decode()}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

# Submit jobs
res = input('Done creating condor submission files. Proceeding to submit jobs? (y/n)').lower()
for dataset in datasets:
    if res == 'y':
        os.chdir(f"{dataset}_condorDir")
        os.system(f"condor_submit condor_batch_analysis.sub")
        os.chdir("..")
    else:
        print(f"\nSubmission skipped\n")
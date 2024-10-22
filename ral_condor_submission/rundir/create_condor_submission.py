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

dagman_file_text_job = ''
dagman_file_text_script = ''
dagman_file_text_relation = ''
datasets = list(condor_submit_config['samples'].keys())
for datasetcount, dataset in enumerate(datasets):
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

    setp1_analysis_filename = 'step1_run_batch_analysis.sh'
    condor_analysis_sub_replacements = {
        'TEMP_DIR': f'{condorDir}',
        'TEMP_SH_FILENAME': f'{condorDir}/{setp1_analysis_filename}',
        'TEMP_MONITORPATH': f'./{condorDir}',
        'TEMP_JOBFLAVOUR': 'espresso',
        'TEMP_JOBNUMS': numjobs,
        'TEMP_INPUTFILES': f'ntuple-tools.tar.gz,{condorDir}/sample_config.yaml,{condorDir}/inputfiles_condorcopy.sh'
        }
    copy_and_replace('../templates/step1_condor.sub', f'{condorDir}/step1_condor_batch_analysis.sub', condor_analysis_sub_replacements)

    condor_analysis_sh_replacements = {
        'TEMPL_CFG': './cfg/egiso_puppi.yaml',
        'TEMPL_INPUT': 'sample_config.yaml',
        'TEMPL_COLL': 'gen_plots',
        'TEMPL_SAMPLE': dataset,
        'TEMPL_NEVENT': events_per_file,
        'TEMPL_ADD_TO_SH': add_to_sh
    }
    copy_and_replace(f'../templates/{setp1_analysis_filename}', f'{condorDir}/{setp1_analysis_filename}', condor_analysis_sh_replacements)

    # copy_and_replace('../templates/step2_condor_hadd.sub', f'{condorDir}/step2_condor_hadd.sub', condor_analysis_sub_replacements)

    # shutil.copyfile('../templates/step2_run_hadd.sh', f'{condorDir}/step2_run_hadd.sh')

    # Add entry for condor dagman file
    dagman_file_text_job += f'JOB analysis{datasetcount} {condorDir}/step1_condor_batch_analysis.sub\n'
    # dagman_file_text_job += f'JOB hadd{datasetcount} {condorDir}/step2_condor_hadd.sub\n'
    # dagman_file_text_script += f'SCRIPT POST analysis{datasetcount} {condorDir}/step1_post_script.sh\n'
    # dagman_file_text_relation += f'PARENT analysis{datasetcount} CHILD hadd{datasetcount}\n'

# Write the dagman file
with open('dagman_file.dag', 'w') as f:
    f.write(dagman_file_text_job)
    f.write("\n")
    # f.write(dagman_file_text_script)
    f.write("\n")
    # f.write(dagman_file_text_relation)

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

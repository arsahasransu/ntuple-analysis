import sys
import argparse

import yaml
import importlib
import pathlib

from rich import print as pprint

from python.analyzer import analyze
from python.parameters import Parameters, get_collection_parameters
from python.submission import to_HTCondor
from python.timecounter import print_stats

description = """
Main script for L1 TP analysis.

The script reads the configuration,
opens the input and output files for the given sample,
runs the event loop and saves histograms to disk.
All the analysis logic is anyhow elsewhere:

Data:
    which data are potentially read is handled in the `collections` module.
    How to select the data is handled in the `selections` module.
Plotters:
    what to do with the data is handled in the `plotters` module
Histograms:
    which histograms are produced is handled in the
    `histos` module (and the plotters).
"""



@print_stats
def analyzeNtuples(args):
    if args.submit and args.local and not args.workdir:
        raise ValueError('The --workdir option is required when submitting jobs locally')

    def parse_yaml(filename):
        with open(filename) as stream:
            return yaml.load(stream, Loader=yaml.FullLoader)

    cfgfile = {}

    # we load the python module with the same name as the yaml file
    pymoudule_path = pathlib.Path(args.configfile.split('.yaml')[0])
    formatted_path = '.'.join(pymoudule_path.with_suffix('').parts)
    sys.modules[formatted_path] = importlib.import_module(formatted_path)

    cfgfile.update(parse_yaml(args.configfile))
    cfgfile.update(parse_yaml(args.datasetfile))

    opt = Parameters(
        {
            'CONFIGFILE': args.configfile,
            'DATASETFILE': args.datasetfile,
            'COLLECTION': args.collection,
            'SAMPLE': args.sample,
            'DEBUG': args.debug,
            'NEVENTS': args.nevents,
            'BATCH': args.batch,
            'RUN': args.run,
            'OUTDIR': args.outdir,
            'LOCAL': args.local,
            'WORKERS': args.workers,
            'WORKDIR': args.workdir,
            'SUBMIT': args.submit,
        }
    )
    collection_params = get_collection_parameters(opt, cfgfile)

    samples_to_process = []

    if not opt.COLLECTION:
        print(f'\nAvailable plotter collections: {collection_params.keys()}')
        sys.exit(0)
    if opt.COLLECTION not in collection_params:
        print(f'ERROR: plotter collection {opt.COLLECTION} not in the cfg file')
        sys.exit(10)
    if not opt.SAMPLE:
        print(f'Plotter collection: {opt.COLLECTION}, available samples: {collection_params[opt.COLLECTION]}')
        sys.exit(0)

    if opt.SAMPLE == 'all':
        samples_to_process.extend(collection_params[opt.COLLECTION])
    else:
        sel_sample = [sample for sample in collection_params[opt.COLLECTION] if sample.name == opt.SAMPLE]
        samples_to_process.append(sel_sample[0])

    pprint(f'About to process samples: {samples_to_process}')

    plot_version = f"{cfgfile['common']['plot_version']}.{cfgfile['dataset']['version']}"

    to_HTCondor(
        analyze=analyze,
        opt=opt,
        submit_mode=args.submit,
        plot_version=plot_version,
        samples_to_process=samples_to_process,
    )

    batch_idx = -1
    if opt.BATCH and opt.RUN:
        batch_idx = int(opt.RUN)

    ret_nevents = 0
    for idx, sample in enumerate(samples_to_process):
        pprint(
            f'\n\n========================== #{idx+1}/{len(samples_to_process)}: {sample.name} ==========================\n'
        )
        ret_nevents += analyze(sample, batch_idx=batch_idx)
    return ret_nevents

def main():
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('-f', '--file', required=True, dest='configfile', help='specify the yaml configuration file')
    parser.add_argument('-i', '--input-dataset', required=True, dest='datasetfile', help='specify the yaml file defining the input dataset')
    parser.add_argument('-p', '--plotters', required=True, dest='collection', help='specify the plotters to be run')
    parser.add_argument('-s', '--sample', required=True, help='specify the sample to be processed')
    parser.add_argument('-d', '--debug', type=int, default=0, help='debug level')
    parser.add_argument('-n', '--nevents', type=int, default=10, help='# of events to process per sample')
    parser.add_argument('-b', '--batch', action='store_true', help='prepare for batch submission via CONDOR')
    parser.add_argument('-r', '--run', help='the batch_id to run (need to be used with the option -b)')
    parser.add_argument('-o', '--outdir', help='override the output directory for the files')
    parser.add_argument('-l', '--local', action='store_true', help='run the batch on local resources')
    parser.add_argument('-j', '--jobworkers', dest='workers', type=int, default=2, help='# of local workers')
    parser.add_argument('-w', '--workdir', help='local work directory')
    parser.add_argument('-S', '--submit', action='store_true', help='submit the jobs via CONDOR')

    args = parser.parse_args()
    analyzeNtuples(args)

if __name__ == '__main__':
    main()

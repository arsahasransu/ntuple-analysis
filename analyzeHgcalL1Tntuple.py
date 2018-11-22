#!/usr/bin/env python
# import ROOT
# from __future__ import print_function
from NtupleDataFormat import HGCalNtuple
import sys
import root_numpy as rnp
import root_numpy.tmva as rnptmva
import pandas as pd
import numpy as np
from multiprocessing import Pool
from shutil import copyfile

# The purpose of this file is to demonstrate mainly the objects
# that are in the HGCalNtuple
import ROOT
import os
import array
import socket
import datetime
import optparse
import yaml

import python.l1THistos as histos
import python.clusterTools as clAlgo
import traceback
import subprocess32
from python.utils import debugPrintOut

import python.file_manager as fm
import python.selections as selections


class Parameters:
    def __init__(self,
                 input_base_dir,
                 input_sample_dir,
                 output_filename,
                 output_dir,
                 clusterize,
                 eventsToDump,
                 events_per_job,
                 version,
                 plotters,
                 maxEvents=-1,
                 computeDensity=False,
                 debug=0,
                 name=''):
        self.name = name
        self.maxEvents = maxEvents
        self.debug = debug
        self.input_base_dir = input_base_dir
        self.input_sample_dir = input_sample_dir
        self.output_filename = output_filename
        self.output_dir = output_dir
        self.clusterize = clusterize
        self.eventsToDump = eventsToDump
        self.computeDensity = computeDensity
        self.events_per_job = events_per_job
        self.version = version
        self.plotters = plotters

    def __str__(self):
        return 'Name: {},\n \
                clusterize: {}\n \
                compute density: {}\n \
                maxEvents: {}\n \
                output file: {}\n \
                events per job: {}\n \
                debug: {}'.format(self.name,
                                  self.clusterize,
                                  self.computeDensity,
                                  self.maxEvents,
                                  self.output_filename,
                                  self.events_per_job,
                                  self.debug)

    def __repr__(self):
        return self.name


def convertGeomTreeToDF(tree):
    branches = [br.GetName() for br in tree.GetListOfBranches()
                if not br.GetName().startswith('c_')]
    cell_array = rnp.tree2array(tree, branches=branches)
    cell_df = pd.DataFrame()
    for idx in range(0, len(branches)):
        cell_df[branches[idx]] = cell_array[branches[idx]]
    return cell_df


def dumpFrame2JSON(filename, frame):
    with open(filename, 'w') as f:
        f.write(frame.to_json())


def unpack(mytuple):
    return mytuple[0].getDataFrame(mytuple[1])


def get_calibrated_clusters(calib_factors, input_3Dclusters):
    calibrated_clusters = input_3Dclusters.copy(deep=True)

    def apply_calibration(cluster):
        calib_factor = 1
        calib_factor_tmp = calib_factors[(calib_factors.eta_l < abs(cluster.eta)) &
                                         (calib_factors.eta_h >= abs(cluster.eta)) &
                                         (calib_factors.pt_l <= cluster.pt) &
                                         (calib_factors.pt_h > cluster.pt)]
        if not calib_factor_tmp.empty:
            # print 'cluster pt: {}, eta: {}, calib_factor: {}'.format(cluster.pt, cluster.eta, calib_factor_tmp.calib.values[0])
            # print calib_factor_tmp
            calib_factor = 1./calib_factor_tmp.calib.values[0]
        # print cluster
        # else:
            # if cluster.eta <= 2.8 and cluster.eta > 1.52 and cluster.pt > 4 and cluster.pt <= 100:
            #     print cluster[['pt', 'eta']]
        cluster.pt = cluster.pt*calib_factor
        # cluster['pt1'] = cluster.pt*calib_factor
        # cluster['cf'] = 1./calib_factor
        return cluster
        # input_3Dclusters[(input_3Dclusters.eta_l > abs(cluster.eta)) & ()]
    calibrated_clusters = calibrated_clusters.apply(apply_calibration, axis=1)
    return calibrated_clusters


def get_calibrated_clusters2(calib_factors, input_3Dclusters):
    calibrated_clusters = input_3Dclusters.copy(deep=True)

    def apply_calibration(cluster):
        calib_factor = 1.
        calib_factor_tmp = calib_factors[(calib_factors.eta_l < abs(cluster.eta)) &
                                         (calib_factors.eta_h >= abs(cluster.eta)) &
                                         (calib_factors.pt_l < cluster.pt) &
                                         (calib_factors.pt_h >= cluster.pt)]
        if not calib_factor_tmp.empty:
            # print 'cluster pt: {}, eta: {}, calib_factor: {}'.format(cluster.pt, cluster.eta, calib_factor_tmp.calib.values[0])
            # print calib_factor_tmp
            calib_factor = 1./calib_factor_tmp.calib.values[0]
        # print cluster
        else:
            if cluster.eta <= 2.8 and cluster.eta > 1.52 and cluster.pt > 4 and cluster.pt <= 100:
                print cluster[['pt', 'eta']]

        cluster['pt2'] = cluster.pt*calib_factor
        return cluster
        # input_3Dclusters[(input_3Dclusters.eta_l > abs(cluster.eta)) & ()]
    calibrated_clusters = calibrated_clusters.apply(apply_calibration, axis=1)
    return calibrated_clusters


def build3DClusters(name, algorithm, triggerClusters, pool, debug):
    trigger3DClusters = pd.DataFrame()
    if triggerClusters.empty:
        return trigger3DClusters
    clusterSides = [x for x in [triggerClusters[triggerClusters.eta > 0],
                                triggerClusters[triggerClusters.eta < 0]] if not x.empty]
    results3Dcl = pool.map(algorithm, clusterSides)
    for res3D in results3Dcl:
        trigger3DClusters = trigger3DClusters.append(res3D, ignore_index=True)

    debugPrintOut(debug, name='{} 3D clusters'.format(name),
                  toCount=trigger3DClusters,
                  toPrint=trigger3DClusters.iloc[:3])
    return trigger3DClusters


def get_merged_clusters(triggerClusters, pool, debug=0):
    merged_clusters = pd.DataFrame(columns=triggerClusters.columns)
    if triggerClusters.empty:
        return merged_clusters
    # FIXME: filter only interesting clusters
    clusterSides = [x for x in [triggerClusters[triggerClusters.eta > 0],
                                triggerClusters[triggerClusters.eta < 0]] if not x.empty]
    results3Dcl = pool.map(clAlgo.merge3DClustersEtaPhi, clusterSides)
    for res3D in results3Dcl:
        merged_clusters = merged_clusters.append(res3D, ignore_index=True)
    return merged_clusters


# @profile
def analyze(params, batch_idx=0):
    print (params)
    doAlternative = False

    debug = int(params.debug)
    computeDensity = params.computeDensity
    plot2DCLDR = False

    pool = Pool(5)

    tc_geom_df = pd.DataFrame()
    tc_rod_bins = pd.DataFrame()
    if False:
        # read the geometry dump
        geom_file = os.path.join(params.input_base_dir, 'geom/test_triggergeom.root')
        tc_geom_tree = HGCalNtuple([geom_file], tree='hgcaltriggergeomtester/TreeTriggerCells')
        tc_geom_tree.setCache(learn_events=100)
        print ('read TC GEOM tree with # events: {}'.format(tc_geom_tree.nevents()))
        tc_geom_df = convertGeomTreeToDF(tc_geom_tree._tree)
        tc_geom_df['radius'] = np.sqrt(tc_geom_df['x']**2+tc_geom_df['y']**2)
        tc_geom_df['eta'] = np.arcsinh(tc_geom_df.z/tc_geom_df.radius)

        if False:
            tc_rod_bins = pd.read_csv(filepath_or_buffer='data/TCmapping_v2.txt',
                                      sep=' ',
                                      names=['id', 'rod_x', 'rod_y'],
                                      index_col=False)
            tc_rod_bins['rod_bin'] = tc_rod_bins.apply(
                func=lambda cell: (int(cell.rod_x), int(cell.rod_y)), axis=1)

            tc_geom_df = pd.merge(tc_geom_df, tc_rod_bins, on='id')

        if debug == -4:
            tc_geom_tree.PrintCacheStats()
        print ('...done')

    tree_name = 'hgcalTriggerNtuplizer/HGCalTriggerNtuple'
    input_files = []
    range_ev = (0, params.maxEvents)

    if params.events_per_job == -1:
        print 'This is interactive processing...'
        input_files = fm.get_files_for_processing(input_dir=os.path.join(params.input_base_dir,
                                                                         params.input_sample_dir),
                                                  tree=tree_name,
                                                  nev_toprocess=params.maxEvents,
                                                  debug=debug)
    else:
        print 'This is batch processing...'
        input_files, range_ev = fm.get_files_and_events_for_batchprocessing(input_dir=os.path.join(params.input_base_dir,
                                                                                                   params.input_sample_dir),
                                                                            tree=tree_name,
                                                                            nev_toprocess=params.maxEvents,
                                                                            nev_perjob=params.events_per_job,
                                                                            batch_id=batch_idx,
                                                                            debug=debug)

    # print ('- dir {} contains {} files.'.format(params.input_sample_dir, len(input_files)))
    print '- will read {} files from dir {}:'.format(len(input_files), params.input_sample_dir)
    for file_name in input_files:
        print '        - {}'.format(file_name)

    ntuple = HGCalNtuple(input_files, tree=tree_name)
    if params.events_per_job == -1:
        if params.maxEvents == -1:
            range_ev = (0, ntuple.nevents())

    print ('- created TChain containing {} events'.format(ntuple.nevents()))
    print ('- reading from event: {} to event {}'.format(range_ev[0], range_ev[1]))

    ntuple.setCache(learn_events=1, entry_range=range_ev)
    output = ROOT.TFile(params.output_filename, "RECREATE")
    output.cd()

    if False:
        hTCGeom = histos.GeomHistos('hTCGeom')
        hTCGeom.fill(tc_geom_df[(np.abs(tc_geom_df.eta) > 1.65) & (np.abs(tc_geom_df.eta) < 2.85)])

# for index, tc_geom in tc_geom_df.iterrows():
#     tc_geom.max_dist_neigh = np.max(tc_geom.neighbor_distance)

    # ---------------------------------------------------
    # TP sets
    # tp_def = selections.tp_def
    # #tp_def_merged =
    # tp_def_calib = selections.tp_def_calib
    # gen_set = selections.gen_set
    # tt_set = selections.tt_set
    # simtt_set = selections.simtt_set
    # eg_set = selections.eg_set


    # instantiate all the plotters
    plotter_collection = []
    plotter_collection.extend(params.plotters)
    print plotter_collection

    # -------------------------------------------------------
    # book histos
    for plotter in plotter_collection:
        plotter.book_histos()

    dump = False
    # print (range_ev)

    # def apply_calibrations(original_clusters, calibration_file_name):
    calibration_file_name = 'data/calib_v2.json'
    calib_factors = pd.read_json(calibration_file_name, dtype={'calib': np.float64,
                                                               'eta_h': np.float64,
                                                               'eta_l': np.float64,
                                                               'pt_h': np.float64,
                                                               'pt_l': np.float64})

    # setup the EGID classifies
    mva_classifier = ROOT.TMVA.Reader()

    mva_classifier.AddVariable('pt_cl', array.array('f', [0.]))
    mva_classifier.AddVariable('eta_cl', array.array('f', [0.]))
    mva_classifier.AddVariable('maxLayer_cl', array.array('f', [0.]))
    mva_classifier.AddVariable('hOverE_cl', array.array('f', [0.]))
    # (this is a variable I created by dividing the eMax variable by the
    # total energy of the cluster)
    mva_classifier.AddVariable('eMaxOverE_cl', array.array('f', [0.]))
    mva_classifier.AddVariable('sigmaZZ_cl', array.array('f', [0.]))

    mva_classifier.BookMVA("BDT", "data/MVAnalysis_Bkg_BDT.weights.xml")

    # -------------------------------------------------------
    # event loop

    nev = 0
    for evt_idx in range(range_ev[0], range_ev[1]+1):
        # print(evt_idx)
        event = ntuple.getEvent(evt_idx)
        if (params.maxEvents != -1 and nev >= params.maxEvents):
            break
        if debug >= 2 or event.entry() % 100 == 0:
            print ("--- Event {}, @ {}".format(event.entry(),
                                               datetime.datetime.now()))
            print ('    run: {}, lumi: {}, event: {}'.format(
                event.run(), event.lumi(), event.event()))

        nev += 1

        # get the interesting data-frames
        genParts = event.getDataFrame(prefix='gen')

        # FIXME: we remove this preselection for now paying the price of reading all branches also
        # for non interesting events, is this a good idea?
        # if len(genParts[(genParts.eta > 1.7) & (genParts.eta < 2.5)]) == 0:
        #     continue
        #
        branches = [(event, 'genpart'),
                    # (event, 'hgcdigi'),
                    (event, 'tc'),
                    (event, 'cl'),
                    (event, 'cl3d'),
                    (event, 'tower'),
                    (event, 'simTower'),
                    (event, 'egammaEE'),
                    (event, 'hgcrocTower'),
                    (event, 'waferTower')
                    ]

        # branches = [(event, 'genpart'),
        #         # (event, 'hgcdigi'),
        #         (event, 'tc'),
        #         (event, 'cl'),
        #         (event, 'cl3d'),
        #         (event, 'tower')]

        # dataframes = pool.map(unpack, branches)

        dataframes = []
        for idx, branch in enumerate(branches):
            dataframes.append(unpack(branch))

        genParticles = dataframes[0]
        # hgcDigis = dataframes[1]
        triggerCells = dataframes[1]
        triggerClusters = dataframes[2]
        trigger3DClusters = dataframes[3]
        triggerTowers = dataframes[4]
        simTriggerTowers = dataframes[5]
        egamma = dataframes[6]
        hgcrocTowers = dataframes[7]
        waferTowers = dataframes[8]


        puInfo = event.getPUInfo()
        debugPrintOut(debug, 'PU', toCount=puInfo, toPrint=puInfo)

        # ----------------------------------
        if not tc_rod_bins.empty:
            triggerCells = pd.merge(triggerCells,
                                    tc_rod_bins,
                                    on='id')

        genParticles['pdgid'] = genParticles.pid
        genParticles['abseta'] = np.abs(genParticles.eta)

        # this is not needed anymore in recent versions of the ntuples
        # tcsWithPos = pd.merge(triggerCells, tc_geom_df[['id', 'x', 'y']], on='id')
        triggerClusters['ncells'] = [len(x) for x in triggerClusters.cells]
        # if 'x' not in triggerClusters.columns:
        #     triggerClusters = pd.merge(triggerClusters, tc_geom_df[['z', 'id']], on='id')
        #     triggerClusters['R'] = triggerClusters.z/np.sinh(triggerClusters.eta)
        #     triggerClusters['x'] = triggerClusters.R*np.cos(triggerClusters.phi)
        #     triggerClusters['y'] = triggerClusters.R*np.sin(triggerClusters.phi)

        trigger3DClusters['nclu'] = [len(x) for x in trigger3DClusters.clusters]

        def compute_hoe(cluster):
            # print cluster
            components = triggerClusters[triggerClusters.id.isin(cluster.clusters)]
            e_energy = components[components.layer <= 28].energy.sum()
            h_enery = components[components.layer > 28].energy.sum()
            if e_energy != 0.:
                cluster.hoe = h_enery/e_energy
            return cluster
        # trigger3DClusters['hoe'] = 999.
        # trigger3DClusters = trigger3DClusters.apply(compute_hoe, axis=1)

        trigger3DClusters['bdt_out'] = rnptmva.evaluate_reader(
            mva_classifier, 'BDT', trigger3DClusters[['pt', 'eta', 'maxlayer', 'hoe', 'emaxe', 'szz']])
        # trigger3DClusters['bdt_l'] = rnptmva.evaluate_reader(mva_classifier, 'BDT', trigger3DClusters[['pt', 'eta', 'coreshowerlength', 'firstlayer', 'hoe', 'eMaxOverE', 'szz', 'srrtot']], 0.8)
        # trigger3DClusters['bdt_t'] = rnptmva.evaluate_reader(mva_classifier, 'BDT', trigger3DClusters[['pt', 'eta', 'coreshowerlength', 'firstlayer', 'hoe', 'eMaxOverE', 'szz', 'srrtot']], 0.95)

        trigger3DClustersP = pd.DataFrame()
        triggerClustersGEO = pd.DataFrame()
        trigger3DClustersGEO = pd.DataFrame()
        triggerClustersDBS = pd.DataFrame()
        trigger3DClustersDBS = pd.DataFrame()
        trigger3DClustersDBSp = pd.DataFrame()
        trigger3DClustersCalib = pd.DataFrame()
        trigger3DClustersMerged = pd.DataFrame()

        triggerTowers.eval('HoE = etHad/etEm', inplace=True)
        simTriggerTowers.eval('HoE = etHad/etEm', inplace=True)
        hgcrocTowers.eval('HoE = etHad/etEm', inplace=True)
        waferTowers.eval('HoE = etHad/etEm', inplace=True)
        # triggerTowers['HoE'] = triggerTowers.etHad/triggerTowers.etEm
        # if 'iX' not in triggerTowers.columns:
        #     triggerTowers['iX'] = triggerTowers.hwEta
        #     triggerTowers['iY'] = triggerTowers.hwPhi

        if not tc_rod_bins.empty:
            clAlgo.computeClusterRodSharing(triggerClusters, triggerCells)

        debugPrintOut(debug, 'gen parts', toCount=genParts, toPrint=genParts)
        debugPrintOut(debug, 'gen particles',
                      toCount=genParticles,
                      toPrint=genParticles[genParticles.gen != -1][['eta', 'phi', 'pt', 'energy', 'mother', 'fbrem', 'pid', 'gen', 'reachedEE', 'fromBeamPipe']].sort_values(by='pt', ascending=False).iloc[:10])
        # print genParticles.columns
        # debugPrintOut(debug, 'digis',
        #               toCount=hgcDigis,
        #               toPrint=hgcDigis.iloc[:3])
        debugPrintOut(debug, 'Trigger Cells',
                      toCount=triggerCells,
                      toPrint=triggerCells.iloc[:3])
        debugPrintOut(debug, '2D clusters',
                      toCount=triggerClusters,
                      toPrint=triggerClusters.sort_values(by='pt', ascending=False).iloc[:3])
        if not trigger3DClusters.empty:
            debugPrintOut(debug, '3D clusters',
                          toCount=trigger3DClusters,
                          toPrint=trigger3DClusters[trigger3DClusters.quality > 0].sort_values(by='pt', ascending=False).iloc[:10])
        debugPrintOut(debug, 'Egamma',
                      toCount=egamma,
                      toPrint=egamma.sort_values(by='pt', ascending=False).iloc[:10])

        debugPrintOut(debug, 'Trigger Towers',
                      toCount=triggerTowers,
                      toPrint=triggerTowers.sort_values(by='pt', ascending=False).iloc[:10])
        debugPrintOut(debug, 'Sim Trigger Towers',
                      toCount=simTriggerTowers,
                      toPrint=simTriggerTowers.sort_values(by='pt', ascending=False).iloc[:10])
        debugPrintOut(debug, 'HGCROC Trigger Towers',
                      toCount=hgcrocTowers,
                      toPrint=hgcrocTowers.sort_values(by='pt', ascending=False).iloc[:10])
        debugPrintOut(debug, 'Wafer Trigger Towers',
                      toCount=waferTowers,
                      toPrint=waferTowers.sort_values(by='pt', ascending=False).iloc[:10])

        # print '# towers eta >0 {}'.format(len(triggerTowers[triggerTowers.eta > 0]))
        # print '# towers eta <0 {}'.format(len(triggerTowers[triggerTowers.eta < 0]))

        trigger3DClustersCalib = get_calibrated_clusters(calib_factors, trigger3DClusters)
        trigger3DClustersMerged = get_merged_clusters(trigger3DClusters[trigger3DClusters.quality > 0], pool)
        # print trigger3DClusters[:3]
        # print trigger3DClustersCalib[:3]
        debugPrintOut(debug, 'Calibrated 3D clusters',
                      toCount=trigger3DClustersCalib,
                      toPrint=trigger3DClustersCalib.sort_values(by='pt', ascending=False).iloc[:10])

        if not trigger3DClustersMerged.empty:
            debugPrintOut(debug, 'Merged 3D clusters',
                          toCount=trigger3DClustersMerged,
                          toPrint=trigger3DClustersMerged.sort_values(by='pt', ascending=False).iloc[:10])

        # from python.selections import genpart_ele_ee_selections,gen_part_selections
        # #print genpart_ele_ee_selections
        # #print gen_part_selections
        # test1_b = [fil for fil in genpart_ele_ee_selections if 'EleEtaB' in fil.name]
        # test2_b = [fil for fil in gen_part_selections if 'GENEtaB' in fil.name]
        # sel1_b = genParticles[genParticles.gen > 0].query(test1_b[0].selection)
        # sel2_b = genParticles[genParticles.gen > 0].query(test2_b[0].selection)
        # if ((not sel1_b.empty) or (not sel2_b.empty) ):
        #     print '---- Ele sel:'
        #     print test1_b
        #     print sel1_b
        #     print '---- GN sel:'
        #     print test2_b
        #     print sel2_b
        #
        # continue

        if params.clusterize:
            # Now build DBSCAN 2D clusters
            for zside in [-1, 1]:
                arg = [(layer, zside, triggerCells) for layer in range(0, 53)]
                results = pool.map(clAlgo.buildDBSCANClustersUnpack, arg)
                for clres in results:
                    triggerClustersDBS = triggerClustersDBS.append(clres, ignore_index=True)

            if not tc_rod_bins.empty:
                clAlgo.computeClusterRodSharing(triggerClustersDBS, triggerCells)

            debugPrintOut(debug, 'DBS 2D clusters',
                          toCount=triggerClustersDBS,
                          toPrint=triggerClustersDBS.iloc[:3])

            trigger3DClustersDBS = build3DClusters(
                'DBS', clAlgo.build3DClustersEtaPhi, triggerClustersDBS, pool, debug)
            trigger3DClustersDBSp = build3DClusters(
                'DBSp', clAlgo.build3DClustersProjTowers, triggerClustersDBS, pool, debug)
            trigger3DClustersP = build3DClusters(
                'DEFp', clAlgo.build3DClustersProjTowers, triggerClusters, pool, debug)
        # if doAlternative:
        #     triggerClustersGEO = event.getDataFrame(prefix='clGEO')
        #     trigger3DClustersGEO = event.getDataFrame(prefix='cl3dGEO')
        #     debugPrintOut(debug, 'GEO 2D clusters',
        #                   toCount=triggerClustersGEO,
        #                   toPrint=triggerClustersGEO.loc[:3])
        #     debugPrintOut(debug, 'GEO 3D clusters',
        #                   toCount=trigger3DClustersGEO,
        #                   toPrint=trigger3DClustersGEO.loc[:3])
        #     print(triggerCells[triggerCells.index.isin(np.concatenate(triggerClusters.cells.iloc[:3]))])

        # fill histograms
        # hdigis.fill(hgcDigis)
        selections.tp_def.set_collections(triggerCells, triggerClusters, trigger3DClusters)
        selections.tp_def_merged.set_collections(triggerCells, triggerClusters, trigger3DClustersMerged)
        selections.tp_def_calib.set_collections(triggerCells, triggerClusters, trigger3DClustersCalib)
        selections.gen_set.set_collections(genParticles)
        selections.tt_set.set_collections(triggerTowers)
        selections.simtt_set.set_collections(simTriggerTowers)
        selections.hgcroc_tt.set_collections(hgcrocTowers)
        selections.wafer_tt.set_collections(waferTowers)
        selections.eg_set.set_collections(egamma)

        for plotter in plotter_collection:
            # print plotter
            plotter.fill_histos(debug=debug)

    print ("Processed {} events/{} TOT events".format(nev, ntuple.nevents()))
    print ("Writing histos to file {}".format(params.output_filename))

    lastfile = ntuple.tree().GetFile()
    print 'Read bytes: {}, # of transaction: {}'.format(
        lastfile.GetBytesRead(),  lastfile.GetReadCalls())
    if debug == -4:
        ntuple.PrintCacheStats()

    output.cd()
    hm = histos.HistoManager()
    hm.writeHistos()

    output.Close()

    return


def editTemplate(infile, outfile, params):
    template_file = open(infile)
    template = template_file.read()
    template_file.close()

    for param in params.keys():
        template = template.replace(param, params[param])

    out_file = open(outfile, 'w')
    out_file.write(template)
    out_file.close()


def main(analyze):
    # ============================================
    # configuration bit

    usage = ('usage: %prog [options]\n'
             + '%prog -h for help')
    parser = optparse.OptionParser(usage)
    parser.add_option('-f', '--file', dest='CONFIGFILE', help='specify the ini configuration file')
    parser.add_option('-c', '--collection', dest='COLLECTION',
                      help='specify the collection to be processed')
    parser.add_option('-s', '--sample', dest='SAMPLE',
                      help='specify the sample (within the collection) to be processed ("all" to run the full collection)')
    parser.add_option('-d', '--debug', dest='DEBUG', help='debug level (default is 0)', default=0)
    parser.add_option('-n', '--nevents', dest='NEVENTS',
                      help='# of events to process per sample (default is 10)', default=10)
    parser.add_option("-b", "--batch", action="store_true", dest="BATCH",
                      default=False, help="submit the jobs via CONDOR")
    parser.add_option("-r", "--run", dest="RUN", default=None,
                      help="the batch_id to run (need to be used with the option -b)")
    parser.add_option("-o", "--outdir", dest="OUTDIR", default=None,
                      help="override the output directory for the files")
    # parser.add_option("-i", "--inputJson", dest="INPUT", default='input.json', help="list of input files and properties in JSON format")

    global opt, args
    (opt, args) = parser.parse_args()

    # read the config file
    cfgfile = None
    with open(opt.CONFIGFILE, 'r') as stream:
        cfgfile = yaml.load(stream)

    basedir = cfgfile['common']['input_dir']
    outdir = cfgfile['common']['output_dir']['default']
    hostname = socket.gethostname()
    for machine, odir in cfgfile['common']['output_dir'].items():
        if machine in hostname:
            outdir = odir
    plot_version = cfgfile['common']['plot_version']

    collection_params = {}
    for collection, collection_data in cfgfile['collections'].items():
        samples = collection_data['samples']
        print ('--- Collection: {} with samples: {}'.format(collection, samples))
        sample_params = []

        plotters = []
        for plotter in collection_data['plotters']:
            plotters.extend(cfgfile['plotters'][plotter])

        for sample in samples:
            events_per_job = -1
            out_file_name = 'histos_{}_{}i.root'.format(sample, plot_version)
            if opt.BATCH:
                events_per_job = cfgfile['samples'][sample]['events_per_job']
                if opt.RUN:
                    out_file_name = 'histos_{}_{}_{}.root'.format(sample, plot_version, opt.RUN)

            if opt.OUTDIR:
                outdir = opt.OUTDIR

            out_file = os.path.join(outdir, out_file_name)

            params = Parameters(input_base_dir=basedir,
                                input_sample_dir=cfgfile['samples'][sample]['input_sample_dir'],
                                output_filename=out_file,
                                output_dir=outdir,
                                clusterize=cfgfile['common']['run_clustering'],
                                eventsToDump=[],
                                version=plot_version,
                                maxEvents=int(opt.NEVENTS),
                                events_per_job=events_per_job,
                                computeDensity=cfgfile['common']['run_density_computation'],
                                plotters=plotters,
                                debug=opt.DEBUG,
                                name=sample)
            sample_params.append(params)
        collection_params[collection] = sample_params

    samples_to_process = list()
    if opt.COLLECTION:
        if opt.COLLECTION in collection_params.keys():
            if opt.SAMPLE:
                if opt.SAMPLE == 'all':
                    samples_to_process.extend(collection_params[opt.COLLECTION])
                else:
                    sel_sample = [sample for sample in collection_params[opt.COLLECTION]
                                  if sample.name == opt.SAMPLE]
                    samples_to_process.append(sel_sample[0])
            else:
                print ('Collection: {}, available samples: {}'.format(
                    opt.COLLECTION, collection_params[opt.COLLECTION]))
                sys.exit(0)
        else:
            print ('ERROR: collection {} not in the cfg file'.format(opt.COLLECTION))
            sys.exit(10)
    else:
        print ('\nAvailable collections: {}'.format(collection_params.keys()))
        sys.exit(0)

    print ('About to process samples: {}'.format(samples_to_process))

    if opt.BATCH and not opt.RUN:
        batch_dir = 'batch_{}_{}'.format(opt.COLLECTION, plot_version)
        if not os.path.exists(batch_dir):
            os.mkdir(batch_dir)
            os.mkdir(batch_dir+'/conf/')
            os.mkdir(batch_dir+'/logs/')

        dagman_sub = ''
        dagman_dep = ''
        dagman_ret = ''
        for sample in samples_to_process:
            dagman_spl = ''
            dagman_spl_retry = ''
            sample_batch_dir = os.path.join(batch_dir, sample.name)
            sample_batch_dir_logs = os.path.join(sample_batch_dir, 'logs')
            os.mkdir(sample_batch_dir)
            os.mkdir(sample_batch_dir_logs)
            print(sample)
            nevents = int(opt.NEVENTS)
            n_jobs = fm.get_number_of_jobs_for_batchprocessing(input_dir=os.path.join(sample.input_base_dir, sample.input_sample_dir),
                                                               tree='hgcalTriggerNtuplizer/HGCalTriggerNtuple',
                                                               nev_toprocess=nevents,
                                                               nev_perjob=sample.events_per_job,
                                                               debug=int(opt.DEBUG))
            print ('Total # of events to be processed: {}'.format(nevents))
            print ('# of events per job: {}'.format(sample.events_per_job))
            if n_jobs == 0:
                n_jobs = 1
            print ('# of jobs to be submitted: {}'.format(n_jobs))

            params = {}
            params['TEMPL_TASKDIR'] = sample_batch_dir
            params['TEMPL_NJOBS'] = str(n_jobs)
            params['TEMPL_WORKDIR'] = os.environ["PWD"]
            params['TEMPL_CFG'] = opt.CONFIGFILE
            params['TEMPL_COLL'] = opt.COLLECTION
            params['TEMPL_SAMPLE'] = sample.name
            params['TEMPL_OUTFILE'] = 'histos_{}_{}.root'.format(sample.name, sample.version)
            params['TEMPL_EOSPROTOCOL'] = fm.get_eos_protocol(dirname=sample.output_dir)
            params['TEMPL_INFILE'] = 'histos_{}_{}_*.root'.format(sample.name, sample.version)
            params['TEMPL_OUTDIR'] = sample.output_dir
            params['TEMPL_VIRTUALENV'] = os.path.basename(os.environ['VIRTUAL_ENV'])

            editTemplate(infile='templates/batch.sub',
                         outfile=os.path.join(sample_batch_dir, 'batch.sub'),
                         params=params)

            editTemplate(infile='templates/run_batch.sh',
                         outfile=os.path.join(sample_batch_dir, 'run_batch.sh'),
                         params=params)

            editTemplate(infile='templates/copy_files.sh',
                         outfile=os.path.join(sample_batch_dir, 'copy_files.sh'),
                         params=params)
            os.chmod(os.path.join(sample_batch_dir, 'copy_files.sh'),  0754)

            editTemplate(infile='templates/batch_hadd.sub',
                         outfile=os.path.join(sample_batch_dir, 'batch_hadd.sub'),
                         params=params)

            editTemplate(infile='templates/run_batch_hadd.sh',
                         outfile=os.path.join(sample_batch_dir, 'run_batch_hadd.sh'),
                         params=params)

            editTemplate(infile='templates/batch_cleanup.sub',
                         outfile=os.path.join(sample_batch_dir, 'batch_cleanup.sub'),
                         params=params)

            editTemplate(infile='templates/run_batch_cleanup.sh',
                         outfile=os.path.join(sample_batch_dir, 'run_batch_cleanup.sh'),
                         params=params)

            editTemplate(infile='templates/hadd_dagman.dag',
                         outfile=os.path.join(batch_dir, 'hadd_{}.dag'.format(sample.name)),
                         params=params)

            for jid in range(0, n_jobs):
                dagman_spl += 'JOB Job_{} batch.sub\n'.format(jid)
                dagman_spl += 'VARS Job_{} JOB_ID="{}"\n'.format(jid, jid)
                dagman_spl_retry += 'Retry Job_{} 3\n'.format(jid)

            dagman_sub += 'SPLICE {} {}.spl DIR {}\n'.format(
                sample.name, sample.name, sample_batch_dir)
            dagman_sub += 'JOB {} {}/batch_hadd.sub\n'.format(sample.name+'_hadd', sample_batch_dir)
            dagman_sub += 'JOB {} {}/batch_cleanup.sub\n'.format(
                sample.name+'_cleanup', sample_batch_dir)

            dagman_dep += 'PARENT {} CHILD {}\n'.format(sample.name, sample.name+'_hadd')
            dagman_dep += 'PARENT {} CHILD {}\n'.format(sample.name+'_hadd', sample.name+'_cleanup')

            # dagman_ret += 'Retry {} 3\n'.format(sample.name)
            dagman_ret += 'Retry {} 3\n'.format(sample.name+'_hadd')

            dagman_splice = open(os.path.join(sample_batch_dir, '{}.spl'.format(sample.name)), 'w')
            dagman_splice.write(dagman_spl)
            dagman_splice.write(dagman_spl_retry)
            dagman_splice.close()

            # copy the config file in the batch directory
            copyfile(opt.CONFIGFILE, os.path.join(sample_batch_dir, opt.CONFIGFILE))

        dagman_file_name = os.path.join(batch_dir, 'dagman.dag')
        dagman_file = open(dagman_file_name, 'w')
        dagman_file.write(dagman_sub)
        dagman_file.write(dagman_dep)
        dagman_file.write(dagman_ret)
        dagman_file.close()

        # create targz file of the code from git
        git_proc = subprocess32.Popen(['git', 'archive', '--format=tar.gz', 'HEAD', '-o',
                                       os.path.join(batch_dir, 'ntuple-tools.tar.gz')], stdout=subprocess32.PIPE)
        # cp TEMPL_TASKDIR/TEMPL_CFG
        print('Ready for submission please run the following commands:')
        # print('condor_submit {}'.format(condor_file_path))
        print('condor_submit_dag {}'.format(dagman_file_name))
        sys.exit(0)

    batch_idx = 0
    if opt.BATCH and opt.RUN:
        batch_idx = int(opt.RUN)

    # test = copy.deepcopy(singleEleE50_PU0)
    # #test.output_filename = 'test2222.root'
    # test.maxEvents = 5
    # test.debug = 6
    # test.eventsToDump = [1, 2, 3, 4]
    # test.clusterize = False
    # test.computeDensity = True
    #
    # test_sample = [test]

    # pool = Pool(1)
    # pool.map(analyze, nugun_samples)
    # pool.map(analyze, test_sample)
    # pool.map(analyze, electron_samples)
    # pool.map(analyze, [singleEleE50_PU200])

    # samples = test_sample
    for sample in samples_to_process:
        analyze(sample, batch_idx=batch_idx)


if __name__ == "__main__":
    try:
        main(analyze=analyze)
    except Exception as inst:
        print (str(inst))
        print ("Unexpected error:", sys.exc_info()[0])
        traceback.print_exc()
        sys.exit(100)

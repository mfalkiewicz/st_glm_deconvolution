#!/usr/bin/env python

from nipype.interfaces.utility import Split
from nipype.interfaces.base import Bunch
from nipype.algorithms.modelgen import SpecifyModel
import nipype.interfaces.fsl as fsl
import nipype.pipeline.engine as pe
import nipype.interfaces.io as nio
import nipype.interfaces.utility as util
from nipype.interfaces.utility import Function
from nipype.interfaces.fsl import Merge
from counter import Counter
import copy
import os

def get_dm(designs,index):
    from nipype.interfaces.base import Bunch

    subject_info = Bunch(conditions = designs.single_events[index][0], onsets = designs.single_events[index][1], durations = designs.single_events[index][2])
    return subject_info

def make_designs(log):
    from stdec import stdec
    # Generate session_infos for all single trials
    nick = "tempsub"
    conditions = ["PT","WT","PL","WL","AT","PTerr","WTerr","PLerr","WLerr","ATerr","miss"]
    cond_cols = ["Code","Type"]
    cond_pattern = [ [['zucz*'],['hit']],[['zsw*'],['hit']],
      [['nucz*'],['incorrect']],[['nsw*'],['incorrect']],
      [['zaut*'],['hit']], [['zucz*'],['incorrect']],
      [['zsw*'],['incorrect']],[['nucz*'],['hit']],
      [['nsw*'],['hit']],[['zaut*'],['incorrect']],
      [['.*'],['miss']]]

    designs = stdec(nick,log,cond_cols,conditions,cond_pattern)
    designs.read_logfile()
    designs.getconds()
    designs.collapse_dm()
    designs.extract_events()
    return designs


def run_workflow(args):

    eb = pe.Workflow(name='eb')
    work_dir = '/home/data/scratch/UP_ST/' + args.subject
    eb.base_dir = work_dir

    get_designs = pe.Node(Function(input_names = ['log'], output_names = ['designs'], function=make_designs), name="get_designs")
    get_designs.inputs.log = args.log

    #ntrials = len(designs.all_labels)
    indxs = range(120)

    # Iterate over the list of timings
    get_info = pe.Node(Function(input_names = ['designs','index'], output_names = ['info'], function=get_dm), name="get_info")
    get_info.iterables = ('index', [1])
    #get_info.iterables = ('idx', indxs)
    
    eb.connect(get_designs,'designs',get_info,'designs')

    # Specify model
    s = pe.Node(SpecifyModel(),name='sm')
    s.inputs.input_units = 'secs'
    s.inputs.time_repetition = 2.5
    s.inputs.high_pass_filter_cutoff = 100.
    s.inputs.functional_runs = args.file
    eb.connect(get_info,'info',s,'subject_info')

    # Create FSL Level 1 Design
    l1d = pe.Node(fsl.Level1Design(),name='l1d')
    l1d.inputs.interscan_interval = 2.5
    l1d.inputs.bases = {'dgamma': {'derivs' : False}}
    l1d.inputs.model_serial_correlations = False
    l1d.inputs.contrasts = [('st','T',['all','st'],[0, 1])]
    eb.connect(s,'session_info',l1d,'session_info')

    # Get it into FEAT-compatible format
    fm = pe.Node(fsl.FEATModel(),name='feet')
    eb.connect(l1d,'ev_files',fm,'ev_files')
    eb.connect(l1d,'fsf_files',fm,'fsf_file')

    # Estimate the GLM
    glm = pe.Node(fsl.GLM(),name='glm')
    glm.inputs.out_cope = 'beta.nii.gz'
    glm.inputs.in_file = args.file

    eb.connect(fm,'design_file',glm,'design')
    eb.connect(fm,'con_file',glm,'contrasts')

    # Merge estimated betas into a single volume

    merger = pe.JoinNode(fsl.Merge(), joinsource = 'get_info', joinfield = 'in_files', name = 'merger')
    merger.inputs.dimension = 't'
    merger.inputs.output_type = 'NIFTI_GZ'
    eb.connect(glm,'out_cope',merger,'in_files')

    # Write outputs

    datasink = pe.Node(nio.DataSink(), name='sinker')
    datasink.inputs.base_directory = '/home/mfalkiewicz/expriments/UP/preprocessed/deconvolution/' + args.subject
    eb.connect(merger,'merged_file',datasink,'beta')

    # Run the whole thing

    #eb.run(plugin='CondorDAGMan')
    #eb.run(plugin='MultiProc')
    eb.run()

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("-s", "--subject", dest="subject",
                        help="Subject name", required=True)
    parser.add_argument("-f", "--infile", dest="file",
                        help="Input filename", required=True)
    parser.add_argument("-d", "--logfile", dest="log",
                        help="Logfile", required=True)

    args = parser.parse_args()

    run_workflow(args)

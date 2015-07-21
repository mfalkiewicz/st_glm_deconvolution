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
from stdec import stdec

def run_workflow(args):
    #from nipype.interfaces.utility import Split
    #from nipype.interfaces.base import Bunch
    #from nipype.algorithms.modelgen import SpecifyModel
    #import nipype.interfaces.fsl as fsl
    #import nipype.pipeline.engine as pe
    #import nipype.interfaces.io as nio
    #import nipype.interfaces.utility as util
    #from nipype.interfaces.utility import Function
    #from nipype.interfaces.fsl import Merge
    #from counter import Counter
    #import copy
    #import nipype.interfaces.nipy as nipy
    #from Experiment import *

    eb = pe.Workflow(name='eb')
    work_dir = /home/data/scratch/UP_ST
    eb.base_dir = work_dir

    # Generate session_infos for all single trials
    conditions = ["PT","WT","PL","WL","AT","PTerr","WTerr","PLerr","WLerr","ATerr","miss"]
    cond_cols = ["Code","Type"]
    cond_pattern = [ [['zucz*'],['hit']],[['zsw*'],['hit']],
      [['nucz*'],['incorrect']],[['nsw*'],['incorrect']],
      [['zaut*'],['hit']], [['zucz*'],['incorrect']],
      [['zsw*'],['incorrect']],[['nucz*'],['hit']],
      [['nsw*'],['hit']],[['zaut*'],['incorrect']], 
      [['.*'],['miss']]]

    designs = stdec(args.subject,args.log,cond_cols,conditions,cond_pattern)
    designs.read_logfile()
    designs.getconds()
    designs.collapse_dm()
    designs.extract_events()
    ntrials = len(designs.all_labels)
    indxs = range(ntrials)

    # Iterate over the list of timings
    get_info = pe.Node(Function(input_names = [], output_names = ['info'], function=designs.get_dm), name="get_info")
    get_info.iterables = ('idx', [0, 1])
    #get_info.iterables = ('idx', indxs)

    eb.connect(make_designs,'g',get_info,'g')

    # Specify model
    s = pe.Node(SpecifyModel(),name='sm')
    s.inputs.input_units = 'secs'
    s.inputs.time_repetition = 2.5
    s.inputs.high_pass_filter_cutoff = 100.
    eb.connect(datasource,'func',s,'functional_runs')
    eb.connect(get_info,'info',s,'subject_info')

    # Make contrast vectors
    make_cvecs = pe.Node(Function(input_names = ['g'], output_names = ['c'], function=make_cvectors),name="make_contrasts")

    eb.connect(make_designs,'g',make_cvecs,'g')

    # Create FSL Level 1 Design
    l1d = pe.Node(fsl.Level1Design(),name='l1d')
    l1d.inputs.interscan_interval = 2.5
    l1d.inputs.bases = {'dgamma': {'derivs' : False}}
    l1d.inputs.model_serial_correlations = False

    eb.connect(make_cvecs,'c',l1d,'contrasts')
    eb.connect(s,'session_info',l1d,'session_info')

    # Get it into FEAT-compatible format
    fm = pe.Node(fsl.FEATModel(),name='feet')
    eb.connect(l1d,'ev_files',fm,'ev_files')
    eb.connect(l1d,'fsf_files',fm,'fsf_file')  

    # Estimate the GLM
    glm = pe.Node(fsl.GLM(),name='glm')
    glm.inputs.out_cope = 'beta.nii.gz'

    eb.connect(fm,'design_file',glm,'design')
    eb.connect(fm,'con_file',glm,'contrasts')
    eb.connect(datasource,'func',glm,'in_file')


    # Merge estimated betas into a single volume

    merger = pe.JoinNode(fsl.Merge(), joinsource = 'get_info', joinfield = 'in_files', name = 'merger')
    merger.inputs.dimension = 't'
    merger.inputs.output_type = 'NIFTI_GZ'
    eb.connect(glm,'out_cope',merger,'in_files')

    # Write outputs

    datasink = pe.Node(nio.DataSink(), name='sinker')
    datasink.inputs.base_directory = '/home/mfalkiewicz/sdt'
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

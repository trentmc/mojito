#!/usr/bin/env python

import os
import sys

from adts import *
from problems import ProblemFactory
from engine.SynthEngine import *

if __name__== '__main__':            
    #set up logging
    import logging
    logging.basicConfig()
    logging.getLogger('part').setLevel(logging.INFO)
    logging.getLogger('problems').setLevel(logging.INFO)
    logging.getLogger('synth').setLevel(logging.DEBUG)
    logging.getLogger('analysis').setLevel(logging.DEBUG)
    logging.getLogger('library').setLevel(logging.DEBUG)

    #set help message
    help = """
Usage: synth PROBLEM_NUM POP_SIZE OUTPUT_DIR POOLED_DB_FILE [RESTART_DB_FILE]

 PROBLEM_NUM -- int -- details below
 POP_SIZE -- int -- population size
 OUTPUT_DIR -- string -- output directory for state db files
 POOLED_DB_FILE -- string or None -- enables parallel synth engines (use same value for every engine!)
 RESTART_DB_FILE -- string or None -- set to a previous state_genXXXX.db to continue a previous run
 
""" + ProblemFactory().problemDescriptions()

    #got the right number of args?  If not, output help
    num_args = len(sys.argv)
    if num_args not in [5,6]:
        print help
        sys.exit(0)

    #yank out the args into values usable for synth engine
    problem_choice = eval(sys.argv[1])
    
    num_inds_per_age_layer = eval(sys.argv[2])
    
    output_dir = sys.argv[3]
    
    pooled_db_file = sys.argv[4]
    if pooled_db_file == 'None': pooled_db_file = None
    
    if num_args == 5: restart_file = None
    else:             restart_file = sys.argv[5]
    if restart_file == 'None': restart_file = None

    #maybe extra args for building ps
    if problem_choice == 81:
        #problem 81 specifies the input dc sweep, and target waveform
        dc_sweep_start_voltage = 0.0
        dc_sweep_end_voltage = 1.8
        target_waveform = [0.0, 0.2, 0.2, 0.2, 1.0, 1.0, 1.1, 1.2, 0.1]
        ps_extra_args = (dc_sweep_start_voltage, dc_sweep_end_voltage,
                         target_waveform)
    else:
        ps_extra_args = None

    #objects for synth engine
    ps = ProblemFactory().build(problem_choice, ps_extra_args)
    ss = SynthSolutionStrategy(num_inds_per_age_layer = num_inds_per_age_layer)
    ss.max_num_inds = 100e6 #100 million
    ss.metric_weights['perc_DOCs_met'] = 10.0

    #go!
    engine = SynthEngine(ps, ss, output_dir, pooled_db_file, restart_file)
    engine.run()
    
    

#!/usr/bin/env python 

import os
import sys

import pickle

from adts import *
from problems import ProblemFactory

from engine.SynthEngine import loadSynthState

if __name__== '__main__':            
    #set up logging
    import logging
    logging.basicConfig()
    logging.getLogger('synth').setLevel(logging.DEBUG)
    logging.getLogger('analysis').setLevel(logging.DEBUG)

    #set help message
    help = """
Usage: netlister2 PROBLEM_NUM IND_FILE ANNOTATE_POINTS ANNOTATE_BB [ANALYSIS_INDEX ENV_INDEX]

Netlists the ind in IND_FILE.  Can annotate to make it prettier.
Can make it simulatable by also specifying an analysis and env_point.

Details:
 PROBLEM_NUM -- int -- see below
 IND_FILE -- string -- the file containing the ind  (saved using get_ind.py)
 ANNOTATE_POINTS -- 0 or 1 -- if 1, add unscaled_point and scaled_point info
 ANNOTATE_BB -- 0 or 1 -- if 1, add building block info
 ANALYSIS_INDEX -- int in {0,1,...,num_analyses-1} (not analysis ID!)
 ENV_INDEX -- int in {0,1,...,num_env_points for analysis} (not env point ID!)
""" + ProblemFactory().problemDescriptions()

    #got the right number of args?  If not, output help
    num_args = len(sys.argv)
    if num_args not in [5,7]:
        print help
        sys.exit(0)

    #yank out the args into usable values
    problem_choice = eval(sys.argv[1])
    ind_file = sys.argv[2]
    annotate_points = bool(eval(sys.argv[3]))
    annotate_bb_info = bool(eval(sys.argv[4]))

    make_simulatable = (num_args == 7)
    if make_simulatable:
        analysis_index = eval(sys.argv[5])
        env_index = eval(sys.argv[6])

    #do the work

    # -load data
    ps = ProblemFactory().build(problem_choice)
    if not os.path.exists(ind_file):
        print "Cannot find file with name %s" % ind_file
        sys.exit(0)
    
    fid=open(ind_file,'r');
    ind=pickle.load(fid);
    fid.close();
        
    ind._ps = ps
    
    # -generate design_netlist; it may be annotated
    design_netlist = ind.netlist(annotate_bb_info = annotate_bb_info, add_infostring=True)

    # -maybe info about unscaled_point, scaled_point
    if annotate_points:
        unscaled = ind.genotype.unscaled_opt_point
        s = ""
        s += "Unscaled_opt_point=%s\n" % str(unscaled)
        s += "-----------------------------------------------------------\n"
        scaled = ps.embedded_part.part.point_meta.scale(unscaled)
        s += "Scaled_opt_point=%s\n" % str(scaled)
        s += "-----------------------------------------------------------\n"
        s += "Netlist=\n%s" % design_netlist
        design_netlist = s

    # -maybe add simulation info
    if make_simulatable:
        #retrieve analysis
        if analysis_index >= len(ps.analyses):
            print "Requested analysis_index=%d but only %d analyses available"%\
                  (analysis_index, len(ps.analyses))
            sys.exit(0)
        analysis = ps.analyses[analysis_index]

        #retrieve env_point
        if env_index >= len(analysis.env_points):
            print "Requested env_index=%d but only %d env_points available"%\
                  (env_index, len(analysis.env_points))
            sys.exit(0)
        env_point = analysis.env_points[env_index]

        #netlist!
        netlist = analysis.createFullNetlist(design_netlist, env_point)
        
    else:
        netlist = design_netlist

    #successful, so print netlist
    print netlist
        
    
    
    

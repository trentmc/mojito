#!/usr/bin/env python 

import os
import sys

from adts import *
from problems import ProblemFactory

import pickle

from engine.SynthEngine import loadSynthState

if __name__== '__main__':            
    #set up logging
    import logging
    logging.basicConfig()
    logging.getLogger('synth').setLevel(logging.DEBUG)
    logging.getLogger('analysis').setLevel(logging.DEBUG)

    #set help message
    help = """
Usage: get_ind PROBLEM_NUM DB_FILE IND_ID OUT_FILE

Netlists an ind having IND_ID in DB_FILE.  Can annotate to make it prettier.
Can make it simulatable by also specifying an analysis and env_point.

Details:
 PROBLEM_NUM -- int -- see below
 DB_FILE -- string -- e.g. ~/synth_results/state_genXXXX.db or pooled_db.db
 IND_ID -- int -- eg 2212
 OUT_FILE -- string -- the file to write the ind to
""" + ProblemFactory().problemDescriptions()

    #got the right number of args?  If not, output help
    num_args = len(sys.argv)
    if num_args not in [5]:
        print help
        sys.exit(0)

    #yank out the args into usable values
    problem_choice = eval(sys.argv[1])
    db_file = sys.argv[2]
    ind_ID = eval(sys.argv[3])
    out_file = sys.argv[4]

    #do the work

    # -load data
    ps = ProblemFactory().build(problem_choice)
    if not os.path.exists(db_file):
        print "Cannot find file with name %s" % db_file
        sys.exit(0)
    state = loadSynthState(db_file, ps)

    # -find ind
    ind = None
    for cand_ind in state.allInds():
        if cand_ind.ID == ind_ID:
            ind = cand_ind
            break
    if ind is None:
        print "ind with ID=%d not found in db; use summarize_db to learn IDs" %\
              ind_ID
        sys.exit(0)
        
    ind.S = None
    ind._ps = None
                    
    fid=open(out_file,'w');
    pickle.dump(ind,fid);
    fid.close();
        
    
    

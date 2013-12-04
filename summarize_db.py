#!/usr/bin/env python 

import os
import sys

import numpy

from adts import *
from problems import ProblemFactory

from engine.SynthEngine import populationSummaryStr, loadSynthState, \
     fastNondominatedSort, minMaxMetrics
from engine.EngineUtils import populationSummaryToMatlab

if __name__== '__main__':            
    #set up logging
    import logging
    logging.basicConfig()
    logging.getLogger('synth').setLevel(logging.DEBUG)
    logging.getLogger('analysis').setLevel(logging.DEBUG)

    #set help message
    help = """
Usage: summarize_db PROBLEM_NUM DB_FILE [SORT_METRIC] [MATLAB_METRIC_FILE] [MATLAB_POINT_FILE]

Prints a summary of db contents:
-has one row entry for each _nondominated_ (layer 0) ind
-in each row, give ind ID plus all worst-case metric values

Details:
 PROBLEM_NUM -- int -- see below
 DB_FILE -- string -- e.g. ~/synth_results/state_genXXXX.db or pooled_db.db
 SORT_METRIC -- string -- if specified, it sorts the inds by that metric name
   in ascending order
 MATLAB_METRIC_FILE -- string -- if specified, outputs the metrics to a file
   readable by Matlab. Metric names are output to MATLAB_METRIC_FILE.hdr and
   metric values are output to MATLAB_METRIC_FILE.val
 MATLAB_POINT_FILE -- string -- if specified, outputs the points to a file
   readable by Matlab. Point names are output to MATLAB_POINT_FILE.hdr and
   point values are output to MATLAB_POINT_FILE.val
   
""" + ProblemFactory().problemDescriptions()

    #got the right number of args?  If not, output help
    num_args = len(sys.argv)
    if num_args not in [3,4,5,6]:
        print help
        sys.exit(0)

    #yank out the args into usable values
    problem_choice = eval(sys.argv[1])
    db_file = sys.argv[2]
    sort_metric = None
    matlab_metric_file = None
    matlab_point_file = None
    
    if num_args >= 4:
        sort_metric = sys.argv[3]
        if sort_metric == 'None': sort_metric = None
    
    if num_args >= 5:
        matlab_metric_file = sys.argv[4]
        if matlab_metric_file == 'None': matlab_metric_file = None
    
    if num_args >= 6:
        matlab_point_file = sys.argv[5]
        if matlab_point_file == 'None': matlab_point_file = None

    #do the work

    # -load data
    ps = ProblemFactory().build(problem_choice)
    if not os.path.exists(db_file):
        print "Cannot find file with name %s" % db_file
        sys.exit(0)
    state = loadSynthState(db_file, ps)

    # -validate sort_metric earlier rather than later
    if sort_metric is not None:
        if sort_metric not in ps.flattenedMetricNames():
            print "Sort_metric '%s' is not in metric names of %s" % \
                  (sort_metric, ps.flattenedMetricNames())
            sys.exit(0)
    
    # -find nondominated inds
    inds = state.allInds()
    minmax = minMaxMetrics(ps, inds)
    print "Begin fastNondominatedSort on %d inds..." % len(inds)
    F = fastNondominatedSort(inds, minmax, max_layer_index=0,
                             metric_weights=state.ss.metric_weights)
    nondom_inds = F[0]
    print "Done fastNondominatedSort; %d inds are nondominated" % \
          len(nondom_inds)

    print populationSummaryStr(ps, nondom_inds, sort_metric)
    
    populationSummaryToMatlab(ps, nondom_inds, matlab_metric_file, matlab_point_file)
    #done!

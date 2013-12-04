#!/usr/bin/env python 

import os
import sys

from regressor.Lut import LutDataPruner

from util.ascii import *

if __name__== '__main__':            
    #set up logging
    import logging
    logging.basicConfig()
    logging.getLogger('lut').setLevel(logging.DEBUG)

    #set help message
    help = """
Usage: doprune_lut_data INPUT_FILEBASE PRUNED_FILEBASE THR_ERROR MIN_NUM_FINAL_SAMPLES TARGET_VARIABLE_NAME

Prunes a set of sample data that is often used in lookup tables (luts),
according to the following algorithm:

  Repeat until stop:
    Stop if modeling error >= ERROR_THR
    Stop if num samples remaining <= MIN_NUM_SAMPLES
    Prune another sample that has modeling error < thr if removed

Details about inputs:
 INPUT_FILEBASE -- string -- initial data is in INPUT_FILEBASE.hdr, .val
 PRUNED_FILEBASE -- string -- pruned data is in INPUT_FILEBASE.hdr, .val
 THR_ERROR -- float in [0,1] -- 
 PRUNESTOP_ERROR -- float -- stop pruning run as soon as error of a pruned_sample gets above this threshold.  E.g. 1e-3 to 1e-6
 MIN_NUM_SAMPLES -- int -- stop pruning run if the new dataset hits this size
 TARGET_VARIABLE_NAME -- string -- the variable that is the target of the lookup table
"""

    #got the right number of args?  If not, output help
    num_args = len(sys.argv)
    if num_args not in [6]:
        print help
        sys.exit(0)

    #yank out the args into usable values
    input_filebase = sys.argv[1]
    pruned_filebase = sys.argv[2]
    thr_error = float(sys.argv[3])
    min_num_samples = int(sys.argv[4])
    target_varname = sys.argv[5]

    #do the work
    # -get data
    Xy, X, y, all_varnames, input_varnames = \
        hdrValFilesToTrainingData(input_filebase, target_varname)

    # -run pruner, save results
    keep_I = LutDataPruner().prune(X, y, Xy, thr_error, min_num_samples,
                                   pruned_filebase, all_varnames)
    
    #done!
    print "Done.  Output is in %s.hdr and %s.val" % \
          (pruned_filebase, pruned_filebase)

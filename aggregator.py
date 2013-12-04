#!/usr/bin/env python 

import os
import sys

from adts import *
from problems import ProblemFactory
from engine.Pooler import *

if __name__== '__main__':

    num_args = len(sys.argv)
    if num_args not in [4,5]:
        print 'Usage: aggregator PROBLEM_NUM DB_DIRS_FILE OUTPUT_DB_FILE [MAX_DB_SIZE]'
        print ProblemFactory().problemDescriptions()
        sys.exit(0)
        
    problem_choice = eval(sys.argv[1])
    db_dirs_file = sys.argv[2]
    pooled_db_file = sys.argv[3]

    pool_size=100000
    
    if num_args >= 5:
        pool_size = eval(sys.argv[4])
    
    import logging
    logging.basicConfig()
    logging.getLogger('pooler').setLevel(logging.DEBUG)

    ps = ProblemFactory().build(problem_choice)
    ss = PoolerStrategy(loop_wait_time=0, max_pool_size=pool_size,
                        just_one_iter=True)

    pooler = Pooler(ps, ss, db_dirs_file, pooled_db_file)
    pooler.run()
    
    

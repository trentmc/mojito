#!/usr/bin/env python 

import os
import sys

from adts import *
from problems import ProblemFactory
from engine.Pooler import *

if __name__== '__main__':

    num_args = len(sys.argv)
    if num_args not in [5]:
        print 'Usage: pooler PROBLEM_NUM DB_DIRS_FILE POOLED_DB_FILE POOL_SIZE'
        print ProblemFactory().problemDescriptions()
        sys.exit(0)
        
    problem_choice = eval(sys.argv[1])
    db_dirs_file = sys.argv[2]
    pooled_db_file = sys.argv[3]
    pool_size = eval(sys.argv[4])
    loop_wait_time = 120 #currently a magic number instead of an argument
    
    import logging
    logging.basicConfig()
    logging.getLogger('pooler').setLevel(logging.DEBUG)

    ps = ProblemFactory().build(problem_choice)
    ss = PoolerStrategy(loop_wait_time=loop_wait_time, max_pool_size=pool_size,
                        just_one_iter=False)

    pooler = Pooler(ps, ss, db_dirs_file, pooled_db_file)
    pooler.run()
    
    

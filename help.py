#!/usr/bin/env python 

import os
import sys

if __name__== '__main__':            

    #set help message
    help = """
Usage: help

TOOLS AVAILABLE:

===================
To generate results
===================
-synth.py - run a single synthesis process (can invoke multiple times to get parallelism)
-pooler.py - enables migration between synthesis processes (just invoke once)
-doprune_lut_data - shrinks the size of a lookup table (lut)

==================
To analyze results
==================
-aggregator.py -- merge results across many DBs into a single DB
-summarize_db.py - list nondominated inds and their performances in a DB
-netlister.py - netlist a single ind

==================
Maintenance
==================
-runtests.py - run unit tests (can also run individual tests from their dirs)
-help.py - this file.  To get help for other files just type filename with no args.

"""
    print help

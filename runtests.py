#!/usr/bin/env python 

import optparse
import logging

from tests import *

def configureLogging():

    # Populate our options, -h/--help is already there for you.
    optp = optparse.OptionParser()
    optp.add_option('-v', '--verbose', dest='verbose', action='count',
                    help="Increase verbosity (specify multiple times for more)")
    # Parse the arguments (defaults to parsing sys.argv).
    opts, args = optp.parse_args()

    log_level = logging.WARNING # default
    if opts.verbose == 1:
        log_level = logging.INFO
    elif opts.verbose >= 2:
        log_level = logging.DEBUG

    # Set up basic configuration, out to stderr with a reasonable default format.
    logging.basicConfig(level=log_level)

if __name__== '__main__':
    configureLogging()

    #want to suppress warnings if they show up.
    for module in ['synth', 'library']:
        logging.getLogger(module).setLevel(logging.ERROR)

    unittest.main(defaultTest='test_suite') 
    


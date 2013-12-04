#!/bin/bash
#
# start a synth run on a remote machine
#
#  $1 = base directory of the synth engine
#  $2 = problem number
#  $3 = population size
#  $4 = path to store results
#  $5 = path to pool database


HOST=`hostname`
USER=`whoami`
echo "Clustered Synth Node check"
echo "  Host: $HOST"
ps -fu $USER | grep synth.py
ps -fu $USER | grep startsim.sh
 
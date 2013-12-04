#!/bin/bash
#
# start a synth run on a remote machine
#
#  $1 = base directory of the synth engine
#  $2 = problem number
#  $3 = population size
#  $4 = path to store results
#  $5 = path to pool database

renice 15 $$ 2> /dev/null 1> /dev/null
source ~/scripts/hspice.rc 2> /dev/null 1> /dev/null
cd $1 2> /dev/null 1> /dev/null

LAST_STATE_FILE=`ls -1 $4/state* 2> /dev/null | tail -n1`
HOST=`hostname`

echo "Clustered Synth Startup"
echo "  Host: $HOST"
if [ "$LAST_STATE_FILE" = "" ]; then  
    echo "  Starting from scratch"
    ./synth.py "$2" "$3" "$4" "$5" 2> /dev/null 1> /dev/null
else
    echo "  Restarting from file: $LAST_STATE_FILE"
    ./synth.py "$2" "$3" "$4" "$5" "$LAST_STATE_FILE" 2> /dev/null 1> /dev/null
fi

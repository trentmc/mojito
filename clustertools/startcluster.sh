#!/bin/bash
#
# start a synth run on a remote maching
#

POPSIZE=100
POOL_SIZE=100
PROBLEM_NUMBER=42

SYNTH_DIR="/esat/ganymedes1/users/ppalmers/projects/synth"
RUN_DIR="run1"

RESULT_BASE_DIR="/esat/micas_sata/no_backup/users/ppalmers/synth_results_9/dsviamp1-1/$RUN_DIR"
RESULT_PREFIX="OP"

POOL_DATABASE_FILE="$RESULT_BASE_DIR/pooled.db"
POOL_DIRLIST_FILE="$RESULT_BASE_DIR/pool.dirs"

DUAL_PROCESSOR_HOSTS=""
SINGLE_PROCESSOR_HOSTS=""

# MICAS machines
# single core
SINGLE_PROCESSOR_HOSTS="$SINGLE_PROCESSOR_HOSTS scapa portellen dalwhinnie benrinnes bushmills lagavulin ileach linkwood longmorn tobermory caolila"
# the dual cores
DUAL_PROCESSOR_HOSTS="$DUAL_PROCESSOR_HOSTS titan hyperion iapetus amalthea ananke deimos  rhea callisto phobos tethys" 
  # these are to be used with care ;)
  #SINGLE_PROCESSOR_HOSTS="$SINGLE_PROCESSOR_HOSTS benrinnes jack daniels "
  #DUAL_PROCESSOR_HOSTS="$DUAL_PROCESSOR_HOSTS tethys tomatin"

# these are some computer class machines

# class 1 (91.56)
  #SINGLE_PROCESSOR_HOSTS="$SINGLE_PROCESSOR_HOSTS durme demer dommel viroin dijle zenne nete warche semois lomme vesder herk jeker rupel leie"

    #all of them
    #SINGLE_PROCESSOR_HOSTS="$SINGLE_PROCESSOR_HOSTS ambleve durme demer dommel viroin dijle zenne nete warche semois lomme vesder herk jeker rupel leie"

# class 2 (00.91)
  
  #SINGLE_PROCESSOR_HOSTS="$SINGLE_PROCESSOR_HOSTS chertal maaseik lixhe vise herstal seraing amay ampsin huy andenne jambes wepion yvoir dinant anseremme hastiere"

    #all of them
    #SINGLE_PROCESSOR_HOSTS="$SINGLE_PROCESSOR_HOSTS chertal maaseik lixhe vise herstal seraing amay ampsin huy andenne jambes wepion yvoir dinant anseremme hastiere"

# class 3 (02.54)

  #SINGLE_PROCESSOR_HOSTS="$SINGLE_PROCESSOR_HOSTS oudenaarde mariekerke burcht lillo eke kallo temse stamands melle hoboken gavere doel zevergem wetteren hemiksem baasrode"

    #all of them
    #SINGLE_PROCESSOR_HOSTS="$SINGLE_PROCESSOR_HOSTS oudenaarde mariekerke burcht lillo eke kallo temse stamands melle hoboken gavere doel  zevergem wetteren hemiksem baasrode"


PIDLIST_FILE="$SYNTH_DIR/clusterpids"

# make the target dirs
mkdir -p "$RESULT_BASE_DIR"

# clear pool file
echo "" > $POOL_DIRLIST_FILE

# clear pid file
echo "" > $POOL_DIRLIST_FILE

# start the engine on the single processors
for HOST in $SINGLE_PROCESSOR_HOSTS
do
	ssh -x -f $HOST bash "$SYNTH_DIR/clustertools/startsim.sh" $SYNTH_DIR $PROBLEM_NUMBER $POPSIZE "$RESULT_BASE_DIR/$RESULT_PREFIX-$HOST-1" "$POOL_DATABASE_FILE"
	LAST_PID=$!
	echo "$LAST_PID" >> $PIDLIST_FILE
	echo "$RESULT_BASE_DIR/$RESULT_PREFIX-$HOST-1" >> $POOL_DIRLIST_FILE
done
# start the engine on the dual processors
for HOST in $DUAL_PROCESSOR_HOSTS
do
	ssh -x -f $HOST bash "$SYNTH_DIR/clustertools/startsim.sh" $SYNTH_DIR $PROBLEM_NUMBER $POPSIZE "$RESULT_BASE_DIR/$RESULT_PREFIX-$HOST-1" "$POOL_DATABASE_FILE"
	LAST_PID=$!
	echo "$LAST_PID" >> $PIDLIST_FILE
	echo "$RESULT_BASE_DIR/$RESULT_PREFIX-$HOST-1" >> $POOL_DIRLIST_FILE

	ssh -x -f $HOST bash "$SYNTH_DIR/clustertools/startsim.sh" $SYNTH_DIR $PROBLEM_NUMBER $POPSIZE "$RESULT_BASE_DIR/$RESULT_PREFIX-$HOST-2" "$POOL_DATABASE_FILE"
	LAST_PID=$!
	echo "$LAST_PID" >> $PIDLIST_FILE
	echo "$RESULT_BASE_DIR/$RESULT_PREFIX-$HOST-2" >> $POOL_DIRLIST_FILE

done


# start the pooler
./pooler.py $PROBLEM_NUMBER "$POOL_DIRLIST_FILE" "$POOL_DATABASE_FILE" "$POOL_SIZE"


# if the pooler exits, all processes should be stopped
for HOST in $SINGLE_PROCESSOR_HOSTS
do
	# a little rude
	ssh -f $HOST "killall synth.py;killall hspice"
done

for HOST in $DUAL_PROCESSOR_HOSTS
do
	# a little rude
	ssh -f $HOST "killall synth.py;killall hspice"
done


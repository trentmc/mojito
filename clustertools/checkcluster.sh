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

# start the engine on the single processors
for HOST in $SINGLE_PROCESSOR_HOSTS
do
	ssh -x $HOST bash "$SYNTH_DIR/clustertools/checksim.sh"
done
# start the engine on the dual processors
for HOST in $DUAL_PROCESSOR_HOSTS
do
	ssh -x $HOST bash "$SYNTH_DIR/clustertools/checksim.sh"
done


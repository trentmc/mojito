"""
This is the search algorithm.  It traverses the set of candidate designs,
stored as Ind objects, to optimize on >=1 goals.

The search algorithm is a combination of: NSGA-II (ref Deb) and ALPS (ref Hornby)
"""

import copy
import os
import random
import shutil
import types
import sys

import numpy

from adts import *
from adts.Part import replaceAutoNodesWithXXX

from util import mathutil
from util.constants import Incomputable, BAD_METRIC_VALUE
from Ind import Genotype, Ind
from EngineUtils import AgeLayeredPop, \
     uniqueIndsByPerformance, populationSummaryStr, \
     SynthState, loadSynthState, \
     fastNondominatedSort, minMaxMetrics, numIndsInNestedPop

import logging
log = logging.getLogger('synth')

class NsgaInd(Ind):
    """
    @description
      Like an 'Ind' but has extra attributes that NSGA-II and ALPS need
      to perform search.
      
    @attributes
      genetic_age -- int -- how many generations the genetic material of this
        ind have been around (NOT the number of generations that _this_ ind
        has been around).  Randomly-generated inds have a genetic_age of 0.
        Inds created from parent(s) have a genetic_age = max genetic_age
        of parent(s) + 1.
      n -- int -- domination count of ind 'p', ie # inds which dominate p
      S -- list of ind -- the inds that this ind dominates (in current iter)
      rank -- int -- rank 0 means it's in the 0th nondominated layer;
        rank 1 means 1st nondominated layer; etc
      distance -- float -- crowding distance; a higher value means
        that the ind has a better chance of being selected because
        it means that the ind is less crowded (and therefore more unique)
      
    """
    def __init__(self, genotype, ps):
        Ind.__init__(self, genotype, ps)

        #Note that genetic age needs to be set later
        self.genetic_age = None

        #Initializing variables to 'Incomputable' is safer than
        # initializing to 'None'
        self.n = Incomputable()
        self.S = Incomputable()
        self.rank = Incomputable()
        self.distance = Incomputable()
        
    def __str__(self):
        s = "NsgaInd={"
        s += ' parent_class_info=%s' % Ind.__str__(self)
        s += '; genetic_age=%s' % self.genetic_age
        s += '; n=%s' % self.n
        #s += '; S=%s' % self.S
        s += '; rank=%s' % self.rank
        s += '; distance=%s' % self.distance
        s += " /NsgaInd}"  
        return s

class SynthSolutionStrategy: 
    """
    @description

      Holds 'magic numbers' related to strategy of running synthesis engine
      
    @attributes

      See implementation.
      
    @notes
    """

    def __init__(self, num_inds_per_age_layer):
        """        
        @arguments
          num_inds_per_age_layer -- int -- 
        
        @return
          SynthSolutionStrategy object
        """
                                            #[default, ok range]

        #plot first two objectives each gen?
        self.do_plot = False

        #population size PER LAYER
        self.num_inds_per_age_layer = num_inds_per_age_layer  #[100, 5 .. 1e5]

        #ALPS settings
        # -overall pop size = num_inds_per_age_layer * num_layers
        # -polynomial scheme used for max_age_per_layer (note that highest
        #  active layer has no age limit)
        self.max_num_age_layers = 10       #[10]
        self.age_gap = 20                  #[20]
        self.max_age_per_layer = [(n**2 + 1) * self.age_gap
                                  for n in range(self.max_num_age_layers)]

        #maximum number of individuals
        self.max_num_inds = 100000          #[1e5, 100 .. 1e7]

        #prob of doing crossover in addition to mutates
        self.prob_crossover = 0.75          #[0.75, 0.1 .. 0.9]

        #probability of mutating 1 var, vs. all vars
        self.prob_mutate_1var = 0.5         #[0.5, 0.1 .. 0.9]

        #in mutating:
        #-probability of doing uniform mutation on 1 var, AND
        # stddev of gaussian distribution (assuming that min=0.0 and max=1.0)
        self.mutate_stddev = 0.05

        #[bias to vary using 1 operator, using 2, using 3, ...]
        self.num_vary_biases = [100.0, 15.0, 5.0, 3.0, 2.0, 2.0, 2.0, 1.0]

        #percentage of inds in a parent population to replace
        # with migrants from pooled_db     #[0.15, 0.0 .. 0.45]
        self.migration_rate = 0.15

        #For emphasizing different metrics when they are still infeasible.
        #  If not None, it's a dict of metric_name : metric_weight.  If
        #  a metric does not have an entry, its value is 1.0.  Default of
        #  None means 1.0 for all metrics.  Values larger than 1.0 mean
        #  that the metric gets emphasized more in the sum of violations
        #  Note that synth.py gives DOCs_metric_name a weight of 10.0
        self.metric_weights = {}
        
    def lowestAllowedAgeLayerOfMigrant(self, genetic_age,
                                       num_active_layers):
        """Returns the smallest age_layer possible that still allows
        'migrant_genetic_age', according to self.max_age_per_layer.
        """
        assert num_active_layers <= len(self.max_age_per_layer)
        for layer_i, max_age in enumerate(self.max_age_per_layer):
            if layer_i == num_active_layers-1 or genetic_age <= max_age:
                return layer_i
        return num_active_layers-1

    def allowIndInAgeLayer(self, age_layer_i, ind_genetic_age,
                           num_active_layers):
        """Returns True if this layer is the top age layer, or
        if the genetic_age of the ind is <= the max age allowed for this layer"""
        if age_layer_i == num_active_layers-1:
            return True
        elif ind_genetic_age+1 <= self.max_age_per_layer[age_layer_i]:
            return True
        else:
            return False
        
    def __str__(self):
        s = "SynthSolutionStrategy={"
        s += ' num_inds_per_age_layer=%d' % self.num_inds_per_age_layer
        s += '; max_num_age_layers=%d' % self.max_num_age_layers
        s += '; overall popsize=%d' % \
             (self.num_inds_per_age_layer * self.max_num_age_layers)
        s += '; age_gap=%d' % self.age_gap
        s += '; max_age_per_layer=%s' % self.max_age_per_layer
        s += '; max_num_inds=%d' % self.max_num_inds
        s += '; prob_crossover=%.3f' % self.prob_crossover
        s += '; prob_mutate_1var=%.3f' % self.prob_mutate_1var
        s += '; mutate_stddev=%.4f' % self.mutate_stddev
        s += '; num_vary_biases=%s' % self.num_vary_biases
        s += '; migration_rate=%.3f' % self.migration_rate
        s += '; metric_weights=%s' % self.metric_weights
        s += " /SynthSolutionStrategy}"  
        return s 

class SynthEngine:
    """
    @description
      Synthesizes circuits.
      
    @attributes
      ps -- ProblemSetup object -- describes the search space and goals
      ss -- SynthSolutionStrategy object -- strategy parameters
      pop -- Pop -- list of Inds, which is effectively the current state
      output_dir -- string -- directory of where results are stored
      simfile_dir -- string -- a subdirectory of output_dir where
        temporary simulation results are stored
      pooled_db_file -- string -- name of state file where we can
        incorporate migrants from (None if not wanted).  Note that
        this may not exist at first, but may get generated over time.  It
        may also be updated on the fly by the Pooler.
      restart_file -- string -- name of state file, where to
        continue a previous run from (None if not wanted)      
    """

    def __init__(self, ps, ss, output_dir, pooled_db_file, restart_file):
        #initialize state, possibly from previous run
        if restart_file is None:
            self.state = SynthState(ps, ss, AgeLayeredPop())
        else:
            restart_file = os.path.abspath(restart_file)
            try:
                self.state = loadSynthState(restart_file, ps)
            except:
                log.error('Could not open restart_file=%s; quitting' %
                          restart_file)
                sys.exit(0)
            
        #clear up output directory
        self.output_dir = os.path.abspath(output_dir)
        if self.output_dir[-1] != '/':
            self.output_dir += '/'
        if os.path.exists(self.output_dir):
            log.warning("Output path '%s' already exists; will rewrite" %
                        self.output_dir)
            shutil.rmtree(self.output_dir)
        os.mkdir(self.output_dir)

        #if we had a restart file, we can ensure that its info wasn't lost
        # due to clearing up the output directory
        if restart_file is not None and not os.path.exists(restart_file):
            self.saveState()

        self.simfile_dir = self.output_dir + 'autogen_simfiles/'
        os.mkdir(self.simfile_dir)

        assert 0.0 <= ss.migration_rate <= 0.5, \
               "migration rate must be in [0.0, 0.5]"
        if pooled_db_file is None:
            self.pooled_db_file = None
        else:
            self.pooled_db_file = os.path.abspath(pooled_db_file)

    #for easier reference, make 'ps' and 'ss' look like attributes of self
    def _ps(self):
        return self.state.ps
    def _ss(self):
        return self.state.ss

    ps = property(_ps)
    ss = property(_ss)

    def run(self):
        """
        @description
          Runs the synthesis engine!  This is the main work routine.
        
        @arguments
          <<none>>
        
        @return
           <<none>> but it continually generates output files to output_dir
        
        @notes
          Some of the files that it generates to output_dir/ are:
            state_gen0001.db -- init results; ie num generations complete = 1
            state_gen0002.db -- results when num generations complete = 2
            state_gen0003.db -- ...
        """
        log.info("Begin.")
        log.info(self.ps.prettyStr())
        log.info(str(self.ss) + "\n")

        while True:
            self.run__oneGeneration()
            self.saveState()
            if self.doStop():
                break

        log.info('Done')

    def saveState(self):
        """Auto-generate a state_genXXXX.db filename and save
        self.state to that file"""
        gen_str = str(self.state.generation)
        while len(gen_str) < 4:
            gen_str = '0' + gen_str
            
        output_file = self.output_dir + 'state_gen%s.db' % gen_str
        self.state.save(output_file)
        

    def run__oneGeneration(self):
        """
        @description
          Run one evolutionary generation
        
        @arguments
          <<none>> but uses self.state
        
        @return
          <<none>> but updates self.state
        """
        N = self.ss.num_inds_per_age_layer
        R_per_age_layer = self.state.R_per_age_layer
        for R in R_per_age_layer:
            num_unique = len(uniqueIndsByPerformance(R))
            assert num_unique == N*2, (num_unique, N*2)
        
        log.info('=============================================')
        log.info('=============================================')
        log.info('Gen=%d (# age layers=%d): begin' %
                 (self.state.generation, R_per_age_layer.numAgeLayers()))
            
        if self.state.generation % self.ss.age_gap == 0:
            log.info('This is an age_gap generation, so grow one more layer,'
                     ' and generate new random inds at layer 0')
            
            #update age-layers population structure based on ages
            # -just having an empty 'R' is ok because _updateR() will fill
            #  it in by include the lower layer when choosing cand_parents
            if R_per_age_layer.numAgeLayers() < self.ss.max_num_age_layers:
                R_per_age_layer.append([])
        
            #randomly genarate new inds for age layer 0 (a la ALPS)
            # (let the previous inds from layer 0 have one last chance by
            #  putting them into level 1)
            if R_per_age_layer.numAgeLayers() > 1:
                R_per_age_layer[1] += R_per_age_layer[0]
            rand_inds = self.generateRandomGoodInds(N*2)
            assert len(rand_inds) == len(uniqueIndsByPerformance(rand_inds)),\
                   "the randomly-generated inds were not unique by performance"
            R_per_age_layer[0] = rand_inds
        
        #incorporate migrants: put each migrant into the lowest layer
        # that it's allowed, so that it can aid search in as many layers
        # as possible (and so that it has a reasonable chance of competing)
        #
        #NOTE: never allow migrants into age layer 0, because this can
        #cause a problem.  Here is the scenario:
        #-incoming migrants are would fit into layer-0, but are older
        # than other layer-0 inds
        #-but they have better performances, and thus would get selected for
        #-but migrant-inds and offspring will get booted out of layer 0 before
        # the current age_gap iteration is over
        #-and then we will not have enough individuals in layer 0 for the
        # next round of selection etc.
        migrants = self.retrieveMigrants()
        for migrant in migrants:
            age_layer_i = self.ss.lowestAllowedAgeLayerOfMigrant( \
                migrant.genetic_age, R_per_age_layer.numAgeLayers())
            if age_layer_i == 0:
                if R_per_age_layer.numAgeLayers() > 1:
                    R_per_age_layer[1].append(migrant)
            else:
                R_per_age_layer[age_layer_i].append(migrant)
        R_per_age_layer.uniquifyInds()

        #compute metric ranges
        minmax_metrics = minMaxMetrics(self.ps, R_per_age_layer.flattened())

        #MAIN WORK: one layer at a time, select and create children to get new R
        # Note how elder_inds from level i bump up to level i+1.
        new_R_per_age_layer = AgeLayeredPop()
        elder_inds = []
        for age_layer_i in range(R_per_age_layer.numAgeLayers()):
            log.info('---------------------------------------------------------')
            log.info('---------------------------------------------------------')
            s = 'Gen=%d / age_layer=%d: select, nondom-sort, create children' %\
                (self.state.generation, age_layer_i)
            log.info(s + ': begin')
            R_per_age_layer[age_layer_i] += elder_inds
            new_R, elder_inds = self._updateR(R_per_age_layer, age_layer_i,
                                              minmax_metrics)
            new_R_per_age_layer.append(new_R)
            log.info(s + ': done')

        #update self.state
        self.state.R_per_age_layer = new_R_per_age_layer
        log.info('Gen=%d: done' % self.state.generation)
        self.state.generation += 1

    def _updateR(self, R_per_age_layer, age_layer_i, minmax_metrics): 
        """
        @description
        
          Update R = R_per_age_layer[age_layer_i] using the following steps:
            1. Chooses candidate parents using ALPS rules on layer i and age.
            2. Nondominated-sorts the candidate parents
            3. Selects parents using NSGA-II style selection
            4. Creates offspring from parents
            5. Returns offspring + parents, both aged accordingly
        
        @arguments
          R_per_age_layer -- list of list_of_NsgaInd -- one list per age layer.
          age_layer_i -- int -- the age layer of interest
          minmax_metrics -- metrics bounds -- see minMaxMetrics for details
        
        @return
          updated_R -- list of NsgaInd -- R, but updated
          elder_inds -- list of NsgaInd -- inds that were in R but could
            not be considered as parents because they were too old
        """
        N = self.ss.num_inds_per_age_layer

        #get candidate parents
        cand_parents, elder_inds = self._alpsCandidateParents(R_per_age_layer,
                                                              age_layer_i)
        
        #cand_F = F[0] + F[1] + ... = nondominated layers
        cand_F = fastNondominatedSort(cand_parents, minmax_metrics,
                                      max_num_inds=N,
                                      metric_weights=self.ss.metric_weights)

        #output state
        self.doStatusOutput(age_layer_i, cand_F)

        #fill parent population P
        P = self._nsgaSelectInds(cand_F, N, minmax_metrics)

        #use selection, mutation, and crossover to create a new child pop Q
        # -note that the new pop gets evaluated within
        Q = self.makeNewPop(P)

        #age the parents
        for ind in P:
            ind.genetic_age += 1

        #combine parent and offspring population
        R = P + Q
        return R, elder_inds
            
 
    def _alpsCandidateParents(self, R_per_age_layer, age_layer_i):
        """
        @description
          Find inds that may be selected as parents, following the ALPS rule:
            'inds at layer i can only breed with inds at i and i-1'
         
          Other restrictions:
          -ind must be young enough (otherwise it'll be an elder_ind)
          -all cand parents must be unique (in performance too)
        
        @arguments
          R_per_age_layer -- list of list_of_NsgaInd -- one list per age layer.
          age_layer_i -- int -- the age layer of interest
        
        @return
          cand_parents -- list of NsgaInd
          elder_inds -- list of NsgaInd -- inds that were in R but could
            not be considered as parents because they were too old
        """
        R = R_per_age_layer[age_layer_i]
        cand_parents = []
        elder_inds = []

        #add from layer i
        for ind in uniqueIndsByPerformance(R):
            if self.ss.allowIndInAgeLayer(age_layer_i, ind.genetic_age,
                                          R_per_age_layer.numAgeLayers()):
                cand_parents.append(ind)
            else:
                elder_inds.append(ind)
        num_from_layer_i = len(cand_parents)
        log.debug('From age layer %d, %d/%d inds are candidate parents' %
                  (age_layer_i, num_from_layer_i, len(R)))

        #add from layer i-1
        if age_layer_i > 0:
            tabu_perfs = [cand_parent.worstCaseMetricValuesStr()
                          for cand_parent in cand_parents]
            R1 = R_per_age_layer[age_layer_i-1]
            for ind in R1:
                ind_str = ind.worstCaseMetricValuesStr()
                if ind_str not in tabu_perfs:
                    cand_parents.append(ind)
                    tabu_perfs.append(ind_str)
            log.debug('From age layer %d, %d/%d inds are candidate parents' %
                      (age_layer_i-1, len(cand_parents) - num_from_layer_i,
                       len(R1)))

        #done
        return cand_parents, elder_inds

    def _nsgaSelectInds(self, F, target_num_inds, minmax_metrics):
        """
        @description
          Selects 'target_num_inds' using nondominated-layered_inds 'F'
          according to NSGA-II's selection algorithm (which basically
          says take the 50% of inds in the top layers).
        
        @arguments
          F -- list of nondom_inds_layer where a nondom_inds_layer is a list
            of inds.  E.g. the output of fastNondominatedSort().
          target_num_inds -- int -- number of inds to select.  
            
        @exceptions
          target_num_inds must be <= total number of inds in F.
        """
        assert target_num_inds <= numIndsInNestedPop(F)
        
        N = target_num_inds
        P, i = [], 0
        while True:
            #set 'distance' value to each ind in F[i]
            self.crowdingDistanceAssignment(F[i], minmax_metrics)

            #stop if this next layer would overfill 
            if len(P) + len(F[i]) > N: break

            #include ith nondominated front in the parent pop P
            P += F[i]

            #stop if we're full
            if len(P) >= N:
                P = P[:N]
                break

            #check the next front for inclusion
            i += 1

        #fill up the rest of P with elements of F[i], going
        # for highest-distance inds first
        if len(P) < N:
            I = numpy.argsort([-ind.distance for ind in F[i]])
            F[i] = list(numpy.take(F[i], I, 1))

            P += F[i][:(N-len(P))]

        #ensure that references to parents in other layers don't hurt us
        # (don't deepcopy because we don't want to copy each 'S' attribute)
        P = [copy.copy(ind) for ind in P]

        return P

    def doStop(self):
        """
        @description
          Stop?
                
        @return
          stop -- bool
        """
        if self.state.tot_num_inds > self.ss.max_num_inds:
            log.info('Stop: num_inds > max')
            return True
        return False
        
    def retrieveMigrants(self):
        """
        @description
          Retrieve some migrants chosen from the 'pooled_db' file,
          if they exist.  
        
        @arguments
          <<none>>
        
        @return
          migrants -- list of Ind -- some migrants
        """
        #corner cases: not interested in migration
        if self.pooled_db_file is None: return []
        if self.ss.migration_rate == 0.0: return []

        #corner case: no pooled db file exists
        # (though it may exist at other times in the run of this engine)
        if not os.path.exists(self.pooled_db_file): return []

        #main case...

        #try to load candidate migrants
        #-this may fail if we are in conflict with another process
        # trying to access the pooled DB file.  No problem, just
        # do it another time
        try:
            pooled_state = loadSynthState(self.pooled_db_file, self.ps)
            cand_migrants = pooled_state.allInds()
        except:
            log.warning('Could not open pooled_db file for migration')
            return []

        #choose num_migrants based on num_inds_per_age_layer and migration_rate
        N = self.ss.num_inds_per_age_layer
        min_num_migrants = 1
        max_num_migrants = N / 2
        num_migrants = int(self.ss.migration_rate * N)
        num_migrants = max(min_num_migrants,min(max_num_migrants,num_migrants))

        #unique-ify cand_migrants
        cand_migrants = uniqueIndsByPerformance(cand_migrants)

        #choose migrants
        if len(cand_migrants) <= num_migrants:
            migrants = cand_migrants
        else:
            migrants = random.sample(cand_migrants, num_migrants)

        log.info('From %d candidate migrants, retrieving %d for pop' %
                 (len(cand_migrants), len(migrants)))
        return migrants
        
    def makeNewPop(self, P):
        """
        @description
          Use selection, mutation, and crossover to create a new child pop Q.
          Via simulation, ensure that each ind is good (if not, generate
          new children until good).
          
          Selection is based on the 'crowded comparison operator' as follows:
           -if possible, first choose based on domination (ie ind.rank)
           -but if they are of same ind.rank, then choose
            the ind with the largest (crowding) distance

          Each new ind will have a unique performance vector.
          (i.e. not one that is in P or any other new inds)
        
        @arguments
          P -- list of Ind -- parent pop
        
        @return
          Q -- list of Ind -- child pop
        
        @notes
          Each ind in P needs to have the attributes of 'rank' and
          'distance' set prior to calling this routine.

          Parent popsize should be self.ss.num_inds_per_age_layer.
          Child popsize will be self.ss.num_inds_per_age_layer.
        """
        N = self.ss.num_inds_per_age_layer
        assert len(P) == N, (len(P), N)
        assert len(P) == len(uniqueIndsByPerformance(P))
        
        #select parents
        parents = []
        while len(parents) < len(P):
            ind_a, ind_b = random.choice(P), random.choice(P)

            #first try selecting based on domination
            if ind_a.rank < ind_b.rank:   parents.append(ind_a)
            elif ind_b.rank < ind_a.rank: parents.append(ind_b)

            #if needed, select based on distance
            elif ind_a.distance > ind_b.distance:  parents.append(ind_a)
            else:                                  parents.append(ind_b)

        #
        tabu_perfs = [ind.worstCaseMetricValuesStr() for ind in P]

        #with parents, generate children via variation
        Q = []
        parent_index = 0
        while len(Q) < self.ss.num_inds_per_age_layer:
            s_Q ="Generating child pop: current #children=%d; target size=%d" %\
                  (len(Q), self.ss.num_inds_per_age_layer)
            s_Q += " (generation=%d)" % self.state.generation
            log.info(s_Q)
            par1 = parents[parent_index]
            if parent_index+1 == len(P): #happens whenever pop size is odd
                par2 = random.choice(parents)
            else:
                par2 = parents[parent_index+1]

            while True:
                success, child1, child2 = \
                         self.varyParentsToGetGoodChildren(par1, par2,
                                                           tabu_perfs, s_Q)
                if success:
                    child1_perf = child1.worstCaseMetricValuesStr()
                    child2_perf = child2.worstCaseMetricValuesStr()
                    assert child1_perf != child2_perf
                    assert child1_perf not in tabu_perfs
                    assert child2_perf not in tabu_perfs
                    tabu_perfs.append(child1_perf)
                    tabu_perfs.append(child2_perf)
                    break
                else:
                    log.debug("Since unsuccessful in vary(), reloop: %s" % s_Q)
                    
                    #once we've tried once with the original parents,
                    # from now on it's a free-for-all (more robust this way)
                    par1 = random.choice(parents)
                    par2 = random.choice(parents)

            #add children in a fashion that can handles an odd-numbered value
            # for num_inds_per_age_layer
            Q.append(child1)
            parent_index += 1
            if len(Q) < len(P): 
                Q.append(child2) 
                parent_index += 1

        #done
        assert len(Q) == N, (len(Q), N)
        assert len(P+Q) == len(uniqueIndsByPerformance(P+Q))
        return Q

    def crowdingDistanceAssignment(self, layer_inds, minmax_metrics):
        """
        @description
          Assign a crowding distance to each individual in list of inds
          at a layer of F.
        
        @arguments
          layer_inds -- list of Ind
          minmax_metrics -- dict of metric_name : (min_val, max_val) as
            computed across _all_ inds, not just across layer_inds
        
        @return
          <<none>> but alters the 'distance' attribute of each individual
           in layer_inds
        """
        #corner case
        if len(layer_inds) == 0:
            return

        #initialize distance for each ind to 0.0
        for ind in layer_inds:
            ind.distance = 0.0

        #increment distance for each ind on a metric-by-metric basis
        for metric in self.ps.flattenedMetrics():
            #retrieve max and min; if max==min then this metric won't
            # affect distance calcs
            (met_min,met_max) = minmax_metrics[metric.name]
            assert met_min > float('-Inf'), "can't scale on inf"
            assert met_max < float('Inf'),  "can't scale on inf"
            if met_min == met_max:
                continue

            #sort layer_inds and metvals, according to metvals 
            metvals = [ind.worstCaseMetricValue(metric.name)
                       for ind in layer_inds]
            I = numpy.argsort(metvals)
            layer_inds = numpy.take(layer_inds, I)
            metvals = numpy.take(metvals, I)

            #ensure that boundary points are always selected via dist = Inf
            layer_inds[0].distance = float('Inf')
            layer_inds[-1].distance = float('Inf')

            #all other points get distance set based on nearness to
            # ind on both sides (scaled by the max and min seen on metric)
            for i in range(1,len(layer_inds)-1):
                d = abs(metvals[i+1] - metvals[i-1]) / (met_max - met_min)
                layer_inds[i].distance += d
                
            
    def doStatusOutput(self, age_layer_i, F):
        """
        @description
          Logs search status for this age layer
        """
        s = ''

        state = self.state
        
        s += 'Gen=%d / age_layer=%d: ' % (state.generation, age_layer_i)

        s += 'tot_#inds=%d' % state.tot_num_inds

        s += '; tot_#_evals=%d (%d on funcs, %d on sim)'%\
             ( state.totalNumEvaluations(),
               state.totalNumFunctionEvaluations(),
               state.totalNumCircuitEvaluations() )
        
        s += '; #evals_per_func_analysis={'
        for an in self.ps.functionAnalyses():
            s += '%s:%d,' % (an.ID, state.num_evaluations_per_analysis[an.ID])
        s += '}'                         
        
        s += '; #evals_per_sim_analysis={'
        for an in self.ps.circuitAnalyses():
            s += '%s:%d,' % (an.ID, state.num_evaluations_per_analysis[an.ID])
        s += '}'

        num_feas_layers = 0
        for layer_inds in F:
            if layer_inds[0].isFeasible(): num_feas_layers += 1
            else: break
        s += '; #nondom_layers=%d (#_with_feas_inds=%d)' % \
             (len(F), num_feas_layers)

        s += '; #inds_per_nondom_layer:'
        for nondom_layer_i, nondom_layer_inds in enumerate(F):
            s += ' %2d' % len(nondom_layer_inds)
            if nondom_layer_i+1 < len(F): s += ','
        
        
        log.info(s)

        log.debug('Inds at top nondominated_layer (of age_layer=%d): %s' %
                  (age_layer_i, populationSummaryStr(self.ps, F[0])))

        metnames = self.ps.flattenedMetricNames()
        if self.ss.do_plot and len(metnames) > 1:
            x0 = [ind.worstCaseMetricValue(metnames[0]) for ind in F[0]]
            y0 = [ind.worstCaseMetricValue(metnames[1]) for ind in F[0]]
            from scipy import gplt
            print x0
            print y0
            gplt.hold('off')
            gplt.plot(x0, y0, 'with points')

            gplt.hold('on')
            for nondom_layer in range(1,7):
                if nondom_layer >= len(F): break
                x = [ind.worstCaseMetricValue(metnames[0])
                     for ind in F[nondom_layer]]
                y = [ind.worstCaseMetricValue(metnames[1])
                     for ind in F[nondom_layer]]
                gplt.plot(x, y, 'with points')

            gplt.title('%s vs. %s' % (metnames[1], metnames[0]))

        return

    def generateRandomGoodInds(self, target_num_good):
        """
        @description
          Randomly generate and eval enough inds such that
          target_num_good of them are not 'bad'.
          Each individual MUST have a unique performance vector.
          Returns the inds.  
        
        @arguments
          target_num_good -- int -- how many good individuals do we want?
        
        @return
           good_inds -- list of Ind -- randomly generated inds, of length
             'target_num_good'
    
        @notes
          Currently has no provisions to avoid infinite loop!
        """
        inds, tabu_netlists, tabu_perfs = [], [], []
        num_tries = 0
        inf = float('Inf')
        for i in range(target_num_good):
            while True:
                log.debug('Gen good rand ind #%d / %d, tot num tries=%d' %
                          (i+1, target_num_good, num_tries))
                num_tries += 1
                ind = self.newRandomInd()
                self.state.tot_num_inds += 1
                
                self.evalInd(ind)
                
                if ind.isBad():
                    log.info("Don't keep random ind because it is Bad")
                elif ind.worstCaseMetricValuesStr() in tabu_perfs:
                    log.info("Don't keep random ind because perfs. aren't"
                             " unique")
                else:
                    log.info('Do keep this random ind')
                    log.debug('  %s' % ind)
                    inds.append(ind)
                    tabu_netlists.append(ind.netlist())
                    tabu_perfs.append(ind.worstCaseMetricValuesStr())
                    break
        return inds

    def newRandomInd(self):
        """
        @description
          Generate a new ind at random.
        
        @arguments
          <<none>>
        
        @return
          new_ind -- Ind object
        """
        pm = self.ps.embedded_part.part.point_meta
        genotype = Genotype()
        genotype.unscaled_opt_point = pm.createRandomUnscaledPoint()
        new_ind = NsgaInd(genotype, self.ps)
        new_ind.genetic_age = 0
        return new_ind

    def evalInd(self, ind):
        """
        @description
          Evaluates this ind on all analysis/env_point combos;
          stores results on the ind.

          Evaluates on the functionAnalyses first.  If any of them
          come out to be infeasible, then forces the ind to 'BAD' and
          does not run the circuit (simulation) analyses.  That
          could be from area analysis, from FunctionDOCs, or otherwise.

          If during simulation, a metric comes out BAD, then
          it forces the ind to be BAD as well.
          
        @arguments
          ind -- Ind object -- ind to evaluate
        
        @return
           <<none>> but it modifies the ind's internal data
        """
        log.info('Evaluate ind...')
        #functions first
        for analysis in self.ps.functionAnalyses():
            for env_point in analysis.env_points:
                sim_results = self.evalIndAtAnalysisEnvPoint(ind, analysis,
                                                             env_point)
                
                for metric_name, metric_value in sim_results.items():
                    if not self.ps.metric(metric_name).isFeasible(metric_value):
                        log.info("Force ind to BAD because function  "
                                 " '%s' is infeasible" % metric_name)
                        ind.forceFullyBad()
                        return
        
        #simulation only if still feasible after funcs
        for analysis in self.ps.circuitAnalyses():
            
            for env_point in analysis.env_points:
                sim_results = self.evalIndAtAnalysisEnvPoint(ind, analysis,
                                                             env_point)
                
                if BAD_METRIC_VALUE in sim_results.values():
                    log.info("Force ind to BAD because BAD_METRIC_VALUE"
                             " found during simulation")
                    ind.forceFullyBad()
                    return
                    
        log.info("This ind evaluates to 'good'.")
        #log.debug(' unscaled_point:  %s', ind.genotype.unscaled_opt_point)
        pm = self.ps.embedded_part.part.point_meta
        scaled_point = pm.scale(ind.genotype.unscaled_opt_point)
        log.debug('  scaled_point:  %s', scaled_point)

    def evalIndAtAnalysisEnvPoint(self, ind, analysis, env_point):
        """
        @description
          Simulates this ind on the given analysis/env_point combo;
          stores results on the ind.

          (Does nothing if the evaluation has previously been done)
        
        @arguments
          ind -- Ind -- ind to evaluate
        
        @return
           MAINLY, IT... modifies the ind's internal data

           ALSO:
           sim_results -- dict of metric_name : metric_value -- the
             simulation values actually found
        """
        #corner case: have already evaluated here
        if ind.simRequestMade(analysis, env_point):
            return

        #main case...
        
        #remember the request
        ind.reportSimRequest(analysis, env_point)
        self.state.num_evaluations_per_analysis[analysis.ID] += 1
        
        #create 'scaled_point'
        pm = self.ps.embedded_part.part.point_meta
        scaled_point = pm.scale(ind.genotype.unscaled_opt_point)
            
        if isinstance(analysis, FunctionAnalysis):
        
            #call the function
            function_result = analysis.function(scaled_point)

            #set results
            sim_results = {analysis.metric.name : function_result}
            ind.setSimResults(sim_results, analysis, env_point)
            
        elif isinstance(analysis, CircuitAnalysis):
            
            #compute netlist
            emb_part = self.ps.embedded_part
            emb_part.functions = scaled_point
            netlist = emb_part.spiceNetlistStr(annotate_bb_info=False)

            #call simulator
            sim_results, lis_results, waveforms_per_ext = analysis.simulate(
                self.simfile_dir, netlist, env_point)

            #set DOCs metric
            assert not sim_results.has_key(DOCs_metric_name)
            assert DOCs_metric_name == 'perc_DOCs_met', 'expected percent DOCs'

            target_metrics = [m.name for m in analysis.metrics]

            if DOCs_metric_name in target_metrics:
                # FIXME: (PP) I don't think this belongs here...
                if not BAD_METRIC_VALUE in sim_results.values():
                    perc = emb_part.percentSimulationDOCsMet(lis_results)
               	    sim_results[DOCs_metric_name] = perc
                    log.info('%s = %.3f' % (DOCs_metric_name, perc))
                else:
                    sim_results[DOCs_metric_name] = 0.0

            #set results
            assert sorted(sim_results.keys()) == sorted(target_metrics)
            ind.setSimResults(sim_results, analysis, env_point,
                              waveforms_per_ext)
            
        else:
            raise AssertionError("Unknown analysis class: %s" %
                                 str(analysis.__class__))

        return sim_results


    def varyParentsToGetGoodChildren(self, par1, par2, tabu_perfs,
                                     status_str,
                                     max_num_rounds=500):
        """
        @description
          Varies par1 and par2 via mutation or crossover, and returns two
          children.
          Repeats generating children as necessary until it is 'accepted'.

          A new child is only accepted if:
          -its netlist is different than both parents
          -its simulation results are not 'bad'
          -its 'nice' metric string is different either parent's string,
           and different than any string in the input 'tabu_perfs'
         
        @arguments
          par1 -- Ind -- first parent
          par2 -- Ind -- second parent
          
          tabu_perfs -- list of string -- the children cannot duplicate
            these
          status_str -- string -- output this string as part of each round,
            to help the user see where we are in the search
          max_num_rounds -- int -- number of rounds at generating
            children.  If this is exceeded, stops and returns success=False.
        
        @return
          success -- bool -- True if two children were generated with
            fewer than 'max_num_rounds'
          child1 -- Ind or None -- offspring #1 (None if unsuccessful)
          child2 -- Ind or None -- offsprign #2 (None if unsuccessful)
        """
        log.debug('Vary parents to get two good, unique children: begin')
        
        child1, child2 = None, None
        child_perfs = []
        par1_perf = par1.worstCaseMetricValuesStr()
        par2_perf = par2.worstCaseMetricValuesStr()

        vary_round = 0
        init_num_inds = self.state.tot_num_inds
        while child1 is None or child2 is None:
            vary_round += 1
            if vary_round > max_num_rounds:
                log.debug('Max # rounds of %d is exceeded, so return '
                          'without success')
                return False, None, None
            
            log.debug('Vary parents: round #%d, tot_num_inds=%d [%s]'%\
                      (vary_round, self.state.tot_num_inds, status_str))

            #note: _varyParents gives children with netlists that are
            # different than either parent's netlist
            (cand_child1, cand_child2) = self._varyParents(par1, par2)

            if child1 is None:
                self.evalInd(cand_child1)
                self.state.tot_num_inds += 1
                child1_perf = cand_child1.worstCaseMetricValuesStr()
                perfs_same = child1_perf == par1_perf or \
                             child1_perf == par2_perf or \
                             child1_perf in child_perfs or \
                             child1_perf in tabu_perfs
                if cand_child1.isBad():
                    log.info('Do not keep cand_child1 b/c bad sim. results')
                elif perfs_same:
                    log.info('Do not keep cand_child1 b/c perf. not unique')
                else:
                    child1 = cand_child1
                    child_perfs.append(child1_perf)
                    log.info("Success: keep cand_child1")

            if child2 is None:
                self.evalInd(cand_child2)
                self.state.tot_num_inds += 1
                child2_perf = cand_child2.worstCaseMetricValuesStr()
                perfs_same = child2_perf == par1_perf or \
                             child2_perf == par2_perf or \
                             child2_perf in child_perfs or \
                             child2_perf in tabu_perfs
                if cand_child2.isBad():
                    log.info('Do not keep cand_child2 b/c bad sim. results')
                elif perfs_same:
                    log.info('Do not keep cand_child2 b/c perf. not unique')
                else:
                    child2 = cand_child2
                    child_perfs.append(child2_perf)
                    log.info("Success: keep cand_child2")  
            
        log.info('Success: took %d ind evals to generate 2 unique children' %
                 (self.state.tot_num_inds - init_num_inds))
        log.debug('Vary parents to get two good, unique children: done')
        return True, child1, child2
        
    def _varyParents(self, par1, par2):
        """
        @description
          Varies par1 and par2 via mutation or crossover, and returns two
          children.
          Repeats variation as necessary so ensure that netlist is different.
        
        @arguments
          par1 -- Ind -- first parent
          par2 -- Ind -- second parent
        
        @return
          child1 -- Ind -- newly generated ind #1
          child2 -- Ind -- newly generated ind #2
        """
        assert par1 is not None
        assert par2 is not None
        
        #choose how much to vary each ind
        num_vary1 = mathutil.randIndex(self.ss.num_vary_biases)
        num_vary2 = mathutil.randIndex(self.ss.num_vary_biases)

        #maybe do crossover before mutating
        do_crossover = random.random() < self.ss.prob_crossover
        if do_crossover:
            (child1, child2) = self.crossoverInds(par1, par2)
            num_vary1 = max(0, num_vary1 - 2)
            num_vary2 = max(0, num_vary2 - 2)
        else:
            (child1, child2) = (par1, par2)

        #always mutate
        child1 = self.mutateInd(child1, num_vary1)
        child2 = self.mutateInd(child2, num_vary2)

        #keep mutating until the child is different
        # (there is huge chance of a same child due to the structure of GRAIL)
        child1 = self.mutateUntilDifferent(child1, par1.netlist())
        child2 = self.mutateUntilDifferent(child2, par2.netlist())

        #set genetic age
        if do_crossover:
            child1.genetic_age = max(par1.genetic_age, par2.genetic_age) + 1
            child2.genetic_age = max(par1.genetic_age, par2.genetic_age) + 1
        else:
            child1.genetic_age = par1.genetic_age + 1
            child2.genetic_age = par2.genetic_age + 1

        return (child1, child2)

    def mutateUntilDifferent(self, ind, reference_netlist):
        """
        @description
          Mutate ind until its netlist is different than reference_netlist.
          Note that it does not continually build on the mutates, i.e.
          we do _not_ wander throughout the neutral space because
          that risks damaging the hidden building blocks.
        """
        num_tries = 0
        while True:
            #avoid infinite loop; and excessive effort
            if num_tries > 100:
                break

            num_vary = mathutil.randIndex(self.ss.num_vary_biases)
            mut_ind = self.mutateInd(ind, num_vary)
            if mut_ind.netlist() != reference_netlist:
                return mut_ind
                                      
        return ind

    def crossoverInds(self, par1, par2):
        """
        @description
          Cross over parent1 and parent2 to create two children, and
          tries to preserve building blocks to the best extent possible.

          Algorithm:
          -in par1, pick a sub-part (or sub-sub-part, etc)
          -determine all the variables that affect that part
          -give par2 those vars' values, and take par2's values in return
        
        @arguments
          par1 -- Ind -- first parent
          par2 -- Ind -- second parent
        
        @return
          (child1, child2) -- tuple of (Ind, Ind) -- newly generated inds
        
        @notes
          The genetic_age attribute of the children is still None. Leave
          setting that to higher-level routines.

          Note that some of the 'affecting' variables will affect places other
          than the part too, i.e. there is crosstalk among trees.  That's
          ok, while this isn't perfect, it's far better than the fully-naive
          uniform crossover which has 100% crosstalk.
        """
        #retrieve parent info
        par1_opt_point = par1.genotype.unscaled_opt_point
        par2_opt_point = par2.genotype.unscaled_opt_point
        
        #choose a sub-part, and find which vars affect it (including
        # alternate topology sub-implementations)
        emb_part = self.ps.embedded_part
        scaled_point = emb_part.part.point_meta.scale(par1_opt_point)
        info_list = emb_part.subPartsInfo(scaled_point)
        cand_info_list = []
        for sub_part_info in info_list:
            (sub_part, sub_point, vars_affecting) = sub_part_info        
            for var in vars_affecting:
                assert var in scaled_point.keys()
            if len(vars_affecting) > 0:
                cand_info_list.append(sub_part_info)

        assert len(cand_info_list) > 0, "vars should affect some parts"
        sub_part_info = random.choice(cand_info_list)
        (sub_emb_part, sub_scaled_point, vars_affecting) = sub_part_info
        log.debug('Crossover: sub_emb_part=%s, vars_affecting=%s' %
                  (sub_emb_part.part.name, vars_affecting))

        #build up dicts
        child1_dict, child2_dict = {}, {}
        for var in par1_opt_point.keys():
            if var in vars_affecting:
                child1_dict[var] = par1_opt_point[var]
                child2_dict[var] = par2_opt_point[var]
            else:
                child1_dict[var] = par2_opt_point[var]
                child2_dict[var] = par1_opt_point[var]

        #build child1
        child1_genotype = Genotype()
        child1_genotype.unscaled_opt_point = Point(False, child1_dict)
        child1 = NsgaInd(child1_genotype, self.ps)

        #build child2
        child2_genotype = Genotype()
        child2_genotype.unscaled_opt_point = Point(False, child2_dict)
        child2 = NsgaInd(child2_genotype, self.ps)

        #done
        return (child1, child2)
        
    def mutateInd(self, parent_ind, num_mutates, force_mutate1var=False):
        """
        @description
          Applies 'num_mutates' mutations to parent_ind.
        
        @arguments
          parent_ind -- Ind_object -- ind to be mutated
        
        @return
          child_ind --  Ind object --
    
        @notes
          The genetic_age attribute of the child is still None. Leave
          setting that to higher-level routines.
        """
        #retrieve base info
        point_meta = self.ps.embedded_part.part.point_meta
        parent_opt_point = parent_ind.genotype.unscaled_opt_point

        #sometimes mutate just 1 var, sometimes mutate all
        if force_mutate1var:
            mutate_1var = True
        else:
            mutate_1var = (random.random() < self.ss.prob_mutate_1var)

        #build up dicts
        child_dict = copy.copy(dict(parent_opt_point))
        for mutate_i in range(num_mutates):
            if mutate_1var: vars_to_mutate = [random.choice(point_meta.keys())]
            else:           vars_to_mutate = point_meta.keys()
            
            for var in vars_to_mutate:
                child_dict[var] = point_meta[var].mutate(child_dict[var],
                                                         self.ss.mutate_stddev)

        #build Ind
        child_genotype = Genotype()
        child_genotype.unscaled_opt_point = Point(False, child_dict)
        child = NsgaInd(child_genotype, self.ps)

        #done
        return child

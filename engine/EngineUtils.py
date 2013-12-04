"""
Utilities useful for different synthesis engines and components.
"""

import cPickle as pickle
import random
import types

import numpy

from adts import *
from util import mathutil
from Ind import Ind

import logging
log = logging.getLogger('synth')

class AgeLayeredPop(list):
    """
    @description
      Holds individuals, stratified by genetic_age.
      
    @attributes
      <list> -- list of list_of_NsgaInd where entry i is for age-level i
    """
    def __init__(self, R_per_age_layer=None):
        if R_per_age_layer is None:
            R_per_age_layer = []
        list.__init__(self, R_per_age_layer)

    def numAgeLayers(self):
        return len(self)

    def uniquifyInds(self):
        """Per level, remove any inds that are duplicate in terms of
        performance"""
        for layer_i, R in enumerate(self):
            self[layer_i] = uniqueIndsByPerformance(R)

    def flattened(self):
        """Return all inds as one big flat list"""
        f = []
        for R in self:
            f.extend(R)
        return f

def populationSummaryStr(ps, inds, sort_metric=None):
    """
    @description
      Returns a string describing a population, with one ind per row.

    @arguments
      ps -- ProblemSetup
      inds -- list of Ind
      sort_metric -- string or None -- if not None, will sort
        the inds by 'sort_metric'.  Else sorts the inds by op_point.ID

    @return
      s -- string
    """
    big_s = '\n'

    # -sort inds according to either ID or sort_metric
    if sort_metric is None:
        I = numpy.argsort([ind.ID for ind in inds])
    else:
        I = numpy.argsort([ind.worstCaseMetricValue(sort_metric)
                             for ind in inds])
    inds = numpy.take(inds, I)
     

    # -output
    #   -row of 'an_index=XX'
    row_s = '%10s  %11s  %10s' % ("","","")
    for analysis_index, analysis in enumerate(ps.analyses):
        for metric in analysis.metrics:
            an_str = 'an_index=%d' % analysis_index
            row_s += '\t%14s' % an_str
    big_s += row_s + '\n'

    #   -row of 'IND_ID   metricname1   metricname2 ...'
    row_s = '%10s  %11s  %10s' % ('IND_ID', 'GENETIC_AGE', 'FEASIBLE')
    for analysis_index, analysis in enumerate(ps.analyses):
        for metric in analysis.metrics:
            row_s += '\t%14s' % metric.name[:14]
    big_s += row_s + '\n'

    #   -for each ind, a row of '<ID_value> <metric1_value> <metric2_value> ...'
    for ind in inds:
        row_s = '%10d  %11d  %10s' % (ind.ID, ind.genetic_age, ind.isFeasible())
        for analysis_index, analysis in enumerate(ps.analyses):
            for metric in analysis.metrics:
                row_s += '\t%14g' % ind.worstCaseMetricValue(metric.name)
        big_s += row_s + '\n'
        
    big_s += '\n'
    return big_s

def populationSummaryToMatlab(ps, inds, metrics_file=None, points_file=None):
    """
    @description
      Returns a string describing a population, with one ind per row.

    @arguments
      ps -- ProblemSetup
      inds -- list of Ind
      metrics_file -- string -- filename to save the performances to
      points_file -- string or None -- filename to save the points to

    @return
      <<nothing>>
    """
    if not metrics_file==None:
        big_s = ''
    
        #-output
        #   -row of 'an_index=XX'
        
        #   -row of 'IND_ID   metricname1   metricname2 ...'
        row_s = '%s,%s,%s' % ('IND_ID', 'GENETIC_AGE', 'FEASIBLE')
        for analysis_index, analysis in enumerate(ps.analyses):
            for metric in analysis.metrics:
                row_s += ',%s' % metric.name[:14]
        big_s += row_s + '\n'
    
        f=open("%s.hdr" % (metrics_file),'w')
        f.write(big_s)
        f.close()    
        
        big_s = ''
        
        #-for each ind, a row of '<ID_value> <metric1_value> <metric2_value>...'
        for ind in inds:
            row_s = '%d,%d,%d' % (ind.ID, ind.genetic_age, ind.isFeasible())
            for analysis_index, analysis in enumerate(ps.analyses):
                for metric in analysis.metrics:
                    row_s += ',%g' % ind.worstCaseMetricValue(metric.name)
            big_s += row_s + '\n'
        
        f=open("%s.val" % (metrics_file),'w')
        f.write(big_s)
        f.close()
    
    
    if not points_file==None:
        unscaled_s = ''
        scaled_s   = ''
        
        unscaled_s += "IND_ID,"
        scaled_s += "IND_ID,"
        
        for ind in inds:
            
            unscaled = ind.genotype.unscaled_opt_point
            for name in unscaled.keys():
                unscaled_s += "%s," % (name)
            
            scaled = ps.embedded_part.part.point_meta.scale(unscaled)
            for name in scaled.keys():
                scaled_s += "%s," % (name)
            
            # exit after the first ind, we only want the keys
            break
        
        # remove the trailing comma
        unscaled_s = unscaled_s[:-1] + '\n'
        scaled_s = scaled_s[:-1] + '\n'
        
        # write the header filess
        f=open("%s.unscaled.hdr" % (points_file),'w')
        f.write(unscaled_s)
        f.close()
        f=open("%s.scaled.hdr" % (points_file),'w')
        f.write(scaled_s)
        f.close()
        
        
        unscaled_s = ""
        scaled_s = ""
        for ind in inds:
            
            unscaled = ind.genotype.unscaled_opt_point
            unscaled_s += "%d," % ind.ID
            for val in unscaled.values():
                unscaled_s += "%g," % (val)
            
            scaled = ps.embedded_part.part.point_meta.scale(unscaled)
            scaled_s += "%d," % ind.ID
            for val in scaled.values():
                scaled_s += "%g," % (val)
                    
            # remove the trailing comma
            unscaled_s = unscaled_s[:-1] + '\n'
            scaled_s = scaled_s[:-1] + '\n'
        
        # write the header filess
        f=open("%s.unscaled.val" % (points_file),'w')
        f.write(unscaled_s)
        f.close()
        f=open("%s.scaled.val" % (points_file),'w')
        f.write(scaled_s)
        f.close()    

def uniqueIndsByPerformance(inds):
    """
    @description
      Prunes away any inds which are duplicate by performance measures.

    @arguments
      inds -- list of Ind

    @return
      unique_inds -- list of Ind
    """
    ind_strs = [ind.worstCaseMetricValuesStr()
                for ind in inds]
    keep_I = mathutil.uniqueStringIndices(ind_strs)
    unique_inds = list(numpy.take(inds, keep_I))
    return unique_inds


class SynthState:
    def __init__(self, ps, ss, R_per_age_layer):
        assert isinstance(R_per_age_layer, AgeLayeredPop), \
               R_per_age_layer.__class__
            
        self.ps = ps #Problem Setup
        self.ss = ss #SolutionStrategy

        #R_per_age_layer is children plus parents per age layer;
        # ie R = P + Q for each layer.
        self.R_per_age_layer = R_per_age_layer
        
        self.generation = 0
        self.tot_num_inds = 0
        
        self.num_evaluations_per_analysis = {} #anID : num_evaluations
        for an in self.ps.analyses:
            self.num_evaluations_per_analysis[an.ID] = 0 

    def totalNumEvaluations(self):
        return sum(self.num_evaluations_per_analysis.values())

    def totalNumFunctionEvaluations(self):
        return sum(self.num_evaluations_per_analysis[an.ID]
                   for an in self.ps.analyses
                   if isinstance(an, FunctionAnalysis))

    def totalNumCircuitEvaluations(self):
        return sum(self.num_evaluations_per_analysis[an.ID]
                   for an in self.ps.analyses
                   if isinstance(an, CircuitAnalysis))

    def allInds(self):
        return self.R_per_age_layer.flattened()

    def save(self, output_file):
        """
        @description
          Pickles self to output_file

          -dereference ps because we can't pickle instancemethod objects
           (and it would be space-consuming if on every ind)
          -also dereference S in inds because that is space-consuming too
        
        @arguments
          output_file -- string
        
        @return
          <<none>> but it has created a file of name 'output_file'
        """

        ps = self.ps
        self.ps = None

        #save info
        Ss_per_age_layer = []
        for R in self.R_per_age_layer:
            Ss_per_age_layer.append( [ind.S for ind in R] )

        for R in self.R_per_age_layer:
            for ind in R:
                ind.S = None
                ind._ps = None
           
        obj_to_save = self

        log.info('Save current state to file: %s...' % output_file)
        
        pickle.dump(obj_to_save, open(output_file,'w'))

        #put the info back
        self.ps = ps
        for Ss, R in zip(Ss_per_age_layer, self.R_per_age_layer):
            for S, ind in zip(Ss, R):
                ind.S = S
                ind._ps = self.ps


def loadSynthState(db_file, ps):
    """
    @description
      Loads a synthesis state from 'db_file'. It can be from any
      generation.

      We need to have 'ps' because we can't fully pickle that, and
       we need to reinsert it

    @arguments
      db_file -- string -- e.g. my_outfile_path/state_gen0026.db

    @return
      synth_state -- SynthState object
    """
    assert isinstance(db_file, types.StringType), db_file.__class__
    num_tries = 0
    max_num_tries = 5 #magic number
    synth_state = pickle.load(open(db_file,'r'))            
    synth_state.ps = ps
    for R in synth_state.R_per_age_layer:
        for ind in R:
            ind._ps = ps
    return synth_state
            
def minMaxMetrics(ps, all_inds):
    """
    @description
      Compute min metric value encountered, and max metric value encountered,
      in 'all_inds'

    @arguments
      all_inds -- list of ind

    @return
      minmax_metrics -- dict of metric_name : (min_val, max_val)
    """
    assert isinstance(all_inds, types.ListType), all_inds.__class__

    minmax_metrics = {}
    for metric in ps.flattenedMetrics():
        min_f, max_f = float('Inf'), float('-Inf')
        for ind in all_inds:
            f = ind.worstCaseMetricValue(metric.name)
            min_f = min(min_f, f)
            max_f = max(max_f, f)
        minmax_metrics[metric.name] = (min_f, max_f)

    return minmax_metrics

    
def fastNondominatedSort(P, minmax_metrics, max_num_inds=None,
                         max_layer_index=None, metric_weights=None):
    """
    @description
      Sort inds in R into layers of nondomination.  The 0th layer's inds
      are the truly nondominated inds; the 1st layer is the nondominated
      inds if you ignore the 0th layer; the 2nd layer is the nondominated
      inds if you ignore the 0th and 1st layers; etc.

      Uses mergeNondominatedSort for speed, and for simplicity
      does merging via Deb_fastNondominatedSort on one layer.

    @arguments
      P -- list of Ind -- inds to sort
      minmax_metrics -- dict of metric_name : (min_val, max_val)
      max_num_inds -- int -- stop building F once it has this number of
        inds.  Specifying None sets max_num_inds = Inf
      max_layer_index -- int -- stop building F once this layer index
        has been built.  Specifying None sets max_layer_index = Inf.
        Example usage: to retrieve just nondominated set, set this to 0.
      metric_weights -- see Ind::constraintViolation().

    @return
      F -- list of nondom_inds_layer where a nondom_inds_layer is a
        list of inds and all inds_layers together make up R.
        E.g. F[2] may have [P[15], P[17], P[4]]

      ALSO: each the inds in P and F have three attributes modified:
        n -- int -- number of inds which dominate the ind
        S -- list of ind -- the inds that this ind dominates
        rank -- int -- 0 means in 0th nondom layer, 1 in 1st layer, etc.
    """
    if max_num_inds is None:
        max_num_inds = float('Inf')
    if max_layer_index is None:
        max_layer_index = float('Inf')

    #corner case
    if len(P) == 0:
        return [[]]

    #main case...
    F = []
    remaining_inds = P
    layer_index = 0
    while len(remaining_inds) > 0:
        next_nondom_inds = mergeNondominatedSort( \
            remaining_inds, minmax_metrics, max_num_inds, metric_weights)
        for ind in next_nondom_inds:
            ind.rank = layer_index
        F.append( next_nondom_inds )
            
        next_nondom_IDs = [ind.ID for ind in next_nondom_inds]
        remaining_inds = [ind for ind in remaining_inds
                          if ind.ID not in next_nondom_IDs]

        #stop if max_layer_index hit
        layer_index += 1
        if layer_index >= max_layer_index:
            break

        #stop if max_num_inds is hit
        if numIndsInNestedPop(F) >= max_num_inds:
            break

    #make sure we don't exceed max_num_inds
    if numIndsInNestedPop(F) > max_num_inds:
        num_extra = numIndsInNestedPop(F) - max_num_inds
        num_keep = max(0, len(F[-1]) - num_extra)
        F[-1] = random.sample(F[-1], num_keep)

    #if the last list_of_inds in F is empty, remove it
    if len(F[-1]) == 0:
        F = F[:-1]

    return F


def Deb_fastNondominatedSort(P, minmax_metrics, max_num_inds=None,
                             max_layer_index=None, metric_weights=None):
    """
    @description
      Like fastNondominatedSort, but uses Deb's algorithm in NSGA-II
      to build up the nondom layers.  (It's slower than fastNondominatedSort)

    @arguments
      <<same as fastNondominatedSort>>

    @return
      <<same as fastNondominatedSort>>
    """
    if max_num_inds is None:
        max_num_inds = float('Inf')
    if max_layer_index is None:
        max_layer_index = float('Inf')
        
    F = [[]]
    
    #corner case
    if len(P) == 0:
        return F

    #main case...
    dataID = UniqueIDFactory().newID()
    for p in P:
        p.n = 0 #n is domination count of ind 'p',ie # inds which dominate p
        p.S = [] #S is the set of solutions that 'p' dominates

        for q in P:
            if p.constrainedDominates(q, minmax_metrics, metric_weights,
                                      dataID):
                p.S += [q]
            elif q.constrainedDominates(p, minmax_metrics, metric_weights,
                                        dataID):
                p.n += 1

        #if p belongs to 0th front, remember that
        if p.n == 0:
            p.rank = 0
            F[0] += [p]

    i = 0
    while len(F[i]) > 0:
        #stop if max_layer_index is hit
        if i == max_layer_index:
            break
        
        Q = [] #stores members of the next front
        for p in F[i]:
            for q in p.S:
                q.n -= 1
                if q.n == 0:
                    q.rank = i + 1
                    Q += [q]
        i += 1
        F.append(Q)

        #stop if max_num_inds is hit
        if numIndsInNestedPop(F) >= max_num_inds:
            break

    #make sure we don't exceed max_num_inds
    if numIndsInNestedPop(F) > max_num_inds:
        num_extra = numIndsInNestedPop(F) - max_num_inds
        num_keep = max(0, len(F[-1]) - num_extra)
        F[-1] = random.sample(F[-1], num_keep)

    #if the last list_of_inds in F is empty, remove it
    if len(F[-1]) == 0:
        F = F[:-1]

    return F

def mergeNondominatedSort(P, minmax_metrics, max_num_inds, metric_weights):
    """
    @description
      Given a list of individuals P, returns the nondominated individuals.
      Uses Trent's merge-sort twist to make nondominated sorting really fast.
      
    @arguments
      <<same as fastNondominatedSort_slow, except does not have
      all of that routine's arguments>>

    @return
      nondom_inds -- list of Ind object

    @notes
      This only returns ONE layer of nondomination.  
    """
    if max_num_inds == 0:
        return []
    elif len(P) <= 1:
        return P
    else:
        N2 = len(P)/2
        left = P[:N2]
        right = P[N2:]

        #do subdivision
        left = mergeNondominatedSort(left,
                                      minmax_metrics,max_num_inds,metric_weights)
        right = mergeNondominatedSort(right,
                                      minmax_metrics,max_num_inds,metric_weights)

        #merge the results
        result = simpleNondominatedSort(left+right, minmax_metrics,
                                        metric_weights)
        return result
    
def simpleNondominatedSort(P, minmax_metrics, metric_weights):
    """
    @description
      Given a list of individuals P, returns the nondominated individuals.
      
    @arguments
      <<same as fastNondominatedSort_slow, except does not have
      all of that routine's arguments>>

    @return
      nondom_inds -- list of Ind object

    @notes
      This only returns ONE layer of nondomination.
    """
    nondom_inds = []
    dataID = UniqueIDFactory().newID()
    for p in P:
        p_is_dominated = False
        for q in P:
            if q.constrainedDominates(p, minmax_metrics, metric_weights,
                                      dataID):
                p_is_dominated = True
                break
        if not p_is_dominated:
            nondom_inds.append(p)

    return nondom_inds

def numIndsInNestedPop(F):
    """
    @description
      Returns the total # inds in a list of list_of_inds

    @arguments
      F -- list of list_of_inds

    @return
      num_inds -- int -- == len(list_of_inds[0]) + len(list_of_inds[1]) + ... 
    """
    return sum([len(Fi) for Fi in F])

class UniqueIDFactory:
    _ID_counter = 0L
    
    def newID(self):
        return self.__class__._ID_counter
        self.__class__._ID_counter += 1
        

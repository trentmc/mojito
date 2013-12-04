from adts import *
from adts.Part import replaceAutoNodesWithXXX


from util import mathutil
from util.constants import BAD_METRIC_VALUE

import logging

log = logging.getLogger('synth')

class Genotype:
    #for now, tack on whatever is needed into this
    pass

class Ind:
    """
    @description
      An 'individual' in the search: a point in a search space, plus results
      
    @attributes
      genotype -- -- defines the point in the search space that the Ind embodies
      sim_requests_made -- dict of [analysis ID][env point ID] : bool --
        for keeping track of if a simulation request has been made
      sim_results -- dict of [metric_name][env point ID] : None/metric_value
        -- for keeping track of completed simulations, and what the value was
      sim_waveforms -- dict of [analysis ID][env point ID] : waveforms_per_ext
        where waveforms_per_ext is either a dict of extension_str :
        2d_waveforms_array, or None.
      _ps -- ProblemSetup object -- keep a reference to this in order
        to conveniently compute worst-case metric values, etc
        :TODO: tlm -- pickled individuals is larger than necessary because
        we pickle ps with every individual.  If we wanted, to save space,we could
        de-reference it before pickling, and re-reference after unpickling.  But
        be careful, such functionality is very error-prone.

      cached attributes; currently only stored if fullyEvaluated() == True:
      _cached_fully_evaluated -- will fullyEvaluated() return True?
      _cached_wc_metvals -- dict of metric_name : worst_case_metval --
        to speed return of worstCaseMetricValue
      _cached_is_feasible -- bool
      _cached_constraint_violation -- dict of (dataID : constraintViolation())
           
    @notes
      -the sim_requests are keyed by analysis, whereas the results
       are keyed by metric.  This is for reasons of convenient access.
    """ 
    def __init__(self, genotype, ps):
        """
        @arguments
            genotype -- see clas description
            ps -- ProblemSetup object -- used to initialize
              self.sim_requests_made and self.sim_results
        
        @return
          ind -- Ind object
        """
        if not isinstance(ps, ProblemSetup): raise ValueError
        
        self.genotype = genotype
        self.sim_requests_made = {} 
        self.sim_results = {}
        self.sim_waveforms = {}
        for an in ps.analyses:
            self.sim_requests_made[an.ID] = {}
            self.sim_waveforms[an.ID] = {}
            for env_point in an.env_points:
                self.sim_requests_made[an.ID][env_point.ID] = False
                self.sim_waveforms[an.ID][env_point.ID] = None

            for metric in an.metrics:
                self.sim_results[metric.name] = {}
                for env_point in an.env_points:
                    self.sim_results[metric.name][env_point.ID] = None

        self._ps = ps

        #cached attributes
        self._cached_fully_evaluated = False
        self._cached_wc_metvals = {}
        self._cached_is_feasible = None
        self._cached_constraint_violation = {} 

    #make Ind look like it has the attribute of 'ID'
    # -warning: will need to change this when we start changing structures too!
    def _ID(self):
        return self.genotype.unscaled_opt_point.ID
    ID = property(_ID)

    def __str__(self):
        s = "Ind={"
        if self.fullyEvaluated():
            s += ' wc_metric_values=%s' % self.worstCaseMetricValuesStr()
            s += ' is_feasible=%s' % self.isFeasible()

        #s += '; sim_requests_made=FIXME'
        #s += '; sim_results=FIXME'
        
        #s += ' genotype=%s' % self.genotype
        
        s += " /Ind}"  
        return s
    
    def reportSimRequest(self, analysis, env_point):
        """
        @description
          Reports that a request was made at (analysis, env_point).
          Call this right before, or right after, you make a sim request;
          this ensures that an ind gets fully evaluated, and not doubly either.
        
        @arguments       
          analysis -- Analysis object -- 
          env_point -- EnvPoint object -- 
        
        @return
          <<none>> but modifies self.sim_requests_made
    
        @notes
          Do not currently support rnd_points.
          Do not currently use EvalRequest objects.
        """
        if self.sim_requests_made[analysis.ID][env_point.ID]:
            raise ValueError("have previously requested this eval;"
                             " can't do it again")
        self.sim_requests_made[analysis.ID][env_point.ID] = True

    def simRequestMade(self, analysis, env_point):
        """
        @description
          Reports whether or not a sim request at a particular
          (analysis, env_point) has been made
        
        @arguments
          analysis -- Analysis object -- 
          env_point -- EnvPoint object -- 
        
        @return
          request_was_made -- bool
    
        @notes
          Do not currently support rnd_points.
          Do not currently use EvalRequest objects.
        """
        return self.sim_requests_made[analysis.ID][env_point.ID]

    def setSimResults(self, sim_results, analysis, env_point,
                      waveforms_per_ext=None):
        """
        @description
          Given the sim_results from eval_request, store it
        
        @arguments
          sim_results -- dict of metric_name:metric_value (therefore we
            do not need the analysis to be identified, because every
            metric name is unique)
          analysis -- Analysis -- the analysis where the ind was eval'd at
          env_point -- EnvPoint -- the env_point where ind was eval'd at
          waveforms_per_ext -- dict of extension_str : 2d_array_of_waveforms
            (or None)
        
        @notes
          Do not currently support rnd_points.
          Do not currently use EvalRequest objects.
        """
        #validate
        if not self.simRequestMade(analysis, env_point):
            raise ValueError('Have to report the sim request before set results')
        for metric_name in sim_results.keys():
            if self.sim_results[metric_name][env_point.ID] is not None:
                raise ValueError('Already have sim_results at metric %s'
                                 ' and env pt ID %d'% (metric_name,env_point.ID))
        if self.sim_waveforms[analysis.ID][env_point.ID] is not None:
            raise ValueError('Already have sim_waveforms at analysis ID %d'
                             ' and env pt ID %d' % (analysis.ID, env_point.ID))

        #set results
        # -metric values
        for metric_name, value in sim_results.items():
            self.sim_results[metric_name][env_point.ID] = value

        # -waveforms
        if waveforms_per_ext is not None:
            self.sim_waveforms[analysis.ID][env_point.ID] = waveforms_per_ext

    def forceFullyBad(self):
        """
        @description
          Puts all sim results to bad (and all sim requests to 'done').
          Therefore, by calling this, a subsequent call to fullyEvaluated()
          will return True.
        """
        for anID in self.sim_requests_made.keys():
            for env_point_ID in self.sim_requests_made[anID].keys():
                self.sim_requests_made[anID][env_point_ID] = True

        for metric_name in self.sim_results.keys():
            for env_point_ID in self.sim_results.keys():
                self.sim_results[metric_name][env_point_ID] = BAD_METRIC_VALUE

    def isBad(self):
        """
        @description
          An Ind is 'bad' if _any_ of the sim results results back so far
          have a value of BAD_METRIC_VALUE.
        
        @arguments
          <<none>>
        
        @return
          is_bad -- bool
        """
        for results_at_metric in self.sim_results.values():
            if BAD_METRIC_VALUE in results_at_metric.values():
                return True
        return False

        
    def fullyEvaluated(self):
        """
        @description
          Returns true if this ind has had sim_requests_made at all possible places.

        @notes
          Note that the caching here is different than other caching.  The
          cache is only used when fullyEvaluated() would return True, but
          not when False.  That's fine, because we get to True quickly,
          and never revert.
        """
        #backwards compatibility
        if not hasattr(self, '_cached_fully_evaluated'):
            self._cached_fully_evaluated = False

        #exploit cache?
        if self._cached_fully_evaluated:
            return True
        
        #main work
        for requests_at_analysis in self.sim_requests_made.values():
            if False in requests_at_analysis.values():
                #(no need to update cached value, it's still False)
                return False

        #if we get here, then we can also change the cached value to True
        self._cached_fully_evaluated = True
        return True
        
    def worstCaseMetricValue(self, metric_name):
        """
        @description
          Returns worst-case metric value at 'metric_name'
          which is found by aggregating across all env points at that metric.

        @notes
          Handles BAD_METRIC_VALUE too
        
          For safety and simplicity, only cache if fully evaluated
           (note that BAD inds return True for fullyEvaluated())
        """
        #exploit cache?
        if self._cached_wc_metvals.has_key(metric_name):
            return self._cached_wc_metvals[metric_name]

        #main case: do the computation
        metric_values = self.sim_results[metric_name].values()
        if BAD_METRIC_VALUE in metric_values:
            wc_metval = BAD_METRIC_VALUE
        else:
            metric = self._ps.metric(metric_name)
            wc_metval = metric.worstCaseValue(metric_values)

        #cache
        if self.fullyEvaluated():
            self._cached_wc_metvals[metric_name] = wc_metval

        #done!
        return wc_metval

    def worstCaseMetricValuesStr(self):
        """Returns a string that prints out the metric values in a 'nice' way"""
        return mathutil.niceValuesStr(self.worstCaseMetricValues())

    def worstCaseMetricValues(self):
        """Returns dict of metric_name : worst_case_metric_value"""
        d = {}
        for metric_name in self.sim_results.keys():
            d[metric_name] = self.worstCaseMetricValue(metric_name)
        return d

    def constraintViolation(self, minmax_metrics, metric_weights=None,
                            dataID = None):
        """
        @description
          Returns a measure of how much this individual has violated
          constraints.  Uses minmax_metrics to scale the metric values.
          Violation is 0.0 if the individual is feasible, and >0 if infeasible.
        
        @arguments
          minmax_metrics -- dict of metric_name : (min_val, max_val).  Need
            an entry for every metric.
          metric_weights -- dict of metric_name: metric_weight.  If
            a metric does not have an entry, its value is 1.0.  Default of
            None means 1.0 for all metrics.  Values larger than 1.0 mean
            that the metric gets emphasized more in the sum of violations.
          dataID -- if None, won't cache.  If not None, it will cache such
            that subsequent calls to this routine with this dataID
            will use the cached value (and ignore minmax_metrics and
            metric_weights)
        
        @return
          violation -- float -- 
    
        @exceptions
          If any of this ind's worst-case metric values are BAD_METRIC_VALUE
          then this routine will return 'Inf' (ie ind.isBad())
          
        @notes
          Caching here doesn't care if the ind is fully evaluated or not,
          because it changes anyway depending on dataID.
        """
        #backwards compatibility
        if not hasattr(self, '_cached_constraint_violation'):
            self._cached_constraint_violation = {}
        
        #exploit cache?
        if dataID is not None and \
               self._cached_constraint_violation.has_key(dataID):
            return self._cached_constraint_violation[dataID]

        #corner case
        if self.isBad():
            total_violation = float('Inf')
            self._cached_constraint_violation[dataID] = total_violation
            return total_violation

        #main case...
        total_violation = 0.0
        if metric_weights is None: metric_weights = {}
        
        for metric in self._ps.flattenedMetrics():
            #note that metric max==min then we ignore it (we can't do
            # anything about violation on it anyway!)
            (metric_min,metric_max) = minmax_metrics[metric.name]
            if metric_min == metric_max:
                continue
            
            metric_value = self.worstCaseMetricValue(metric.name)
            metric_violation = metric.constraintViolation(metric_value)
            scaled_violation = metric_violation / (metric_max - metric_min)

            if not metric_weights.has_key(metric.name):
                metric_w = 1.0
            else:
                metric_w = metric_weights[metric.name]
                
            total_violation += metric_w * scaled_violation

        #cache and return
        self._cached_constraint_violation[dataID] = total_violation
        return total_violation

    def isFeasible(self):
        """
        @description
          Does this individual meet all constraints?
        
        @arguments
          <<none>>
        
        @return
          is_feasible -- bool
    
        @exceptions
          Handles BAD_METRIC_VALUEs because Metric handles them
    
        @notes
          Currently assumes that the Ind has been simulated at least
          once on each analysis

          Only caches if the ind has been fully evaluated (for safety)
        """
        #backwards compatibility
        if not hasattr(self, '_cached_is_feasible'):
            self._cached_is_feasible = None
        
        #exploit cache?
        if self._cached_is_feasible is not None:
            assert self.fullyEvaluated(), "should only cache if fully eval'd"
            return self._cached_is_feasible

        #main work
        is_feasible = True
        for metric in self._ps.flattenedMetrics():
            metric_value = self.worstCaseMetricValue(metric.name)
            if not metric.isFeasible(metric_value):
                is_feasible = False
                break

        #cache
        if self.fullyEvaluated():
            self._cached_is_feasible = is_feasible

        #return
        return is_feasible

    def constrainedDominates(self, ind_b, minmax_metrics, metric_weights=None,
                             dataID=None):
        """
        @description
          Returns True if any of the following are True:
          1. ind_a (=self) is feasible and ind_b is not
          2. ind_a and ind_b are both infeasible, but ind_a has a smaller
             overall constraint violation
          3. ind_a and ind_b are both feasible, and ind_a dominates ind_b.

          Remember that 'feasible' means meets _all_ constraints.
        
        @arguments
          self==ind_a -- Ind object
          ind_b -- Ind object
          minmax_metrics -- dict of metric_name : (min_val, max_val)
          metric_weights -- see constraintViolation()
          dataID -- if None, won't cache constraintViolation().
            If not None, it will cache such
            that subsequent calls to this routine with this dataID
            will use the cached value (and ignore minmax_metrics and
            metric_weights)
        
        @return

          a_dominates -- bool
    
        @exceptions
    
        @notes

          Currently assumes that the Ind has been simulated at least
          once on each analysis 
        """
        ind_a = self
        feasible_a = ind_a.isFeasible()
        feasible_b = ind_b.isFeasible()

        #case 1
        if feasible_a and not feasible_b:
            return True

        #case 2
        elif not feasible_a and not feasible_b and \
             (ind_a.constraintViolation(minmax_metrics,metric_weights,dataID)<\
              ind_b.constraintViolation(minmax_metrics,metric_weights,dataID)):
            return True

        #case 3
        elif feasible_a and feasible_b and ind_a.dominates(ind_b):
            return True

        #default case
        else:
            return False

    def dominates(self, ind_b):
        """
        @description
          Returns True if ind_a=self dominates ind_b, and False otherwise.

          'Dominates' means that ind_a is better than ind_b in at least
          one objective; and for remaining objectives, at least equal.

          Does not concern itself with metrics that have no objectives
          (ie metric.improve_past_feasible is False)
        
        @arguments
          self==ind_a -- Ind object
          ind_b -- Ind object
        
        @return
          a_dominates -- bool
    
        @exceptions
          Can only call this if ind is feasible, because constrainedDominates()
          should handle the cases where the ind is infeasible
        """
        assert self.isFeasible()
        ind_a = self
        
        found_better = False
        at_least_equal = True
        for metric in self._ps.flattenedMetrics():
            if not metric.improve_past_feasible: continue
            
            value_a = ind_a.worstCaseMetricValue(metric.name)
            value_b = ind_b.worstCaseMetricValue(metric.name)
            
            if metric.isBetter(value_a, value_b):
                found_better = True
            elif metric.isBetter(value_b, value_a):
                at_least_equal = False
                break

        return found_better and at_least_equal

    def netlist(self, annotate_bb_info=False, add_infostring=False):
        """Returns the netlist that this ind's genotype represents.
        """
        emb_part = self._ps.embedded_part
        old_functions = emb_part.functions #save
        
        pm = emb_part.part.point_meta
        emb_part.functions = pm.scale(self.genotype.unscaled_opt_point)
        netlist = emb_part.spiceNetlistStr(annotate_bb_info, add_infostring)
        
        emb_part.functions = old_functions #restore
        return netlist

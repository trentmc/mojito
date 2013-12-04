import numpy

from util.constants import BAD_METRIC_VALUE
from util import mathutil

MAXIMIZE = 0
MINIMIZE = 1
IN_RANGE = 2

class Metric:
    """
    @description
      Defines a single measurable performance value, including
      a lower and/or upper constraint threshold.
      
    @attributes
      name -- string -- the metric's name
      min_threshold -- float or int
      max_threshold -- float or int
      _aim -- IN_RANGE, MAXIMIZE, MINIMIZE -- direction of metric
      improve_past_feasible -- bool -- keep trying to improve further, once we're
      feasible?  (which gives an objective sitting on top of the constraint)
      
    @notes
      To clarify objectives and constraints:
      -every metric always has two threshold constraints (though
       one may have no effect if it is -Inf or +Inf)
      -and if improve_past_feasible is True, then it also has one objective
    """
    
    def __init__(self, name, min_threshold, max_threshold,
                 improve_past_feasible):
        """        
        @arguments        
          name -- see class description
          min_threshold -- ''
          max_threshold -- ''
          improve_past_feasible -- ''
        
        @return
          Metric object
    
        @exceptions
          Can't have min_threshold == -inf at the same time as max_threshold==inf
        """
        #validate inputs
        if not mathutil.isNumber(min_threshold):
            raise ValueError('min_threshold was not a number: %s' %min_threshold)
        if not mathutil.isNumber(max_threshold):
            raise ValueError('max_threshold was not a number: %s' %max_threshold)
        if min_threshold > max_threshold:
            raise ValueError("Can't have min_threshold > max")
        if min_threshold == float('-inf') and max_threshold == float('inf'):
            raise ValueError("Can't have both min and max thresholds at inf")
        if min_threshold == max_threshold:
            if improve_past_feasible:
                raise ValueError("Can't have min_threshold=max with objectives")
            if abs(min_threshold) == float('inf'):
                raise ValueError("Can't have min_threshold=max with an Inf")

        #set values
        self.name = name
        self.min_threshold = min_threshold
        self.max_threshold = max_threshold
        self.improve_past_feasible = improve_past_feasible

        if min_threshold != float('-inf') and max_threshold != float('inf'):
            self._aim = IN_RANGE
        elif min_threshold == float('-inf'):
            self._aim = MINIMIZE
        else:
            self._aim = MAXIMIZE

    def worstCaseValue(self, metric_values):
        """
        @description
          Returns worst-case value, by aggregating metric_values.  These
          are typically from different env_points.
        
        @arguments
          metric_values -- list of numbers (ints and/or floats)          
        
        @return
          worst_case_metric_value -- int or float
          
        @exceptions
          If any metric_value is BAD_METRIC_VALUE, it returns BAD_METRIC_VALUE
    
        @notes
          This works even for an IN_RANGE aim -- what it does is find
          the metric value that gives the smallest safety margin within
          the thresholds
        """
        if BAD_METRIC_VALUE in metric_values:
            return BAD_METRIC_VALUE
        elif self._aim == MINIMIZE:
            return max(metric_values)
        elif self._aim == MAXIMIZE:
            return min(metric_values)
        else:
            margins = [min(value - self.min_threshold,self.max_threshold - value)
                       for value in metric_values]
            return metric_values[numpy.argmin(margins)]

    def isFeasible(self, metric_value):
        """
        @description
          Returns True if metric_value is between [min_threshold, max_threshold]
        
        @arguments
          metric_value -- float or int
        
        @return
          is_feasible -- bool
    
        @exceptions
          Returns False if metric_value is BAD_METRIC_VALUE
    
        @notes
          This works equally for constraints and objectives.
        """
        if metric_value == BAD_METRIC_VALUE:
            return False
        else:
            return self.min_threshold <= metric_value <= self.max_threshold

    def isBetter(self, value_a, value_b):
        """
        @description
          Returns True if metric value_a is better than metric value_b,
          and False otherwise.

          Details:
            -if a is feasible and b is not, returns True
            -else if b is feasible and a is not, returns False
            -else if both a and b are feasible:
               if self.improve_past_feasible is False: returns False
               else: return (a has higher safety margin than b)
            -else both are infeasible:
              return (a violates constraint less than b)
        
        @arguments
          value_a -- float or int
          value_b -- float or int          
        
        @return
          a_is_better -- bool
    
        @exceptions
          If both value_a and value_b are BAD_METRIC_VALUEs, then
          it will return False.  If only one is a BAD_METRIC_VALUE,
          then the non-BAD value is considered to be better.
          
        @notes
          See that we can define 'is better' even for in-range constraints
          when both values are feasible and improve_past_feasible is True --
          it's 'which value gives a higher safety margin?'

          Note that margin == -violation, but we make them distinct
          for the purpose of clarity.
        """
        #corner case: handle BAD_METRIC_VALUE
        if value_a == BAD_METRIC_VALUE and value_b == BAD_METRIC_VALUE:
            return False
        elif value_a == BAD_METRIC_VALUE:
            return False
        elif value_b == BAD_METRIC_VALUE:
            return True

        #main cases
        a_feas, b_feas = self.isFeasible(value_a), self.isFeasible(value_b)
        if a_feas and not b_feas: return True
        elif b_feas and not a_feas: return False
        elif a_feas and b_feas:
            if not self.improve_past_feasible: return False
            else:
                margin_a = min(value_a - self.min_threshold,
                               self.max_threshold - value_a)
                margin_b = min(value_b - self.min_threshold,
                               self.max_threshold - value_b)
                return margin_a > margin_b
        else: 
            violation_a = max(self.min_threshold - value_a,
                              value_a - self.max_threshold)
            violation_b = max(self.min_threshold - value_b,
                              value_b - self.max_threshold)
            return violation_a < violation_b

    def constraintViolation(self, metric_value):
        """
        @description
          Returns the degree to which metric_value violates this
          metric's constraint(s).
          -violation is 0.0 if the metric_value is feasible
          -and >0.0 otherwise
        
        @arguments
          metric_value -- float or int       
        
        @return
          constraint_violation -- float or int
    
        @exceptions
          returns Inf if metric_value is BAD_METRIC_VALUE
        """
        #corner case
        if metric_value == BAD_METRIC_VALUE:
            return float('Inf')

        #main case
        violation = max(self.min_threshold - metric_value,
                        metric_value - self.max_threshold)
        violation = max(0.0, violation)
            
        return violation

    def __str__(self):
        s = ''
        s += 'Metric={'
        s += ' name=%s' % self.name
        s += '; min_threshold=%s' % self.min_threshold
        s += '; max_threshold=%s' % self.max_threshold
        s += '; improve_past_feasible=%s' % self.improve_past_feasible
        s += ' /Metric}'
        return s

    def prettyStr(self):
        s = 'Constraint: '

        if self._aim == MINIMIZE:
            s += '%s <= %s' % (self.name, self.max_threshold)
        elif self._aim == MAXIMIZE:
            s += '%s >= %s' % (self.name, self.min_threshold)
        else:
            s += '%s <= %s <= %s' % (self.min_threshold, self.name,
                                     self.max_threshold)

        if self.improve_past_feasible:
            s += '; Objective: '
            if self._aim == MINIMIZE:
                s += 'minimize'
            elif self._aim == MAXIMIZE:
                s += 'maximize'
            else:
                s += 'center within constraint bounds'
            
        return s
        
        

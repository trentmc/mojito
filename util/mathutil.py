import types
import random
import math
import copy

import numpy
try:
    import scipy
except ImportError:
    class scipy:
        @classmethod
        def isnan(self, val):
            return 'nan' in str(val)
        @classmethod
        def hasInf(self, val):
            return 'inf' in str(val)

from constants import BAD_METRIC_VALUE

def stddev(x):
    """
    @description
      Returns standard deviation of vector x.
      
    @arguments
      x -- list of ints and/or floats, or 1d array -- 

    @return
      stddev_of_x -- float
    """
    if len(numpy.asarray(x).shape) != 1:
        raise ValueError('expect a 1d array or list')

    if len(x) == 1:
        return 0.0
    else:
        return numpy.std(x, ddof=1)

def hasNan(x):
    """Returns true if any entry in vector or array x has a 'nan' in it"""
    for val in x:
        if scipy.isnan(val):
            return True
    return False

def hasInf(x):
    """Returns true if any entry in vector or array x has an 'inf' in it"""
    for val in x:
        if scipy.isinf(val):
            return True
    return False

def hasNanOrInf(x):
    """Returns true if any entry in vector or array x has a 'nan' or
    'inf' in it"""
    return hasNan(x) or hasInf(x)
    
def allEntriesAreUnique(x):
    """Returns true if every entry in x is unique"""
    return len(x) == len(set(x))

def listDiff( list_a, items_to_remove ):
    """Returns list_a, minus 'items_to_remove'
    """
    return [entry_a for entry_a in list_a if entry_a not in items_to_remove]

def listsOverlap( list_a, list_b):
    """Returns True if list_a and list_b share at least one common item '
    """
    set_a, set_b = set(list_a), set(list_b)
    return len( set_a.intersection(set_b) ) > 0

def isNumber( x ):
    """Returns True only if x is a Float, Int, or Long, and NOT complex"""
    return isinstance(x, types.FloatType) or \
           isinstance(x, types.IntType) or \
           isinstance(x, types.LongType)

def allEntriesAreNumbers( xs ):
    """Returns true if every entry in this list, 1-d array, or set is
    a NumberType"""
    for x in xs:
        if not isNumber( x ):
            return False
    return True

def randIndex( biases ):
    """
    @description
      Randomly chooses an int in range {0,1,....,len(biases)-1), where
      with a bias towards higher values of biases
      
    @arguments
      biases -- list of [bias_for_index0, bias_for_index1, ...] where
        each bias is a float or int

    @return
      chosen_index -- int -- 
    """
    #validate inputs
    if len(biases) == 0:
        raise ValueError("Need >0 biases")
    if min(biases) < 0.0:
        raise ValueError("All biases must be >=0")

    #corner case: every bias is zero
    if float(min(biases)) == float(max(biases)) == 0.0:
        return random.randint(0, len(biases)-1)

    #main case
    accbiases = numpy.cumsum(biases)
    maxval = accbiases[-1]
    thr = maxval * random.random()
    
    for i, accbias in enumerate(accbiases):
        if accbias > thr or accbias == maxval:
            return i

def niceValuesStr( d ):
    """
    @description
      Given a dict of key : number_value, output as a string
      where the values are printed with '%g'.
      
    @arguments
      d -- dict

    @return
      s -- string

    @exceptions
      If number_value is a BAD_METRIC_VALUE, it will print that instead
      of applying %g.
    """
    s = '{'
    for index, (key, value) in enumerate(d.items()):
        s += '%s:' % key
        if value == BAD_METRIC_VALUE:
            s += str(BAD_METRIC_VALUE)
        else:
            s += '%g' % value
        if (index+1) < len(d):
            s += ','
    s += '}'
    return s
    


def uniqueStringIndices(strings_list):
    """
    @description
      Returns a list of indices of strings_list such
      that there is only one id.  Always returns the index
      of the first unique element that occurs.

    @arguments
      strings_list -- list of string objects

    @return
      I -- list of indices into strings_list
    """
    if not isinstance(strings_list, types.ListType):
        raise ValueError("argument needs to be a list, not a %s" %
                         (strings_list.__class__))
    
    #The trick: python dictionaries are very efficient at knowing
    # what keys they already have.  So exploit that for O(NlogN) efficiency.
    #(Otherwise the algorithm is O(N^2)
    
    I = []
    strings_dict = {}
    for i,s in enumerate(strings_list):
        if not isinstance(s, types.StringType):
            raise ValueError("an entry was %s rather than string" %
                             (s.__class__))
        len_before = len(strings_dict)
        strings_dict[s] = 1
        len_after = len(strings_dict)
        if len_after > len_before:
            I.append(i)
    return I


def minPerRow(X):
    """
    @description
      Returns the minimum value found in each row

    @arguments
      X -- 2d array of numbers

    @return
      min_per_row -- 1d array of numbers
    """
    assert len(X.shape) == 2, "should be 2d array"
    return numpy.array([min(X[row_i,:]) for row_i in range(X.shape[0])])

def maxPerRow(X):
    """
    @description
      Returns the maximum value found in each row

    @arguments
      X -- 2d array of numbers

    @return
      max_per_row -- 1d array of numbers
    """
    assert len(X.shape) == 2, "should be 2d array"
    return numpy.array([max(X[row_i,:]) for row_i in range(X.shape[0])])

def scaleTo01(X, min_x, max_x):
    """
    @description
      Assuming that min_x and max_x define the min and max values for
      each row of X, then this will return values of X that are each
      scaled to within [0,1].

    @arguments
      X -- 2d array of numbers [# input vars][# samples] -- data to be scaled
      min_x -- 1d array of numbers [# input vars] -- minimum bounds of X
      max_x -- 1d array of numbers [# input vars] -- maximum bounds of X

    @return
      scaled_X -- 2d array of numbers [# input vars][# samples] -- like X,
        but each value is in [0,1] according to min_x and max_x
      
    @exceptions
      If min_x and max_x do not correspond precisely to the
      min and max values of X, that's ok, it just means that the
      output won't be precisely in [0,1]
    """
    assert len(X.shape) == 2, "X should be a 2d array"
    assert len(min_x) == len(max_x) == X.shape[0]
    for var_i in range(len(min_x)):
        assert min_x[var_i] < max_x[var_i]

    scaled_X = numpy.zeros(X.shape)
    for var_i in range(X.shape[0]):
        scaled_X[var_i,:] = (X[var_i,:] - min_x[var_i]) / \
                            (max_x[var_i] - min_x[var_i])

    return scaled_X
    

def distance(x1, x2):
    """
    @description
      Returns the euclidian distane between x1 and x2

    @arguments
      x1, x2 -- 1d array [input variable #] -- input points

    @return
      d -- float -- the distance

    @notes
      Does _not_ scale to a [0,1] range
    """
    assert len(x1) == len(x2) > 0
    return math.sqrt( sum((x1[i] - x2[i])**2 for i in range(len(x1))) )


def epanechnikovQuadraticKernel(distance01, lambd):
    """
    @description
      A popular kernel function for local regression (and other apps).
      The smaller that 'distance' is, the closer to 1.0 the output comes.
      And if 'distance' is too large, then output is 0.0.

    @arguments
      distance01 -- float -- expect this to be scaled in [0,1]
      lambd -- float -- 'bandwidth'

    @return
      k -- float -- kernel output

    @notes
      Reference: Hastie, Tibhsirani and Friedman, 2001, page 167
    """
    t = distance01 / lambd
    if abs(t) <= 1.0:
        return 3.0/4.0 + (1.0 - t**2)
    else:
        return 0.0

def permutations(var_bases):
    """
    @description
      Returns all permutations as specified by var_bases.  

    @arguments
      var_bases -- list of int -- var_bases[i] > 0 specifies the number of
        values that this base can take on.  len(var_bases) = num vars = n

    @return
      perms -- list of perm, where perm is a list of n values, one
        for each var.  0 <= perm[var] < var_bases[var]

    @notes    
      var_bases[0] is most significant digit, and var_bases[-1] is least
        significant.
    """
    perms = []
    cur_number = [0 for base in var_bases]
    overflowed = False
    while not overflowed:
        perms.append(cur_number)
        cur_number, overflowed = baseIncrement(cur_number, var_bases)

    return perms

def baseIncrement(cur_number, var_bases):
    """
    @description
      Increments cur_number according to the base-system of 'var_bases'

      If cur_number is at its maximum possible value, and this is called,
      then (None, overflowed=True) is returned.

    @arguments
      cur_number -- list of int -- len(cur_number) = num_vars = n
      var_bases -- list of int -- var_bases[i] > 0 specifies the number of
        values that this base can take on.  len(var_bases) = n

    @return
      next_number -- list of int --
      overflowed -- bool -- only True if cur_number is at max possible value

    @notes
      Assumes that cur_number is within the proper range as specified by var_bases
    """
    if len(var_bases)==0:
        return None, True

    active_var = len(var_bases)
    next_number = copy.copy(cur_number)
    next_number[active_var-1] += 1
    while True:
        if next_number[active_var-1] >= var_bases[active_var-1]:
            next_number[active_var-1] = 0
            active_var -= 1
            if active_var-1 < 0:
                return None, True
            next_number[active_var-1] += 1
        else:
            break

    return next_number, False
    
def uniquifyVector( v):
    """
    @description
      Returns a vector which has no duplicate entries.

    @arguments
      v -- 1d array -- 

    @return
      unique_v -- 1d array
    """
    return numpy.array(sorted(set(v)))



                          

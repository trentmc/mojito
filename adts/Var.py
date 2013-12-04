"""
Holds:
-VarMeta
-Var
"""
import math
import types
import random

import numpy

from util import mathutil

class VarMeta:
    """
    @description
      Abstract class describing the space for a single variable, which can be
      continuous or discrete.
      
    @attributes
      name -- string -- the variable's name
      use_eq_in_netlist -- bool -- when doing SPICE netlisting, use an '=' ?
    """
    
    def __init__(self, name=None, use_eq_in_netlist=True):
        """        
        @arguments        
          name -- string -- name for the var. If None, then a name is
            auto-generated which will have the word 'auto' in it.
            For SPICE vars, this must be the SPICE name, e.g. 'R' for resistors.
            
          use_eq_in_netlist -- bool -- use '=' (vs ' ') when SPICE netlisting
            (only matters for PointMetas on AtomicParts)
        
        @return
          VarMeta           
        """ 
        if name is None:
            self.name = VarMetaNameFactory().create()
        else:
            if not isinstance(name, types.StringType):
                raise ValueError("'name' %s is not a string" % name)
            self.name = name

        assert isinstance(use_eq_in_netlist, types.BooleanType)
        self.use_eq_in_netlist = use_eq_in_netlist

    def __eq__(self, other):
        """
        @description
          Abstract.
          Override '==' operator          
        """
        raise NotImplementedError("implement in child")
    
    def __ne__(self, other):
        return not self.__eq__(other)
        
    def __str__(self):
        raise NotImplementedError('Implement in child')

    def spiceNetlistStr(self, scaled_var_value):
        """
        @description
          Gives string version of this var that can be used in SPICE.
        
        @arguments
          scaled_var_value -- float or int -- _scaled_ value of the variable
        
        @return
          SPICE_string_rep -- string
    
        @notes        
          Assumes scaling (and railing / binning) has already been done!
        """ 
        if self.use_eq_in_netlist: eq_s = '='
        else: eq_s = ' '
        s = '%s%s%g' % (self.name, eq_s, scaled_var_value)
        return s
        
    def railbinUnscaled(self, unscaled_var_value):
        """
        @description
          Abstract.
          If continuous, rails the var if necessary.
          If discrete var, bins the var if necessary.
          Does NOT scale!  Does NOT check to see if it's truly unscaled before.
        
        @arguments
          unscaled_var_value -- float or int --
        
        @return
          railbinned_unscaled_value -- float or int --           
        """ 
        raise NotImplementedError('Implement in child')

    def scale(self, unscaled_var_value):
        """
        @description
          Abstract.
          Scales the input value.
        
        @arguments
          unscaled_var_value -- float or int
        
        @return
          scaled_var_value -- float or int          
        """ 
        raise NotImplementedError('Implement in child')
        
    #def railbinThenScale(self, unscaled_var_value):
    #    raise NotImplementedError('Implement in child')

    def unscale(self, scaled_var_value):
        """
        @description
          Abstract.
          Unscales the input value.
        
        @arguments
          scaled_var_value -- float or int
        
        @return
          unscaled_var_value -- float or int          
        """ 
        raise NotImplementedError('Implement in child')

    def createRandomUnscaledVar(self):
        """
        @description
          Draw an unscaled var, with uniform bias, from the 1-d space
          described by this VarMeta.
        
        @arguments
          <<none>>
        
        @return
          unscaled_var -- float or int (depending if Continuous or Discrete)
        
        @notes
          Abstract.
        """
        raise NotImplementedError('Implement in child')

    def mutate(self, unscaled_var_value, stddev):
        """
        @description
          Abstract.
          Mutates the var value.
        
        @arguments
          unscaled_var_value -- float (depending on if Cont or Discrete)
          stddev -- float  in [0,1] -- amount to vary the float or int;
            0.0 means no vary, 0.05 or 0.01 is reasonable, 1.0 is crazy vary.
        
        @return
          unscaled_var_value -- float (depending on if Cont or Discrete)
        
        @notes
          The returned value will be binned and scaled appropriately.
        """ 
        raise NotImplementedError('Implement in child')
        
        
class ContinuousVarMeta(VarMeta):
    """
    @description
      A VarMeta that is continuous, i.e. has an infinite number of
      possible values (within a bounded range).
      
    @attributes    
      name -- string -- the variable's name
      use_eq_in_netlist -- bool -- when doing SPICE netlisting, use an '=' ?
      
      logscale -- bool -- is scaled_value = 10**unscaled_value ?  Tells
        how to scale the var.
      min_unscaled_value -- float or int -- lower bound
      max_unscaled_value -- float or int -- upper bound.  With min_unscaled_value
        tells how to rail the var.
      
    @notes
      min_unscaled_value and max_unscaled_value define how to rail the var.      
    """
    
    def __init__(self, logscale, min_unscaled_value, max_unscaled_value,
                 name=None, use_eq_in_netlist=True):
        """        
        @arguments
          logscale -- bool -- is scaled_value = 10**unscaled_value ?
          min_unscaled_value -- float or int -- lower bound
          max_unscaled_value -- float or int -- upper bound
          name -- string -- see doc for VarMeta __init__
          use_eq_in_netlist -- bool -- see doc for VarMeta __init__
        
        @return
          ContinuousVarMeta object
        """
        VarMeta.__init__(self, name, use_eq_in_netlist)

        #validate inputs
        if not isinstance(logscale, types.BooleanType):
            raise ValueError("'logscale' must be boolean: %s" % logscale)
        if not mathutil.isNumber(min_unscaled_value):
            raise ValueError("'min_unscaled_value' must be a number: %s" %
                             min_unscaled_value)
        if not mathutil.isNumber(max_unscaled_value):
            raise ValueError("'max_unscaled_value' must be a number: %s" %
                             max_unscaled_value)
        if min_unscaled_value > max_unscaled_value:
            raise ValueError("min_unscaled_value(=%s) was > max (=%s)" %
                             (min_unscaled_value, max_unscaled_value))

        #set values
        self.logscale = logscale
        self.min_unscaled_value = min_unscaled_value
        self.max_unscaled_value = max_unscaled_value

    def __eq__(self, other):
        """
        @description
          Abstract.
          Override '==' operator          
        """
        return self.__class__ == other.__class__ and \
               self.name == other.name and \
               self.use_eq_in_netlist == other.use_eq_in_netlist and \
               self.logscale == other.logscale and \
               self.min_unscaled_value == other.min_unscaled_value and \
               self.max_unscaled_value == other.max_unscaled_value
    
    def __ne__(self, other):
        return not self.__eq__(other)
        
    def __str__(self):
        s = ''
        s += 'ContinuousVarMeta={'
        s += ' name=%s' % self.name
        s += '; logscale? %d' % self.logscale
        s += '; min/max_unscaled_value=%g/%g' % \
             (self.min_unscaled_value, self.max_unscaled_value)
        s += " ; use_'='? %s" % self.use_eq_in_netlist
        s += ' /ContinuousVarMeta}'
        return s
        
    def railbinUnscaled(self, unscaled_var_value):
        """
        @description
          Rails the unscaled input value to within
          [self.min_unscaled_var_value, self.max_unscaled_value].
          
          Does not need to 'bin' because that has no meaning for
          continuous variables (but 'bin' is in the method name
          in order to have a common interface with discreteVarMeta).
        
        @arguments
          unscaled_var_value -- float or int
        
        @return
          railbinned_unscaled_var_value -- float or int          
        """ 
        return max(self.min_unscaled_value,
                   min(self.max_unscaled_value, unscaled_var_value))

    def scale(self, unscaled_var_value):
        """
        @description
          Scales the unscaled var.
          -If self.logscale is False, returns unscaled_var_value
          -If self.logscale is True, returns 10^unscaled_var_value
        
        @arguments
          unscaled_var_value -- float or int
        
        @return
          scaled_var_value -- float or int
    
        @notes
          Does NOT rail!  (And 'bin' has no meaning of course.)
        """ 
        assert mathutil.isNumber(unscaled_var_value), unscaled_var_value
        if self.logscale:
            return 10 ** unscaled_var_value
        else:
            return unscaled_var_value

    #def railbinThenScale(self, unscaled_var_value):
    #    return self.scale( self.railbinUnscaled( unscaled_var_value ) )

    def unscale(self, scaled_var_value):
        """
        @description
          Unscales the unscaled var.
          -If self.logscale is False, returns scaled_var_value
          -If self.logscale is True, returns log10(unscaled_var_value)
        
        @arguments
          scaled_var_value -- float or int
        
        @return
          unscaled_var_value -- float or int
    
        @notes
          Provides no guarantee that the var is railed properly.
          (And 'bin' has no meaning of course.)
        """
        if self.logscale:
            try:
                return math.log10(float(scaled_var_value))
            except OverflowError:
                s = 'math range error: scaled_var_value=%g, varmeta=self=%s' %\
                    (scaled_var_value, self)
                raise OverflowError(s)
        else:
            if not mathutil.isNumber(scaled_var_value):
                raise ValueError(scaled_var_value)
            return scaled_var_value

    def createRandomUnscaledVar(self):
        """
        @description
          Draw an unscaled var, with uniform bias, from the 1-d space
          described by this VarMeta.
        
        @arguments
          <<none>>
        
        @return
          unscaled_var -- float in range [self.min_unscaled_value, self.max..]
        """
        return random.uniform(self.min_unscaled_value, self.max_unscaled_value)

    def mutate(self, unscaled_var_value, stddev):
        """
        @description
          Mutates the var value.
        
        @arguments
          unscaled_var_value -- float
          stddev -- float  in [0,1] -- amount to vary the float;
            0.0 means no vary, 0.05 or 0.01 is reasonable, 1.0 is crazy vary.
        
        @return
          unscaled_var_value -- float or int (depending on if Cont or Discrete)
    
        @notes
          The returned value will be binned and scaled appropriately.
          The input value can be out of the range.
        """
        if not (0.0 <= stddev <= 1.0):
            raise ValueError("stddev=%g is not in [0,1]" % stddev)
        
        #a fraction of the time, choose the value uniformly
        if random.random() < stddev:
            return self.createRandomUnscaledVar()
        else:
            rng = self.max_unscaled_value - self.min_unscaled_value
            new_value = random.gauss(unscaled_var_value, stddev*rng)
            new_value = self.railbinUnscaled(new_value)
            return new_value
    
class DiscreteVarMeta(VarMeta):
    """
    @description
      Describes the set of possible discrete values that a variable can take.
      
    @attributes    
      name -- string -- the variable's name
      use_eq_in_netlist -- bool -- when doing SPICE netlisting, use an '=' ?
        
      possible_values  -- list of numbers
      min_unscaled_value -- int -- always 0
      _is_choice_var -- cached value to speed isChoiceVar() calcs
      
    @notes
      An 'unscaled_value' for a discrete var is always one of the
      integers indexing into its list of possible_values.
      
      It does not use (or need) the notion of logscaling because that can
      be handled directly by values stored in the possible_values.
    """
    
    def __init__(self, possible_values, name=None, use_eq_in_netlist=True):
        """        
        @arguments
          possible_values -- list of number (float or int) -- the values
            that this var can take.  Must be sorted in ascending order.
          name -- string -- see doc for VarMeta __init__
          use_eq_in_netlist -- bool -- see doc for VarMeta __init__
        
        @return
          DiscreteVarMeta object          
        """ 
        VarMeta.__init__(self, name, use_eq_in_netlist)

        if not mathutil.allEntriesAreNumbers(possible_values):
            raise ValueError("Each value of possible_values must be a number")
        if sorted(possible_values) != possible_values:
            raise ValueError("expect possible_values to be sorted")
        
        #DO NOT have the following check, because we want to be able
        # to add possible values after creation of the DiscreteVarMeta
        #if len(possible_values) == 0:
        #    raise ValueError("need >0 possible values")
        
        self.possible_values = possible_values
        
        self.min_unscaled_value = 0
        self._is_choice_var = None

    def __eq__(self, other):
        """
        @description
          Abstract.
          Override '==' operator          
        """
        return self.__class__ == other.__class__ and \
               self.name == other.name and \
               self.use_eq_in_netlist == other.use_eq_in_netlist and \
               self.possible_values == other.possible_values
    
    def __ne__(self, other):
        return not self.__eq__(other)

    def _maxUnscaledValue(self):
        """
        @description        
          Helper func to implement self.max_unscaled_value such
          that it's always correct.  Works in conjucntion with a
          property() call (see below) to achieve this functionality.
        
        @arguments
          <<none>>
        
        @return
          max_unscaled_value -- int
        """ 
        return len(self.possible_values) - 1
    max_unscaled_value = property(_maxUnscaledValue)
        
    def __str__(self):
        s = ''
        s += 'DiscreteVarMeta={'
        s += ' name=%s' % self.name
        
        n = len(self.possible_values)
        ndisp = 6
        s += '; # possible values=%d' % n
        s += '; possible_values=['
        for i,possible_value in enumerate(self.possible_values[:ndisp]):
            s += '%.3g' % possible_value
            if i < ndisp-1: s += ', '
        if n > ndisp+1: s += ', ...'
        if n > ndisp:   s += ', %.2g' % self.possible_values[-1]
        s += ']'
        s += '; min/max_unscaled_value=%g/%g' % \
             (self.min_unscaled_value, self.max_unscaled_value)
        s += ' /DiscreteVarMeta}'
        return s

    def addNewPossibleValue(self, scaled_var_value):
        """
        @description
          Add another possible value.  It will ensure that the
          possible values stay sorted.  Note that if there are
          existing unscaled_points, then they may end up referring to a
          different value now!  That can be avoided by scaling them first
        
        @arguments
          scaled_var_value -- float or int -- new value to add
        
        @return
          <<none>> but updates self.possible_values          
        """ 
        assert scaled_var_value not in self.possible_values
        assert mathutil.isNumber(scaled_var_value)
        self.possible_values = sorted(self.possible_values + [scaled_var_value])
        
        self._is_choice_var = None
        #self.max_unscaled_value does not need updating because it's a
        # function of self.possible_values
        
    def railbinUnscaled(self, unscaled_var_value):
        """
        @description
          Bins the var to closest allowable integer (index) value
        
        @arguments
          unscaled_var_value -- int --
        
        @return
          railbinned_unscaled_var_value -- int --
        """ 
        max_index = len(self.possible_values) - 1
        index = int(round(unscaled_var_value))
        index = max(0, min(max_index, index))
        return index

    def scale(self, unscaled_var_value):
        """
        @description
          Returns self.possible_values[unscaled_var_value]
        
        @arguments
          unscaled_var_value -- int --          
        
        @return
          scaled_var_value -- float or int --    
        """
        return self._railbinThenScale(unscaled_var_value) #safer 
 
    def _railbinThenScale(self, unscaled_var_value):
        """
        @description
          Helper function which railbins, then scales, the input value.
        
        @arguments
          unscaled_var_value -- int
        
        @return
          railbinned_scaled_var_value -- float or int
        """ 
        unscaled_val = self.railbinUnscaled(unscaled_var_value)
        safe_index = unscaled_val
        try:
            scaled_val = self.possible_values[safe_index]
        except:
            import pdb; pdb.set_trace()
            scaled_val = self.possible_values[safe_index]            
        return scaled_val

    def unscale(self, scaled_var_value):
        """
        @description
          Unscales the scaled input value.

          Returns the index corresponding to the item that
          self.possible_values that scaled_var_value is closest
          to in non-log space
          Example:
           If self.possible_values = [10,100,1000] and scaled_var_value = 400
           then unscaled_var_value = 1 (corresponding to varval = 100, NOT 1000)
        
        @arguments
          scaled_var_value -- float or int --    
        
        @return
          unscaled_var_value -- int          
        """
        return numpy.argmin([abs(scaled_var_value - v)
                               for v in self.possible_values])
    def isChoiceVar(self):
        """
        @description
          Is this Discrete VarMeta a 'choice' var?>
          ie are its possible values integers that are identical to it indices?
          i.e. are its possible values [0,1,2,...,n-1] ?

          Auto-detects based on its possible values.
        
        @arguments
         <<none>>
        
        @return
          is_choice_var -- bool
    
        @notes
          Caches self._is_choice_var, or uses the cache if it's there
        """
        if self._is_choice_var is not None:
            return self._is_choice_var
        
        self._is_choice_var = True
        for index, poss_value in enumerate(self.possible_values):
            if not isinstance(poss_value, types.IntType) or \
               poss_value != index:
                self._is_choice_var = False
                break

        return self._is_choice_var

    def createRandomUnscaledVar(self):
        """
        @description
          Draw an unscaled var, with uniform bias, from the 1-d space
          described by this VarMeta.
        
        @arguments
          <<none>>
        
        @return
          unscaled_var -- float or int (depending if Continuous or Discrete)
        """
        num_choices = len(self.possible_values)
        return random.randint(0, num_choices-1)

    def mutate(self, unscaled_var_value, stddev):
        """
        @description
          Mutates the var value.
        
        @arguments
          unscaled_var_value -- int
          stddev -- float  in [0,1] -- amount to vary the int;
            0.0 means no vary, 0.05 or 0.01 is reasonable, 1.0 is crazy vary.
        
        @return
          unscaled_var_value -- int (depending on if Cont or Discrete)
    
        @notes
          Does not care if the input value is not binned and scaled.
          The returned value will be binned and scaled appropriately.
        """
        #corner case:
        #'choice' vars have no concept of small change from one value to next
        if self.isChoiceVar():
            return self.createRandomUnscaledVar()

        #main case: ...
        
        #a fraction of the time, choose the value uniformly
        if random.random() < stddev:
            return self.createRandomUnscaledVar()

        #the rest of the time, change value by +1 or -1 with equal
        # probability.  (There are special cases to handle too, of course)
        else:
            unscaled_var_value = self.railbinUnscaled(unscaled_var_value)
            num_choices = len(self.possible_values)
            if num_choices == 1:
                return unscaled_var_value
            elif unscaled_var_value <= 0: #at min value
                return 1
            elif unscaled_var_value >= (num_choices-1): #at max value
                return unscaled_var_value - 1
            else:
                if random.random() < 0.5:
                    return unscaled_var_value + 1
                else:
                    return unscaled_var_value - 1
    
class VarMetaNameFactory:
    """
    @description
      Auto-generates a varmeta name, with the guarantee that each
      auto-generated name is unique compared to every other auto-generated
      name (but does NOT compare to manually generated names)
    """
    
    _name_counter = 0L
    def __init__(self):
        pass

    def create(self):
        """
        @description
          Returns an auto-created var name.
        
        @arguments
          <<none>>
        
        @return
          new_var_name -- string          
        """ 
        self.__class__._name_counter += 1
        return 'var_auto_' + str(self.__class__._name_counter)
    

REGION_LINEAR     = 0
REGION_SATURATION = 1
REGION_CUTOFF     = 2

class Incomputable(object):
    """This class is for not-yet-used values so that you don't
    accidentally invoke any mathematical operations or comparisons.
    It's safer than using 'None'.
    
    E.g. '<' is disallowed, so is +, ==, etc.
    """
    def __cmp__(self, other):
        """This is the override to disallow most, e.g. <, >, +"""
        raise ValueError("Tried to compare using an Incomputable")
    
    def __eq__(self, other):
        """Override =="""
        raise ValueError("Tried to check equality using an Incomputable")
    
    def __ne__(self, other):
        """Override !="""
        raise ValueError("Tried to check inequality using an Incomputable")
    
    def __str__(self):
        return 'INCOMPUTABLE_VALUE'
    
    def __repr__(self):
        return 'INCOMPUTABLE_VALUE'
    

class OnlyEqualityComparable(object):
    """Like the Incomputable class, except that it allows the
    operators: == and !=.
    """
    def __cmp__(self, other):
        raise ValueError("Tried to compare using an OnlyEqualityComparable")
    
    def __eq__(self, other):
        """
        Returns True only if both a and b are this class.
        """
        if self.__class__ == other.__class__:
            return True
        else:
            return False
        
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __str__(self):
        return 'ONLY_EQUALITY_VALUE'
    
    def __repr__(self):
        return 'ONLY_EQUALITY_VALUE'

class BadMetricValue(OnlyEqualityComparable):
    
    def __str__(self):
        return 'BAD_METRIC_VALUE'
    
    def __repr__(self):
        return 'BAD_METRIC_VALUE'
    
#Instantiate the constant BAD_METRIC_VALUE just once, and thus
# it can compare to itself, but not do anything else
BAD_METRIC_VALUE = BadMetricValue()

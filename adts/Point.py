"""
Defines Point and PointMeta types
"""
import types

from Var import *

class PointMeta(dict):
    """
    @description
      Defines the bounds for a space, that points can occupy.
      
    @attributes
      inherited__dict__ maps var_name : VarMeta
    """ 
    
    def __init__(self, list_of_varmetas):
        """        
        @arguments        
            list_of_varmetas -- list of VarMeta objects -- collectively
              the varmetas will fully describe the point's space
    
        @notes        
          Order does not matter in 'list_of_varmetas' as a dict
          is stored internally.          
        """ 
        dict.__init__(self,{})

        for varmeta in list_of_varmetas:
            assert varmeta.name not in self.keys(), (varmeta.name, self.keys())
            self[varmeta.name] = varmeta
    
    def addVarMeta(self, varmeta):
        """
        @description
          Add another variable (dimension) to this space.
        
        @arguments
          varmeta -- VarMeta object -- defines the new dimension
        
        @return
          <<none>>, but alters self's __dict__
        """ 
        assert varmeta.name not in self.keys(), (varmeta.name, self.keys())
        assert isinstance(varmeta, ContinuousVarMeta) or \
               isinstance(varmeta, DiscreteVarMeta)
        self[varmeta.name] = varmeta

    def __str__(self):
        s = ''
        s += 'PointMeta={'
        for i, varmeta in enumerate(self.values()):
            if len(self) > 1: s += '\n   '
            s += str(varmeta)
            if i < len(self)-1: s += ', '
            
        if len(self) > 1: s += '\n'
        s += '/PointMeta}'
        return s

    def unityVarMap(self):
        """
        @description

          Returns a dict of {varname1:varname1, varname2:varname2, ...}
          for all vars of self.
        
        @arguments

          <<none>>
        
        @return

          unity_var_map -- dict of string : string --
    
        @exceptions
    
        @notes
        """
        names = self.keys()
        return dict(zip(names, names))

    def createRandomUnscaledPoint(self):
        """
        @description
          Draw an unscaled Point, with uniform bias, from the space
          described by this PointMeta.
        
        @arguments
          <<none>>
        
        @return
          unscaled_point -- Point object
    
        @notes
          This is completely different than RndPoint.
        """
        unscaled_d = {}
        for varname, varmeta in self.items():
            unscaled_d[varname] = varmeta.createRandomUnscaledVar()

        return Point(False, unscaled_d)
        

    def spiceNetlistStr(self, scaled_point):
        """
        @description
          Returns 'scaled_point' as a SPICE-netlist ready string.
        
        @arguments
          scaled_point -- Point object -- 
        
        @return
          netlist_string -- string --
        """ 
        s = ''
        for i, (varname, scaled_varvalue) in enumerate(scaled_point.items()):
            s += self[varname].spiceNetlistStr( scaled_varvalue )
            if i < len(scaled_point)-1:
                s += ' '
        return s

    def minValuesScaledPoint(self):
        """
        @description
          Returns a scaled point, where the value of each dimension is
          its minimum value.
        
        @arguments
          <<none>>
        
        @return
          scaled_point -- Point object --
        """ 
        unscaled_d = {}
        for varname, varmeta in self.items():
            unscaled_d[varname] = varmeta.min_unscaled_value
        unscaled_p = Point(False, unscaled_d) 
        scaled_p = self.scale( unscaled_p )
        return scaled_p

    def railbin(self, unscaled_or_scaled_point):
        """
        @description

          Rails then bins the input point, which may be scaled or unscaled.
          If it was unscaled coming in, it's unscaled coming out.
          If it was scaled coming in, it's scaled coming out.
          I.e. output maintains the same scaling as input.
        
        @arguments
          unscaled_or_scaled_point -- Point --
        
        @return
          railbinned_point -- Point -- the same info as the incoming point,
            but it has been railed (brought to [min,max]) and binned
    
        @notes
          Always does the actual railing/binning in UNSCALED var space
          (very significant for logspace continuous vars and discrete vars!).
        """
        p = unscaled_or_scaled_point
        if p.is_scaled:
            unscaled_d = dict([(varname, varmeta.unscale( p[varname]) )
                               for varname, varmeta in self.items()])
            unscaled_p = Point(False, unscaled_d)
            railbinned_unscaled_p = self._railbinUnscaled( unscaled_p )
            railbinned_scaled_p = self.scale(railbinned_unscaled_p)
            return railbinned_scaled_p
        else:
            railbinned_unscaled_p = self._railbinUnscaled(p)
            return railbinned_unscaled_p
        
    def _railbinUnscaled(self, unscaled_point):
        """
        @description
          Helper function for railbin(); works only on unscaled points.
        
        @arguments
          unscaled_point -- Point object -- point needing railbinning
          
        @return
          railbinned_unscaled_point -- Point object that's been railbinned
        """ 
        ru_d = dict([(varname, varmeta.railbinUnscaled(unscaled_point[varname]))
                     for varname, varmeta in self.items()])
        return Point(False, ru_d)

    def scale(self, unscaled_or_scaled_point):
        """
        @description
          Returns a scaled version of the incoming point, which
          may or not be scaled.
        
        @arguments
          unscaled_or_scaled_point -- Point object
        
        @return
          scaled_point -- Point object
    
        @notes
          Doesn't have to do any work if the incoming point is already scaled.
        """ 
        p = unscaled_or_scaled_point
        if p.is_scaled:
            return p
        else:
            scaled_d = dict([(varname, varmeta.scale(p[varname]))
                             for varname,varmeta in self.items()])
            return Point(True, scaled_d)
            
class Point(dict):
    """
    @description
      A point in a space.  That space is often defined by PointMeta.
      Can be unscaled or scaled (keeps track of what it is).
      
    @attributes
      ID -- int -- unique ID for this point
      __dict__ -- maps var_name : var_value.  These values can all
        be scaled or unscaled.
      is_scaled -- bool -- are all the var_values scaled, or unscaled?
      
    @notes
      Each var_value may be float or int type.      
    """
    
    # Each point created get a unique ID
    _ID_counter = 0L
    
    def __init__(self, is_scaled, *args):
        """        
        @arguments
          is_scaled -- bool -- is this point scaled or unscaled?
          *args -- whatever is wanted for dict constructor.  Typically
            this is a dict of varname : var_value.
        """
        #manage 'ID'
        self._ID = self.__class__._ID_counter
        self.__class__._ID_counter += 1
        
        #validate inputs
        assert isinstance(is_scaled, types.BooleanType)

        #initialize parent class
        dict.__init__(self,*args)

        #set values
        self.is_scaled = is_scaled

    ID = property(lambda s: s._ID)
        

class EnvPoint(Point):
    """
    @description
      A Point in environmental variable space.
      
    @notes
      EnvPoints keep their own ID counters.  Which means
      that an EnvPoint may have the same ID as another non-EnvPoint;
      but it does not make them the same point!
    """ 
    _ID_counter = 0L
    
class RndPoint(Point):
    """
    @description
      A Point in random variable space.
      
    @notes    
      RndPoints keep their own ID counters.  Which means
      that an RndPoint may have the same ID as another non-RndPoint;
      but it does not make them the same point!
    """
    _ID_counter = 0L


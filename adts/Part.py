"""
A Part can either be
-an atomic 'primitive', e.g. a resistor or MOS, or
-a collection of EmbeddedParts (and therefore hierarchically composed)

Thus, a (synthesized) circuit design is a PartEmbpart holding a CompoundPart.

A 'port' is what is at the Part end of a connection.
A 'node' connects to ports (i.e. like a hyperedge), e.g. internal_nodes.
"""
import copy
import string
import types

from util import mathutil
from Metric import Metric
from Point import *
from Schema import Schema, Schemas

import logging
log = logging.getLogger('part')


def switchAndEval(case, case2result):
    """
    @description
      This is an on-the-fly 'switch' statement, where 'case' is like
      the argument to a hardcoded case statement, and 'case2result'
      is what replaces the hardcoded statement itself.

      Example: 
      -case2result == {3:'4.2', 'yo':'7+2', 'p':'1/0', 'default':'400/9'}
      -then the equivalent hardcoded behavior would be:
      
       if case == 3:      return 4.2
       elif case == 'yo': return 9
       elif case == 'p':  return 1/0 (which raises a ZeroDivisionError!)
       else:              return 1000.0
       
      -so if the input was 3 then it would return 4.2
      -note the use of the special key 'default', for default behavior

    @arguments
      case -- a comparable_value, usually one of the key values in case2result
      case2result -- dict of comparable_value : result_value, ie case : result

    @return
      result -- one of the result_values in case2result

    @notes
      It will not complain that there is a missing 'default' unless it
      does not find another key in case2result that matches 'case'.
    """
    if case2result.has_key(case):
        return eval(case2result[case])
    else:
        return eval(case2result['default'])

class WireFactory:
    """
    @description
      Builds singleton wire Parts.  (Because sometimes it's useful
      to treat a wire as a part, e.g. where you have a choice of a 2-port part
      or a short circuit).
      
    @attributes
      _wire_part -- Part object -- 
    """
    _wire_part = None
    
    def build(self):
        """
        @description
           Returns a singleton wire Part.
           If that Part has never been built, it builds it and caches it
           into self._wire_part, and returns it.  Otherwise just returns it.
        
        @arguments
          <<none>>
        
        @return
          wire_part -- Part object
    
        @notes
          The wire part is currently implemented as a resistor with
          zero resistance.          
        """ 
        wire_part = self.__class__._wire_part
        if wire_part is None: 
            res_pointmeta = PointMeta( [ContinuousVarMeta(False, 0,0, 'R')] )
            res_part = AtomicPart('R', ['1','2'], res_pointmeta, name='wire_res')

            wire_part = CompoundPart(['1','2'], PointMeta({}), 'wire')
            wire_part.addPart(res_part, {'1':'1', '2':'2'}, {'R':0.0} )
            self.__class__._wire_part = wire_part
        return wire_part


class FunctionDOC:
    """
    @description
      FunctionDOC = Function-based Device Operating Constraint.
      
      E.g. to ensure that transistors stay in their proper operating region etc.
      'Function' DOCs can be measured with functions, ie without simulation.

    @attributes
      metric -- Metric object -- the metric associated with the DOC.  Should not
        have an objective on it.
      function_str -- string -- to compute the metric value from an
        input scaled_points dict.  Example: '(W - L)*2'
    """
    def __init__(self, metric, function_str):
        """
        @arguments        
          metric -- Metric object -- see class description
          function_str -- string -- ''
        
        @return
          new_probe -- Probe object
        """
        #validate inputs
        if not isinstance(metric, Metric):
            raise ValueError(metric.__class__)
        if metric.improve_past_feasible:
            raise ValueError("no objectives allowed on DOC metric")
        if not isinstance(function_str, types.StringType):
            raise ValueError(function_str.__class__)

        #set attributes
        self.metric = metric
        self.function_str = function_str

    def resultsAreFeasible(self, scaled_point):
        """
        @description
          Is 'scaled_point' feasible?
        
        @arguments
          scaled_point -- Point object
        
        @return
          feasible -- bool
        """
        metric_value = evalFunction(scaled_point, self.function_str)
        return self.metric.isFeasible(metric_value)

class SimulationDOC:
    """
    @description
      Simulation DOC = Device Operating Constraint found by simulation.
      E.g. to ensure that transistors
      stay in their proper operating region etc.

    @attributes
      metric -- Metric object -- the metric associated with the DOC.  Should not
        have an objective on it.
      function_str -- string -- to compute the metric value from an 
        input lis_results dict.  Example: '(vgs - vt)*2' 
    """
    def __init__(self, metric, function_str):
        """        
        @arguments        
          metric -- Metric object -- see class description
          function_str -- string -- ''
        
        @return
          new_probe -- Probe object
    
        @notes
          We only allow lowercase letters in function_str so that
          it matches up more readily with SPICE-simulation-extracted info.
        """
        #validate inputs
        if not isinstance(metric, Metric):
            raise ValueError(metric.__class__)
        if metric.improve_past_feasible:
            raise ValueError("no objectives allowed on DOC metric")
        if not isinstance(function_str, types.StringType):
            raise ValueError(function_str.__class__)
        if function_str != string.lower(function_str):
            raise ValueError("function_str needs to be lowercase: %s" %
                             function_str)

        #set attributes
        self.metric = metric
        self.function_str = function_str

    def resultsAreFeasible(self, lis_results, device_name):
        """
        @description
          Are 'lis_results' feasible for this DOC on the specified device?
        
        @arguments
          lis_results -- dict of 'lis__device_name__measure_name' : lis_value 
          device_name -- name of the device that we're interested in
        
        @return
          feasible -- bool
        """
        metric_value = self.evaluateFunction(lis_results, device_name)
        return self.metric.isFeasible(metric_value)

    def evaluateFunction(self, lis_results, device_name):
        """
        @description
          Evaluate the value of 'lis_results' on the specified device
        
        @arguments
          lis_results -- dict of 'lis__device_name__measure_name' : lis_value --
            Note that this will contain many device names that are not
            equal to the next argument ('device_name')
          device_name -- name of the device that we're interested in evaluating
            this DOC on
        
        @return
          evaluated_value -- float (or int)
    
        @notes
          WARNING: because 'lis_results' are extracted from a SPICE output
           and SPICE puts everything to lowercase, we lowercase the device_name
           within this routine.  
        """
        #Build up a lis_point that function_str can interpret
        #Example: 'lis__INSTANCENAME__vgs' => 'vgs', wherever INSTANCENAME
        # matches device_name
        device_name = string.lower(device_name)
        lis_point = {}
        for big_lis_name, lis_value in lis_results.items():
            prefix = 'lis__' + device_name + '__'
            if prefix == big_lis_name[:len(prefix)]:
                lis_name = big_lis_name[len(prefix):]
                lis_point[lis_name] = lis_value

        #Now evaluate it!
        value = evalFunction(lis_point, self.function_str)

        #Done
        return value


class Part:
    """
    @description
      A Part can be an atomic 'primitive', e.g. a resistor or MOS,
      or it can be built up by other types of parts, eg CompoundPart.
      (The Part class is abstract.)
  
      Note that because non-Atomic Parts have point_meta
      rather than just variable names, it means that they bound
      variables from its higher level, but also there will be other
      bounds as values get computed going towards the bottom AtomicParts.
      E.g.: a higher-level 'Vbias' may be more constraining than
      the lowest-level 'DC' voltage.
        
      But it can be the other way too, e.g. a higher-level multiplier 'K'
      may be less constraining than the 'K' on a specific type of current
      mirror.  Or a higher level 'W*L' variable is still subject
      to lower-level constraints on 'W' and 'L' individually.
      
    @attributes
      name -- string -- this part's name
      point_meta -- PointMeta object -- defines the variable names and ranges
        that this part has

      function_DOCs -- list of DOC -- these are the DOCs that can
        be found merely by evaluating a funcion (no simulation necessary).
        Work for any level of Part, not just atomic parts.
        Can be very nice for quickly determining if a circuit will
        be feasible, without doing simulation.
        Example: have Vgs-0.4 > 0.2 on
        an operating-point driven formulation where Vgs is a var in the
        part's point_meta and 0.4 / 0.2 are approximations of Vgs / Vod.
        
      simulation_DOCs -- list of DOC -- these are DOCs that will be found
        on AtomicParts during simulation.

      probes -- list of Probe -- used for measuring and constraining
        device operating conditions
      
      _external_portnames -- list of string -- names for each port that is
        visible to other parts that use this.  Order is important.
        
      _internal_nodenames -- list of string -- names for each node that
        is defined internally by this Part.  Order is important

      _summary_str_tuples -- list of (label, func_str) -- these can
        be set such that additional info is put at the beginning of a netlist
        See summaryStr().
      
    @notes
      Each Part created get a unique ID.  This is implemented
      by the class-level attribute '_ID_counter' in combination with
      the 'ID' property() call.

      Methods that all Parts provide:
        externalPortnames() : list of string
        internalNodenames() : list of string
        embeddedParts(scaled_point) : part_list
        internalNodenames(scaled_point) : name_list
        portNames() : list of string
        unityVarMap() : dict of varname : varname
        unityPortMap() : dict of {ext_port1:ext_port1, ext_port2:ext_port, ...}
        __str__() : string
        str2(tabdepth) : string
    """ 
    _ID_counter = 0L
            
    def __init__(self, external_portnames, point_meta, name=None):
        """        
        @arguments        
          external_portnames -- list of strings (order is important!!) --
            names for each port that is visible to other parts that use this
          point_meta -- PointMeta object -- describes varnames & ranges that
            this part has
          name - string -- this part's name; auto-generated if 'None' is input
        
        @return
          new_part -- Part object
        """
        self._ID = self.__class__._ID_counter
        self.__class__._ID_counter += 1

        assert mathutil.allEntriesAreUnique(external_portnames)
        self._external_portnames = external_portnames

        self._internal_nodenames = []

        assert isinstance(point_meta, PointMeta)
        self.point_meta = point_meta

        if name is None:
            self.name = 'part_ID' + str(self.ID)
        else:
            assert isinstance(name, types.StringType)
            self.name = name

        self.function_DOCs = []
        self.simulation_DOCs = []

        self._summary_str_tuples = []

    ID = property(lambda s: s._ID)

    def addFunctionDOC(self, function_DOC):
        """
        @description
          Adds DOC_instance to self.function_DOCs
        
        @arguments
          function_DOC -- FunctionDOC object
        
        @return
          <<none>>
        """
        assert isinstance(function_DOC, FunctionDOC)
        self.function_DOCs.append(function_DOC)

    def addSimulationDOC(self, simulation_DOC):
        """
        @description
          Adds DOC_instance to self.simulation_DOCs
        
        @arguments
          simulation_DOC -- SimulationDOC object
        
        @return
          <<none>>
        """
        assert isinstance(simulation_DOC, SimulationDOC)
        self.simulation_DOCs.append(simulation_DOC)

    def externalPortnames(self):
        """
        @description
          Returns a list of self's external portnames
        
        @arguments
          <<none>>
        
        @return
          external_portnames -- list of string --
    
        @notes
          Implemented here, therefore no need to implement in children.
        """
        return self._external_portnames
        
    def internalNodenames(self):
        """
        @description
          Returns a list of self's internal nodenames.
            
        @notes        
          Abstract method -- child to implement.
        """ 
        raise NotImplementedError('implement in child')  

    def numSubpartPermutations(self):
        """
        @description
          Returns the number of possible permutations of different
          subparts, i.e. total size of the (structural part) of topology
          space for this part.
        
        @arguments
          <<none>>
        
        @return
          count -- int
        """
        return self.schemas().numPermutations()

    def schemas(self):
        """
        @description
          Returns a list of possible structures, in a compact fashion.
          Useful to count the total possible number of topologies,
          and also for a more fair random generation of individuals.
        
        @arguments
          <<none>>
        
        @return
          schemas -- Schemas object
        """
        raise NotImplementedError('implement in child')
    
    def schemasWithVarRemap(self, emb_part):
        """
        @description
          Returns the schemas that come from 'emb_part', but remapping
          the vars of that to line up with self's point_meta vars.
          Assumes that emb_part can be found in self.embedded_parts

        @arguments
          emb_part -- EmbeddedPart --
        
        @return
          schemas -- Schemas object

        @notes
          This is currently a helper function used by CompoundPart and FlexPart
        """
        remap_schemas = Schemas()
        for emb_schema in emb_part.part.schemas():
            remap_schema = Schema()
            for emb_schema_var, emb_schema_vals in emb_schema.items():
                emb_schema_func = emb_part.functions[emb_schema_var]
                if emb_schema_func in self.point_meta.keys(): #1:1 mapping
                    remap_var = emb_schema_func
                    poss_vals = emb_schema_vals
                    remap_schema[remap_var] = poss_vals
                elif isSimpleEqualityFunc(emb_schema_func):
                    remap_var1, remap_var2 = \
                                varsOfSimpleEqualityFunc(emb_schema_func)
                    assert remap_var1 != None and remap_var2 != None
                    poss_vals1 = self.point_meta[remap_var1].possible_values
                    remap_schema[remap_var1] = poss_vals1
                    
                    poss_vals2 = self.point_meta[remap_var2].possible_values
                    remap_schema[remap_var2] = poss_vals2
                elif isInversionFunc(emb_schema_func):
                    remap_var = varOfInversionFunc(emb_schema_func)
                    assert remap_var is not None
                    if emb_schema_vals == [0,1]: poss_vals = [0,1]
                    elif emb_schema_vals == [1]: poss_vals = [0]
                    elif emb_schema_vals == [0]: poss_vals = [1]
                    else: raise "shouldn't get here"
                    remap_schema[remap_var] = poss_vals
                else:
                    import pdb; pdb.set_trace()
                    raise AssertionError("general case not handled yet")
            remap_schema.checkConsistency()
            remap_schemas.append(remap_schema)
            
        remap_schemas.checkConsistency()
        return remap_schemas

    def embeddedParts(self, scaled_point):
        """       
        @description
          Returns list of embedded parts
 
        @arguments
          scaled_point -- 
        
        @return
          list of EmbeddedPart
        
        @notes             
          Abstract method -- child to implement.
        """ 
        raise NotImplementedError('implement in child') 

    def portNames(self):  
        """
        @description
          Returns list of external_port_names + internal_node_names
            
        @notes               
          Abstract method -- child to implement.   
        """ 
        raise NotImplementedError('implement in child')

    def unityVarMap(self):
        """
        @description
          Returns a dict of {varname1:varname1, varname2:varname2, ...}
          Which can be useful for the 'functions' arg of EmbeddedParts
    
        @notes
          Implemented here, therefore no need to implement in children.  
        """
        varnames = self.point_meta.keys()
        return dict(zip(varnames, varnames))

    def unityPortMap(self):
        """
        @description        
          Returns a dict of {ext_port1:ext_port1, ext_port2:ext_port, ...}
          Which can be useful for the 'connections' arg of Embedded Parts
    
        @notes
          Implemented here, therefore no need to implement in children.  
        """
        ports = self.externalPortnames()
        return dict(zip(ports, ports))

    def __str__(self):
        raise NotImplementedError('implement in child')

    def str2(self, tabdepth):
        raise NotImplementedError('implement in child')

    def summaryStr(self, scaled_point):
        """This is helpful for quickly identifying the structural
        characteristics of a netlist defined by the point of this Part."""
        if len(self._summary_str_tuples) == 0: return ''
        s = '\n* ==== Summary for: %s ====\n' % self.name
        for label, func_str in self._summary_str_tuples:
            if func_str == '':
                s += '* %s\n' % label
            else:
                s += '* %s = %s\n' % (label, evalFunction(scaled_point,func_str))
        s += '* ==== Done summary ====\n\n'
        return s

    def addToSummaryStr(self, label, func_str):
        self._summary_str_tuples.append((label, func_str))
        
class AtomicPart(Part):
    """
    @description
      An AtomicPart can be instantiated directly as a SPICE primitive
      
    @attributes        
      spice_symbol -- string -- what's used in SPICE netlisting;
        e.g. 'R' for resistor and 'G' for vccs
      external_portnames -- see Part
      point_meta --  see Part
      model_name -- string -- if this needs a SPICE model name, this is it
        e.g. mos models need this; they're foundry-dependent
      name -- string -- see Part    
    """

    def __init__(self, spice_symbol, external_portnames,
                 point_meta,  model_name = None, name = None):
        """        
        @arguments        
          spice_symbol -- string -- what's used in SPICE netlisting
          external_portnames -- see Part
          point_meta --  see Part
          model_name -- string -- if this needs a SPICE model name, this is it
          name -- string -- see Part
        """
        Part.__init__(self, external_portnames, point_meta, name)
        assert isinstance(spice_symbol, types.StringType)
        assert len(spice_symbol) == 1
        self.spice_symbol = spice_symbol
        if model_name is None:
            self.model_name = ''
        else:
            assert isinstance(model_name, types.StringType)
            self.model_name = model_name

    def internalNodenames(self):
        """
        @description
          Returns a list of self's internal nodes.

          Because this is an AtomicPart, the list is empty.
        
        @arguments
          <<none>>
        
        @return
          internal_nodenames -- list of string --
        """ 
        return []
    
    def schemas(self):
        """
        @description
          Returns a list of possible structures, in a compact fashion.
          Useful to count the total possible number of topologies,
          and also for a more fair random generation of individuals.
        
        @arguments
          <<none>>
        
        @return
          schemas -- Schemas object
        """
        return Schemas([Schema()])

    def embeddedParts(self, scaled_point):
        return []

    def portNames(self):
        return self.externalPortnames() + self.internalNodenames()
    
    def __str__(self):
        return self.str2()
        
    def str2(self, tabdepth=0):
        s = ''
        s += tabString(tabdepth)
        s += 'AtomicPart={'
        s += ' name=%s' % self.name
        s += '; ID=%s' % self.ID
        s += '; spice_symbol=%s' % self.spice_symbol
        s += '; external_portnames=%s' % self.externalPortnames()
        s += '; model_name=%s' % self.model_name
        s += '; point_meta=%s' % self.point_meta
        s += ' /AtomicPart} '
        return s

        
class CompoundPart(Part):
    """
    @description

      A CompoundPart is a collection of other parts and
      their connections.  It can have internal ports.  It cannot be directly
      instantiated directly as a spice primitive.

      After __init___, a CompoundPart has no embedded parts/connections or
      internal nodes.  New parts/connections are embedded via addPart(),
      and new internal nodes are added via addInternalNode().
    """

    def __init__(self, external_portnames, point_meta, name = None):
        """        
        @arguments        
          external_portnames -- see Part.  Remember, it's only the ports that
            the outside world sees, not internal nodes.
          point_meta -- see Part.
          name -- see Part
        
        @return
          new_compound_part -- CompoundPart object
        """
        Part.__init__(self, external_portnames, point_meta, name)

        # Each entry of embedded_parts is an EmbeddedPart.
        # Order is not important, _except_ to make netlisting consistent.
        self.embedded_parts = [] 
    
    def addInternalNode(self):
        """
        @description
          Adds a new internal port, and returns its name.
        
        @arguments
          <<none>>
        
        @return
          name -- string -- name of new internal port
    
        @notes
          Modifies self.
        """
        name = NodeNameFactory().build()
        self._internal_nodenames.append(name)
        return name

    def addPart(self, part_to_add, connections, functions):
        """
        @description
          Adds part_to_add to this Part using connections / functions as
          the 'how to add'.
        
        @arguments        
          part_to_add -- Part object -- a description of the sub-part to add
          connections --
            -- dict of part_to_add_ext_portname : self_intrnl_or_ext_portname --
            -- how to wire part_to_add's external ports from
            self's external_ports or self's internal_nodes. 
          functions --
            -- dict of subpart_to_add_varname : str_func_of_self_var_names
            -- stores how to compute sub-part_to_add's vars from self.
            
        @return
          <<nothing>>
        """ 
        for sub_port, self_port in connections.items():
            if self_port not in self.portNames():
                raise ValueError("self_port=%s not in self.portnames=%s" %
                                 (self_port, self.portNames()))
        for var_name, function in functions.items():
            if function == 'IGNORE':
                raise ValueError('Forgot to specify the function for var: %s'%
                                 var_name)
                                                         
        embpart = EmbeddedPart(part_to_add, connections, functions)
        self.embedded_parts.append(embpart)
        
        validateFunctions(functions, self.point_meta.minValuesScaledPoint())

    def internalNodenames(self):
        """
        @description
          Returns a list of self's internal nodes.

          Because this is an AtomicPart, the list is empty.
        
        @arguments
          <<none>>
        
        @return
          internal_nodenames -- list of string --
        """ 
        return self._internal_nodenames
    
    def schemas(self):
        """
        @description
          For this CompoundPart, returns a list of possible structures,
          in a compact fashion (i.e. effectively a list of Schema objects).
          
          Useful to count the total possible number of topologies,
          and also for a more fair random generation of individuals.
        
        @arguments
          <<none>>
        
        @return
          schemas -- Schemas object
        """
        #gather the schemas per emb part, and keep a count per emb part
        num_schema_per_emb_part = [] # emb_part_i : num_schema
        remapped_emb_schemas = [] # list of Schemas objects
        for emb_part in self.embedded_parts:
            next_remap_schemas = self.schemasWithVarRemap(emb_part)
            remapped_emb_schemas.append(next_remap_schemas)
            num_schema_per_emb_part.append( len(next_remap_schemas) )

        #now build up the actual schemas, by permuting the groups
        # of schemas.  Variables may implicitly merge; that's ok.
        schemas = Schemas()

        perms = mathutil.permutations(num_schema_per_emb_part)
        for perm in perms:
            #perm[emb_part_i] = schema_j means chosen schema_j for emb_part_i
            new_schema = Schema()
            for emb_part_i, schema_j in enumerate(perm):
                #FIXME: possible bug here!!
                new_schema.update( remapped_emb_schemas[emb_part_i][schema_j] )
            new_schema.checkConsistency()
            schemas.append( new_schema )

        #sometimes the groups can be merged further.  Do it.
        schemas.merge() 

        return schemas
    

    def embeddedParts(self, scaled_point):
        """
        @description
          Returns the embedded parts that arise when 'scaled_point' is input. 
        
        @arguments
          scaled_point -- Point object -- 
        
        @return
          embedded_parts -- list of EmbeddedPart objects
    
        @notes
          It takes in scaled_point in order to maintain a consistent
          interface with other Parts, which actually need such an input
          in order to determine the current embedded parts (e.g. FlexPart).
          But for this part (CompoundPart) it actually does not use scaled_point.          
        """ 
        return self.embedded_parts
    
    def portNames(self):
        """
        @description
          Returns a concatenated list of external portnames and internal
          nodenames.
        
        @arguments
          <<none>>
        
        @return
          port_names -- list of string
        """ 
        return self.externalPortnames() + self.internalNodenames()
    
    def __str__(self):
        return self.str2()
        
    def str2(self, tabdepth=0):
        """
        @description
          'Nice' tabbed string object.  
        
        @arguments
          tabdepth -- int -- how deep in the hierarchy are we, and therefore
            how many tabs do we want to space our output?
        
        @return
          string_rep -- string
    
        @notes
          This is not directly implemented in str() because we wanted
          the extra argument of 'tabdepth' which makes it easier
          to figure out hierarchy of complex Parts.
        """ 
        s = ''
        s += tabString(tabdepth)
        s += 'CompoundPart={'
        s += ' ID=%s' % self.ID
        s += "; name='%s'" % self.name
        s += '; externalPortnames()=%s' % self.externalPortnames()
        s += '; point_meta=%s' % self.point_meta
        s += '; # embedded_parts=%d' % len(self.embedded_parts)
        s += '; actual embedded_parts: '

        if len(self.embedded_parts) == 0: s += '(None)'
        else: s += '\n'

        for embpart in self.embedded_parts:
            descr_s = "('%s' within '%s')(ID=%d within ID=%d) :" % \
                      (embpart.part.name, self.name,
                       embpart.part.ID, self.ID)
            
            s += '\n%ssub-EMBPART: %s \n%s%s' % \
                 (tabString(tabdepth), descr_s, ' '*(tabdepth+1), embpart)
            
            s += '\n%sPART of sub-embpart: %s \n%s' % \
                 (tabString(tabdepth), descr_s, embpart.part.str2(tabdepth+1))

            s += '\n'

        s += tabString(tabdepth)
        s += ' /CompoundPart (ID=%s)} ' % self.ID
        return s

class FlexPart(Part):
    """
    @description
      A FlexPart can implement one of many sub-parts, depending on
      the value that its variable 'chosen_part_index' has.

      It is akin to an 'interface' that holds all the possible implementations.
      
    @attributes
      part_choices -- list of EmbeddedPart --
      <<plus the attributes inherited from Part>>
    """

    def __init__(self, external_portnames, point_meta, name = None):
        """        
        @arguments        
          external_portnames -- see Part
          point_meta -- see Part.  Note that an extra VarMeta will be added,
            named 'chosen_part_index' and having the
            range (0,1,...,num_choices-1)
          name -- see Part
        
        @return
          FlexPart object.
        """ 
        self_point_meta = copy.deepcopy(point_meta)
        self_point_meta.addVarMeta( DiscreteVarMeta([], 'chosen_part_index') )
        
        Part.__init__(self, external_portnames, self_point_meta, name)
        self.part_choices = []

    def addPartChoice(self, part_choice_to_add, connections, functions):
        """
        @description
          Add a candidate part, returns the embedded_part created

          The external_portnames of part_choice_to_add must be
          a subset of self.externalPortnames().
        
        @arguments        
          part_choice_to_add -- Part object -- another 'part choice' 
          connections -- 
            -- dict of part_to_add_ext_portname : self_ext_portname --
            -- how to wire part_to_add's external ports from
            self's external_ports
          functions --
            -- dict of subpart_to_add_varname : str_func_of_self_var_names
            -- stores how to compute sub-part_to_add's vars from self.
            
        @notes
          The 'connections' and 'functions' arguments are identical
          to those of CompoundPart.addPart(), except for 'connections' we
          actually don't have to use all of a FlexPart's external ports and
          there are no possible internal ports of 'self' to connect to.
        """
        #This implementation is nearly identical to CompoundPart.addPart()
        for sub_port, self_port in connections.items():
            if self_port not in self.portNames():
                raise ValueError("self_port=%s not in self.portnames=%s" %
                                 (self_port, self.portNames()))
        for var_name, function in functions.items():
            if function == 'IGNORE':
                raise ValueError('Forgot to specify the function for var: %s'%
                                 var_name)
            
        for self_port in connections.values():
            assert self_port in self.portNames(), (self_port, self.portNames())
                                                         
        embpart = EmbeddedPart(part_choice_to_add, connections, functions)
        self.part_choices.append(embpart)
        
        new_v = len(self.part_choices) - 1
        self.point_meta['chosen_part_index'].addNewPossibleValue(new_v)
        
        validateFunctions(functions, self.point_meta.minValuesScaledPoint())
        return embpart

    def chosenPart(self, scaled_point):
        """
        @description
          Returns the part that's chosen according to the input point.

          Specifically: uses index = scaled_point['chosen_part_index'] to
          return self.part_choices[index]
        
        @arguments
          scaled_point -- Point object --
        
        @return
          chosen_part -- EmbeddedPart object --
        """
        assert scaled_point.is_scaled
        assert len(self.part_choices) > 0, "need to have added choices to self"
        index = scaled_point['chosen_part_index']
        return self.part_choices[index]

    def internalNodenames(self):
        """
        @description
          Returns a list of all the internal nodenames.  Because this
          is a FlexPart, that means it returns an empty list.
        
        @arguments
          <<none>>
        
        @return
          internal_nodenames -- list of string -- in this case []
        """ 
        return []

    def portNames(self):
        return self.externalPortnames() + self.internalNodenames()

    def schemas(self):
        """
        @description
          Returns a list of possible structures, in a compact fashion.
          Useful to count the total possible number of topologies,
          and also for a more fair random generation of individuals.
        
        @arguments
          <<none>>
        
        @return
          schemas -- Schemas object
        """
        #get remap_schemas, and remember which emb_part they came from
        tuples = [] #hold (emb_remap_schema, list of emb_part_i's holding it)
        for emb_part_i, emb_part in enumerate(self.part_choices):
            next_remap_schemas = self.schemasWithVarRemap(emb_part)

            for next_remap_schema in next_remap_schemas:
                #if we find an identical already-existing schema,
                # add emb_part_i to its list of emb_parts
                found_dup = False
                for tup_i,(existing_remap_schema, existing_emb_part_I) in \
                        enumerate(tuples):
                    if next_remap_schema == existing_remap_schema:
                        tuples[tup_i][1].append(emb_part_i)
                        found_dup = True
                        break
                #didn't find a duplicate, so we can create a whole new tuple
                if not found_dup:
                    tuples.append( (next_remap_schema, [emb_part_i]) )
            

        #create final schemas: add 'chosen_part_index' to each schema,
        schemas = Schemas()
        for remap_schema, emb_part_I in tuples:
            new_schema = copy.copy(remap_schema)
            new_schema['chosen_part_index'] = list(set(emb_part_I))
            new_schema.checkConsistency()
            schemas.append(new_schema)

        return schemas
    
    def embeddedParts(self, scaled_point):
        """
        @description
          Returns the embedded parts that arise when 'scaled_point' is input.

          Because this is a FlexPart, it generates the lists ON THE FLY
          according to the value of 'chosen_part_index' in scaled_point
        
        @arguments
          scaled_point -- Point object --
        
        @return
          embedded_parts -- list of EmbeddedPart objects
    
        @notes
          Being a FlexPart, the list of embedded_parts will always
          have exactly one entry.
        """
        return [self.chosenPart(scaled_point)]
    
    def __str__(self):
        return self.str2()
        
    def str2(self, tabdepth=0):
        """
        @description
          'Nice' tabbed string object.  
        
        @arguments
          tabdepth -- int -- how deep in the hierarchy are we, and therefore
            how many tabs do we want to space our output?
        
        @return
          string_rep -- string
    
        @notes
          This is not directly implemented in str() because we wanted
          the extra argument of 'tabdepth' which makes it easier
          to figure out hierarchy of complex Parts.
        """ 
        s = ''
        s += tabString(tabdepth)
        s = 'FlexPart={'
        s += ' ID=%s' % self.ID
        s += "; name='%s'" % self.name
        s += '; external_portnames=%s' % self.externalPortnames()
        s += '; point_meta=%s' % self.point_meta
        s += '; # part_choices=%d' % len(self.part_choices)
        s += '; actual part_choices: '

        if len(self.part_choices) == 0: s += '(None)'
        else: s += '\n'

        for part_choice in self.part_choices:
            descr_s = "('%s' option for '%s')(ID=%d option for ID=%d) :" % \
                      (part_choice.part.name, self.name,
                       part_choice.part.ID, self.ID)
            
            s += '\n%spart_choice EMBPART: %s \n%s%s' % \
                 (tabString(tabdepth), descr_s, ' '*(tabdepth+1), part_choice)
            
            s += '\n%sPART of part_choice: %s \n%s' % \
                 (tabString(tabdepth), descr_s,
                  part_choice.part.str2(tabdepth+1))

            s += '\n'

        s += tabString(tabdepth)
        s += ' /FlexPart (ID=%s)} ' % self.ID
        return s


class EmbeddedPart:
    """
    @description
      An EmbeddedPart holds a Part _instantiated_ in the context of
      a parent Part.  It tells how that sub part's ports are connected to
      the parent part's ports, and how to compute the sub part's variables
      from the parent's variables.
      
    @attributes    
      part - Part object -- for this sub part
      connections -- dict of self_portname : parent_portname
        -- how to wire self's external ports from parent ports
      functions -- dict of self_varname : str_func_of_parent_var_names
        -- how to compute self's variables from parent.  
    """
    _partnum = 0
    
    def __init__(self, part, connections, functions):
        """        
        @arguments
          part -- see 'attributes' section above
          connections -- see 'attributes' section above
          functions -- see 'attributes' section above
                      
        @return
          new_embedded_part -- EmbeddedPart object
    
        @notes
          If this EmbeddedPart is going to be the top-level part,
          then set the function dict's values to scaled_var_values (numbers),
          not str funcs. That's all that's needed in order to propagate
          number values to all the child blocks, thus instantiating the
          whole part.          
        """
        assert sorted(connections.keys()) == sorted(part.externalPortnames()),\
               (part.name,
                sorted(connections.keys()), sorted(part.externalPortnames()))
        for conn_value in connections.values():
            assert isinstance(conn_value, type(''))
        if sorted(functions.keys()) != sorted(part.point_meta.keys()):
            fnames, pnames = functions.keys(), part.point_meta.keys()
            extra_fnames = sorted(mathutil.listDiff(fnames, pnames))
            extra_pnames = sorted(mathutil.listDiff(pnames, fnames))
            ddd = ""
            if len(functions) > 5: ddd = "..."
            raise ValueError("Var names in 'functions' and '%s.point_meta' do "
                             "not align; \n\nextra names in 'functions'"
                             " (or missing names in %s.point_meta) = %s"
                             "\n\nextra names in %s.point_meta"
                             " (or missing names in 'functions') = %s\n"
                             "\npart.name = %s\n"
                             "\nfunctions = %s%s"
                             % (part.name,
                                part.name, extra_fnames,
                                part.name, extra_pnames,
                                part.name, functions.items()[:5], ddd ))
        
        self.part = part
        self.connections = connections
        self.functions = functions

    def numAtomicParts(self, scaled_point):
        """
        @description
          Returns the number of atomic parts in the instantiation of this
          Part defined by 'point', which overrides self.functions.
          
          Includes all child parts.
        
        @arguments
          scaled_point -- dict of varname : var_value
        
        @return
          num_parts -- int -- total number of atomic parts
    
        @notes
          Be careful: this routine modifies self.functions to be 'point'!!
        """
        assert scaled_point.is_scaled
        
        if isinstance(self.part, AtomicPart):
            return 1
        
        else: # CompoundPart or FlexPart
            emb_parts = self.part.embeddedParts(scaled_point)
            
            num_atomic_parts = 0                    
            for embpart in emb_parts:
                embpart_scaled_point = self._embPoint(embpart, scaled_point)
                num_atomic_parts += embpart.numAtomicParts(embpart_scaled_point)
                
            return num_atomic_parts

    def subPartsInfo(self, scaled_point):
        """
        @description
          Returns info about each sub part, sub-sub-part, etc.
        
        @arguments
          scaled_point -- dict of varname : var_value
        
        @return
          info_list -- list of (sub_EmbeddedPart, sub_scaled_point, \
                                toplevel_vars_used_by_sub_EmbeddedPart)

        @notes
          Be careful: this routine modifies self.functions to be 'point'!!
        """
        assert scaled_point.is_scaled
        
        if isinstance(self.part, AtomicPart):
            return [] #[(self, scaled_point, self.part.point_meta.keys())]
        
        else: # CompoundPart or FlexPart
            info_list = []
            flat_emb_parts = self.part.embeddedParts(scaled_point)

            for emb_part in flat_emb_parts:
                #prepare for recurse
                emb_scaled_point = self._embPoint(emb_part, scaled_point)

                #recurse
                emb_info_list = emb_part.subPartsInfo(emb_scaled_point)

                par_vars = self._varsUsedByEmbPart(emb_part, scaled_point)
                
                #modify recurse info such that toplevel vars are
                # for _this_ level rather than a sub-level.  Then
                # add to info_list.
                for (sub_emb_part, sub_scaled_point, sub_par_vars) in \
                        emb_info_list:
                    emb_vars_used_by_sub_emb_part = sub_par_vars
                    par_vars_used = self._varsUsedByEmbVarsOfEmbPart( \
                        emb_part, emb_vars_used_by_sub_emb_part, scaled_point)
                    tup = (sub_emb_part, sub_scaled_point, par_vars_used)
                    info_list.append(tup)
                
                #build up at this level
                tup = (emb_part, scaled_point, par_vars)
                info_list.append(tup)
                
            return info_list
        
    def transistorArea(self, scaled_point):
        """
        @description
          Returns the area of transistors in the instantiation of this
          Part defined by 'point', which overrides self.functions.
          
          Includes all child parts.
        
        @arguments
          scaled_point -- dict of varname : var_value
        
        @return
          num_parts -- int -- total number of atomic parts
        
        @notes
          Be careful: this routine modifies self.functions to be 'point'!!
        """
        assert scaled_point.is_scaled
        
        if isinstance(self.part, AtomicPart):
            if scaled_point.has_key('W') and scaled_point.has_key('L'):
                return scaled_point['W'] * scaled_point['L']
            else:
                return 0.0
        
        else: # CompoundPart or FlexPart
            emb_parts = self.part.embeddedParts(scaled_point)
            
            area = 0.0           
            for embpart in emb_parts:
                embpart_scaled_point = self._embPoint(embpart, scaled_point)
                area += embpart.transistorArea(embpart_scaled_point)
                
            return area

    def functionDOCsAreFeasible(self, scaled_point):
        """
        @description
          Returns the True only if all of this part's AND its sub-parts'
          function DOCs have been met.
        
        @arguments
          scaled_point -- Point object
        
        @return
          feasible -- bool
        """
        assert scaled_point.is_scaled
        scaled_point = self.part.point_meta.railbin(scaled_point)
        
        log.debug("  %s point: %s " % (self.part.name, scaled_point))
        
        #evaluate the function DOCs of this part
        for function_DOC in self.part.function_DOCs:
            if not function_DOC.resultsAreFeasible(scaled_point):
                log.debug("  functionDOC %s fails for part %s in point %s " % (function_DOC.metric.name, self.part.name, scaled_point))
                return False
        
        #case: AtomicPart, so no recursion and nothing left to do
        if isinstance(self.part, AtomicPart):
            pass

        # case: CompoundPart or FlexPart, so recurse
        else: 
            emb_parts = self.part.embeddedParts(scaled_point)
                    
            for embpart_i, embpart in enumerate(emb_parts):
                embpart_scaled_point = self._embPoint(embpart, scaled_point)

                f = embpart.functionDOCsAreFeasible(embpart_scaled_point)
                if not f:
                    return False
                
        return True
            

    def percentSimulationDOCsMet(self, lis_results):
        """
        @description
          Returns the percentage of the simulation DOCs that all of
          this part's devices have met.

          If there are no simulation DOCs, then returns 1.0.
        
        @arguments
          lis_results -- dict of 'lis__device_name__measure_name' : lis_value --
            used to compute DOCs higher up
        
        @return
          percent_simulation_DOCs_met -- float in [0,1]
        """
        #setup
        self.__class__._partnum = 0
        scaled_point = Point(True, self.functions)
        sim_DOCs = []

        #main call
        (success, num_passed, num_seen) = \
                  self.percentSimDOCsMet_helper(scaled_point, sim_DOCs,
                                                lis_results)
        
        #wrapup
        if not success:
            percent = 0.0
        elif num_seen == 0:
            percent = 1.0
        else:
            percent = float(num_passed) / float(num_seen)
            
        self.__class__._partnum = 0
        return percent
        
    def percentSimDOCsMet_helper(self, scaled_point0, sim_DOCs, lis_results):
        """
        @description
          Helper function for percentSimulationDOCsMet().

          Returns the percentage simulation DOCs that all of this
          part's devices have met.  If there are no DOCs, then returns 1.0.
        
        @arguments
          scaled_point0 -- Point object, i.e. dict of
            self_varname : scaled_value_computed_from_above
            -- how to assign self's vars based on values from parent;
            for here, it's only really needed to figure out the building
            blocks used, not to compute widths and lengths, etc
          sim_DOCs -- list of DOC objects -- for each building block that led
            to this part, include its DOCs.  All its DOCs have to
            ultimately be calculatable with device-level measurements
          lis_results -- dict of 'lis__device_name__measure_name' : lis_value --
            these values are compared with the DOC needs to see
            if all DOCs have been met
        
        @return
          success -- bool -- successfully found and computed?
          num_passed -- int -- number of DOCs that were met at this level and
            below.  Will be None if success is False.
          num_seen -- int -- number of DOCs that were encountered at this
            level and below.  num_seen >= num_passed.  Will be None
            if success is False.
        """
        #case: bad lis_results
        if len(lis_results) == 0 and len(sim_DOCs) > 0:
            return (False, None, None)

        assert scaled_point0.is_scaled
        scaled_point = self.part.point_meta.railbin(scaled_point0)

        num_passed, num_seen = 0, 0

        #case: AtomicPart, so we actually have to measure the sim_DOCs
        if isinstance(self.part, AtomicPart):
            new_DOCs = sim_DOCs[:] + self.part.simulation_DOCs
            name_s = self._atomicPartInstanceName(scaled_point)
            
            #subcase: it's Atomic, but not a MOS (only measure MOSes right now)
            allowed_parts = ['nmos4','pmos4','nmos4_sized','pmos4_sized']
            if not self.part.name in allowed_parts:
                assert len(new_DOCs) == 0, "shouldn't have sim_DOCs here"
                
            #subcase: it's a MOS, so test it
            else:
                for DOC_instance in new_DOCs:
                    num_passed += DOC_instance.resultsAreFeasible(lis_results,
                                                                  name_s)
                    num_seen += 1

            self.__class__._partnum += 1
            return (True, num_passed, num_seen)

        # case: CompoundPart or FlexPart, so recurse and add sim_DOCs
        else: 
            emb_parts = self.part.embeddedParts(scaled_point)
                    
            for embpart_i, embpart in enumerate(emb_parts):
                embpart_scaled_point = self._embPoint(embpart, scaled_point)

                new_DOCs = sim_DOCs[:] + self.part.simulation_DOCs
                (success, next_num_passed, next_num_seen) = \
                          embpart.percentSimDOCsMet_helper(embpart_scaled_point,
                                                           new_DOCs, lis_results)
                if not success:
                    return (False, None, None)
                num_passed += next_num_passed
                num_seen += next_num_seen
                
            return (True, num_passed, num_seen)
            
    def spiceNetlistStr(self, annotate_bb_info=False, add_infostring=False):
        """
        @description
          Returns a SPICE-simulatable netlist of self, INCLUDING all
          the child blocks and their blocks etc.  This means that if
          we call this from the very top-level block, via recursion we generate
          a SPICE netlist for the whole circuit.
        
        @arguments
          annotate_bb_info -- bool -- annotate with building block information?
        
        @return
          spice_netlist_str -- string -- a netlist of 'self' and its sub-blocks
        
        @notes
          We can get away with no needed arguments, rather than an input point,
          because 'self' is already an _instantiated_ part.  Either at this
          level or an ancestor's level, the parameters have been set as numbers.
        """
        scaled_point = Point(True, self.functions)
        
        if annotate_bb_info: bb_list = []
        else:                bb_list = None

        #reset part and node names (need this for checking unique netlists)
        self.__class__._partnum = 0 
        NodeNameFactory._port_counter = 0L 

        #do actual work
        netlist = self.spiceNetlistStr_helper(scaled_point,
                                              self.connections, bb_list)

        #reset (for safety)
        self.__class__._partnum = 0 
        NodeNameFactory._port_counter = 0L 
        
        if add_infostring:
            netlist = self.part.summaryStr(scaled_point) + netlist
        
        return netlist
        
    def spiceNetlistStr_helper(self, scaled_point0, subst_connections,
                               bb_list):
        """
        @description
          This is the worker function for spiceNetlistStr().
        
        @arguments        
          scaled_point0 -- Point object, i.e. dict of
            self_varname : scaled_value_computed_from_above
            -- how to assign self's vars based on values from parent
          subst_connections -- dict of self_ext_portname : portname_from_above
            -- tells how to substitute connections going from above
            to this level
          bb_list -- list of (Part,point) -- list of building blocks that led
            to this part.  Gets added to as it recursively dives.
            If None, ignore; else make part of netlist.
        
        @return        
          spice_netlist_str -- string
             -- if self's Part is atomic, it returns the spice string
                else returns a set of spice strings for all sub-parts
                (recursively calculated)
        """
        assert scaled_point0.is_scaled
        scaled_point = self.part.point_meta.railbin(scaled_point0)
        
        if isinstance(self.part, AtomicPart):
            #build part name string 
            name_s = self._atomicPartInstanceName(scaled_point)

            #build portnames string
            portnames = [subst_connections[port]
                         for port in self.part.externalPortnames()]
            #  -special case: dcvs has only one port
            if self.part.name == 'dcvs':
                portnames.append('0')
            ports_s = string.join(portnames)

            #build model string, vars string
            model_s = self.part.model_name
            vars_s  = self.part.point_meta.spiceNetlistStr(scaled_point)

            #build whole string
            s = name_s + ' ' + ports_s + ' ' + model_s + ' ' + vars_s + '\n'

            #handle bb_list
            if bb_list is not None:
                bb_list.append((self.part, scaled_point))
                s = self._annotatedAtomicPartStr(bb_list) + s

            #wrapup
            self.__class__._partnum += 1
            return s
        
        else: # CompoundPart or FlexPart
            emb_parts = self.part.embeddedParts(scaled_point)
            internal_nodenames = self.part.internalNodenames()
            s = ''
            global_intnl_nodenames = {}
            for nodename in internal_nodenames:
                global_intnl_nodenames[nodename] = NodeNameFactory().build()
                    
            for embpart_i, embpart in enumerate(emb_parts):
                #substitute values into funcs to make sub-point
                embpart_scaled_point = self._embPoint(embpart, scaled_point)

                #substitute ports from parent ports and this' internal ports
                embpart_subst_connections = {}
                for embpart_portname, parent_portname in \
                        embpart.connections.items():
                    if subst_connections.has_key(parent_portname):
                        subst_portname = subst_connections[parent_portname]
                    else: 
                        subst_portname = global_intnl_nodenames[parent_portname]
                    embpart_subst_connections[embpart_portname] = subst_portname

                if bb_list is None:
                    new_bb_list = None
                else:
                    new_bb_list = bb_list[:] + [(self.part, scaled_point)]
                s += embpart.spiceNetlistStr_helper(embpart_scaled_point,
                                                    embpart_subst_connections,
                                                    new_bb_list)
            return s

    def _embPoint(self, embpart, scaled_point):
        """
        @description
          Substitute scaled_point's values into embpart.functions to
          create sub-point for this embpart.

        @arguments
          embpart -- embeddedPart -- from self's computed embedded_parts
          scaled_point -- Point -- holds the values which embpart will
            use to do the computing

        @return
          embpart_scaled_point -- Point object --

        @notes        
          Helper for spice netlisting, and elsewhere.    
        """
        scaled_d = {}
        for embpart_varname, f in embpart.functions.items():
            try:
                v = evalFunction(scaled_point, f, self.part)
            except:
                s = "The call to evalFunction() broke.\n"
                s += "  We were trying to compute embedded_part_varname=%s" % \
                     embpart_varname
                s += "  The function f is: '%s\n' " % f
                s += "  The (scaled) input point which broke it was: %s\n" % \
                     scaled_point
                raise ValueError(s)
                
            assert mathutil.isNumber(v), (v, scaled_point, f)
            scaled_d[embpart_varname] = v
        scaled_p = Point(True, scaled_d)
        embpart_scaled_point = embpart.part.point_meta.railbin(scaled_p)
        return embpart_scaled_point

    def _varsUsedByEmbPart(self, embpart, scaled_point):
        """
        @description
          Returns the list of var names in 'scaled_point' that embpart depends
          on for its computations.

        @arguments
          embpart -- embeddedPart -- from self's computed embedded_parts
          scaled_point -- Point -- holds the values which embpart will
            use to do the computing

        @return
          vars_used -- list of string -- subset of variable names found
            in 'scaled_point'           
        """
        vars_used = []
        for cand_var in scaled_point.keys():
            for embpart_varname, f in embpart.functions.items():
                if functionUsesVar(cand_var, scaled_point, f, self.part):
                    vars_used.append(cand_var)
                    break
                
        return vars_used

    def _varsUsedByEmbVarsOfEmbPart(self, embpart, embvars, scaled_point):
        """Like _varsUsedByEmbPart, except only considers a subset
        of the vars of embpart"""
        for embvar in embvars:
            assert embvar in embpart.functions.keys()
        vars_used = []
        for cand_var in scaled_point.keys():
            for embpart_varname, f in embpart.functions.items():
                if embpart_varname not in embvars: continue
                if functionUsesVar(cand_var, scaled_point, f, self.part):
                    vars_used.append(cand_var)
                    break
                
        return vars_used

    def _atomicPartInstanceName(self, scaled_point):
        """Build the name string of an Atomic Part, for use
        in SPICE netlisting and maybe elsewhere"""
        assert isinstance(self.part, AtomicPart)
        
        name_s = self.part.spice_symbol
        
        #  -special case: make it easy to identify wires
        if self.part.spice_symbol=='R' and scaled_point['R']==0.0:
            name_s += 'wire'
            
        name_s  += str(self.__class__._partnum)
        return name_s

            
    def _annotatedAtomicPartStr(self, bb_list):
        """
        @description
          Helper function for netlisting with bb annotations.

          Returns a string describing the info to annotate prior
          to the actual instantiating line of an atomic part.
    
        """
        bb_s = '\n*--------------------------------------------\n'
        for level, (list_part, list_point) in enumerate(bb_list):
            bb_s += '* ' + ' '*level*2 + list_part.name + ': '
            bb_s += self._bbPointStr(list_point)
            bb_s +='\n'
        return bb_s
            
    def _bbPointStr(self, list_point):
        """
        @description
          Helper function for _annotatedAtomicPartStr()

          Returns a string describing a bb list_point that can fit onto a line.
          Tries to focus on the vars with topology info, and if there
          is still space, if adds other vars.
        """
        #set magic numbers
        max_num_vars = 700000 #magic number alert
        subvars_to_avoid = ['W','L','R','Vbias','K','C','Ids','GM','DC_V',
                            'Ibias', 'Ibias2']

        #intialize
        vars_covered = []
        s = ''

        #first priority: include chosen_part_index if it's there
        if 'chosen_part_index' in list_point.keys():
            var, val = 'chosen_part_index', list_point['chosen_part_index']
            s += '%s=%g, ' % (var, val)
            vars_covered.append(var)

        #next priority: get all vars except ones to 'avoid', up to max_num_vars
        for var, val in list_point.items():
            if len(vars_covered) >= max_num_vars: break
            if var in vars_covered: continue
            if self._doAvoidVar(var, subvars_to_avoid):
                continue
            s += '%s=%g, ' % (var, val)
            vars_covered.append(var)

        #if still space, fill up some vars that were avoided
        for var, val in list_point.items():
            if len(vars_covered) >= max_num_vars: break
            if var in vars_covered: continue
            s += '%s=%g, ' % (var, val)
            vars_covered.append(var)
            
        return s

    def _doAvoidVar(self, var, subvars_to_avoid):
        """
        @description
          Returns True if the tail characters of 'var' line up
          with any of the subvars to avoid.

        """
        for subvar in subvars_to_avoid:
            if var[-len(subvar):] == subvar:
                return True
        return False
                    
    def __str__(self):
        s = ''
        s += 'EmbeddedPart={'
        s += " partname='%s'" % self.part.name
        s += '; partID=%s' % self.part.ID
        s += '; functions=%s' % self.functions
        s += '; connections=%s' % self.connections
        s += ' /EmbeddedPart}'

        return s    


def validateFunctions(functions, scaled_point):
    """
    @description
      Validate functions by substituting scaled_point into
      the function, and ensuring that it can be then evaluated into a
      numeric value.

      Useful for making sure that a Library is defined well.

    @arguments
      functions --
        -- dict of varname : str_func_of_func_varnames
        -- stores how to compute sub-part_to_add's vars from self.
      scaled_point -- Point object -- holds a number for each func_varname
    """
    if not scaled_point.is_scaled:
        raise ValueError
    
    for embpart_varname, f in functions.items():
        #anything that calls 'part.' gets a free pass in this validation
        if isinstance(f, types.StringType) and f[:5] == 'part.':
            continue

        #but we test the rest!
        try:
            embpart_varval = evalFunction(scaled_point, f)
        except:
            s = "func to compute '%s' (='%s') is bad\n" % (embpart_varname,f)
            s += "  scaled_point=%s\n  f=%s\n" % (scaled_point, f)
            s += "  can only use vars: %s" % scaled_point.keys()
            raise ValueError(s)


_alphanumeric = '1234567890qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM_'

def evalFunction(point, func_str, part=None):
    """
    @description
      Substitutes all values of point into func_str, then return eval(func_str).
      E.g: if point is {'a':1.0, 'b':2.0} and func_str is 'b*2.0', returns 4.0.
      E.g: if func_str is merely a number, returns that number (nothing to subst)

    @arguments
      point -- Point object --
      func_str -- string --
      part -- Part object -- makes 'part' visible to eval,
        such that we can call part.REQUESTS,
        e.g. for part.approx_mos_models.estimateNmosWidth(Ids, Vs, Vd, Vbs, L)

    @exceptions
      If func_str is '', then merely return the string '' rather than a number.   
    """
    if func_str == '': return ''
    f = copy.copy(func_str)
    if mathutil.isNumber(func_str): return f
    
    try:
        #Algorithm:
        #while not out of letters:
        #  identify start of cand word
        #  identify end of cand word
        #  calc word
        #  if word is in point.keys(), replace it (otherwise assume it's a func)
        #  repeat sequence, starting from end of cand word + 1

        #while not out of letters:
        len_f = len(f)
        st = 0
        while True:
            
            #  identify start of cand word
            letters_left = True
            while True:
                if f[st] in _alphanumeric: break
                st += 1
                if st >= len_f:
                    letters_left = False
                    break
            if not letters_left: break
            
            #  identify end of cand word
            fin = st+1
            while True:
                if fin >= len_f:
                    break
                if f[fin] not in _alphanumeric: break
                fin += 1
                
            #  calc word
            word = f[st:fin]

            # if word is in point.keys(), replace it
            # (otherwise assume it's a func)
            new_st = fin + 1
            for cand_var, cand_val in point.items():
                if cand_var == word:
                    f = f[:st] + str(cand_val) + f[fin:]
                    old_len = (fin-st)
                    new_len = len(str(cand_val))
                    new_st = fin + 1 - old_len + new_len
                    len_f = len(f)
                    break
                
            #  repeat sequence, starting from end of cand word + 1
            st = new_st
            if st >= len_f:
                break

        return eval(f)
    
    except:
        s = "Encountered an error in evalFunction()\n"
        s + "orig func_str = %s\n" % func_str
        s += "point = %s\n" % point
        s += "func_str with values subst. = %s" % f
        raise ValueError(s)

def functionUsesVar(compare_var, point, func_str, part=None):
    """
    @description
      Returns True if 'func_str' uses 'compare_var',
      using similar functionality to that of evalFunction().
      
    @arguments
      compare_var -- string -- 
      <<rest>> -- see evalFunction()
    """
    if func_str == '': return False
    f = copy.copy(func_str)
    if mathutil.isNumber(func_str): return False

    try:
        #Algorithm:
        #while not out of letters:
        #  identify start of cand word
        #  identify end of cand word
        #  calc word
        #  if word is in point.keys(), replace it (otherwise assume it's a func)
        #  repeat sequence, starting from end of cand word + 1

        #while not out of letters:
        len_f = len(f)
        st = 0
        while True:
            
            #  identify start of cand word
            letters_left = True
            while True:
                if f[st] in _alphanumeric: break
                st += 1
                if st >= len_f:
                    letters_left = False
                    break
            if not letters_left: break
            
            #  identify end of cand word
            fin = st+1
            while True:
                if fin >= len_f:
                    break
                if f[fin] not in _alphanumeric: break
                fin += 1
                
            #  calc word
            word = f[st:fin]

            # found it?
            if word == compare_var:
                return True

            # if word is in point.keys(), replace it
            # (otherwise assume it's a func)
            new_st = fin + 1
            for cand_var, cand_val in point.items():
                if cand_var == word:
                    f = f[:st] + str(cand_val) + f[fin:]
                    old_len = (fin-st)
                    new_len = len(str(cand_val))
                    new_st = fin + 1 - old_len + new_len
                    len_f = len(f)
                    break
                
            #  repeat sequence, starting from end of cand word + 1
            st = new_st
            if st >= len_f:
                break

        return False
    
    except:
        s = "Encountered an error in functionUsesVar()\n"
        s + "orig func_str = %s\n" % func_str
        s += "point = %s\n" % point
        s += "func_str with values subst. = %s" % f
        raise ValueError(s)
   
def flattenedTupleList(tup_list):
    """
    @description
      Flatten the input list of tuples by returning a non-tuple list
      that has all the entries of the left-item-of-tuple, followed
      by all the entries of the right-item-of-tuple.

    @arguments
      tup_list -- shaped like [(a1,b1), (a2,b2), ...]

    @return
      flattened_list -- shaped like [a1,a2,...,b1,b2,...]
    """ 
    return [a for (a,b) in tup_list] + [b for (a,b) in tup_list]

class NodeNameFactory:
    """
    @description
      Builds unique node names.  This is helpful for internally generated
      node names.
    """

    _port_counter = 0L
    def __init__(self):
        pass

    def build(self):
        """
        @description
          Return a unique node name.

        @arguments
          <<none>>

        @return
          new_node_name -- string -- 
        """ 
        self.__class__._port_counter += 1
        return 'n_auto_' + str(self.__class__._port_counter)
    
def replaceAutoNodesWithXXX(netlist_in):
    """
    @description
      Replaces all nodes having name 'n_auto_NUM' with 'XXX'.
      Makes unit-testing easier.

    @arguments
      netlist_in -- string -- a SPICE netlist

    @return
      modified_netlist_in -- string -- 

    @notes
      Nodes with a name like 'n_auto_NUM' come from NodeNameFactory
    """ 
    netlist = copy.copy(netlist_in)
    while True:
        Istart = string.find(netlist, 'n_auto')
        if Istart == -1: break
        Iend = string.find(netlist, ' ', Istart)
        netlist = netlist[:Istart] + 'XXX' + netlist[Iend:]
    return netlist
    
def tabString(tabdepth):
    """
    @description
      Returns a string with 2 x tabdepth '.' symbols.  Used by str2().

    @arguments
      tabdepth -- int --

    @return
      tab_string -- string
    """ 
    return '.' * tabdepth * 2


def isInversionFunc(func):
    """
    @description
      Returns True if this function is of the form:
      '(1-VAR)' or '1-VAR'.  Whitespace is ignored.
    """
    v = varOfInversionFunc(func)
    return (v is not None)

def varOfInversionFunc(func):
    """
    @description
      If 'func' is of the form:
      '(1-VAR)' or '1-VAR', then it returns the name of VAR
      If it cannot find that form, then it returns None.
      Whitespace is ignored.
    """
    #remove leading and trailing whitespace
    func = string.strip(func)

    #strip brackets if they exist
    if func[0] == '(':
        assert func[-1] == ')'
        func = func[1:-1]

    #ensure whitespace is around the first '-'
    Istart = string.find(func, '-')
    if Istart == -1: return None
    func = func[:Istart] + ' - ' + func[Istart+1:]

    #split into 3 parts and analyze
    s = string.split(func)
    if len(s) != 3: return None
    if s[0] != '1': return None
    if s[1] != '-': return None
            
    return s[2]


def isSimpleEqualityFunc(func):
    """
    @description
      Returns True if this function is of the form 'VAR1 == VAR2' where
      VAR1 and VAR2 are any string.  Whitespace is ignored.
    """
    v1, v2 = varsOfSimpleEqualityFunc(func)
    return (v1 is not None)

def varsOfSimpleEqualityFunc(func):
    """
    @description
      Assuming that 'func' is a simpleEquality func of the form
      '(VAR1 == VAR2)' or 'VAR1 == VAR2',
      then this returns the var names for VAR1 and VAR2
      If it cannot find that form, then it returns (None,None)
    """
    #remove leading and trailing whitespace
    func = string.strip(func)

    #strip brackets if they exist
    if func[0] == '(':
        assert func[-1] == ')'
        func = func[1:-1]

    #ensure whitespace is around the first '==' 
    Istart = string.find(func, '==')
    if Istart == -1: return (None,None)
    func = func[:Istart] + ' == ' + func[Istart+2:]

    #split into 3 parts and analyze
    s = string.split(func)
            
    if len(s) != 3: return (None, None)
    
    return (s[0], s[2])
                                


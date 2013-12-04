"""
This is a library of building blocks that uses device sizes (W's, L's, etc), as
opposed to operating-point-driven
"""
import types
import copy
import sys
import math

import numpy

from util import mathutil

from adts import *
from util.constants import REGION_SATURATION
from Library import whoami, Library

import logging
log = logging.getLogger('problems')

def Point18SizesLibrary():
    """
    @description
      Returns a parts library for 0.18 microns.  This largely consists
      of defining the nmos and pmos model files, and vth and vdd.

    @arguments
      <<none>>

    @return
      point_18_library -- Library object
    """ 
    ss = SizesLibraryStrategy(0.18e-6, 'N_18_MM', 'P_18_MM', 1.8)
    return SizesLibrary(ss)

class SizesLibraryStrategy:
    """
    @description

      Strategy to build a Library object.

      Like most 'Strategy' classes, it tries to balance:
      -making it convenient to set commonly-changed attributes, by
       having them in the interface but maybe with default values
      -vs. hiding values which take more thought to set if they
       are used (and those are the non-default values, sometimes
       not accessible via the constructor but must be
       changed by accessing the attribute directly)

      Note that it does _not_ inherit from a class like LibraryStrategy
      (that class does not exist, and is not really useful at this point).
      
    @attributes

      Holds things like:
      -feature_size
      -nmos/pmos_modelname
      -vdd
      -min/max for R's, C's, L's, W's, Vbias's, etc
      
    @notes
    """
    
    def __init__(self, feature_size, nmos_modelname, pmos_modelname, vdd):
        """
        @arguments        
          feature_size -- float -- feature size (in m) (e.g. 0.18e-6)
          nmos_modelname -- string -- the SPICE modelname for NMOS transistor
          pmos_modelname -- string -- the SPICE modelname for PMOS transistor
          vdd -- float -- power supply voltage (in V) (e.g. 5.0)

        @return
          library_ss -- LibraryStrategy object --
        """ 
        #
        self.feature_size = feature_size
        self.nmos_modelname = nmos_modelname
        self.pmos_modelname = pmos_modelname
        self.vdd = vdd

        pico, nano, micro, milli = 1e-12, 1e-9, 1e-6, 1e-3
        kilo, mega, giga = 1e3, 1e6, 1e9

        #default values (user can change these after initialization)

        #for mos
        # -wfinger
        self.wfinger=5 * micro

        # -width
        self.min_W = 0.24 * micro
        self.max_W = 100 * micro

        # -length
        self.min_L = self.feature_size
        self.max_L = 50 * micro
        
        # -transistor device multiplier (number of fingers)
        self.min_M = 1 
        self.max_M = 100
        
        #current mirror multiplier
        self.min_K = 1 
        self.max_K = 10

        #resistance
        self.min_R = 1
        self.max_R = 10 * mega

        #capacitance
        self.min_C = 1 * pico
        self.max_C = 10 * micro

        #DC voltage source's 'DC' value
        self.min_DC_V = 0.0
        self.max_DC_V = self.vdd
                

class SizesLibrary(Library):
    """
    @description
      A 'Library' holds a set of Parts, e.g. resistors and caps all the
      way up to current mirrors and amplifiers.
      
    @attributes
      ss -- LibraryStrategy object --
      wire_factory -- WireFactory object -- builds wire Part
      _ref_varmetas -- dict of generic_var_name : varmeta.  
      _parts -- dict of part_name : Part object    
    """

    def __init__(self, ss):
        """        
        @arguments
          ss -- LibraryStrategy object --
        
        @return
          new_library -- Library object
    
        @notes
          This constructor method doesn't bother building each possible Part
          right now; rather, it defers that to a 'just in time' basis
          for the first request for a given part.  Once it builds the
          requested part, it _does_ store it in self._parts, such that
          subsequent calls for the same part do not need to rebuild the part.
        """
        Library.__init__(self)
        self.ss = ss

        #
        self.wire_factory = WireFactory()

        #'rvm' will be stored as self._ref_varmetas
        rvm = {}
        rvm['W'] = ContinuousVarMeta(False, ss.min_W, ss.max_W, 'W')
        rvm['L'] = ContinuousVarMeta(False, ss.min_L, ss.max_L, 'L')
        rvm['M'] = DiscreteVarMeta(range(ss.min_M, ss.max_M+1), 'M')
        rvm['K'] = DiscreteVarMeta(range(ss.min_K, ss.max_K+1), 'K')
        
        mn,mx = math.log10(float(ss.min_R)), math.log10(float(ss.max_R))
        rvm['R'] = ContinuousVarMeta(True, mn, mx, 'R')
        
        mn, mx = math.log10(float(ss.min_C)), math.log10(float(ss.max_C))
        rvm['C'] = ContinuousVarMeta(True, mn, mx, 'C')
        
        rvm['DC_V'] = ContinuousVarMeta(False, self.ss.min_DC_V,
                                        self.ss.max_DC_V, 'DC_V', False)
        rvm['bool_var']=DiscreteVarMeta([0,1], 'bool_var')
        for keyname, varmeta in rvm.items():
            assert keyname == varmeta.name, (keyname, varmeta.name)
        self._ref_varmetas = rvm

        self._parts = {}
    
    #====================================================================
    #====================================================================
    #Start actual definition of library parts here.  Each part's name
    # is identical to the function name.
    def nmos4(self):
        """
        Description: 4-terminal nmos
        Ports: D,G,S,B
        Variables: W,L,M
        """
        name = whoami()
        if self._parts.has_key(name):  return self._parts[name]
        part = AtomicPart('M', ['D', 'G', 'S', 'B'],
                          self.buildPointMeta(['W','L','M']),
                          self.ss.nmos_modelname, name)
        self._parts[name] = part
        return part

    def pmos4(self):
        """
        Description: 4-terminal pmos
        Ports: D,G,S,B
        Variables: W,L,M
        """
        name = whoami()
        if self._parts.has_key(name):  return self._parts[name] 
        part = AtomicPart('M', ['D', 'G', 'S', 'B'],
                          self.buildPointMeta(['W','L','M']),
                          self.ss.pmos_modelname, name)
        self._parts[name] = part
        return self._parts[name]

    def dcvs(self):
        """
        Description: DC voltage source, with reference to 0.
        Ports: NPOS  
        Variables: DC (V)

        Note: this does not need 'GND' as a port because there is a special
        check in Part.py for parts of name 'dcvs' which adds a second port
        of '0' there if seen.  This way, we get to keep all Vbias nodes
        internal, which would have otherwise been an issue esp. for cascodes.
        """
        name = whoami()
        if self._parts.has_key(name):  return self._parts[name]
        pm = self.buildPointMeta({'DC':'DC_V'})
        part = AtomicPart('V', ['NPOS'], pm, name=name)
        self._parts[name] = part
        return part
        
    def wire(self):
        """
        Description: wire as a Part.  (short circuit).
        Ports: 1,2
        Variables: (none)
        """
        wire_part = self.wire_factory.build()
        if not self._parts.has_key(wire_part.name):
            self._parts[wire_part.name] = wire_part
        return wire_part
    
    def openCircuit(self):
        """
        Description: open circuit
          Implemented as a 2-port compound part with no embedded parts.
        Ports: 1,2
        Variables: 
        """
        name = whoami()
        if self._parts.has_key(name):  return self._parts[name]
        part = CompoundPart(['1','2'], PointMeta({}), name=name)
        self._parts[name] = part
        return part
    
    def resistor(self):
        """
        Description: resistor
        Ports: 1,2
        Variables: R
        """
        name = whoami()
        if self._parts.has_key(name):  return self._parts[name]
        part = AtomicPart('R', ['1','2'], self.buildPointMeta(['R']), name=name)
        self._parts[name] = part
        return part

    def capacitor(self):
        """
        Description: resistor
        Ports: 1,2
        Variables: C
        """
        name = whoami()
        if self._parts.has_key(name):  return self._parts[name]
        part = AtomicPart('C', ['1','2'], self.buildPointMeta(['C']), name=name)
        self._parts[name] = part
        return part        

    def mos4(self):
        """
        Description: 4-terminal mos that can be pmos or nmos, depending on
          the input point's value of chosen_part_index.
          
        Ports: D,G,S,B
          
        Variables: chosen_part_index, W, L

        Variable breakdown:
          For overall part: chosen_part_index (=='use_pmos')
            0: use nmos4
            1: use pmos4
            
          wfinger=from library
          Mult=int(W/wfinger)+1
            
          For nmos4: W=W/Mult, L=L, M=Mult
          For pmos4: W=2*W/Mult, L=L, M=Mult
          
         Note: for pmos4, the effective Width is 2*W for smoothness
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]
        
        
        #parts to embed
        nmos_part = self.nmos4()
        pmos_part = self.pmos4()

        #build the point_meta (pm)
        pm = self.buildPointMeta(['W','L'])
        
        #build functions
        wfinger = str(self.ss.wfinger)
        
        nmos_functions = {'L':'L'}
        Mult = '(int((W)/(' + wfinger + '))+1)'
        Weff = 'W/(' + Mult + ')'
        
        nmos_functions['M'] = Mult
        nmos_functions['W'] = Weff
        
        pmos_functions = {'L':'L'}
        Mult = '(int((2*W)/(' + wfinger + '))+1)'
        Weff = '(2*W)/(' + Mult + ')'
        
        pmos_functions['M'] = Mult
        pmos_functions['W'] = Weff
        
        #build the main part
        part = FlexPart(['D', 'G', 'S', 'B'], pm, name)

        part.addPartChoice( nmos_part, nmos_part.unityPortMap(), nmos_functions)
        part.addPartChoice( pmos_part, pmos_part.unityPortMap(), pmos_functions)
        
        self._parts[name] = part
        return part

    def mos3(self):
        """
        Description: 3-terminal mos that can be pmos or nmos, depending on
          the input point's value of use_pmos.
          
        Ports: D, G, S
        
        Variables: W, L, use_pmos
        
        Variable breakdown:
          For mos4: W=W, L=L, use_pmos=use_pmos
          
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        mos4_part = self.mos4()

        #build the point_meta (pm)
        pm = PointMeta({})
        mos4_varmap = mos4_part.point_meta.unityVarMap()
        mos4_varmap['chosen_part_index'] = 'use_pmos'
        pm = self.updatePointMeta(pm, mos4_part, mos4_varmap)

        #build the main part
        part = CompoundPart(['D','G','S'], pm, name)
        
        part.addPart(mos4_part, {'D':'D','G':'G','S':'S','B':'S'}, mos4_varmap)
                
        self._parts[name] = part
        return part

    def saturatedMos3(self):
        """
        Description: mos3 that has to be in saturated operating region
          
        Ports: D, G, S
        
        Variables: W, L, use_pmos
        
        Variable breakdown:
          For mos3: W=W, L=L, use_pmos=use_pmos
          
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        mos3_part = self.mos3()

        #build the point_meta (pm)
        pm = PointMeta({})
        mos3_varmap = mos3_part.point_meta.unityVarMap()
        pm = self.updatePointMeta(pm, mos3_part, mos3_varmap)

        #build the main part
        part = CompoundPart(['D','G','S'], pm, name)
        
        part.addPart(mos3_part, mos3_part.unityPortMap(), mos3_varmap)

        #add DOCs (Device Operating Constraint)
        metric = Metric('operating_region', REGION_SATURATION,
                        REGION_SATURATION, False)
        function = 'region'
        doc = SimulationDOC(metric, function)
        part.addSimulationDOC(doc)
                
        self._parts[name] = part
        return part

    def mosDiode(self):
        """
        Description: MOS diode.  G is tied to D.
          
        Ports: D,S
        
        Variables: W, L, use_pmos

        Variable breakdown:
          For mos3: W=W, L=L, use_pmos=use_pmos
          
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        mos3_part = self.saturatedMos3()

        #build the point_meta (pm)
        pm = PointMeta({})
        mos3_varmap = mos3_part.unityVarMap()
        
        pm = self.updatePointMeta(pm, mos3_part, mos3_varmap)

        #build the main part
        part = CompoundPart(['D','S'], pm, name)
        
        part.addPart(mos3_part, {'D':'D','G':'D','S':'S'}, mos3_varmap)
                
        self._parts[name] = part
        return part

    def shortOrOpenCircuit(self):
        """
        Description: short circuit OR open circuit.  This can be
          useful for making flexible topologies.
          
        Ports: 1, 2
        
        Variables: chosen_part_index

        Variable breakdown:
          For overall part: chosen_part_index (=='open_circuit')
            0: use wire
            1: use openCircuit

        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        part = FlexPart(['1', '2'], PointMeta({}), name)
        part.addPartChoice( self.wire(), {'1':'1','2':'2'}, {} )
        part.addPartChoice( self.openCircuit(), {'1':'1','2':'2'}, {} )
                
        self._parts[name] = part
        return part

    def resistorOrMosDiode(self):
        """
        Description: resistor OR mosDiode
          
        Ports: D, S
        
        Variables: chosen_part_index, R, W, L, use_pmos

        Variable breakdown:
          For overall part: chosen_part_index (=='use_mosDiode')
            0: use resistor
            1: use mosDiode
          For resistor: R=R
          For mosDiode: W=W, L=L, use_pmos=use_pmos

        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        res_part = self.resistor()
        diode_part = self.mosDiode()

        #build the point_meta (pm)
        pm = PointMeta({})
        res_varmap = res_part.unityVarMap()
        diode_varmap = diode_part.unityVarMap()
        
        pm = self.updatePointMeta(pm, res_part, res_varmap)
        pm = self.updatePointMeta(pm, diode_part, diode_varmap)

        #build the main part
        part = FlexPart(['D', 'S'], pm, name)
        
        part.addPartChoice( res_part, {'1':'D','2':'S'}, res_varmap )
        part.addPartChoice( diode_part, diode_part.unityPortMap(), diode_varmap )
                
        self._parts[name] = part
        return part

    def biasedMos(self):
        """
        Description: mos3 with a DC voltage bias on its base port
          
        Ports: D,S
        
        Variables: W, L, use_pmos, Vbias

        Variable breakdown:
          For mos3: W=W, L=L, use_pmos=use_pmos
          For dcvs: DC={use_pmos=0: Vbias
                        use_pmos=1: Vdd-Vbias}
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        mos3_part = self.saturatedMos3()
        dcvs_part = self.dcvs()

        #build the point_meta (pm)
        pm = PointMeta({})
        mos3_varmap = mos3_part.unityVarMap()
        dcvs_varmap = dcvs_part.unityVarMap()
        dcvs_varmap['DC'] = 'Vbias'
        
        pm = self.updatePointMeta(pm, mos3_part, mos3_varmap)
        pm = self.updatePointMeta(pm, dcvs_part, dcvs_varmap)

        #build functions
        mos3_functions = mos3_varmap
        dcvs_functions = dcvs_varmap
        
        vdd = str(self.ss.vdd)
        dcvs_functions['DC'] = "switchAndEval(use_pmos, {" + \
                               "0:'(Vbias)', " + \
                               "1:'("+ vdd + "-Vbias)'})"    

        #build the main part
        part = CompoundPart(['D','S'], pm, name)
        
        n1 = part.addInternalNode()
        
        part.addPart(mos3_part, {'D':'D','G':n1,'S':'S'}, mos3_varmap)
        part.addPart(dcvs_part, {'NPOS':n1}, dcvs_varmap)
                
        self._parts[name] = part
        return part

    def biasedMosOrWire(self):
        """
        Description: either a biasedMos or a wire (short circuit)
          
        Ports: D,S
        
        Variables: chosen_part_index, W, L, use_pmos, Vbias

        Variable breakdown:
          For overal part: chosen_part_index (==do_short_circuit)
            0 : use biasedMos
            1 : use wire
          For biasedMos: 1:1 mapping of all vars except chosen_part_index
          For wire: <<none>>
          
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        bias_part = self.biasedMos()
        wire_part = self.wire()

        #build the point_meta (pm)
        pm = PointMeta({})
        bias_varmap = bias_part.unityVarMap()
        pm = self.updatePointMeta(pm, bias_part, bias_varmap)

        #build the main part
        part = FlexPart(['D','S'], pm, name)
        part.addPartChoice(bias_part, bias_part.unityPortMap(), bias_varmap)
        part.addPartChoice(wire_part, {'1':'D','2':'S'}, {})
                
        self._parts[name] = part
        return part

    def RC_series(self):
        """
        Description: resistor and capacitor in series
          
        Ports: N1, N2
        
        Variables: R, C

        Variable breakdown:
          For R: R=R
          For C: C=C
          
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        res_part = self.resistor()
        cap_part = self.capacitor()

        #build the point_meta (pm)
        pm = PointMeta({})
        res_varmap = res_part.unityVarMap()
        cap_varmap = cap_part.unityVarMap()
        
        pm = self.updatePointMeta(pm, res_part, res_varmap)
        pm = self.updatePointMeta(pm, cap_part, cap_varmap)

        #build the main part
        part = CompoundPart(['N1','N2'], pm, name)
        
        n1 = part.addInternalNode()
        
        part.addPart(res_part, {'1':'N1','2':n1}, res_varmap)
        part.addPart(cap_part, {'1':n1,'2':'N2'}, cap_varmap)
                
        self._parts[name] = part
        return part

    def twoBiasedMoses(self):
        """
        Description: two mos's, stacked.  Both either nmos or pmos.
          
        Ports: D,S
        
        Variables: use_pmos, D_W, D_L, D_Vbias, S_W, S_L, S_Vbias

        Variable breakdown:
          biasedMos closest to D: use_pmos=use_pmos, W=D_W, L=D_L, Vbias=D_Vbias
          biasedMos closest to S: use_pmos=use_pmos, W=S_W, L=S_L, Vbias=S_Vbias
          
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        mos_part = self.biasedMos()

        #build the point_meta (pm)
        pm = PointMeta({})
        D_varmap = {'use_pmos':'use_pmos','W':'D_W','L':'D_L','Vbias':'D_Vbias'}
        S_varmap = {'use_pmos':'use_pmos','W':'S_W','L':'S_L','Vbias':'S_Vbias'}
        
        pm = self.updatePointMeta(pm, mos_part, D_varmap)
        pm = self.updatePointMeta(pm, mos_part, S_varmap, True)
                                  
        #build the main part
        part = CompoundPart(['D','S'], pm, name)
        
        n1 = part.addInternalNode()
        
        part.addPart(mos_part, {'D':'D','S':n1}, D_varmap)
        part.addPart(mos_part, {'D':n1,'S':'S'}, S_varmap)
                
        self._parts[name] = part
        return part

    def stackedCascodeMos(self):
        """
        Description: one or two biased mos's, stacked
          
        Ports: D,S
        
        Variables: chosen_part_index,
          use_pmos, D_W, D_L, D_Vbias, S_W, S_L, S_Vbias

        Variable breakdown:
          For overal part: chosen_part_index (==do_stack)
            0 : use biasedMos
            1 : use twoBiasedMoses
          biasedMos: use_pmos=use_pmos, W=S_W, L=S_L, Vbias=S_Vbias
          twoBiasedMoses: 1:1 mapping (except chosen_part_index)
          
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        onemos_part = self.biasedMos()
        twomos_part = self.twoBiasedMoses()

        #build the point_meta (pm)
        pm = PointMeta({})
        onemos_varmap = {'use_pmos':'use_pmos','W':'S_W','L':'S_L',
                         'Vbias':'S_Vbias'}
        twomos_varmap = twomos_part.unityVarMap()
        
        pm = self.updatePointMeta(pm, twomos_part, twomos_varmap)

        #build the main part
        part = FlexPart(['D', 'S'], pm, name)
        
        part.addPartChoice( onemos_part, {'D':'D','S':'S'}, onemos_varmap )
        part.addPartChoice( twomos_part, {'D':'D','S':'S'}, twomos_varmap )
                
        self._parts[name] = part
        return part

    def levelShifter(self):
        """
        Description: 'amplifier' that shifts voltage down
          
        Ports: Vin, Iout, Drail, Srail
        
        Variables: Drail_is_vdd,
          amp_W, amp_L,
          cascode_do_stack,
          cascode_D_W, cascode_D_L, cascode_D_Vbias,
          cascode_S_W, cascode_S_L, cascode_S_Vbias

        Variable breakdown:
          amp (mos3):
            use_pmos=1-Drail_is_vdd, W=amp_W,L=amp_L
          cascode (stackedCascodeMos):
            chosen_part_index=cascode_do_stack,
            use_pmos=1-Drail_is_vdd,
            D_W=cascode_D_W, D_L=cascode_D_L, D_Vbias=cascode_D_Vbias,
            S_W=cascode_S_W, S_L=cascode_S_L, S_Vbias=cascode_S_Vbias
          
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        amp_part = self.saturatedMos3()
        cascode_part = self.stackedCascodeMos()

        #build the point_meta (pm)
        pm = PointMeta({})
        pm['Drail_is_vdd'] = self.buildVarMeta('bool_var','Drail_is_vdd')
        amp_varmap = {'use_pmos':'IGNORE',
                      'W':'amp_W','L':'amp_L'}
        cascode_varmap = {'use_pmos':'IGNORE',
                          'chosen_part_index':'cascode_do_stack',
                          'D_W':'cascode_D_W', 'D_L':'cascode_D_L',
                          'D_Vbias':'cascode_D_Vbias',
                          'S_W':'cascode_S_W', 'S_L':'cascode_S_L',
                          'S_Vbias':'cascode_S_Vbias'}
        
        pm = self.updatePointMeta(pm, amp_part, amp_varmap)
        pm = self.updatePointMeta(pm, cascode_part, cascode_varmap, True)

        #build functions
        amp_functions = amp_varmap
        amp_functions['use_pmos'] = '(1-Drail_is_vdd)'
        cascode_functions = cascode_varmap
        cascode_functions['use_pmos'] = '(1-Drail_is_vdd)'
                                  
        #build the main part
        part = CompoundPart(['Drail','Srail','Vin','Iout'], pm, name)
        
        part.addPart(amp_part, {'D':'Drail','G':'Vin','S':'Iout'}, amp_functions)
        part.addPart(cascode_part, {'D':'Iout','S':'Srail'}, cascode_functions)
                
        self._parts[name] = part
        return part

    def levelShifterOrWire(self):
        """
        Description: this is merely a FlexPart which can select
          a levelShifter or wire part
          
        Ports: Vin, Iout, Drail, Srail
        
        Variables: chosen_part_index (=='use_wire'),
          Drail_is_vdd,
          amp_W, amp_L,
          cascode_do_stack,
          cascode_D_W, cascode_D_L, cascode_D_Vbias,
          cascode_S_W, cascode_S_L, cascode_S_Vbias

        Variable breakdown:
          For overall part: chosen_part_index (=='use_wire')
            0: use levelShifter
            1: use wire
          For levelShifter: 1:1 mapping with levelShifter vars
          For wire:  <<none>>
          
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        shifter_part = self.levelShifter()
        wire_part = self.wire()

        #build the point_meta (pm)
        pm = PointMeta({})
        shifter_varmap = shifter_part.unityVarMap()
        pm = self.updatePointMeta(pm, shifter_part, shifter_varmap)
                                  
        #build the main part
        part = FlexPart(['Drail','Srail','Vin','Iout'], pm, name)
        
        part.addPartChoice(shifter_part, shifter_part.unityPortMap(),
                           shifter_varmap)
        part.addPartChoice(wire_part, {'1':'Vin','2':'Iout'}, {})
                
        self._parts[name] = part
        return part

    def levelShifterOrWire_VddGndPorts(self):
        """
        Description: Vdd and gnd are ports rather than Drail and Srail.
          The choice of how to allocate Vdd and gnd is
          done by 'chosen_part_index'
          
        Ports: Vin, Iout, Vdd, gnd
        
        Variables: chosen_part_index (==Drail_is_vdd),
          Drail_is_vdd,
          use_wire,
          amp_W, amp_L,
          cascode_do_stack,
          cascode_D_W, cascode_D_L, cascode_D_Vbias,
          cascode_S_W, cascode_S_L, cascode_S_Vbias

        Variable breakdown:
          For overall part: chosen_part_index (=='Drail_is_vdd')
            0: set Drail to gnd, and Srail to vdd
            1: set Drail to vdd, and Srail to gnd
          For levelShifterOrWire: 1:1 mapping, except chosen_part_index=use_wire
          
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        emb_part = self.levelShifterOrWire()

        #build the point_meta (pm)
        pm = PointMeta({})
        emb_varmap = emb_part.unityVarMap()
        pm = self.updatePointMeta(pm, emb_part, emb_varmap)
        del pm['chosen_part_index']
        pm['use_wire'] = self.buildVarMeta('bool_var','use_wire')

        #build the functions
        emb_functions = emb_varmap
        emb_functions['chosen_part_index'] = 'use_wire'
                                  
        #build the main part
        part = FlexPart(['Vin','Iout','Vdd','gnd'], pm, name)
        
        part.addPartChoice(emb_part,
                           {'Vin':'Vin','Iout':'Iout',
                            'Drail':'gnd','Srail':'Vdd'},
                           emb_varmap)
        part.addPartChoice(emb_part,
                           {'Vin':'Vin','Iout':'Iout',
                            'Drail':'Vdd','Srail':'gnd'},
                           emb_varmap)
                
        self._parts[name] = part
        return part


    def viFeedback_levelShifter(self):
        """
        Description: voltage-current feedback implemented
         as a source follower
          
        Ports: Ifpos, Ifneg, VsensePos, VsenseNeg, loadrail, opprail
        
        Variables: C,
          use_pmos,
          amp_W, amp_L,
          cascode_do_stack,
          cascode_D_W, cascode_D_L, cascode_D_Vbias,
          cascode_S_W, cascode_S_L, cascode_S_Vbias

        Variable breakdown:
          For levelShifter: 1:1 mapping of all vars except C
          For capacitor: C=C
          
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        sf_part = self.levelShifter()
        cap_part = self.capacitor()

        #build the point_meta (pm)
        pm = PointMeta({})
        sf_varmap = sf_part.unityVarMap()
        cap_varmap = cap_part.unityVarMap()
        
        pm = self.updatePointMeta(pm, sf_part, sf_varmap)
        del pm['Drail_is_vdd']
        pm = self.updatePointMeta(pm, cap_part, cap_varmap)
                                  
        #build the main part
        part = CompoundPart(['loadrail','opprail',
                             'Ifpos','Ifneg',
                             'VsensePos','VsenseNeg'],
                            pm, name)
        
        n1 = part.addInternalNode()

        sf_varmap['Drail_is_vdd'] = '(1-use_pmos)'
        part.addPart(sf_part, {'Drail':'loadrail','Srail':'opprail',
                               'Vin':'VsensePos','Iout':n1}, sf_varmap)
        part.addPart(cap_part, {'1':'Ifpos','2':n1}, cap_varmap)

                
        self._parts[name] = part
        return part

    def viFeedback(self):
        """
        Description: voltage-current feedback, with many options
          for implementation: capacitor, RC_series, and
          viFeedback_levelShifter
          
        Ports: Ifpos, Ifneg, VsensePos, VsenseNeg, loadrail, opprail
        
        Variables: chosen_part_index, R, C,
          use_pmos,
          amp_W, amp_L,
          cascode_do_stack,
          cascode_D_W, cascode_D_L, cascode_D_Vbias,
          cascode_S_W, cascode_S_L, cascode_S_Vbias

        Variable breakdown:
          For overall part: chosen_part_index
            0: use capacitor
            1: use RC_series
            2: use viFeedback_levelShifter
          For capacitor: C=C
          For RC_series: R=R, C=C
          For viFeedback_levelShifter: 1:1 mapping of all vars except R
          
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        cap_part = self.capacitor()
        rc_part = self.RC_series()
        visf_part = self.viFeedback_levelShifter()
        
        #build the point_meta (pm)
        pm = PointMeta({})
        cap_varmap = cap_part.unityVarMap()
        rc_varmap = rc_part.unityVarMap()
        visf_varmap = visf_part.unityVarMap()

        pm = self.updatePointMeta(pm, cap_part, cap_varmap)
        pm = self.updatePointMeta(pm, rc_part, rc_varmap, True)
        pm = self.updatePointMeta(pm, visf_part, visf_varmap, True)

        #build the main part
        part = FlexPart(['loadrail','opprail',
                         'Ifpos','Ifneg',
                         'VsensePos','VsenseNeg'],
                        pm, name)
        
        part.addPartChoice( cap_part, {'1':'Ifpos','2':'VsensePos'}, cap_varmap )
        part.addPartChoice( rc_part, {'N1':'Ifpos','N2':'VsensePos'}, rc_varmap )
        part.addPartChoice( visf_part, visf_part.unityPortMap(), visf_varmap )
                
        self._parts[name] = part
        return part
        

    def sourceDegen(self):
        """
        Description: Source degeneration of an amplifier.
          Instantiate as a wire, OR resistor.
          
        Ports: D, S
        
        Variables: chosen_part_index, W, L, use_pmos, Vbias, R
        
        Variable breakdown:
          For overall part: chosen_part_index
            0: use wire
            1: use resistor
          For wire: <<none>>
          For resistor: R
          
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        wire_part = self.wire()
        resistor_part = self.resistor()

        #build the point_meta (pm)
        pm = PointMeta({})
        wire_varmap = wire_part.unityVarMap()
        resistor_varmap = resistor_part.unityVarMap()
        
        pm = self.updatePointMeta(pm, wire_part, wire_varmap)
        pm = self.updatePointMeta(pm, resistor_part, resistor_varmap)

        #build the main part
        part = FlexPart(['D', 'S'], pm, name)
        
        part.addPartChoice( wire_part, {'1':'D','2':'S'}, wire_varmap )
        part.addPartChoice( resistor_part, {'1':'D','2':'S'}, resistor_varmap )
                
        self._parts[name] = part
        return part


    def cascodeDevice(self):
        """
        Description: biasedMos OR gainBoostedMos.  Used in an inputCascodeStage.
        
        NOTE: currently just biasedMos because gainBoostedMos not implemented!!
          
        Ports: D, S, loadrail, opprail
        
        Variables: chosen_part_index, loadrail_is_vdd, W, L, Vbias

        Variable breakdown:
          For overall part: chosen_part_index (=='cascode_recurse')
            0: use biasedMos
            1: use gainBoostedMos (FIXME -- not implemented yet)
          For biasedMos: use_pmos=1-loadrail_is_vdd, W=W, L=L, Vbias=Vbias
          For gainBoostedMos: <<none>> (FIXME)
          
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        biasedMos_part = self.biasedMos()

        #build the point_meta (pm)
        pm = PointMeta({})
        biasedMos_varmap = biasedMos_part.unityVarMap()
        biasedMos_varmap['use_pmos'] = 'loadrail_is_vdd'
        
        pm = self.updatePointMeta(pm, biasedMos_part, biasedMos_varmap)

        #build the main part
        part = FlexPart(['D', 'S', 'loadrail', 'opprail'], pm, name)

        biasedMos_funcs = biasedMos_varmap
        biasedMos_funcs['use_pmos'] = '1-loadrail_is_vdd'
        part.addPartChoice( biasedMos_part, {'D':'D','S':'S'}, biasedMos_varmap )
                
        self._parts[name] = part
        return part

    
    def cascodeDeviceOrWire(self):
        """
        Description: cascodeDevice OR wire
          
        Ports: D, S, loadrail, opprail
        
        Variables: chosen_part_index,
          cascode_recurse, loadrail_is_vdd, W, L, Vbias

        Variable breakdown:
          For overall part: chosen_part_index (=='cascode_is_wire')
            0: use cascodeDevice
            1: use wire
          For cascodeDevice: chosen_part_index=cascode_recurse,
            loadrail_is_vdd=loadrail_is_vdd, W=W, L=L, Vbias=Vbias
          For wire: <<none>>

        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        cascodeDevice_part = self.cascodeDevice()
        wire_part = self.wire()

        #build the point_meta (pm)
        pm = PointMeta({})
        cascodeDevice_varmap = cascodeDevice_part.unityVarMap()
        cascodeDevice_varmap['chosen_part_index'] = 'cascode_recurse'
        wire_varmap = wire_part.unityVarMap()
        
        pm = self.updatePointMeta(pm, cascodeDevice_part, cascodeDevice_varmap)
        pm = self.updatePointMeta(pm, wire_part, wire_varmap)

        #build the main part
        part = FlexPart(['D', 'S', 'loadrail', 'opprail'], pm, name)
        
        part.addPartChoice( cascodeDevice_part,
                            cascodeDevice_part.unityPortMap(),
                            cascodeDevice_varmap )
        part.addPartChoice( wire_part, {'1':'D','2':'S'}, wire_varmap )
                
        self._parts[name] = part
        return part

    def inputCascode_Stacked(self):
        """
        Description: inputCascode stage in a 'stacked' (as opposed to folded)
          configuration.  Has a cascodeDeviceOrWire, mos3, and sourceDegen.
          
        Ports: Vin, Iout, loadrail, opprail
        
        Variables: input_is_pmos, 
          cascode_is_wire, cascode_W, cascode_L, cascode_Vbias, cascode_recurse,
          ampmos_W, ampmos_L,
          degen_R, degen_choice
          
        Variable breakdown:
          For cascodeDeviceOrWire: chosen_part_index=cascode_is_wire,
            cascode_recurse=cascode_recurse, loadrail_is_vdd=1-input_is_pmos
            W=cascode_W, L=cascode_L, Vbias=cascode_Vbias            
          For mos3: W=ampmos_W, L=ampmos_L, use_pmos=input_is_pmos
          For sourceDegen: R=degen_R, chosen_part_index=degen_choice

        Remember: if input_is_pmos=True, then loadrail_is_Vdd=False; OR
                  if input_is_pmos=False, then loadrail_is_Vdd=True; OR
          
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        cascode_part = self.cascodeDeviceOrWire()
        ampmos_part = self.saturatedMos3()
        degen_part = self.sourceDegen()

        #build the point_meta (pm)
        pm = PointMeta({})
        
        cascode_varmap = {
            'chosen_part_index':'cascode_is_wire',
            'cascode_recurse':'cascode_recurse',
            'loadrail_is_vdd':'input_is_pmos',
            'W':'cascode_W',
            'L':'cascode_L',
            'Vbias':'cascode_Vbias'
            }
        ampmos_varmap = {
            'W':'ampmos_W',
            'L':'ampmos_L',
            'use_pmos':'input_is_pmos'
            }
        degen_varmap = {
            'R':'degen_R',
            'chosen_part_index':'degen_choice'
            }
            
        pm = self.updatePointMeta(pm, cascode_part, cascode_varmap)
        pm = self.updatePointMeta(pm, ampmos_part, ampmos_varmap, True)
        pm = self.updatePointMeta(pm, degen_part, degen_varmap, True)

        #build the main part
        part = CompoundPart(['Vin', 'Iout', 'loadrail', 'opprail'], pm, name)
        
        n_cascode_ampmos = part.addInternalNode()
        n_ampmos_degen = part.addInternalNode()

        cascode_funcs = cascode_varmap
        cascode_funcs['loadrail_is_vdd'] = '1 - input_is_pmos'
        
        ampmos_funcs = ampmos_varmap
        
        degen_funcs = degen_varmap
        
        part.addPart(cascode_part,
                     {'D':'Iout', 'S':n_cascode_ampmos,
                      'loadrail':'loadrail','opprail':'opprail'},
                     cascode_funcs)
        part.addPart(ampmos_part,
                     {'D':n_cascode_ampmos,'G':'Vin','S':n_ampmos_degen},
                     ampmos_funcs)
        part.addPart(degen_part, {'D':n_ampmos_degen,'S':'opprail'},
                     degen_funcs)
                
        self._parts[name] = part
        return part

    def inputCascode_Folded(self):
        """
        Description: inputCascode stage in a 'folded' (as opposed to stacked)
          configuration.  Has a cascodeDeviceOrWire, mos3, sourceDegen,
          and biasedMos.
          
        Ports: Vin, Iout, loadrail, opprail
        
        Variables: input_is_pmos, 
          cascode_W, cascode_L, cascode_Vbias, cascode_recurse,
          ampmos_W, ampmos_L,
          degen_R, degen_choice,
          inputbias_W, inputbias_L, inputbias_Vbias
          
        Variable breakdown:
          For cascodeDevice: chosen_part_index=cascode_recurse,
            loadrail_is_vdd=input_is_pmos,
            W=cascode_W, L=cascode_L, Vbias=cascode_Vbias            
          For mos3: W=ampmos_W, L=ampmos_L, use_pmos=input_is_pmos
          For sourceDegen: R=degen_R, chosen_part_index=degen_choice
          For biasedMos:  W=inputbias_W, L=inputbias_L,
            use_pmos=1-input_is_pmos, Vbias=inputbias_Vbias

        Remember: if input_is_pmos=True, then loadrail_is_Vdd=True; OR
                  if input_is_pmos=False, then loadrail_is_Vdd=False
                  
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        cascode_part = self.cascodeDevice()
        ampmos_part = self.saturatedMos3()
        degen_part = self.sourceDegen()
        inputbias_part = self.biasedMos()

        #build the point_meta (pm)
        pm = PointMeta({})
        
        cascode_varmap = {
            'chosen_part_index':'cascode_recurse',
            'loadrail_is_vdd':'input_is_pmos',
            'W':'cascode_W',
            'L':'cascode_L',
            'Vbias':'cascode_Vbias'
            }
        ampmos_varmap = {
            'W':'ampmos_W',
            'L':'ampmos_L',
            'use_pmos':'input_is_pmos'
            }
        degen_varmap = {
            'R':'degen_R',
            'chosen_part_index':'degen_choice'
            }
        inputbias_varmap = {
            'W':'inputbias_W',
            'L':'inputbias_L',
            'use_pmos':'input_is_pmos',
            'Vbias':'inputbias_Vbias',
            }
            
        pm = self.updatePointMeta(pm, cascode_part, cascode_varmap)
        pm = self.updatePointMeta(pm, ampmos_part, ampmos_varmap, True)
        pm = self.updatePointMeta(pm, degen_part, degen_varmap, True)
        pm = self.updatePointMeta(pm, inputbias_part, inputbias_varmap, True)

        #build the main part
        part = CompoundPart(['Vin', 'Iout', 'loadrail', 'opprail'], pm, name)
        
        n_ampmos_degen = part.addInternalNode()
        n_cascode_ampmos_inputbias = part.addInternalNode()

        cascode_funcs = cascode_varmap
        cascode_funcs['loadrail_is_vdd'] = 'input_is_pmos' 

        #note that the assignment of ampmos.use_pmos is wrong in the GRAIL pdf
        ampmos_funcs = ampmos_varmap
        ampmos_funcs['use_pmos'] = 'input_is_pmos'
            
        degen_funcs = degen_varmap
        
        inputbias_funcs = inputbias_varmap
        inputbias_funcs['use_pmos'] = '1 - input_is_pmos'

        part.addPart(cascode_part,
                     {'D':'Iout', 'S':n_cascode_ampmos_inputbias,
                      'loadrail':'loadrail','opprail':'opprail'},
                     cascode_funcs)
        part.addPart(ampmos_part,
                     {'D':n_cascode_ampmos_inputbias,'G':'Vin',
                      'S':n_ampmos_degen},
                     ampmos_funcs)
        part.addPart(degen_part, {'D':n_ampmos_degen,'S':'loadrail'},
                     degen_funcs)
        part.addPart(inputbias_part,
                     {'D':n_cascode_ampmos_inputbias,'S':'opprail'},
                     inputbias_funcs)
                
        self._parts[name] = part
        return part


    def inputCascodeFlex(self):
        """
        Description: choose between folded or stacked input cascode stage.
          
        Ports: Vin, Iout, loadrail, opprail
        
        Variables:
          chosen_part_index
          input_is_pmos, 
          cascode_W, cascode_L, cascode_Vbias, cascode_recurse, cascode_is_wire,
          ampmos_W, ampmos_L,
          degen_R, degen_choice,
          inputbias_W, inputbias_L, inputbias_Vbias
        
        Variable breakdown:
          For overall part: chosen_part_index
            0: use inputCascode_Stacked
            1: use inputCascode_Folded
          For inputCascode_Stacked:
            All the input variables, as is, except chosen_part_index and
            the inputbias_XXX vars.
          For inputCascode_Folded:
            All the input variables, as is, except chosen_part_index and
            cascode_is_wire.
          
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        stacked_part = self.inputCascode_Stacked()
        folded_part = self.inputCascode_Folded()

        #build the point_meta (pm)
        pm = PointMeta({})
        pm = self.updatePointMeta(pm, stacked_part, stacked_part.unityVarMap())
        pm = self.updatePointMeta(pm, folded_part, folded_part.unityVarMap(),
                                  True)
        
        #build the main part
        part = FlexPart(['Vin', 'Iout', 'loadrail', 'opprail'], pm, name)

        part.addPartChoice( stacked_part,
                            stacked_part.unityPortMap(),
                            stacked_part.unityVarMap() )
        part.addPartChoice( folded_part,
                            folded_part.unityPortMap(),
                            folded_part.unityVarMap() )
        
        self._parts[name] = part
        return part


    def inputCascodeStage(self):
        """
        Description: Wraps a single embedded part, an inputCascodeFlex.
          AUTOMATICALLY chooses between folded vs. stacked 
          based on loadrail_is_vdd and input_is_pmos.
          
        Ports: Vin, Iout, loadrail, opprail
        
        Variables:
          loadrail_is_vdd, input_is_pmos,
          
          cascode_W, cascode_L, cascode_Vbias, cascode_recurse, cascode_is_wire,
          ampmos_W, ampmos_L,
          degen_R, degen_choice,
          inputbias_W, inputbias_L, inputbias_Vbias
        
        Variable breakdown:
          For overall part: chosen_part_index (=='use_wire')
            0: use inputCascode_Stacked
            1: use inputCascode_Folded
          For inputCascode_Stacked:
            All the input variables, as is, except chosen_part_index and
            the inputbias_XXX vars.
          For inputCascode_Folded:
            All the input variables, as is, except chosen_part_index and
            cascode_is_wire.
          
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        emb_part = self.inputCascodeFlex()

        #build the point_meta (pm)
        # -nearly identical to inputCascodeFlex, except it adds one var
        #  and removes another
        pm = PointMeta({})
        pm = self.updatePointMeta(pm, emb_part, emb_part.unityVarMap())
        pm.addVarMeta( self.buildVarMeta('bool_var', 'loadrail_is_vdd') )#add var
        del pm['chosen_part_index']                                      #remove
        
        #build the main part
        part = CompoundPart(['Vin', 'Iout', 'loadrail', 'opprail'], pm, name)

        # -here is where we auto-choose between stacked and folded: note the '=='
        emb_funcs = emb_part.unityVarMap()
        emb_funcs['chosen_part_index'] = '(input_is_pmos == loadrail_is_vdd)'

        part.addPart( emb_part, emb_part.unityPortMap(), emb_funcs )
        
        self._parts[name] = part
        return part

    def ssViInput(self):
        """
        Description: Single-ended input voltage in, single-ended current out
          stage.  Turns out that this is merely a wrapper for inputCascodeStage
          (but with a more appropriate name for higher-level use.)
          
        Ports: Vin, Iout, loadrail, opprail
        
        Variables:
          loadrail_is_vdd, input_is_pmos,
          
          cascode_W, cascode_L, cascode_Vbias, cascode_recurse, cascode_is_wire,
          ampmos_W, ampmos_L,
          degen_R, degen_choice,
          inputbias_W, inputbias_L, inputbias_Vbias
        
        Variable breakdown:
          For inputCascodeStage:
            All, a 1:1 mapping.
          
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        emb_part = self.inputCascodeStage()

        #build the point_meta (pm)
        pm = PointMeta({})
        pm = self.updatePointMeta(pm, emb_part, emb_part.unityVarMap())
        
        #build the main part
        part = CompoundPart(['Vin', 'Iout', 'loadrail', 'opprail'], pm, name)

        part.addPart( emb_part, emb_part.unityPortMap(), emb_part.unityVarMap() )
        
        self._parts[name] = part
        return part

    def ssIiLoad_Cascoded(self):
        """
        Description: This is has a biasedMos transistor as the main load device,
           plus a cascodeDevice which may amplify the effect of the load.
          
        Ports: Iout, loadrail, opprail
        
        Variables:
          loadrail_is_vdd, 
          mainload_W, mainload_L, mainload_Vbias
          loadcascode_recurse, loadcascode_W, loadcascode_L, loadcascode_Vbias
        
        Variable breakdown:
          For biasedMos:
            W=mainload_W, L=mainload_L, use_pmos=loadrail_is_vdd, Vbias=mainload_Vbias
          For cascodeDevice:
            chosen_part_index=loadcascode_recurse,
            loadrail_is_vdd=loadrail_is_vdd, W=loadcascode_W, L=loadcascode_L,
            Vbias=loadcascode_Vbias
          
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        mainload_part = self.biasedMos()
        loadcascode_part = self.cascodeDevice()

        mainload_varmap = {
            'use_pmos':'loadrail_is_vdd',
            
            'W':'mainload_W',
            'L':'mainload_L',
            'Vbias':'mainload_Vbias'
            }
        loadcascode_varmap = {
            'loadrail_is_vdd':'loadrail_is_vdd',
            
            'chosen_part_index':'loadcascode_recurse',
            'W':'loadcascode_W',
            'L':'loadcascode_L',
            'Vbias':'loadcascode_Vbias'
            }

        #build the point_meta (pm)
        pm = PointMeta({})
        pm = self.updatePointMeta(pm, mainload_part, mainload_varmap)
        pm = self.updatePointMeta(pm, loadcascode_part, loadcascode_varmap, True)
        
        loadcascode_functions = loadcascode_varmap;
        loadcascode_functions['loadrail_is_vdd']='1-loadrail_is_vdd'
        
        #build the main part
        part = CompoundPart(['Iout', 'loadrail', 'opprail'], pm, name)

        n_mos_to_cascode = part.addInternalNode()
        
        part.addPart( mainload_part,
                      {'S':'loadrail','D':n_mos_to_cascode},
                      mainload_varmap )
        part.addPart( loadcascode_part,
                      {'S':n_mos_to_cascode,'D':'Iout',
                       'loadrail':'loadrail', 'opprail':'opprail'},
                      loadcascode_functions )
        
        self._parts[name] = part
        return part


    def ssIiLoad(self):
        """
        Description: single-ended I in, single-ended I out load.
          Is a Flex part which may be: resistor, biasedMos, or ssIiLoad_Cascoded.
          
        Ports: Iout, loadrail, opprail
        
        Variables:
          chosen_part_index,
          loadrail_is_vdd,
          R,
          W, L, Vbias,
          loadcascode_recurse, loadcascode_W, loadcascode_L, loadcascode_Vbias
          
        Variable breakdown:
          For overall part: chosen_part_index
            0: use resistor
            1: use biasedMos
            2: use ssIiLoad_Cascoded
          For resistor:
            R=R
          For biasedMos:
            use_pmos=loadrail_is_vdd, 
            W=W, L=L, Vbias=Vbias
          For ssIiLoad_Cascoded:
            loadrail_is_vdd=loadrail_is_vdd, 
            mainload_W=W, mainload_L=L, mainload_Vbias=Vbias,
            loadcascode_recurse=loadcascode_recurse,
            loadcascode_W=loadcascode_W, loadcascode_L=loadcascode_L,
            loadcascode_Vbias=loadcascode_Vbias
          
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        res_part = self.resistor()
        biasedmos_part = self.biasedMos()
        cascodemos_part = self.ssIiLoad_Cascoded()

        #build the point_meta (pm)
        pm = PointMeta({})

        res_varmap = {'R':'R'}
        biasedmos_varmap = {
            'use_pmos':'loadrail_is_vdd',
            'W':'W',
            'L':'L',
            'Vbias':'Vbias'
            }
        cascodemos_varmap = {
            'loadrail_is_vdd':'loadrail_is_vdd',
            'mainload_W':'W',
            'mainload_L':'L',
            'mainload_Vbias':'Vbias',
            'loadcascode_recurse':'loadcascode_recurse',
            'loadcascode_W':'loadcascode_W',
            'loadcascode_L':'loadcascode_L',
            'loadcascode_Vbias':'loadcascode_Vbias'
            }
        
        pm = self.updatePointMeta(pm, res_part, res_varmap)
        pm = self.updatePointMeta(pm, biasedmos_part, biasedmos_varmap)
        pm = self.updatePointMeta(pm, cascodemos_part, cascodemos_varmap, True)
        
        #build the main part
        part = FlexPart(['Iout', 'loadrail', 'opprail'], pm, name)

        part.addPartChoice( res_part, {'1':'loadrail','2':'Iout'}, res_varmap)
        part.addPartChoice( biasedmos_part,  {'D':'Iout','S':'loadrail'},
                            biasedmos_varmap)
        part.addPartChoice( cascodemos_part, cascodemos_part.unityPortMap(),
                            cascodemos_varmap)
        
        self._parts[name] = part
        return part


    def ssViAmp1(self):
        """
        Description: single-ended V in, single-ended I out, 1-stage
         (common-source) amplifier.
          
        Ports: Vin, Iout, loadrail, opprail
        
        Variables:
            loadrail_is_vdd,
            input_is_pmos,
            
            inputcascode_W,inputcascode_L,inputcascode_Vbias,inputcascode_recurse,
            ampmos_W, ampmos_L,
            degen_R, degen_choice,
            inputbias_W, inputbias_L, inputbias_Vbias

            load_part_index,
            load_R,
            load_W, load_L, load_Vbias,
            loadcascode_recurse, loadcascode_W, loadcascode_L, loadcascode_Vbias
          
        Variable breakdown:
          For ssViInput:
            loadrail_is_vdd=loadrail_is_vdd,
            input_is_pmos=input_is_pmos,
            
            cascode_W=inputcascode_W,
            cascode_L=inputcascode_L,
            cascode_Vbias=inputcascode_Vbias,
            cascode_recurse=inputcascode_recurse,
            cascode_is_wire=inputcascode_is_wire,
            ampmos_W=ampmos_W, ampmos_L=ampmos_L,
            degen_R=degen_R, degen_choice=degen_choice,
            inputbias_W=inputbias_W, inputbias_L=inputbias_L,
            inputbias_Vbias=inputbias_Vbias
            
          For ssIiLoad:
            loadrail_is_vdd=loadrail_is_vdd,
            
            chosen_part_index=load_part_index,
            R=load_R,
            W=load_W, L=load_L, Vbias=load_Vbias,
            loadcascode_recurse=loadcascode_recurse,
            loadcascode_W=loadcascode_W,
            loadcascode_L=loadcascode_L,
            loadcascode_Vbias=loadcascode_Vbias
          
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        input_part = self.ssViInput()
        load_part = self.ssIiLoad()

        #build the point_meta (pm)
        pm = PointMeta({})

        input_varmap = {
            'loadrail_is_vdd':'loadrail_is_vdd',
            'input_is_pmos':'input_is_pmos',
            
            'cascode_W':'inputcascode_W',
            'cascode_L':'inputcascode_L',
            'cascode_Vbias':'inputcascode_Vbias',
            'cascode_recurse':'inputcascode_recurse',
            'cascode_is_wire':'inputcascode_is_wire',
            'ampmos_W':'ampmos_W',
            'ampmos_L':'ampmos_L', 
            'degen_R':'degen_R',
            'degen_choice':'degen_choice',
            'inputbias_W':'inputbias_W',
            'inputbias_L':'inputbias_L',
            'inputbias_Vbias':'inputbias_Vbias',
            }
        load_varmap = {
            'chosen_part_index':'load_part_index',
            'loadrail_is_vdd':'loadrail_is_vdd',
            
            'R':'load_R',
            'W':'load_W',
            'L':'load_L',
            'Vbias':'load_Vbias',
            'loadcascode_recurse':'loadcascode_recurse',
            'loadcascode_W':'loadcascode_W',
            'loadcascode_L':'loadcascode_L',
            'loadcascode_Vbias':'loadcascode_Vbias',         
            }

        pm = self.updatePointMeta(pm, input_part, input_varmap)
        pm = self.updatePointMeta(pm, load_part, load_varmap, True)
        
        #build the main part
        part = CompoundPart(['Vin','Iout', 'loadrail', 'opprail'], pm, name)

        part.addPart( input_part, input_part.unityPortMap(), input_varmap )

        # -note that the GRAIL pdf wrongly labels the 'Iout' to be 'Iin' (Fig 17)
        part.addPart( load_part, load_part.unityPortMap(), load_varmap )
        
        self._parts[name] = part
        return part
        
    def ssViAmp1_VddGndPorts(self):
        """
        Description: Just like ssViAmp1, except it has 'Vdd' and 'gnd'
          as external ports, which are less flexible than ssViAmp1's
          ports of 'loadrail' and 'opprail'.  But it makes it directly
          interfaceable to the outside world (unlike ssViAmp1 on its own).
          
        Ports: Vin, Iout, Vdd, gnd
        
        Variables:
          -like dsViAmp1, except replace its 'loadrail_is_vdd'
           with 'chosen_part_index', ie vars are:

            chosen_part_index (==loadrail_is_vdd),
            input_is_pmos,
            
            inputcascode_W,inputcascode_L,inputcascode_Vbias,inputcascode_recurse,
            ampmos_W, ampmos_L,
            degen_R, degen_choice,
            inputbias_W, inputbias_L, inputbias_Vbias

            load_part_index,
            load_R,
            load_W, load_L, load_Vbias,
            loadcascode_recurse, loadcascode_W, loadcascode_L, loadcascode_Vbias
          
        Variable breakdown:
          For overall part: chosen_part_index (==loadrail_is_vdd)
            0: set 'loadrail' of ssViAmp1 to 'gnd', and 'opprail' to 'Vdd'
            1: set 'loadrail' of ssViAmp1 to 'Vdd', and 'opprail' to 'gnd'
          For ssViamp1:
            All, a 1:1 mapping, except: loadrail_is_vdd=chosen_part_index
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        amp_part = self.ssViAmp1()

        #build the point_meta (pm)
        pm = PointMeta({})
        pm = self.updatePointMeta(pm, amp_part, amp_part.unityVarMap())
        del pm['loadrail_is_vdd']
        # -remember: don't need to add 'chosen_part_index' to pm
        #  because FlexParts do that automatically

        varmap = amp_part.unityVarMap()
        varmap['loadrail_is_vdd'] = 'chosen_part_index'
        
        #build the main part
        part = FlexPart(['Vin', 'Iout', 'Vdd','gnd'], pm, name)

        part.addPartChoice( amp_part,
                            {'Vin':'Vin', 'Iout':'Iout',
                             'loadrail':'gnd', 'opprail':'Vdd'},
                            varmap)
        part.addPartChoice( amp_part,
                            {'Vin':'Vin', 'Iout':'Iout',
                             'loadrail':'Vdd', 'opprail':'gnd'},
                            varmap )

        #build a summaryStr
        part.addToSummaryStr('loadrail is vdd','chosen_part_index')
        part.addToSummaryStr('input is pmos (rather than nmos)', 'input_is_pmos')
        part.addToSummaryStr('folded', 'chosen_part_index == input_is_pmos')
        part.addToSummaryStr('degen_choice (0=wire,1=resistor)', 'degen_choice')
        part.addToSummaryStr('load type (0=resistor,1=biasedMos,'
                             '2=ssIiLoad_Cascoded)', 'load_part_index')
        
        self._parts[name] = part
        return part

    def currentMirror_Simple(self):
        """
        Description: simple 2-transistor current mirror
          
        Ports: Irefnode, Ioutnode, loadrail
        ##NOTE PP: the name loadrail might not be completely correct
        
        Variables:
            loadrail_is_vdd, base_W, ref_K, out_K, L
          
        Variable breakdown:
          For reference-input MOS (a mos3):
            use_pmos=loadrail_is_vdd, W=base_W*ref_K, L=L
          For output MOS (a mos3):
            use_pmos=loadrail_is_vdd, W=base_W*out_K, L=L
          
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        ref_part = self.saturatedMos3()
        out_part = self.saturatedMos3()

        #build the point_meta (pm)
        pm = self.buildPointMeta({'loadrail_is_vdd':'bool_var',
                                  'base_W':'W',
                                  'ref_K':'K','out_K':'K',
                                  'L':'L'})
        
        #build the main part
        part = CompoundPart(['Irefnode','Ioutnode', 'loadrail'], pm, name)

        part.addPart( ref_part, {'D':'Irefnode','G':'Irefnode','S':'loadrail'},
                      {'use_pmos':'loadrail_is_vdd','W':'base_W*ref_K', 'L':'L'})
        part.addPart( out_part, {'D':'Ioutnode','G':'Irefnode','S':'loadrail'},
                      {'use_pmos':'loadrail_is_vdd','W':'base_W*out_K','L':'L'})
        
        self._parts[name] = part
        return part



    def currentMirror_Cascode(self):
        """
        Description: standard cascode current mirror
          
        Ports: Irefnode, Ioutnode, loadrail
        
        Variables:
            loadrail_is_vdd, base_W, ref_K, out_K, cascode_K, main_K, L
          
        Variable breakdown:
          For cascode reference-input MOS (a mos3):
            use_pmos=loadrail_is_vdd, W=base_W*cascode_K*ref_K, L=L
          For main reference-input MOS (a mos3):
            use_pmos=loadrail_is_vdd, W=base_W*main_K*ref_K, L=L
          For cascode output MOS (a mos3):
            use_pmos=loadrail_is_vdd, W=base_W*cascode_K*out_K, L=L
          For main output MOS (a mos3):
            use_pmos=loadrail_is_vdd, W=base_W*main_K*out_K, L=L
          
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        cascoderef_part = self.saturatedMos3()
        mainref_part = self.saturatedMos3()
        cascodeout_part = self.saturatedMos3()
        mainout_part = self.saturatedMos3()

        #build the point_meta (pm)
        pm = self.buildPointMeta({'loadrail_is_vdd':'bool_var',
                                  'base_W':'W',
                                  'ref_K':'K','out_K':'K',
                                  'cascode_K':'K','main_K':'K',
                                  'L':'L'})
        
        #build the main part
        part = CompoundPart(['Irefnode','Ioutnode', 'loadrail'], pm, name)
        
        n_ref = part.addInternalNode()
        n_out = part.addInternalNode()

        part.addPart( cascoderef_part,
                      {'D':'Irefnode','G':'Irefnode','S':n_ref},
                      {'use_pmos':'loadrail_is_vdd',
                       'W':'base_W*cascode_K*ref_K',
                       'L':'L'} )

        part.addPart( mainref_part,
                      {'D':n_ref,'G':n_ref,'S':'loadrail'},
                      {'use_pmos':'loadrail_is_vdd',
                       'W':'base_W*main_K*ref_K',
                       'L':'L'} )

        part.addPart( cascodeout_part,
                      {'D':'Ioutnode','G':'Irefnode','S':n_out},
                      {'use_pmos':'loadrail_is_vdd',
                       'W':'base_W*cascode_K*out_K',
                       'L':'L'} )

        part.addPart( mainout_part,
                      {'D':n_out,'G':n_ref,'S':'loadrail'},
                      {'use_pmos':'loadrail_is_vdd',
                       'W':'base_W*main_K*out_K',
                       'L':'L'} )
        
        self._parts[name] = part
        return part


    def currentMirror_LowVoltageA(self):
        """
        Description: low-voltage-A current mirror
          
        Ports: Irefnode, Ioutnode, loadrail
        
        Variables:
            loadrail_is_vdd, base_W, ref_K, out_K, cascode_K, main_K, L, Vbias
          
        Variable breakdown:
          For cascode reference-input MOS (a biasedMos):
            use_pmos=loadrail_is_vdd, W=base_W*cascode_K*ref_K, L=L, Vbias=Vbias
          For main reference-input MOS (a mos3):
            use_pmos=loadrail_is_vdd, W=base_W*main_K*ref_K, L=L
          For cascode output MOS (a biasedMos):
            use_pmos=loadrail_is_vdd, W=base_W*cascode_K*out_K, L=L, Vbias=Vbias
          For main output MOS (a mos3):
            use_pmos=loadrail_is_vdd, W=base_W*main_K*out_K, L=L
          
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        cascoderef_part = self.biasedMos()
        mainref_part = self.saturatedMos3()
        cascodeout_part = self.biasedMos()
        mainout_part = self.saturatedMos3()

        #build the point_meta (pm)
        pm = self.buildPointMeta({'loadrail_is_vdd':'bool_var',
                                  'base_W':'W',
                                  'ref_K':'K','out_K':'K',
                                  'cascode_K':'K','main_K':'K',
                                  'L':'L',
                                  'Vbias':'DC_V'})
        
        #build the main part
        part = CompoundPart(['Irefnode','Ioutnode', 'loadrail'], pm, name)
        
        n_ref = part.addInternalNode()
        n_out = part.addInternalNode()

        part.addPart( cascoderef_part,
                      {'D':'Irefnode','S':n_ref},
                      {'use_pmos':'loadrail_is_vdd',
                       'W':'base_W*cascode_K*ref_K',
                       'L':'L',
                       'Vbias':'Vbias'} )

        part.addPart( mainref_part,
                      {'D':n_ref,'G':'Irefnode','S':'loadrail'},
                      {'use_pmos':'loadrail_is_vdd',
                       'W':'base_W*main_K*ref_K',
                       'L':'L'} )

        part.addPart( cascodeout_part,
                      {'D':'Ioutnode','S':n_out},
                      {'use_pmos':'loadrail_is_vdd',
                       'W':'base_W*cascode_K*out_K',
                       'L':'L',
                       'Vbias':'Vbias'} )

        part.addPart( mainout_part,
                      {'D':n_out,'G':'Irefnode','S':'loadrail'},
                      {'use_pmos':'loadrail_is_vdd',
                       'W':'base_W*main_K*out_K',
                       'L':'L'} )
        
        self._parts[name] = part
        return part

    def currentMirror(self):
        """
        Description: current mirror (selects one of several possible
          implementations)
          
        Ports: Irefnode, Ioutnode, loadrail
        
        Variables:
            chosen_part_index,
            loadrail_is_vdd, base_W, ref_K, out_K, L, 
            topref_usemos, topref_R, topref_K         
            middleref_K,                             
            bottomref_K,  
            topout_K,
            bottomout_K,
            Vbias
          
        Variable breakdown:
          For overall part: chosen_part_index
            0: use currentMirror_Simple
            1: use currentMirror_Cascode
            2: use currentMirror_LowVoltageA
            
          For currentMirror_Simple:
            loadrail_is_vdd=loadrail_is_vdd, base_W=base_W, ref_K=ref_K,
            out_K=out_K, L=L
          For currentMirror_Cascode:
            loadrail_is_vdd=loadrail_is_vdd, base_W=base_W, ref_K=ref_K,
            out_K=out_K, cascode_K=topout_K, main_K=bottomout_K, L=L
            -note how we set cascode_K and main_K 
          For currentMirror_LowVoltageA:
            loadrail_is_vdd=loadrail_is_vdd, base_W=base_W, ref_K=ref_K,
            out_K=out_K, cascode_K=topout_K, main_K=bottomout_K, L=L,
            Vbias=Vbias
            -note how we set cascode_K and main_K 
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        cm_Simple = self.currentMirror_Simple()
        cm_Cascode = self.currentMirror_Cascode()
        cm_LowVoltageA = self.currentMirror_LowVoltageA()

        #build the point_meta (pm)
        pm = self.buildPointMeta({'loadrail_is_vdd':'bool_var',
                                  'base_W':'W',
                                  'ref_K':'K','out_K':'K',
                                  'L':'L',
                                  'topref_usemos':'bool_var','topref_R':'R',
                                  'topref_K':'K',
                                  'middleref_K':'K',
                                  'bottomref_K':'K',
                                  'topout_K':'K',
                                  'bottomout_K':'K',
                                  'Vbias':'DC_V',
                                  })            
        
        #build the main part
        part = FlexPart(['Irefnode','Ioutnode', 'loadrail'], pm, name)
        portmap = cm_Simple.unityPortMap()
        part.addPartChoice(cm_Simple, portmap,
                           {'loadrail_is_vdd':'loadrail_is_vdd',
                           'base_W':'base_W', 'ref_K':'ref_K','out_K':'out_K',
                            'L':'L'}
                           )
        part.addPartChoice(cm_Cascode, portmap,
                           {'loadrail_is_vdd':'loadrail_is_vdd',
                            'base_W':'base_W', 'ref_K':'ref_K',
                            'out_K':'out_K', 'cascode_K':'topout_K',
                            'main_K':'bottomout_K', 'L':'L'}
                           )
        part.addPartChoice(cm_LowVoltageA, portmap,
                           {'loadrail_is_vdd':'loadrail_is_vdd',
                            'base_W':'base_W', 'ref_K':'ref_K',
                            'out_K':'out_K', 'cascode_K':'topout_K',
                            'main_K':'bottomout_K', 'L':'L', 'Vbias':'Vbias'}
                           )
        
        self._parts[name] = part
        return part



    def dsIiLoad(self):
        """
        Description: Differential-in current, single-ended out current load.
          This turns out to merely a wrapper for a current mirror with
          different ports, and a name name more appropriate for embedding
          in higher-level blocks.
          
        Ports: Iin1, Iin2, Iout, loadrail
          (Iin1 and Iin2 are differential.)
        
        Variables:
          Same as currentMirror          
        
        Variable breakdown:
          For currentMirror:
            All, a 1:1 mapping.
          
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        cm_part = self.currentMirror()
        wire_part = self.wire()

        #build the point_meta (pm)
        pm = PointMeta({})
        pm = self.updatePointMeta(pm, cm_part, cm_part.unityVarMap())
        pm = self.updatePointMeta(pm, wire_part, wire_part.unityVarMap())
        
        #build the main part
        part = CompoundPart(['Iin1', 'Iin2', 'Iout', 'loadrail'], pm, name)

        part.addPart( cm_part,
                      {'Irefnode':'Iin1', 'Ioutnode':'Iin2',
                       'loadrail':'loadrail'},
                      cm_part.unityVarMap() )
        part.addPart( wire_part, {'1':'Iin2','2':'Iout'},
                      wire_part.unityVarMap() )
        
        self._parts[name] = part
        return part


    def ddViInput_stacked(self):
        """
        Description: stacked ddViInput
          
        Ports: Vin1, Vin2, Iout1, Iout2, loadrail, opprail
        
        Variables:
          
        Variable breakdown:
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        ssvi_part = self.ssViInput()
        bias_part = self.biasedMos()

        #build the point_meta (pm)
        pm = PointMeta({})
        ssvi_varmap = ssvi_part.unityVarMap()
        bias_varmap = {'W':'inputbias_W', 'L':'inputbias_L',
                       'use_pmos':'input_is_pmos',
                       'Vbias':'inputbias_Vbias',
                       }
        pm = self.updatePointMeta(pm, ssvi_part, ssvi_varmap)
        pm = self.updatePointMeta(pm, bias_part, bias_varmap, True)
        
        #build the main part
        part = CompoundPart(['Vin1', 'Vin2', 'Iout1', 'Iout2',
                             'loadrail','opprail'], pm, name)
        virtual_ground = part.addInternalNode()
        
        part.addPart( ssvi_part,
                      {'Vin':'Vin1', 'Iout':'Iout1',
                      'loadrail':'loadrail', 'opprail':virtual_ground},
                      ssvi_varmap )
        part.addPart( ssvi_part,
                      {'Vin':'Vin2', 'Iout':'Iout2',
                      'loadrail':'loadrail', 'opprail':virtual_ground},
                      ssvi_varmap)
      
        part.addPart( bias_part,
                      {'D':virtual_ground, 'S':'opprail'},
                      bias_varmap )
                
        self._parts[name] = part
        return part

        
    def ddViInput_folded(self):
        """
        Description: folded ddViInput
          
        Ports: Vin1, Vin2, Iout1, Iout2, loadrail,opprail
        
        Variables:
          
        Variable breakdown:
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        ssvi_part = self.ssViInput()
        bias_part = self.biasedMos()

        #build the point_meta (pm)
        pm = PointMeta({})
        ssvi_varmap = ssvi_part.unityVarMap()
        bias_varmap = {'W':'inputbias_W', 'L':'inputbias_L',
                       'use_pmos':'input_is_pmos',
                       'Vbias':'inputbias_Vbias',
                       }
        pm = self.updatePointMeta(pm, ssvi_part, ssvi_varmap)
        pm = self.updatePointMeta(pm, bias_part, bias_varmap, True)
        
        #build the main part
        part = CompoundPart(['Vin1', 'Vin2', 'Iout1', 'Iout2',
                             'loadrail','opprail'], pm, name)
        virtual_ground = part.addInternalNode()
        
        part.addPart( ssvi_part,
                      {'Vin':'Vin1', 'Iout':'Iout1',
                      'loadrail':virtual_ground, 'opprail':'opprail'},
                      ssvi_varmap )
        part.addPart( ssvi_part,
                      {'Vin':'Vin2', 'Iout':'Iout2',
                      'loadrail':virtual_ground, 'opprail':'opprail'},
                      ssvi_varmap)
      
        part.addPart( bias_part,
                      {'D':virtual_ground, 'S':'loadrail'},
                      bias_varmap )
                
        self._parts[name] = part
        return part
        
    def ddViInput_Flex(self):
        """
        Description: Chooses between folded and stacked 
          
        Ports: Vin1, Vin2, Iout1, Iout2, loadrail,opprail
        
        Variables:
          
        Variable breakdown:
          For overall part: chosen_part_index (==use_folded?)
            0 : ddViInput_Stacked
            1 : ddViInput_Folded
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        stacked_part = self.ddViInput_stacked()
        folded_part = self.ddViInput_folded()

        #build the point_meta (pm)
        pm = PointMeta({})
        stacked_or_folded_varmap = stacked_part.unityVarMap()
        pm = self.updatePointMeta(pm, stacked_part, stacked_or_folded_varmap)
        
        #build the main part
        part = FlexPart(['Vin1', 'Vin2', 'Iout1', 'Iout2',
                         'loadrail','opprail'], pm, name)
        
        part.addPartChoice( stacked_part, stacked_part.unityPortMap(), stacked_or_folded_varmap)
        part.addPartChoice( folded_part, folded_part.unityPortMap(), stacked_or_folded_varmap)
                
        self._parts[name] = part
        return part

    def ddViInput(self):
        """
        Description: diff-voltage in, diff-current out, Input stage.  Holds
          a twin pair of ssViInput stages and a bias (via biasedMos).
          The simplest version of this is simply a diff pair.
         
          This is merely a wrapper of ddViInput_Flex which has chosen_part_index.
          Chosen_part_index == (input_is_pmos==loadrail_is_vdd) == do_fold?        
          
        Ports: Vin1, Vin2, Iout1, Iout2, loadrail,opprail
        
        Variables:
          loadrail_is_vdd, input_is_pmos,
          cascode_W, cascode_L, cascode_Vbias, cascode_recurse, cascode_is_wire,
          ampmos_W, ampmos_L,
          degen_R, degen_choice,
          inputbias_W, inputbias_L, inputbias_Vbias
          
        Variable breakdown:
          
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        flex_part = self.ddViInput_Flex()

        #build the point_meta (pm)
        pm = PointMeta({})
        flex_varmap = flex_part.unityVarMap()
        pm = self.updatePointMeta(pm, flex_part, flex_varmap)
        del pm['chosen_part_index']
        
        #build functions
        flex_functions = flex_varmap
        flex_functions['chosen_part_index'] = '(input_is_pmos==loadrail_is_vdd)'
        
        #build the main part
        part = CompoundPart(['Vin1', 'Vin2', 'Iout1', 'Iout2',
                             'loadrail','opprail'], pm, name)
        
         # -the only difference between the choices is in allocation of opprail and loadrail to floatingbias_rail           
        part.addPart( flex_part, {'Vin1':'Vin1', 'Vin2':'Vin2', 'Iout1':'Iout1', 'Iout2':'Iout2',
                          'loadrail':'loadrail','opprail':'opprail'}, flex_varmap)
                
        self._parts[name] = part
        return part

    def dsViAmp1(self):
        """
        Description: Differential-in voltage, single-ended out current amplifier.
          Combines together a ddViInput and dsIiLoad.
          
        Ports: Vin1, Vin2, Iout, loadrail, opprail
          (Vin1 and Vin2 are differential.)
        
        Variables:
            loadrail_is_vdd, input_is_pmos
            
            cascode_W, cascode_L, cascode_Vbias, cascode_recurse,cascode_is_wire,
            ampmos_W, ampmos_L,
            degen_R, degen_choice,
            inputbias_W, inputbias_L, inputbias_Vbias,

            load_chosen_part_index, load_base_W, load_ref_K,  load_out_K,
            load_L, load_topref_usemos, load_topref_R, load_topref_K,
            load_middleref_K, load_bottomref_K,load_topout_K, load_bottomout_K,
            load_Vbias
        
        Variable breakdown:
          For ddViInput:
            1:1 mapping of all ddViInput vars
          For dsIiLoad:
            chosen_part_index=load_chosen_part_index,
            loadrail_is_vdd=loadrail_is_vdd,
            base_W=load_base_W,
            ref_K=load_ref_K, out_K=load_out_K, L=load_L, 
            topref_usemos=load_topref_usemos, topref_R=load_topref_R,
            topref_K=load_topref_K,
            middleref_K=load_middleref_K,                             
            bottomref_K=load_bottomref_K,  
            topout_K=load_topout_K,
            bottomout_K=load_bottomout_K,
            Vbias=load_Vbias
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        input_part = self.ddViInput()
        load_part = self.dsIiLoad()

        #build the point_meta (pm)
        pm = PointMeta({})
        input_varmap =  input_part.unityVarMap()
        load_varmap = {
            'chosen_part_index':'load_chosen_part_index',
            'loadrail_is_vdd':'loadrail_is_vdd',
            'base_W':'load_base_W',
            'ref_K':'load_ref_K', 'out_K':'load_out_K', 'L':'load_L', 
            'topref_usemos':'load_topref_usemos', 'topref_R':'load_topref_R',
            'topref_K':'load_topref_K',
            'middleref_K':'load_middleref_K',                           
            'bottomref_K':'load_bottomref_K',  
            'topout_K':'load_topout_K',
            'bottomout_K':'load_bottomout_K',
            'Vbias':'load_Vbias'}
        pm = self.updatePointMeta(pm, input_part, input_varmap)
        pm = self.updatePointMeta(pm, load_part, load_varmap, True)
        
        #build the main part
        part = CompoundPart(['Vin1', 'Vin2', 'Iout', 'loadrail','opprail'],
                            pm, name)

        n1 = part.addInternalNode()
        n2 = part.addInternalNode()

        part.addPart( input_part,
                      {'Vin1':'Vin1', 'Vin2':'Vin2', 'Iout1':n1, 'Iout2':n2,
                       'loadrail':'loadrail', 'opprail':'opprail'},
                      input_varmap )
        part.addPart( load_part,
                      {'Iin1':n1, 'Iin2':n2, 'Iout':'Iout',
                       'loadrail':'loadrail'},
                      load_varmap )
        
        self._parts[name] = part
        return part


    def dsViAmp1_VddGndPorts(self):
        """
        Description: Just like dsViAmp1, except it has 'Vdd' and 'gnd'
          as external ports, which are less flexible than dsViAmp1's
          ports of 'loadrail' and 'opprail'.  But it makes it directly
          interfaceable to the outside world (unlike dsViAmp1 on its own).
          
        Ports: Vin1, Vin2, Iout, Vdd, gnd
          (Vin1 and Vin2 are differential.)
        
        Variables:
          -like dsViAmp1, except replace its 'loadrail_is_vdd'
           with 'chosen_part_index'
        
        Variable breakdown:
          For overall part: chosen_part_index (==loadrail_is_vdd)
            0: set 'loadrail' of dsViAmp1 to 'gnd', and 'opprail' to 'Vdd'
            1: set 'loadrail' of dsViAmp1 to 'Vdd', and 'opprail' to 'gnd'
          For dsViamp1:
            All, a 1:1 mapping, except: loadrail_is_vdd=chosen_part_index
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        amp_part = self.dsViAmp1()

        #build the point_meta (pm)
        pm = PointMeta({})
        pm = self.updatePointMeta(pm, amp_part, amp_part.unityVarMap())
        del pm['loadrail_is_vdd']
        # -remember: don't need to add 'chosen_part_index' to pm
        #  because FlexParts do that automatically

        varmap = amp_part.unityVarMap()
        varmap['loadrail_is_vdd'] = 'chosen_part_index'
        
        #build the main part
        part = FlexPart(['Vin1', 'Vin2', 'Iout', 'Vdd','gnd'], pm, name)

        part.addPartChoice( amp_part,
                            {'Vin1':'Vin1', 'Vin2':'Vin2', 'Iout':'Iout',
                             'loadrail':'gnd', 'opprail':'Vdd'},
                            varmap)
        part.addPartChoice( amp_part,
                            {'Vin1':'Vin1', 'Vin2':'Vin2', 'Iout':'Iout',
                             'loadrail':'Vdd', 'opprail':'gnd'},
                            varmap )
        
        #build a summaryStr
        part.addToSummaryStr('loadrail is vdd','chosen_part_index')
        part.addToSummaryStr('input is pmos (rather than nmos)', 'input_is_pmos')
        part.addToSummaryStr('folded', 'chosen_part_index == input_is_pmos')
        part.addToSummaryStr('cascode_is_wire', 'cascode_is_wire')
        part.addToSummaryStr('degen_choice (0=wire,1=resistor)', 'degen_choice')
        part.addToSummaryStr('load_chosen_part_index (0=simple CM,1=cascode CM,'
                             '2=low-voltageA CM)', 'load_chosen_part_index')
        
        self._parts[name] = part
        return part

    def ddIiLoad(self):
        """
        Description: diff-current-in, diff-current-out load.
          Merely twins up two ssIiLoads.
          
        Ports: Iout1, Iout2, loadrail, opprail
        
        Variables:
          chosen_part_index,
          loadrail_is_vdd,
          R,
          W, L, Vbias,
          loadcascode_recurse, loadcascode_W, loadcascode_L, loadcascode_Vbias
        
        Variable breakdown:
          For each ssIiLoad: 1:1 mapping

        Note: GRAIL pdf is wrong because it thinks ddIiLoad has Iin1,Iin2 when
          it actually doesn't
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        ss_part = self.ssIiLoad()

        #build the point_meta (pm)
        pm = PointMeta({})
        ss_varmap = ss_part.unityVarMap()
        pm = self.updatePointMeta(pm, ss_part, ss_varmap)
        
        #build the main part
        part = CompoundPart(['Iout1','Iout2','loadrail','opprail'],
                            pm, name)

        part.addPart( ss_part,
                      {'Iout':'Iout1','loadrail':'loadrail','opprail':'opprail'},
                      ss_varmap )
        part.addPart( ss_part,
                      {'Iout':'Iout2','loadrail':'loadrail','opprail':'opprail'},
                      ss_varmap )
        
        self._parts[name] = part
        return part

    def ddViAmp1(self):
        """
        Description: diff-voltage-in, diff-current-out 1-stage amp.
          Is a sequence of a ddViInput followed by a ddIiLoad.
          
        Ports: Vin1, Vin2, Iout1, Iout2, loadrail, opprail
        
        Variables:
          loadrail_is_vdd, input_is_pmos,
          cascode_W, cascode_L, cascode_Vbias, cascode_recurse, cascode_is_wire,
          ampmos_W, ampmos_L,
          degen_R, degen_choice,
          inputbias_W, inputbias_L, inputbias_Vbias
        
        Variable breakdown:
          For ddViInput:
            1:1 mapping of ddViInput vars
          For ddIiLoad:
            chosen_part_index=load_chosen_part_index,
            loadrail_is_vdd=loadrail_is_vdd,
            R=load_R,
            W=load_W, L=load_L, Vbias=load_Vbias,
            loadcascode_recurse, loadcascode_W, loadcascode_L, loadcascode_Vbias
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        input_part = self.ddViInput()
        load_part = self.ddIiLoad()

        #build the point_meta (pm)
        pm = PointMeta({})
        input_varmap = input_part.unityVarMap()
        load_varmap = {
            'chosen_part_index':'load_chosen_part_index',
            'loadrail_is_vdd':'loadrail_is_vdd',
            'R':'load_R', 'W':'load_W', 'L':'load_L', 'Vbias':'load_Vbias',
            'loadcascode_recurse':'loadcascode_recurse',
            'loadcascode_W':'loadcascode_W',
            'loadcascode_L':'loadcascode_L',
            'loadcascode_Vbias':'loadcascode_Vbias'}
            
        
        pm = self.updatePointMeta(pm, input_part, input_varmap)
        pm = self.updatePointMeta(pm, load_part, load_varmap, True)
        
        #build the main part
        part = CompoundPart(['Vin1','Vin2','Iout1','Iout2','loadrail','opprail'],
                            pm, name)

        part.addPart( input_part, input_part.unityPortMap(), input_varmap)
        part.addPart( load_part, load_part.unityPortMap(), load_varmap)
        
        self._parts[name] = part
        return part



    def ddViAmp1_VddGndPorts(self):
        """
        Description: Just like ddViAmp1, except it has 'Vdd' and 'gnd'
          as external ports
          
        Ports: Vin1, Vin2, Iout1, Iout2, Vdd, gnd
        
        Variables:
          -like ddViAmp1, except replace its 'loadrail_is_vdd'
           with 'chosen_part_index'
        
        Variable breakdown:
          For overall part: chosen_part_index (==loadrail_is_vdd)
            0: set 'loadrail' of ddViAmp1 to 'gnd', and 'opprail' to 'Vdd'
            1: set 'loadrail' of ddViAmp1 to 'Vdd', and 'opprail' to 'gnd'
          For ddViamp1:
            All, a 1:1 mapping, except: loadrail_is_vdd=chosen_part_index
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        amp_part = self.ddViAmp1()

        #build the point_meta (pm)
        pm = PointMeta({})
        pm = self.updatePointMeta(pm, amp_part, amp_part.unityVarMap())
        del pm['loadrail_is_vdd']
        # -remember: don't need to add 'chosen_part_index' to pm
        #  because FlexParts do that automatically

        #
        amp_functions = amp_part.unityVarMap()
        amp_functions['loadrail_is_vdd'] = 'chosen_part_index'
        
        #build the main part
        part = FlexPart(['Vin1', 'Vin2', 'Iout1', 'Iout2','Vdd','gnd'], pm, name)

        part.addPartChoice( amp_part,
                            {'Vin1':'Vin1', 'Vin2':'Vin2',
                             'Iout1':'Iout1', 'Iout2':'Iout2',
                             'loadrail':'gnd', 'opprail':'Vdd'},
                            amp_functions)
        part.addPartChoice( amp_part,
                            {'Vin1':'Vin1', 'Vin2':'Vin2',
                             'Iout1':'Iout1', 'Iout2':'Iout2',
                             'loadrail':'Vdd', 'opprail':'gnd'},
                            amp_functions )
        
        self._parts[name] = part
        return part

    def dsViAmp2_DifferentialMiddle_VddGndPorts(self):
        """
        Description: differential-voltage-in, single-ended-current out
          two-stage amplifier.  Communication between stages is
          DIFFERENTIAL (ie output of first stage is diff, and input to
          second stage is diff).  A level shifter can exist between
          the stages, as can feedback.
          
        Ports: Vin1, Vin2, Iout, Vdd, gnd
        
        Variables:
            stage1_loadrail_is_vdd, stage1_input_is_pmos,
            
            stage1_cascode_W, stage1_cascode_L, stage1_cascode_Vbias,
            stage1_cascode_recurse,cascode_is_wire,
            stage1_ampmos_W, stage1_ampmos_L,
            stage1_degen_R, stage1_degen_choice,
            stage1_inputbias_W, stage1_inputbias_L, stage1_inputbias_Vbias,

            stage2_loadrail_is_vdd, stage2_input_is_pmos,
            
            stage2_cascode_W, stage2_cascode_L, stage2_cascode_Vbias,
            stage2_cascode_recurse, stage2_cascode_is_wire,
            stage2_ampmos_W, stage2_ampmos_L,
            stage2_degen_R,
            stage2_degen_choice,
            stage2_inputbias_W, stage2_inputbias_L, stage2_inputbias_Vbias,
            stage2_load_chosen_part_index, stage2_load_base_W, stage2_load_ref_K,
            stage2_load_out_K,
            stage2_load_L, stage2_load_topref_usemos, stage2_load_topref_R,
            stage2_load_topref_K,
            stage2_load_middleref_K, stage2_load_bottomref_K,
            stage2_load_topout_K, stage2_load_bottomout_K,
            stage2_load_Vbias

            shifter_Drail_is_vdd,
            
            shifter_chosen_part_index,
            shifter_amp_W, shifter_amp_L,
            shifter_cascode_do_stack,
            shifter_cascode_D_W, shifter_cascode_D_L, shifter_cascode_D_Vbias,
            shifter_cascode_S_W, shifter_cascode_S_L, shifter_cascode_S_Vbias

            feedback_use_pmos,
            feedback_chosen_part_index, feedback_R, feedback_C,
            feedback_amp_W, feedback_amp_L,
            feedback_cascode_do_stack,
            feedback_cascode_D_W, feedback_cascode_D_L, feedback_cascode_D_Vbias,
            feedback_cascode_S_W, feedback_cascode_S_L, feedback_cascode_S_Vbias
        
        Variable breakdown:
          For ddViAmp1_VddGndPorts (stage 1): 1:1 mapping of ddViAmp1 variables,
            EXCEPT that each variable here has the prefix 'stage1_'
            
          For dsViAmp1_VddGndPorts (stage 2): 1:1 mapping of dsViAmp1 variables,
            EXCEPT with the prefix 'stage2_'
            
          For each levelShifterOrWire_VddGndPorts twin:
            use_pmos=stage1_loadrail_is_vdd,
            and all others are 1:1 with levelShifterOrWire
            EXCEPT with the prefix 'shifter_'
            
          For viFeedback_VddGndPorts: 1:1 mapping of viFeedback variables,
            EXCEPT with the prefix 'feedback_'
          
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        stage1_part = self.ddViAmp1_VddGndPorts()
        stage2_part = self.dsViAmp1_VddGndPorts()
        shifter_part = self.levelShifterOrWire_VddGndPorts()
        feedback_part = self.viFeedback_VddGndPorts()

        #build the point_meta (pm)
        pm = PointMeta({})
        stage1_varmap = {}
        for old_name in  stage1_part.point_meta.keys():
            stage1_varmap[old_name] = 'stage1_' + old_name
        stage2_varmap = {}
        for old_name in  stage2_part.point_meta.keys():
            stage2_varmap[old_name] = 'stage2_' + old_name
        shifter_varmap = {}
        for old_name in  shifter_part.point_meta.keys():
            shifter_varmap[old_name] = 'shifter_' + old_name
        feedback_varmap = {}
        for old_name in  feedback_part.point_meta.keys():
            feedback_varmap[old_name] = 'feedback_' + old_name
            
        pm = self.updatePointMeta(pm, stage1_part, stage1_varmap)
        pm = self.updatePointMeta(pm, stage2_part, stage2_varmap)
        pm = self.updatePointMeta(pm, shifter_part, shifter_varmap)
        pm = self.updatePointMeta(pm, feedback_part, feedback_varmap)

        #build functions
        stage1_functions = stage1_varmap
        stage2_functions = stage2_varmap
        shifter_functions = shifter_varmap
        feedback_functions = feedback_varmap
        
        #build the main part
        part = CompoundPart(['Vin1','Vin2', 'Iout','Vdd','gnd'], pm, name)

        stage1_out1 = part.addInternalNode()
        stage1_out2 = part.addInternalNode()
        stage2_in1 = part.addInternalNode()
        stage2_in2 = part.addInternalNode()

        # switch the inputs to make the non-inverting amplifier inverting
        part.addPart( stage1_part,
                      {'Vin1':'Vin2', 'Vin2':'Vin1','Iout1':stage1_out1,
                       'Vdd':'Vdd', 'gnd':'gnd'},
                      stage1_functions)
        part.addPart( stage2_part,
                      {'Vin1':stage2_in1, 'Vin2':stage2_in2, 'Iout':'Iout',
                       'Vdd':'Vdd', 'gnd':'gnd'},
                      stage2_functions)
        part.addPart( shifter_part,
                      {'Vin':stage1_out1, 'Iout':stage2_in1,
                       'Vdd':'Vdd', 'gnd':'gnd'},
                      shifter_functions) #twin #1
        part.addPart( shifter_part,
                      {'Vin':stage1_out2, 'Iout':stage2_in2,
                       'Vdd':'Vdd', 'gnd':'gnd'},
                      shifter_functions) #twin #2

        #FIXME: is feedback hooked up ok???
        # -especially loadrail, opprail?
        part.addPart( feedback_part,
                      {'Ifpos':stage1_out1, 'Ifneg':'gnd',
                       'VsensePos':'Iout', 'VsenseNeg':'gnd'},
                      feedback_functions)
        
        self._parts[name] = part
        return part

    def dsViAmp2_SingleEndedMiddle_VddGndPorts(self):
        """
        Description: differential-voltage-in, single-ended-current out
          two-stage amplifier.  Communication between stages is
          SINGLE-ended (ie output of first stage is single-ended, and input to
          second stage is single-ended).  A level shifter can exist between
          the stages, as can feedback.
          
        Ports: Vin1, Vin2, Iout, Vdd, gnd
        
        Variables:
            stage1_loadrail_is_vdd, stage1_input_is_pmos
            
            stage1_cascode_W, stage1_cascode_L, stage1_cascode_Vbias,
            stage1_cascode_recurse, stage1_cascode_is_wire,
            stage1_ampmos_W, stage1_ampmos_L,
            stage1_degen_R,
            stage1_degen_choice,
            stage1_inputbias_W, stage1_inputbias_L, stage1_inputbias_Vbias,
            stage1_load_chosen_part_index, stage1_load_base_W, stage1_load_ref_K,
            stage1_load_out_K,
            stage1_load_L, stage1_load_topref_usemos, stage1_load_topref_R,
            stage1_load_topref_K,
            stage1_load_middleref_K, stage1_load_bottomref_K,
            stage1_load_topout_K, stage1_load_bottomout_K,
            stage1_load_Vbias

            stage2_loadrail_is_vdd,  stage2_input_is_pmos,
            
            stage2_inputcascode_W, stage2_inputcascode_L,
            stage2_inputcascode_Vbias, stage2_inputcascode_recurse,
            stage2_ampmos_W, stage2_ampmos_L,
            stage2_degen_R, stage2_degen_choice,
            stage2_inputbias_W, stage2_inputbias_L, stage2_inputbias_Vbias
            stage2_load_part_index,
            stage2_load_R,
            stage2_load_W, stage2_load_L, stage2_load_Vbias,
            stage2_loadcascode_recurse, stage2_loadcascode_W,
            stage2_loadcascode_L, stage2_loadcascode_Vbias

            shifter_Drail_is_vdd,
            
            shifter_chosen_part_index,
            shifter_amp_W, shifter_amp_L,
            shifter_cascode_do_stack,
            shifter_cascode_D_W, shifter_cascode_D_L, shifter_cascode_D_Vbias,
            shifter_cascode_S_W, shifter_cascode_S_L, shifter_cascode_S_Vbias

            feedback_use_pmos,
            feedback_chosen_part_index, feedback_R, feedback_C,
            feedback_amp_W, feedback_amp_L,
            feedback_cascode_do_stack,
            feedback_cascode_D_W, feedback_cascode_D_L, feedback_cascode_D_Vbias,
            feedback_cascode_S_W, feedback_cascode_S_L, feedback_cascode_S_Vbias
        
        Variable breakdown:
          For stage 1 dsViAmp1_VddGndPorts (stage 1):
            1:1 mapping of ddViAmp1_VddGndPorts variables,
            EXCEPT that each variable here has the prefix 'stage1_'
            
          For stage 2 ssViAmp1_VddGndPorts (stage 2):
            1:1 mapping of ssViAmp1_VddGndPorts variables,
            EXCEPT with the prefix 'stage2_'
            
          For levelShifterOrWire_VddGndPorts:
            levelShifterOrWire_VddGndPorts
            EXCEPT with the prefix 'shifter_'
            
          For viFeedback:
            Currently a HACK to just use a capacitor!!
            1:1 mapping of viFeedback variables,
            EXCEPT with the prefix 'feedback_'
          
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        stage1_part = self.dsViAmp1_VddGndPorts()
        stage2_part = self.ssViAmp1_VddGndPorts()
 #       shifter_part = self.levelShifterOrWire_VddGndPorts()
        feedback_part = self.capacitor() #note the HACK for just capacitor

        #build the point_meta (pm)
        pm = PointMeta({})
        stage1_varmap = {}
        for old_name in  stage1_part.point_meta.keys():
            stage1_varmap[old_name] = 'stage1_' + old_name
        stage2_varmap = {}
        for old_name in  stage2_part.point_meta.keys():
            stage2_varmap[old_name] = 'stage2_' + old_name
 #       shifter_varmap = {}
 #       for old_name in  shifter_part.point_meta.keys():
 #           shifter_varmap[old_name] = 'shifter_' + old_name
        feedback_varmap = {}
        for old_name in  feedback_part.point_meta.keys():
            feedback_varmap[old_name] = 'feedback_' + old_name
            
        pm = self.updatePointMeta(pm, stage1_part, stage1_varmap)
        del pm['stage1_chosen_part_index']
        pm['stage1_loadrail_is_vdd']= self.buildVarMeta('bool_var',
                                                        'stage1_loadrail_is_vdd')
        
        pm = self.updatePointMeta(pm, stage2_part, stage2_varmap)
        del pm['stage2_chosen_part_index']
        pm['stage2_loadrail_is_vdd']= self.buildVarMeta('bool_var',
                                                        'stage2_loadrail_is_vdd')
        
#        pm = self.updatePointMeta(pm, shifter_part, shifter_varmap)
#        del pm['shifter_chosen_part_index']
#        pm['shifter_Drail_is_vdd'] = self.buildVarMeta('bool_var',
#                                                       'shifter_Drail_is_vdd')
        
        pm = self.updatePointMeta(pm, feedback_part, feedback_varmap)
        
        

        #build functions
        stage1_functions = stage1_varmap
        stage1_functions['chosen_part_index'] = 'stage1_loadrail_is_vdd'
        
        stage2_functions = stage2_varmap
        stage2_functions['chosen_part_index'] = 'stage2_loadrail_is_vdd'
        
#        shifter_functions = shifter_varmap
#        shifter_functions['chosen_part_index'] = 'shifter_Drail_is_vdd'
        
        feedback_functions = feedback_varmap
        
        #build the main part
        part = CompoundPart(['Vin1','Vin2', 'Iout', 'Vdd', 'gnd'], pm, name)

        stage1_out = part.addInternalNode()
        stage2_in = part.addInternalNode()
        
        # switch the inputs to make the non-inverting amplifier inverting
        part.addPart( stage1_part,
                      {'Vin1':'Vin2', 'Vin2':'Vin1',
                       'Iout':stage1_out, 'Vdd':'Vdd', 'gnd':'gnd'},
                      stage1_functions)
        part.addPart( stage2_part,
#                      {'Vin':stage2_in, 'Iout':'Iout',
                      {'Vin':stage1_out, 'Iout':'Iout',
                       'Vdd':'Vdd', 'gnd':'gnd'},
                      stage2_functions)
#        part.addPart( shifter_part,
#                      {'Vin':stage1_out, 'Iout':stage2_in,
#                       'Vdd':'Vdd', 'gnd':'gnd'},
#                      shifter_functions)

        #Note: this is a HACK for just capacitor!
        part.addPart( feedback_part, {'1':'Iout','2':stage1_out},
                      feedback_functions)
        

        #build a summaryStr
        part.addToSummaryStr('STAGE 1:','')
        part.addToSummaryStr('  loadrail is vdd','stage1_loadrail_is_vdd')
        part.addToSummaryStr('  input is pmos', 'stage1_input_is_pmos')
        part.addToSummaryStr('  folded','stage1_loadrail_is_vdd == stage1_input_is_pmos')
        part.addToSummaryStr('  degen type (0=wire,1=resistor)', 'stage1_degen_choice')
        part.addToSummaryStr('  load type (0=resistor,1=biasedMos,2=ssIiLoad_Cascoded)', 'stage1_load_chosen_part_index')
        
        part.addToSummaryStr('','')
        part.addToSummaryStr('STAGE 2:','')
        part.addToSummaryStr('  loadrail is vdd','stage2_loadrail_is_vdd')
        part.addToSummaryStr('  input is pmos', 'stage2_input_is_pmos')
        part.addToSummaryStr('  folded','stage2_loadrail_is_vdd == stage2_input_is_pmos')
        part.addToSummaryStr('  degen type (0=wire,1=resistor)', 'stage2_degen_choice')
        part.addToSummaryStr('  load type (0=resistor,1=biasedMos,2=ssIiLoad_Cascoded)', 'stage2_load_part_index')
        
#         part.addToSummaryStr('','')
#         part.addToSummaryStr('LEVEL SHIFTER:','')
#         part.addToSummaryStr('  D-rail is vdd (==implement in nmos if not wire)','shifter_Drail_is_vdd')
#         part.addToSummaryStr('  is wire','shifter_use_wire')
#         part.addToSummaryStr('  stack cascode','shifter_cascode_do_stack')
        
        part.addToSummaryStr('','')
        part.addToSummaryStr('FEEDBACK:','')
        part.addToSummaryStr('  (just currently a capacitor)','')
        
        self._parts[name] = part
        return part

    def dsViAmp2_VddGndPorts(self):
        """
        Description: differential-voltage-in, single-ended-current out
          two-stage amplifier.  Can be instantiated with having
          differential communication between stages, or single-ended
          (it's a FlexPart).
          
        Ports: Vin1, Vin2, Iout, stage1_loadrail, stage2_loadrail,
          stage1_opprail, stage2_opprail
        
        Variables: A merge of the variables of dsViAmp2_DifferentialMiddle
         and of dsViAmp2_SingleEndedMiddle
         -Plus 'chosen_part_index'
        
        Variable breakdown:
          For overall part: chosen_part_index
            0 : choose dsViAmp2_DifferentialMiddle_VddGndPorts
            1 : choose dsViAmp2_SingleEndedMiddle_VddGndPorts
          For  dsViAmp2_DifferentialMiddle_VddGndPorts: 1:1 mapping of its vars
          For  dsViAmp2_SingleEndedMiddle_VddGndPorts: 1:1 mapping of its vars
        """ 
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        dds_part = self.dsViAmp2_DifferentialMiddle_VddGndPorts()
        dss_part = self.dsViAmp2_SingleEndedMiddle_VddGndPorts()

        #build the point_meta (pm)
        pm = PointMeta({})
        dds_varmap = dds_part.unityVarMap()
        dss_varmap = dss_part.unityVarMap()
        
        pm = self.updatePointMeta(pm, dds_part, dds_varmap)
        pm = self.updatePointMeta(pm, dss_part, dss_varmap, True)

        #build the main part
        part = FlexPart(dss_part.externalPortnames(), pm, name)
        
        part.addPartChoice( dds_part, dds_part.unityPortMap(), dds_varmap)
        part.addPartChoice( dss_part, dss_part.unityPortMap(), dss_varmap)
        
        self._parts[name] = part
        return part
 
    def dsViAmp_VddGndPorts(self):
        """
        Description: chooses between dsViAmp1_VddGndPorts and
          dsViAmp2_VddGndPorts
          
        Ports: Vin1, Vin2, Iout, Vdd, gnd
        
        Variables: same as dsViAmp2
        
        Variable breakdown:
          For overall part: chosen_part_index (=do_two_stage)
            0 : choose dsViAmp1_VddGndPorts
            1 : choose dsViAmp2_VddGndPorts
          For  dsViAmp1_VddGndPorts: use all the stage1_xxx variables to set
            its corresponding xxx variables          
          For  dsViAmp2_VddGndPorts: 1:1 mapping of its vars
        """
        name = whoami()
        if self._parts.has_key(name): return self._parts[name]

        #parts to embed
        onestage_part = self.dsViAmp1_VddGndPorts()
        twostage_part = self.dsViAmp2_VddGndPorts()

        #build the point_meta (pm)
        pm = PointMeta({})
        twostage_varmap = twostage_part.unityVarMap()
        onestage_varmap = {}
        for new_name in onestage_part.point_meta.keys():
            old_name = 'stage1_' + new_name
            onestage_varmap[new_name] = old_name
        pm = self.updatePointMeta(pm, twostage_part, twostage_varmap)
        
        #build the main part
        part = FlexPart(['Vin1', 'Vin2', 'Iout', 'Vdd', 'gnd'], pm, name)

        part.addPartChoice( onestage_part, onestage_part.unityPortMap(),
                            onestage_varmap)
        part.addPartChoice( twostage_part, twostage_part.unityPortMap(),
                            twostage_varmap)
        
        self._parts[name] = part
        return part


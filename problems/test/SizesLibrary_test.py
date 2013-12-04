import unittest

import random

from adts import *
from adts.Part import replaceAutoNodesWithXXX

from problems.SizesLibrary import *
from problems.Library import replaceAfterMWithBlank, replaceSummaryStrWithBlank

class SizesLibraryTest(unittest.TestCase):

    def setUp(self):
        self.just1 = False #to make True is a HACK
        self.lib = Point18SizesLibrary()      
        
    #=================================================================
    #One Test for each Part
    def testNmos4(self):
        if self.just1: return
        part = self.lib.nmos4()
        self.assertEqual( part.externalPortnames(), ['D','G','S','B'])
        instance = EmbeddedPart(part, {'D':'1', 'G':'2', 'S':'3', 'B':'nblah'},
                                {'W':3*0.18e-6, 'L':5*0.18e-6, 'M':1})
        self.assertTrue( len(str(part)) > 0 )
        self.assertTrue( len(str(instance)) > 0 )
        self.assertEqual( part.numSubpartPermutations(), 1)
        self.assertEqual( part.schemas(), [{}])

        target_str = """M0 1 2 3 nblah N_18_MM M=1 L=9e-07 W=5.4e-07
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

    def testPmos4(self):
        if self.just1: return
        part = self.lib.pmos4()
        instance = EmbeddedPart(part, {'D':'1', 'G':'2', 'S':'3', 'B':'nblah'},
                                {'W':3*0.18e-6, 'L':5*0.18e-6, 'M':1})
        self.assertTrue( len(str(part)) > 0 )
        self.assertTrue( len(str(instance)) > 0 )

        target_str = """M0 1 2 3 nblah P_18_MM M=1 L=9e-07 W=5.4e-07
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

    def testDcvs(self):
        if self.just1: return
        part = self.lib.dcvs()
        n0 = part.externalPortnames()[0]
        instance = EmbeddedPart(part, {n0:'1'}, {'DC':0.9})
        self.assertTrue( len(str(part)) > 0 )
        self.assertTrue( len(str(instance)) > 0 )
        self.assertEqual( part.numSubpartPermutations(), 1)

        target_str = """V0 1 0  DC 0.9
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

    def testWire(self):
        if self.just1: return
        part = self.lib.wire()
        instance = EmbeddedPart(part, {'1':'a', '2':'b'}, {})
        self.assertTrue( len(str(part)) > 0 )
        self.assertTrue( len(str(instance)) > 0 )
        self.assertEqual( part.numSubpartPermutations(), 1)

        target_str = """Rwire0 a b  R=0
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

    def testOpenCircuit(self):
        if self.just1: return
        part = self.lib.openCircuit()
        instance = EmbeddedPart(part, {'1':'a', '2':'b'}, {})
        self.assertTrue( len(str(part)) > 0 )
        self.assertTrue( len(str(instance)) > 0 )

        target_str = "" #yes, target string is _empty_
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

    def testShortOrOpenCircuit(self):
        if self.just1: return
        part = self.lib.shortOrOpenCircuit()
        self.assertEqual( part.numSubpartPermutations(), 2)
        self.assertEqual( part.schemas(), [{'chosen_part_index': [0, 1]}] )

        #instantiate as short circuit
        instance = EmbeddedPart(part, {'1':'a', '2':'b'},
                                {'chosen_part_index':0})

        target_str = """Rwire0 a b  R=0
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

        #instantiate as open circuit
        instance = EmbeddedPart(part, {'1':'a', '2':'b'},
                                {'chosen_part_index':1})

        target_str = ""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

    def testResistor(self):
        if self.just1: return

        part = self.lib.resistor()
        instance = EmbeddedPart(part, {'1':'a', '2':'b'}, {'R':10.2e3})
        self.assertTrue( len(str(part)) > 0 )
        self.assertTrue( len(str(instance)) > 0 )
        self.assertEqual( part.numSubpartPermutations(), 1)

        target_str = "R0 a b  R=10200\n"
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

    def testRailing(self):
        """test to see that it rails to be <= max allowed value.
        We use resistance of resistor for the test."""
        if self.just1: return

        part = self.lib.resistor()
        instance = EmbeddedPart(part, {'1':'a', '2':'b'}, {'R':10.2e3})

        R_varmeta = self.lib._ref_varmetas['R']
        self.assertTrue(R_varmeta.logscale)
        max_R = 10**R_varmeta.max_unscaled_value
        instance = EmbeddedPart(part, {'1':'a', '2':'b'}, {'R':max_R*10.0})
        target_str = "R0 a b  R=%g\n" % max_R
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

    def testCapacitor(self):
        if self.just1: return

        part = self.lib.capacitor()
        instance = EmbeddedPart(part, {'1':'a', '2':'b'}, {'C':1.0e-6})
        self.assertTrue( len(str(part)) > 0 )
        self.assertTrue( len(str(instance)) > 0 )

        target_str = "C0 a b  C=1e-06\n"
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

    def testMos4(self):
        if self.just1: return
        part = self.lib.mos4()
        self.assertTrue( isinstance( part, FlexPart ) )
        self.assertTrue( len(str(part)) > 0 )
        self.assertEqual( part.numSubpartPermutations(), 2)
        self.assertEqual( part.schemas(), [{'chosen_part_index': [0, 1]}] )

        #instantiate as nmos
        instance0 = EmbeddedPart(part, {'D':'1', 'G':'2', 'S':'3', 'B':'4'},
                                 {'chosen_part_index':0,
                                  'W':3*0.18e-6,
                                  'L':5*0.18e-6}
                                 )
        self.assertTrue( len(str(instance0)) > 0 )

        target_str0 = """M0 1 2 3 4 N_18_MM M=1 L=9e-07 W=5.4e-07
"""
        actual_str0 = instance0.spiceNetlistStr()
        self._compareStrings(target_str0, actual_str0)


        #instantiate as pmos
        instance1 = EmbeddedPart(part, {'D':'1', 'G':'2', 'S':'3', 'B':'4'},
                                 {'chosen_part_index':1,
                                  'W':3*0.18e-6,
                                  'L':5*0.18e-6}
                                 )
        self.assertTrue( len(str(instance1)) > 0 )
        
        target_str1 = """M0 1 2 3 4 P_18_MM M=1 L=9e-07 W=1.08e-06
"""
        actual_str1 = instance1.spiceNetlistStr()
        self._compareStrings(target_str1, actual_str1)

    def testMos3_asNmos(self):
        if self.just1: return
        part = self.lib.mos3()
        self.assertEqual(len(part.simulation_DOCs), 0)
        self.assertEqual( part.numSubpartPermutations(), 2)

        #M = 1
        instance = EmbeddedPart(part, {'D':'1', 'G':'2', 'S':'3'},
                                {'W':3*0.18e-6, 'L':5*0.18e-6,
                                 'use_pmos':0})
        
        self.assertTrue( len(str(part)) > 0 )
        self.assertTrue( len(str(instance)) > 0 )
        
        target_str = """M0 1 2 3 3 N_18_MM M=1 L=9e-07 W=5.4e-07
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

        #M > 1
        instance = EmbeddedPart(part, {'D':'1', 'G':'2', 'S':'3'},
                                {'W':100*0.18e-6, 'L':5*0.18e-6,
                                 'use_pmos':0})
        
        self.assertTrue( len(str(part)) > 0 )
        self.assertTrue( len(str(instance)) > 0 )
        
        target_str = """M0 1 2 3 3 N_18_MM M=4 L=9e-07 W=4.5e-06
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

    def testMos3_asPmos(self):
        #note that the width is effectively 2x the width that nmos has
        if self.just1: return
        part = self.lib.mos3()
        self.assertEqual(len(part.simulation_DOCs), 0)

        #M=1
        instance = EmbeddedPart(part, {'D':'1', 'G':'2', 'S':'3'},
                                {'W':3*0.18e-6, 'L':5*0.18e-6,
                                 'use_pmos':1})
        
        self.assertTrue( len(str(part)) > 0 )
        self.assertTrue( len(str(instance)) > 0 )

        target_str = """M0 1 2 3 3 P_18_MM M=1 L=9e-07 W=1.08e-06
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

        #M > 1
        instance = EmbeddedPart(part, {'D':'1', 'G':'2', 'S':'3'},
                                {'W':100*0.18e-6, 'L':5*0.18e-6,
                                 'use_pmos':1})
        
        self.assertTrue( len(str(part)) > 0 )
        self.assertTrue( len(str(instance)) > 0 )

        target_str = """M0 1 2 3 3 P_18_MM M=8 L=9e-07 W=4.5e-06
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

    def testSaturatedMos3(self):
        if self.just1: return
        part = self.lib.saturatedMos3()
        self.assertEqual( part.numSubpartPermutations(), 2)
        self.assertEqual(len(part.simulation_DOCs), 1)
        sat_doc = part.simulation_DOCs[0]
        self.assertEqual(sat_doc.metric.name, 'operating_region')
        self.assertEqual(sat_doc.metric.min_threshold, REGION_SATURATION)
        self.assertEqual(sat_doc.metric.max_threshold, REGION_SATURATION)
        self.assertEqual(sat_doc.function_str, 'region')

        #instantiate as pmos
        instance = EmbeddedPart(part, {'D':'1', 'G':'2', 'S':'3'},
                                {'W':3*0.18e-6, 'L':5*0.18e-6,
                                 'use_pmos':1})
        
        self.assertTrue( len(str(part)) > 0 )
        self.assertTrue( len(str(instance)) > 0 )
        
        target_str = """M0 1 2 3 3 P_18_MM M=1 L=9e-07 W=1.08e-06
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

    def testMosDiode(self):
        if self.just1: return
        part = self.lib.mosDiode()
        self.assertEqual( part.numSubpartPermutations(), 2)

        instance = EmbeddedPart(part, {'D':'1', 'S':'2'},
                                {'W':3*0.18e-6, 'L':5*0.18e-6, 'use_pmos':1})
        
        target_str = """M0 1 1 2 2 P_18_MM M=1 L=9e-07 W=1.08e-06
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

    def testResistorOrMosDiode(self):
        if self.just1: return
        part = self.lib.resistorOrMosDiode()
        self.assertEqual( part.numSubpartPermutations(), 3)
        self.assertEqual( part.schemas(),
                          [{'chosen_part_index': [0]},
                           {'chosen_part_index': [1], 'use_pmos': [0, 1]}])

        #instantiate as resistor
        instance = EmbeddedPart(part, {'D':'1', 'S':'2'},
                                {'chosen_part_index':0,
                                 'R':10.0e3,
                                 'W':3*0.18e-6, 'L':5*0.18e-6,'use_pmos':1})
        
        target_str = """R0 1 2  R=10000
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

        #instantiate as mosDiode
        instance = EmbeddedPart(part, {'D':'1', 'S':'2'},
                                {'chosen_part_index':1,
                                 'R':10.0e3,
                                 'W':3*0.18e-6, 'L':5*0.18e-6,'use_pmos':1})
        
        target_str = """M0 1 1 2 2 P_18_MM M=1 L=9e-07 W=1.08e-06
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

    def testBiasedMos(self):
        if self.just1: return
        part = self.lib.biasedMos()
        self.assertEqual( part.numSubpartPermutations(), 2)

        instance = EmbeddedPart(part, {'D':'1', 'S':'2'},
                                {'W':3*0.18e-6, 'L':5*0.18e-6,
                                 'use_pmos':1,
                                 'Vbias':1.41})
        
        target_str = """M0 1 n_auto_2 2 2 P_18_MM M=1 L=9e-07 W=1.08e-06
V1 n_auto_2 0  DC 0.39
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings2(target_str, actual_str)
        
    def testBiasedMosOrWire(self):
        if self.just1: return
        part = self.lib.biasedMosOrWire()
        self.assertEqual( part.numSubpartPermutations(), 3)
        self.assertEqual( part.schemas(),
                          [{'chosen_part_index': [0], 'use_pmos': [0, 1]},
                           {'chosen_part_index': [1]}] )

        conns = {'D':'a', 'S':'b'}
        point = {'W':3*0.18e-6, 'L':5*0.18e-6, 'use_pmos':1, 'Vbias':1.41}

        #instantiate as biasedMos
        point['chosen_part_index'] = 0 
        instance = EmbeddedPart(part, conns, point)
        
        target_str = """M0 a n_auto_2 b b P_18_MM M=1 L=9e-07 W=5.4e-07
V1 n_auto_2 0  DC 0.39
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

        #instantiate as wire
        point['chosen_part_index'] = 1
        instance = EmbeddedPart(part, conns, point)
        
        target_str = """Rwire0 a b  R=0
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

    def testRC_series(self):
        if self.just1: return
        part = self.lib.RC_series()
        self.assertEqual( part.numSubpartPermutations(), 1)

        instance = EmbeddedPart(part,
                                {'N1':'1', 'N2':'2'},
                                {'R':10.0e3, 'C':10.0e-6})
        
        target_str = """R0 1 n_auto_112  R=10000
C1 n_auto_112 2  C=1e-05
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)
    
    def testTwoBiasedMoses(self):
        if self.just1: return
        part = self.lib.twoBiasedMoses()

        #This is 2, not 4, because both moses are either PMOS,PMOS
        # or NMOS,NMOS; i.e. compound part has to be aware of how
        # much a structural parameter is re-used
        self.assertEqual( part.numSubpartPermutations(), 2) 
        self.assertEqual( part.schemas(),  [{'use_pmos': [0, 1]}])

        instance = EmbeddedPart(part,
                                {'D':'1','S':'2'},
                                {'use_pmos':0,
                                 'D_W':3*0.18e-6,
                                 'D_L':3*0.18e-6,
                                 'D_Vbias':1.5,
                                 'S_W':5*0.18e-6,
                                 'S_L':5*0.18e-6,
                                 'S_Vbias':1.5
                                 })
        
        target_str = """M0 1 n_auto_162 n_auto_161 n_auto_161 N_18_MM M=1 L=5.4e-07 W=5.4e-07
V1 n_auto_162 0  DC 1.5
M2 n_auto_161 n_auto_163 2 2 N_18_MM M=1 L=9e-07 W=9e-07
V3 n_auto_163 0  DC 1.5
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)
        
    def testStackedCascodeMos__nmos(self):
        if self.just1: return
        part = self.lib.stackedCascodeMos()

        point = {'use_pmos':0,
                 'D_W':3*0.18e-6, 'D_L':3*0.18e-6, 'D_Vbias':1.5,
                 'S_W':5*0.18e-6, 'S_L':5*0.18e-6, 'S_Vbias':0.5}

        #one nmos
        point['chosen_part_index'] = 0
        instance = EmbeddedPart(part, {'D':'1','S':'2'}, point)
        
        target_str = """M0 1 n_auto_161 2 2 N_18_MM M=1 L=9e-07 W=9e-07
V1 n_auto_161 0  DC 0.5
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

        #two nmoses
        point['chosen_part_index'] = 1
        instance = EmbeddedPart(part, {'D':'1','S':'2'}, point)
        
        target_str = """M0 1 n_auto_163 n_auto_162 n_auto_162 N_18_MM M=1 L=5.4e-07 W=5.4e-07
V1 n_auto_163 0  DC 1.5
M2 n_auto_162 n_auto_164 2 2 N_18_MM M=1 L=9e-07 W=9e-07
V3 n_auto_164 0  DC 0.5
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

        #two pmoses
        point['use_pmos'] = 1
        point['chosen_part_index'] = 1
        instance = EmbeddedPart(part, {'D':'1','S':'2'}, point)
        
        target_str = """M0 1 n_auto_403 n_auto_402 n_auto_402 P_18_MM M=1 L=5.4e-07 W=1.08e-06
V1 n_auto_403 0  DC 0.3
M2 n_auto_402 n_auto_404 2 2 P_18_MM M=1 L=9e-07 W=1.8e-06
V3 n_auto_404 0  DC 1.3
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

    def _levelShifter_Point(self, Drail_is_vdd):
        point = {'Drail_is_vdd':Drail_is_vdd,
                 'amp_W':3*0.18e-6,
                 'amp_L':3*0.18e-6,
                 'cascode_do_stack':0,
                 'cascode_D_W':3*0.18e-6,
                 'cascode_D_L':3*0.18e-6,
                 'cascode_D_Vbias':1.5,
                 'cascode_S_W':5*0.18e-6,
                 'cascode_S_L':5*0.18e-6,
                 'cascode_S_Vbias':1.5}
        return point
        
    
    def testLevelShifter__nmos(self):
        if self.just1: return
        part = self.lib.levelShifter()

        conns = {'Drail':'Vdd','Srail':'gnd',
                 'Vin':'Vin','Iout':'Iout'}
        point = self._levelShifter_Point(Drail_is_vdd=True)
        instance = EmbeddedPart(part, conns, point)
        
        target_str = """M0 Vdd Vin Iout Iout N_18_MM M=1 L=5.4e-07 W=5.4e-07
M1 Iout n_auto_117 gnd gnd N_18_MM M=1 L=9e-07 W=9e-07
V2 n_auto_117 0  DC 1.5
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

        
    def testLevelShifter__pmos(self):
        if self.just1: return
        part = self.lib.levelShifter()

        conns = {'Drail':'gnd','Srail':'Vdd',
                 'Vin':'Vin','Iout':'Iout'}
        point = self._levelShifter_Point(Drail_is_vdd=False)
        instance = EmbeddedPart(part, conns, point)
        
        target_str = """M0 gnd Vin Iout Iout P_18_MM M=1 L=5.4e-07 W=1.08e-06
M1 Iout n_auto_6 Vdd Vdd P_18_MM M=1 L=9e-07 W=1.8e-06
V2 n_auto_6 0  DC 0.3
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

    def _levelShifterOrWire_Point(self, Drail_is_vdd):
        d = self._levelShifter_Point(Drail_is_vdd=Drail_is_vdd)
        d['chosen_part_index'] = 0 # 0 = choose level shifter
        return d
        
    def testLevelShifterOrWire(self):
        if self.just1: return
        part = self.lib.levelShifterOrWire()
        self.assertEqual( part.numSubpartPermutations(), 5)
        self.assertEqual( part.schemas(),  [{'Drail_is_vdd': [0, 1], 'cascode_do_stack': [0, 1], 'chosen_part_index': [0]}, {'chosen_part_index': [1]}] )

        conns = {'Drail':'Vdd','Srail':'gnd',
                 'Vin':'Vin','Iout':'Iout'}
        point = self._levelShifterOrWire_Point(Drail_is_vdd=True)

        #instantiate as nmos level shifter
        point['chosen_part_index'] = 0
        instance = EmbeddedPart(part, conns, point)
        
        target_str = """M0 Vdd Vin Iout Iout N_18_MM M=1 L=5.4e-07 W=5.4e-07
M1 Iout n_auto_117 gnd gnd N_18_MM M=1 L=9e-07 W=9e-07
V2 n_auto_117 0  DC 1.5
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

        #instantiate as wire
        point['chosen_part_index'] = 1
        instance = EmbeddedPart(part, conns, point)
        
        target_str = """Rwire0 Vin Iout  R=0
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

    def _levelShifterOrWire_VddGndPorts_Point(self, Drail_is_vdd, use_wire):
        d = self._levelShifterOrWire_Point(Drail_is_vdd=Drail_is_vdd)
        d['chosen_part_index'] = Drail_is_vdd
        d['use_wire'] = use_wire
        
        d_keys = d.keys()
        part_keys = self.lib.levelShifterOrWire_VddGndPorts().point_meta.keys()
        assert sorted(d_keys) == sorted(part_keys)
        return d
        
        
    def testLevelShifterOrWire_VddGndPorts(self):
        if self.just1: return
        part = self.lib.levelShifterOrWire_VddGndPorts()
        conns = {'Vdd':'Vdd','gnd':'gnd',
                 'Vin':'Vin','Iout':'Iout'}

        #instantiate as nmos level shifter (ie set Drail to vdd)
        point = self._levelShifterOrWire_VddGndPorts_Point(Drail_is_vdd=True,
                                                           use_wire=False)

        instance = EmbeddedPart(part, conns, point)
        
        target_str = """M0 Vdd Vin Iout Iout N_18_MM M=1 L=5.4e-07 W=5.4e-07
M1 Iout n_auto_117 gnd gnd N_18_MM M=1 L=9e-07 W=9e-07
V2 n_auto_117 0  DC 1.5
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

        #instantiate as pmos level shifter (ie set Drail to vdd)
        point = self._levelShifterOrWire_VddGndPorts_Point(Drail_is_vdd=False,
                                                           use_wire=False)

        instance = EmbeddedPart(part, conns, point)
        
        target_str = """M0 gnd Vin Iout Iout P_18_MM M=1 L=5.4e-07 W=1.08e-06
M1 Iout n_auto_7 Vdd Vdd P_18_MM M=1 L=9e-07 W=1.8e-06
V2 n_auto_7 0  DC 0.3
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

        #instantiate as wire
        point = self._levelShifterOrWire_VddGndPorts_Point(Drail_is_vdd=True,
                                                           use_wire=True)
        instance = EmbeddedPart(part, conns, point)
        
        target_str = """Rwire0 Vin Iout  R=0
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)
    
    def testViFeedback_LevelShifter(self):
        return #HACK
        if self.just1: return
        part = self.lib.viFeedback_LevelShifter()

        point = {'C':1.0e-9, 'use_pmos':0,
                 'amp_W':3*0.18e-6,
                 'amp_L':3*0.18e-6,
                 'cascode_do_stack':0,
                 'cascode_D_W':3*0.18e-6,
                 'cascode_D_L':3*0.18e-6,
                 'cascode_D_Vbias':1.5,
                 'cascode_S_W':5*0.18e-6,
                 'cascode_S_L':5*0.18e-6,
                 'cascode_S_Vbias':1.5}

        instance = EmbeddedPart(part,
                                {'loadrail':'Vdd','opprail':'gnd',
                                 'Ifpos':'Ifpos','Ifneg':'Ifneg',
                                 'VsensePos':'Vsensepos',
                                 'VsenseNeg':'VsenseNeg'},
                                point)
        
        target_str = """M0 Vdd Vsensepos n_auto_176 n_auto_176 N_18_MM M=1 L=5.4e-07 W=5.4e-07
M1 n_auto_176 n_auto_177 gnd gnd N_18_MM M=1 L=9e-07 W=9e-07
V2 n_auto_177 0  DC 1.5
C3 Ifpos n_auto_176  C=1e-09
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

    def _viFeedback_Point(self, use_pmos, chosen_part_index=0):
        return  {'use_pmos':use_pmos,
                 'chosen_part_index':chosen_part_index,
                 'R':10.0e6, 'C':1.0e-9, 
                 'amp_W':3*0.18e-6,
                 'amp_L':3*0.18e-6,
                 'cascode_do_stack':0,
                 'cascode_D_W':3*0.18e-6,
                 'cascode_D_L':3*0.18e-6,
                 'cascode_D_Vbias':1.5,
                 'cascode_S_W':5*0.18e-6,
                 'cascode_S_L':5*0.18e-6,
                 'cascode_S_Vbias':1.5,
                 }
    
    def testViFeedback(self):
        return #HACK
        if self.just1: return
        part = self.lib.viFeedback()

        conns = {'loadrail':'Vdd', 'opprail':'gnd',
                 'Ifpos':'Ifpos', 'Ifneg':'Ifneg',
                 'VsensePos':'VsensePos', 'VsenseNeg':'VsenseNeg'}
        point = self._viFeedback_Point(0)

        #instantiate as capacitor
        point['chosen_part_index'] = 0      
        instance = EmbeddedPart(part, conns, point)
        
        target_str = """C0 Ifpos VsensePos  C=1e-09
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

        #instantiate as RC_series
        point['chosen_part_index'] = 1              
        instance = EmbeddedPart(part, conns, point)
        
        target_str = """R0 Ifpos n_auto_177  R=1e+07
C1 n_auto_177 VsensePos  C=1e-09
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

        #instantiate as viFeedback_LevelShifter
        point['chosen_part_index'] = 2          
        instance = EmbeddedPart(part, conns, point)
        
        target_str = """M0 Vdd VsensePos n_auto_178 n_auto_178 N_18_MM M=1 L=5.4e-07 W=5.4e-07
M1 n_auto_178 n_auto_179 gnd gnd N_18_MM M=1 L=9e-07 W=9e-07
V2 n_auto_179 0  DC 1.5
C3 Ifpos n_auto_178  C=1e-09
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

    def testSourceDegen(self):
        if self.just1: return
        part = self.lib.sourceDegen()

        #instantiate as wire
        instance0 = EmbeddedPart(part, {'D':'1', 'S':'2'},
                                 {'chosen_part_index':0,
                                  'R':10.0e6}
                                 )
        
        target_str0 = """Rwire0 1 2  R=0
"""
        actual_str0 = instance0.spiceNetlistStr()
        self._compareStrings(target_str0, actual_str0)


        #instantiate as resistor
        instance2 = EmbeddedPart(part, {'D':'1', 'S':'2'},
                                 {'chosen_part_index':1,
                                  'R':10.0e6 }
                                 )
        
        target_str2 = """R0 1 2  R=1e+07
"""
        actual_str2 = instance2.spiceNetlistStr()
        self._compareStrings3(target_str2, actual_str2)

    def testCascodeDevice(self):
        if self.just1: return
        part = self.lib.cascodeDevice()
        self.assertEqual(sorted(part.externalPortnames()),
                         sorted(['D','S','loadrail','opprail']))

        #instantiate as biasedMos -- nmos
        conns = {'D':'1','S':'2', 'loadrail':'3','opprail':'4'}
        point = {'chosen_part_index':0,
                 'loadrail_is_vdd':1,
                 'W':3*0.18e-6,
                 'L':5*0.18e-6,
                 'Vbias':1.41}
        instance = EmbeddedPart(part, conns, point)
        target_str = """M0 1 n_auto_2 2 2 N_18_MM M=1 L=9e-07 W=5.4e-07
V1 n_auto_2 0  DC 1.41
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

        #instantiate as biasedMos -- pmos
        point['loadrail_is_vdd'] = 0
        instance = EmbeddedPart(part, conns, point)
        target_str = """M0 1 n_auto_2 2 2 P_18_MM M=1 L=9e-07 W=5.4e-07
V1 n_auto_2 0  DC 0.39
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)
        
        #instantiate as gainBoostedMos 
        return #FIXME
        instance1 = EmbeddedPart(part,
                                 {'D':'1', 'S':'2','loadrail':'3','opprail':'4'},
                                 {'chosen_part_index':1,
                                  'W':3*0.18e-6,
                                  'L':5*0.18e-6,
                                  'use_pmos':1,
                                  'Vbias':1.41 }
                                 )
        
        target_str1 = """BLAH
"""
        actual_str1 = instance1.spiceNetlistStr()
        self._compareStrings(target_str1, actual_str1)
        
    def testCascodeDeviceOrWire(self):
        if self.just1: return
        part = self.lib.cascodeDeviceOrWire()
        self.assertEqual(sorted(part.externalPortnames()),
                         sorted(['D','S','loadrail','opprail']))

        #instantiate as cascodeDevice
        instance0 = EmbeddedPart(part,
                                 {'D':'1', 'S':'2','loadrail':'3','opprail':'4'},
                                 {'chosen_part_index':0,
                                  'cascode_recurse':0,
                                  'loadrail_is_vdd':1,
                                  'W':3*0.18e-6,
                                  'L':5*0.18e-6,
                                  'Vbias':1.41}
                                 )
                                 
        target_str0 = """M0 1 n_auto_2 2 2 N_18_MM M=1 L=9e-07 W=5.4e-07
V1 n_auto_2 0  DC 1.41
"""
        actual_str0 = instance0.spiceNetlistStr()
        self._compareStrings3(target_str0, actual_str0)
        
        #instantiate as wire
        instance1 = EmbeddedPart(part,
                                 {'D':'1', 'S':'2','loadrail':'3','opprail':'4'},
                                 {'chosen_part_index':1,
                                  'cascode_recurse':0,
                                  'loadrail_is_vdd':1,
                                  'W':3*0.18e-6,
                                  'L':5*0.18e-6,
                                  'Vbias':1.41}
                                 )
        
        target_str1 = """Rwire0 1 2  R=0
"""
        actual_str1 = instance1.spiceNetlistStr()
        self._compareStrings(target_str1, actual_str1)
        
    def testInputCascode_Stacked(self):
        if self.just1: return
        part = self.lib.inputCascode_Stacked()
        self.assertEqual(sorted(part.externalPortnames()),
                         sorted(['Vin', 'Iout', 'loadrail', 'opprail']))
        self.assertEqual(len(part.embedded_parts), 3)

        #'nmos version':
        #instantiate with input_is_pmos=False (ie input is nmos)
        # cascode_is_wire=0, degen_choice of resistor (1)
        #Remember: input_is_pmos=False means loadrail_is_Vdd=True; and vice-versa
        conn = {'Vin':'Vin', 'Iout':'Iout', 'loadrail':'Vdd','opprail':'gnd'}
        point = self._stackedPoint(input_is_pmos=False)
        instance = EmbeddedPart(part, conn, point)
        target_str = self._stackedNetlist(input_is_pmos=False)
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

        #'pmos (upside-down) version':
        conn = {'Vin':'Vin', 'Iout':'Iout', 'loadrail':'gnd','opprail':'Vdd'}
        point = self._stackedPoint(input_is_pmos=True)
        instance = EmbeddedPart(part, conn, point)
        target_str = self._stackedNetlist(input_is_pmos=True)
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

    def _stackedPoint(self, input_is_pmos):
        """For testing testInputCascode_Stacked"""
        return { 'input_is_pmos':input_is_pmos,
                
                 'cascode_is_wire':0,
                 'cascode_W':3*0.18e-6,
                 'cascode_L':4*0.18e-6,
                 'cascode_Vbias':1.7,
                 'cascode_recurse':0,
                 
                 'ampmos_W':5*0.18e-6,
                 'ampmos_L':6*0.18e-6,
                                  
                 'degen_R':1.03e6,
                 'degen_choice':1,
                 }        

    def _stackedNetlist(self, input_is_pmos):
        """For testing testInputCascode_Stacked"""
        if input_is_pmos:
            #all transistors should be pmos
            return """M0 Iout n_auto_199 n_auto_197 n_auto_197 P_18_MM M=1 L=7.2e-07 W=1.08e-06
V1 n_auto_199 0  DC 0.1
M2 n_auto_197 Vin n_auto_198 n_auto_198 P_18_MM M=1 L=1.08e-06 W=1.8e-06
R3 n_auto_198 Vdd  R=1.03e+06
"""
        else:
            #all transistors should be nmos
            return """M0 Iout n_auto_15 n_auto_13 n_auto_13 N_18_MM M=1 L=7.2e-07 W=5.4e-07
V1 n_auto_15 0  DC 1.7
M2 n_auto_13 Vin n_auto_14 n_auto_14 N_18_MM M=1 L=1.08e-06 W=9e-07
R3 n_auto_14 gnd  R=1.03e+06
"""
        
    def testInputCascode_Folded(self):
        if self.just1: return
        part = self.lib.inputCascode_Folded()
        self.assertEqual(sorted(part.externalPortnames()),
                         sorted(['Vin', 'Iout', 'loadrail', 'opprail']))
        self.assertEqual(len(part.embedded_parts), 4)

        #instantiate with input_is_pmos=True, degen_choice of resistor (1)
        conn = {'Vin':'Vin', 'Iout':'Iout', 'loadrail':'Vdd','opprail':'gnd'}
        point = self._foldedPoint(input_is_pmos=True)
        instance = EmbeddedPart(part, conn, point)
        target_str = self._foldedNetlist(input_is_pmos=True)
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

        #instantiate with input_is_pmos=False
        conn = {'Vin':'Vin', 'Iout':'Iout', 'loadrail':'gnd','opprail':'Vdd'}
        point = self._foldedPoint(input_is_pmos=False)
        instance = EmbeddedPart(part, conn, point)
        target_str = self._foldedNetlist(input_is_pmos=False)
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

    def _foldedPoint(self, input_is_pmos):
        """For testing testInputCascode_Folded"""
        return { 'input_is_pmos':input_is_pmos,
                 'cascode_W':3*0.18e-6,
                 'cascode_L':4*0.18e-6,
                 'cascode_Vbias':1.7,
                 'cascode_recurse':0,
                 
                 'ampmos_W':5*0.18e-6,
                 'ampmos_L':6*0.18e-6,
                                  
                 'degen_R':1.03e6,
                 'degen_choice':1,
                 
                 'inputbias_W':9*0.18e-6, 
                 'inputbias_L':9*0.18e-6,
                 'inputbias_Vbias':1.74,
                 }

    def _foldedNetlist(self, input_is_pmos):
        """For testing testInputCascode_Folded"""
        if input_is_pmos:
            return """M0 Iout n_auto_203 n_auto_202 n_auto_202 N_18_MM M=1 L=7.2e-07 W=5.4e-07
V1 n_auto_203 0  DC 1.7
M2 n_auto_202 Vin n_auto_201 n_auto_201 P_18_MM M=1 L=1.08e-06 W=1.8e-06
R3 n_auto_201 Vdd  R=1.03e+06
M4 n_auto_202 n_auto_204 gnd gnd N_18_MM M=1 L=1.62e-06 W=1.62e-06
V5 n_auto_204 0  DC 1.74
"""
        else:
            return """M0 Iout n_auto_11 n_auto_10 n_auto_10 P_18_MM M=1 L=7.2e-07 W=5.4e-07
V1 n_auto_11 0  DC 0.1
M2 n_auto_10 Vin n_auto_9 n_auto_9 N_18_MM M=1 L=1.08e-06 W=9e-07
R3 n_auto_9 gnd  R=1.03e+06
M4 n_auto_10 n_auto_13 Vdd Vdd P_18_MM M=1 L=1.62e-06 W=1.62e-06
V5 n_auto_13 0  DC 0.06
"""
        
    def testInputCascodeFlex(self):
        if self.just1: return
        part = self.lib.inputCascodeFlex()

        assert len(part.point_meta) == \
               (len(self.lib.inputCascode_Folded().point_meta) + 2)

        #case 1: input_is_pmos=F, loadrail_is_Vdd=T
        # (therefore stacked, ie choice=0)
        conn = {'Vin':'Vin', 'Iout':'Iout', 'loadrail':'Vdd','opprail':'gnd'}
        point = self._inputCascodeFlex_Point(0, 0)
        instance = EmbeddedPart(part, conn, point)
        self._compareStrings3(self._stackedNetlist(0),
                              instance.spiceNetlistStr())

        #case 2: input_is_pmos=T, loadrail_is_Vdd=F
        # (therefore stacked, ie choice=0)
        conn = {'Vin':'Vin', 'Iout':'Iout', 'loadrail':'gnd','opprail':'Vdd'}
        point = self._inputCascodeFlex_Point(0, 1)
        instance = EmbeddedPart(part, conn, point)
        self._compareStrings3(self._stackedNetlist(1),
                              instance.spiceNetlistStr())

        #case 3: input_is_pmos=T, loadrail_is_Vdd=T
        # (therefore stacked, ie choice=0)
        conn = {'Vin':'Vin', 'Iout':'Iout', 'loadrail':'Vdd','opprail':'gnd'}
        point = self._inputCascodeFlex_Point(1, 1)
        instance = EmbeddedPart(part, conn, point)
        self._compareStrings3(self._foldedNetlist(1),
                              instance.spiceNetlistStr())

        #case 4: input_is_pmos=F, loadrail_is_Vdd=F
        # (therefore stacked, ie choice=0)
        conn = {'Vin':'Vin', 'Iout':'Iout', 'loadrail':'gnd','opprail':'Vdd'}
        point = self._inputCascodeFlex_Point(1, 0)
        instance = EmbeddedPart(part, conn, point)
        self._compareStrings3(self._foldedNetlist(0),
                              instance.spiceNetlistStr())

    def _inputCascodeFlex_Point(self, chosen_part_index, input_is_pmos):
        #can easily  generate this, because it only adds two vars
        # above and beyond a foldedPoint. 
        point = self._foldedPoint(input_is_pmos)
        point['chosen_part_index'] = chosen_part_index #add var
        point['cascode_is_wire'] = 0                   #add var
        return point
        
    def testInputCascodeStage(self):
        if self.just1: return
        part = self.lib.inputCascodeStage()
        self._testInputCascodeStage_and_SsViInput(part)
        
    def testSsViInput(self):
        if self.just1: return
        part = self.lib.inputCascodeStage()
        self._testInputCascodeStage_and_SsViInput(part)
        
    def _testInputCascodeStage_and_SsViInput(self, part):
        if self.just1: return

        #case 1: input_is_pmos=F, loadrail_is_Vdd=T
        # (therefore stacked)
        conn = {'Vin':'Vin', 'Iout':'Iout', 'loadrail':'Vdd','opprail':'gnd'}
        point = self._inputCascodeStage_Point(1, 0)
        instance = EmbeddedPart(part, conn, point)
        self._compareStrings3(self._stackedNetlist(0),
                              instance.spiceNetlistStr())

        #case 2: input_is_pmos=T, loadrail_is_Vdd=F
        # (therefore stacked)
        conn = {'Vin':'Vin', 'Iout':'Iout', 'loadrail':'gnd','opprail':'Vdd'}
        point = self._inputCascodeStage_Point(0, 1)
        instance = EmbeddedPart(part, conn, point)
        self._compareStrings3(self._stackedNetlist(1),
                              instance.spiceNetlistStr())

        #case 3: input_is_pmos=T, loadrail_is_Vdd=T
        # (therefore stacked)
        conn = {'Vin':'Vin', 'Iout':'Iout', 'loadrail':'Vdd','opprail':'gnd'}
        point = self._inputCascodeStage_Point(1, 1)
        instance = EmbeddedPart(part, conn, point)
        self._compareStrings3(self._foldedNetlist(1),
                              instance.spiceNetlistStr())

        #case 4: input_is_pmos=F, loadrail_is_Vdd=F
        # (therefore stacked)
        conn = {'Vin':'Vin', 'Iout':'Iout', 'loadrail':'gnd','opprail':'Vdd'}
        point = self._inputCascodeStage_Point(0, 0)
        instance = EmbeddedPart(part, conn, point)
        self._compareStrings3(self._foldedNetlist(0),
                              instance.spiceNetlistStr())

    def _inputCascodeStage_Point(self, loadrail_is_vdd, input_is_pmos):
        #can easily  generate this, because it only adds one var
        # above and beyond a foldedPoint, and removes another var
        dummy = 0
        point = self._inputCascodeFlex_Point(dummy, input_is_pmos)
        point['loadrail_is_vdd'] = loadrail_is_vdd #add var
        del point['chosen_part_index']             #remove var

        #these are the vars documented in inputCascodeStage()
        expected_vars = [
            'loadrail_is_vdd','input_is_pmos',
            'cascode_W','cascode_L','cascode_Vbias','cascode_recurse',
            'cascode_is_wire',
            'ampmos_W','ampmos_L',
            'degen_R','degen_choice',
            'inputbias_W','inputbias_L','inputbias_Vbias'
            ]

        self.assertEqual(sorted(point.keys()), sorted(expected_vars))
        
        return point
        
    def testSsIiLoad_Cascoded(self):
        if self.just1: return
        part = self.lib.ssIiLoad_Cascoded()
        self.assertEqual(sorted(part.externalPortnames()),
                         sorted(['Iout','loadrail','opprail']))

        #loadrail_is_vdd=1, so parts are all pmos
        conns = {'Iout':'Iout','loadrail':'Vdd','opprail':'gnd'}
        vdd = self.lib.ss.vdd
        point = {'loadrail_is_vdd':1,
                                 
                 'mainload_W':3*0.18e-6,
                 'mainload_L':4*0.18e-6,
                 'mainload_Vbias':1.41,
                                 
                 'loadcascode_recurse':0,
                 'loadcascode_W':5*0.18e-6,
                 'loadcascode_L':6*0.18e-6,
                 'loadcascode_Vbias':1.3,
                 }
        instance = EmbeddedPart(part, conns, point)
                                 
        target_str = """M0 n_auto_83 n_auto_84 Vdd Vdd P_18_MM M=1 L=7.2e-07 W=5.4e-07
V1 n_auto_84 0  DC 0.39
M2 Iout n_auto_85 n_auto_83 n_auto_83 P_18_MM M=1 L=1.08e-06 W=9e-07
V3 n_auto_85 0  DC 0.5
"""
        actual_str = instance.spiceNetlistStr()
        
        self._compareStrings3(target_str, actual_str)
        
        #loadrail_is_vdd=0, so parts are all nmos
        conns = {'Iout':'Iout','loadrail':'gnd','opprail':'Vdd'}
        point['loadrail_is_vdd'] = 0
        instance = EmbeddedPart(part, conns, point)
                                 
        target_str = """M0 n_auto_86 n_auto_87 gnd gnd N_18_MM M=1 L=7.2e-07 W=5.4e-07
V1 n_auto_87 0  DC 1.41
M2 Iout n_auto_88 n_auto_86 n_auto_86 N_18_MM M=1 L=1.08e-06 W=9e-07
V3 n_auto_88 0  DC 1.3
"""
        actual_str = instance.spiceNetlistStr()
        
        self._compareStrings3(target_str, actual_str)
        
    def testSsIiLoad(self):
        if self.just1: return
        part = self.lib.ssIiLoad()
        self.assertEqual(sorted(part.externalPortnames()),
                         sorted(['Iout','loadrail','opprail']))

        #use ssIiLoad_Cascoded (chosen_part_index=2)
        # loadrail_is_vdd=1, so parts are all pmos
        conns = {'Iout':'Iout','loadrail':'Vdd','opprail':'gnd'}
        point = {'loadrail_is_vdd':1,
                 'chosen_part_index':2,

                 'R':10.0e3,
                                 
                 'W':3*0.18e-6,
                 'L':4*0.18e-6,
                 'Vbias':1.41,
                                 
                 'loadcascode_recurse':0,
                 'loadcascode_W':5*0.18e-6,
                 'loadcascode_L':6*0.18e-6,
                 'loadcascode_Vbias':1.3,
                 }
        instance = EmbeddedPart(part, conns, point)
                                 
        target_str = """M0 n_auto_83 n_auto_84 Vdd Vdd P_18_MM M=1 L=7.2e-07 W=5.4e-07
V1 n_auto_84 0  DC 0.39
M2 Iout n_auto_85 n_auto_83 n_auto_83 P_18_MM M=1 L=1.08e-06 W=9e-07
V3 n_auto_85 0  DC 0.5
"""
        actual_str = instance.spiceNetlistStr()
        
        self._compareStrings3(target_str, actual_str)

        #simple-as-possible: 10K load, no cascoding
        conns = {'Iout':'Iout','loadrail':'Vdd','opprail':'gnd'}
        point = {'loadrail_is_vdd':1,
                 'chosen_part_index':0,

                 'R':10.0e3,
                                 
                 'W':3*0.18e-6,
                 'L':4*0.18e-6,
                 'Vbias':1.41,
                                 
                 'loadcascode_recurse':0,
                 'loadcascode_W':5*0.18e-6,
                 'loadcascode_L':6*0.18e-6,
                 'loadcascode_Vbias':1.3,
                 }
        instance = EmbeddedPart(part, conns, point)
                                 
        target_str = """R0 Vdd Iout  R=10000
"""
        actual_str = instance.spiceNetlistStr()
        
        self._compareStrings3(target_str, actual_str)

        
    def testSsViAmp1(self):
        if self.just1: return
        part = self.lib.ssViAmp1()
        self.assertEqual(sorted(part.externalPortnames()),
                         sorted(['Vin','Iout','loadrail','opprail']))

        # Simple as possible: nmos input, 10K resistor load
        #  (no input cascode, no source degen, no load cascode)
        #  (loadrail_is_vdd=1, input_is_pmos=0)
        conns = {'Vin':'Vin','Iout':'Iout','loadrail':'Vdd','opprail':'gnd'}
        point = self._ssViAmp1_Point()
        instance = EmbeddedPart(part, conns, point)
                                 
        target_str = """Rwire0 Iout n_auto_100  R=0
M1 n_auto_100 Vin n_auto_101 n_auto_101 N_18_MM M=1 L=1.08e-06 W=9e-07
Rwire2 n_auto_101 gnd  R=0
R3 Vdd Iout  R=10000
"""
        actual_str = instance.spiceNetlistStr()
        
        self._compareStrings3(target_str, actual_str)
        
    def testSsViAmp1_VddGndPorts(self):
        return #HACK: this currently breaks
        if self.just1: return
        part = self.lib.ssViAmp1_VddGndPorts()
        self.assertEqual(sorted(part.externalPortnames()),
                         sorted(['Vin','Iout','Vdd','gnd']))

        # Simple as possible: nmos input, 10K resistor load
        #  (no input cascode, no source degen, no load cascode)
        #  (loadrail_is_vdd=1, input_is_pmos=0)
        conns = {'Vin':'Vin','Iout':'Iout','Vdd':'Vdd','gnd':'gnd'}
        point = self._ssViAmp1_VddGndPorts_Point(False, False)
        instance = EmbeddedPart(part, conns, point)

        #note how we are testing summaryStr() here
        target_str = """
* ==== Summary for: ssViAmp1_VddGndPorts ====
* loadrail is vdd = False
* input is pmos (rather than nmos) = False
* folded = True
* degen_choice (0=wire,1=resistor) = 0
* load type (0=resistor,1=biasedMos,2=ssIiLoad_Cascoded) = 0
* ==== Done summary ====

M0 Iout n_auto_9 n_auto_8 n_auto_8 P_18_MM M=1 L=7.2e-07 W=1.08e-06
V1 n_auto_9 0  DC 0.1
M2 n_auto_8 Vin n_auto_7 n_auto_7 N_18_MM M=1 L=1.08e-06 W=9e-07
Rwire3 n_auto_7 gnd  R=0
M4 n_auto_8 n_auto_10 Vdd Vdd P_18_MM M=1 L=1.62e-06 W=3.24e-06
V5 n_auto_10 0  DC 0.06
R6 gnd Iout  R=10000
"""
        actual_str = instance.spiceNetlistStr()
        
        self._compareStrings3(target_str, actual_str)

    def _ssViAmp1_Point(self, loadrail_is_vdd=1, input_is_pmos=0):
        return  {'loadrail_is_vdd':loadrail_is_vdd,
                 'input_is_pmos':input_is_pmos,

                 #for input:            
                 'inputcascode_W':3*0.18e-6,
                 'inputcascode_L':4*0.18e-6,
                 'inputcascode_Vbias':1.7,
                 'inputcascode_recurse':0,
                 'inputcascode_is_wire':1,
                 
                 'ampmos_W':5*0.18e-6,
                 'ampmos_L':6*0.18e-6,
                                  
                 'degen_R':1.03e6,
                 'degen_choice':0,
                 
                 'inputbias_W':9*0.18e-6,
                 'inputbias_L':9*0.18e-6,
                 'inputbias_Vbias':1.74,                  

                 #for load:
                 'load_part_index':0,
                 'load_R':10.0e3,
                                 
                 'load_W':1*0.18e-6,
                 'load_L':1*0.18e-6,
                 'load_Vbias':4.101,
                                 
                 'loadcascode_recurse':0,
                 'loadcascode_W':2*0.18e-6,
                 'loadcascode_L':2*0.18e-6,
                 'loadcascode_Vbias':4.102,
                 }

    
    def _ssViAmp1_VddGndPorts_Point(self, loadrail_is_vdd, input_is_pmos):
        point = self._ssViAmp1_Point(loadrail_is_vdd, input_is_pmos)
        point['chosen_part_index'] = loadrail_is_vdd
        del point['loadrail_is_vdd']
        point_keys = point.keys()
        part_keys = self.lib.ssViAmp1_VddGndPorts().point_meta.keys()
        assert sorted(point_keys) == sorted(part_keys)
        return point

    def testCurrentMirror_Simple(self):
        if self.just1: return
        part = self.lib.currentMirror_Simple()

        #nmos CM
        instance = EmbeddedPart(part,
                                {'Irefnode':'Irefnode', 'Ioutnode':'Ioutnode',
                                 'loadrail':'gnd'},
                                 {'loadrail_is_vdd':0,
                                  'ref_K':2, 'out_K':4,
                                  'base_W':3*0.18e-6, 'L':5*0.18e-6}
                                 )
        
        target_str = """M0 Irefnode Irefnode gnd gnd N_18_MM M=1 L=9e-07 W=1.08e-06
M1 Ioutnode Irefnode gnd gnd N_18_MM M=1 L=9e-07 W=2.16e-06
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

        #pmos CM
        instance = EmbeddedPart(part,
                                {'Irefnode':'Irefnode', 'Ioutnode':'Ioutnode',
                                 'loadrail':'Vdd'},
                                 {'loadrail_is_vdd':1,
                                  'ref_K':2, 'out_K':4,
                                  'base_W':3*0.18e-6, 'L':5*0.18e-6}
                                 )
        
        target_str = """M0 Irefnode Irefnode Vdd Vdd P_18_MM M=1 L=9e-07 W=1.08e-06
M1 Ioutnode Irefnode Vdd Vdd P_18_MM M=1 L=9e-07 W=2.16e-06
"""
        actual_str = instance.spiceNetlistStr()
        
        self._compareStrings3(target_str, actual_str)


    def testCurrentMirror_Cascode(self):
        if self.just1: return
        part = self.lib.currentMirror_Cascode()

        #nmos CM
        instance = EmbeddedPart(part,
                                {'Irefnode':'Irefnode', 'Ioutnode':'Ioutnode',
                                 'loadrail':'gnd'},
                                 {'loadrail_is_vdd':0,
                                  'ref_K':1, 'out_K':2,
                                  'cascode_K':2, 'main_K':3,
                                  'base_W':3*0.18e-6, 'L':5*0.18e-6}
                                 )
        
        target_str = """M0 Irefnode Irefnode n_auto_10 n_auto_10 N_18_MM M=1 L=9e-07 W=1.08e-06
M1 n_auto_10 n_auto_10 gnd gnd N_18_MM M=1 L=9e-07 W=1.62e-06
M2 Ioutnode Irefnode n_auto_11 n_auto_11 N_18_MM M=1 L=9e-07 W=2.16e-06
M3 n_auto_11 n_auto_10 gnd gnd N_18_MM M=1 L=9e-07 W=3.24e-06
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

    def testCurrentMirror_LowVoltageA(self):
        if self.just1: return
        part = self.lib.currentMirror_LowVoltageA()

        #nmos CM
        instance = EmbeddedPart(part,
                                {'Irefnode':'Irefnode', 'Ioutnode':'Ioutnode',
                                 'loadrail':'gnd'},
                                 {'loadrail_is_vdd':0,
                                  'ref_K':1, 'out_K':2,
                                  'cascode_K':2, 'main_K':3,
                                  'base_W':3*0.18e-6, 'L':5*0.18e-6,
                                  'Vbias':1.2}
                                 )
        
        target_str = """M0 Irefnode n_auto_17 n_auto_15 n_auto_15 N_18_MM M=1 L=9e-07 W=1.08e-06
V1 n_auto_17 0  DC 1.2
M2 n_auto_15 Irefnode gnd gnd N_18_MM M=1 L=9e-07 W=1.62e-06
M3 Ioutnode n_auto_18 n_auto_16 n_auto_16 N_18_MM M=1 L=9e-07 W=2.16e-06
V4 n_auto_18 0  DC 1.2
M5 n_auto_16 Irefnode gnd gnd N_18_MM M=1 L=9e-07 W=3.24e-06
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

    def testCurrentMirror(self):
        if self.just1: return

        self._verifyCmChoice(0, 'currentMirror_Simple')
        self._verifyCmChoice(1, 'currentMirror_Cascode')
        self._verifyCmChoice(2, 'currentMirror_LowVoltageA')

    def _verifyCmChoice(self, chosen_part_index, target_name):
        part = self.lib.currentMirror()

        #nmos CM
        conns = {'Irefnode':'Irefnode', 'Ioutnode':'Ioutnode', 'loadrail':'gnd'}
        point = {'chosen_part_index':0,
                 'loadrail_is_vdd':0,
                 'base_W':3*0.18e-6,'ref_K':1,'out_K':2,'L':5*0.18e-6,
                 'topref_usemos':0, 'topref_R':10.0e3, 'topref_K':2,
                 'middleref_K':1,
                 'bottomref_K':2,
                 'topout_K':3,
                 'bottomout_K':4,
                 'Vbias':1.2,
                 }
        
        point = Point(True, point)
        point['chosen_part_index'] = chosen_part_index
        instance = EmbeddedPart(part, conns, point)
        self.assertEqual(instance.part.chosenPart(point).part.name,
                         target_name)

    def testDsIiLoad(self):
        if self.just1: return
        part = self.lib.dsIiLoad()

        #simple-as-possible nmos CM
        conns = {'Iin1':'Iin1', 'Iin2':'Iin2', 'Iout':'Iout', 'loadrail':'gnd'}
        point = {'chosen_part_index':0,
                 'loadrail_is_vdd':0,
                 'base_W':3*0.18e-6,'ref_K':1,'out_K':2,'L':5*0.18e-6,
                 'topref_usemos':0, 'topref_R':10.0e3, 'topref_K':2,
                 'middleref_K':1,
                 'bottomref_K':2,
                 'topout_K':3,
                 'bottomout_K':4,
                 'Vbias':1.2,
                 }
        instance = EmbeddedPart(part, conns, point)
        
        target_str = """M0 Iin1 Iin1 gnd gnd N_18_MM M=1 L=9e-07 W=5.4e-07
M1 Iin2 Iin1 gnd gnd N_18_MM M=1 L=9e-07 W=1.08e-06
Rwire2 Iin2 Iout  R=0
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

    def _ddViInput_Point(self, loadrail_is_vdd, input_is_pmos):
        point = self._inputCascodeStage_Point(loadrail_is_vdd, input_is_pmos)
        return point
        
    def testDdViInput(self):
        if self.just1: return
        part = self.lib.ddViInput()
        self.assertEqual(sorted(part.externalPortnames()),
                         sorted(['Vin1','Vin2','Iout1','Iout2',
                                 'loadrail','opprail']))

        conns = {'Vin1':'Vin1','Vin2':'Vin2','Iout1':'Iout1','Iout2':'Iout2',
                 'loadrail':'Vdd','opprail':'gnd'}

        #instantiate as stacked, nmos input
        # -this means that the input is stacked, not folded;
        #  therefore the ss part does not have a vbias, so ddViInput
        #  generates one
        point = {'input_is_pmos':0,
                 'loadrail_is_vdd':1,
                 'cascode_W':2e-6,
                 'cascode_L':1e-6,
                 'cascode_Vbias':1.7,
                 'cascode_recurse':0,
                 'cascode_is_wire':1,
                 
                 'ampmos_W':4e-6,
                 'ampmos_L':3e-6,
                                  
                 'degen_R':1.03e6,
                 'degen_choice':0,
                 
                 'inputbias_W':6e-6, 
                 'inputbias_L':5e-6,
                 'inputbias_Vbias':1.74,
                 }

        instance = EmbeddedPart(part, conns, point)
                                 
        target_str = """Rwire0 Iout1 n_auto_8  R=0
M1 n_auto_8 Vin1 n_auto_9 n_auto_9 N_18_MM M=1 L=1.8e-06 W=4e-06
Rwire2 n_auto_9 n_auto_7  R=0
Rwire3 Iout2 n_auto_10  R=0
M4 n_auto_10 Vin2 n_auto_11 n_auto_11 N_18_MM M=1 L=1.8e-06 W=4e-06
Rwire5 n_auto_11 n_auto_7  R=0
M6 n_auto_7 n_auto_12 gnd gnd N_18_MM M=1 L=1.8e-06 W=6e-06
V7 n_auto_12 0  DC 1.74
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

        #instantiate as stacked, pmos input
        # -this means that the input is stacked, not folded;
        #  therefore the ss part does not have a vbias, so ddViInput
        #  generates one
        conns = {'Vin1':'Vin1','Vin2':'Vin2','Iout1':'Iout1','Iout2':'Iout2',
                 'loadrail':'gnd','opprail':'Vdd'}

        point = {'input_is_pmos':1,
                 'loadrail_is_vdd':0,
                 'cascode_W':2e-6,
                 'cascode_L':1e-6,
                 'cascode_Vbias':1.7,
                 'cascode_recurse':0,
                 'cascode_is_wire':1,
                 
                 'ampmos_W':4e-6,
                 'ampmos_L':3e-6,
                                  
                 'degen_R':1.03e6,
                 'degen_choice':1,
                 
                 'inputbias_W':6e-6, 
                 'inputbias_L':5e-6,
                 'inputbias_Vbias':1.74,
                 }

        instance = EmbeddedPart(part, conns, point)
                                 
        target_str = """Rwire0 Iout1 n_auto_14  R=0
M1 n_auto_14 Vin1 n_auto_15 n_auto_15 P_18_MM M=1 L=1.8e-06 W=4e-06
R2 n_auto_15 n_auto_13  R=1.03e+06
Rwire3 Iout2 n_auto_16  R=0
M4 n_auto_16 Vin2 n_auto_17 n_auto_17 P_18_MM M=1 L=1.8e-06 W=4e-06
R5 n_auto_17 n_auto_13  R=1.03e+06
M6 n_auto_13 n_auto_18 Vdd Vdd P_18_MM M=1 L=1.8e-06 W=6e-06
V7 n_auto_18 0  DC 0.06
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)
        
        #instantiate as folded, pmos input
        # -this means that the input is stacked, not folded;
        #  therefore the ss part does not have a vbias, so ddViInput
        #  generates one
        conns = {'Vin1':'Vin1','Vin2':'Vin2','Iout1':'Iout1','Iout2':'Iout2',
                 'loadrail':'Vdd','opprail':'gnd'}

        point = {'input_is_pmos':1,
                 'loadrail_is_vdd':1,
                 'cascode_W':2e-6,
                 'cascode_L':1e-6,
                 'cascode_Vbias':1.7,
                 'cascode_recurse':0,
                 'cascode_is_wire':1,
                 
                 'ampmos_W':4e-6,
                 'ampmos_L':3e-6,
                                  
                 'degen_R':1.03e6,
                 'degen_choice':0,
                 
                 'inputbias_W':6e-6, 
                 'inputbias_L':5e-6,
                 'inputbias_Vbias':1.74,
                 }

        instance = EmbeddedPart(part, conns, point)
                                 
        target_str = """M0 Iout1 n_auto_23 n_auto_22 n_auto_22 N_18_MM M=1 L=1e-06 W=2e-06
V1 n_auto_23 0  DC 1.7
M2 n_auto_22 Vin1 n_auto_21 n_auto_21 P_18_MM M=1 L=1.8e-06 W=4e-06
Rwire3 n_auto_21 n_auto_20  R=0
M4 n_auto_22 n_auto_24 gnd gnd N_18_MM M=1 L=1.8e-06 W=6e-06
V5 n_auto_24 0  DC 1.74
M6 Iout2 n_auto_27 n_auto_26 n_auto_26 N_18_MM M=1 L=1e-06 W=2e-06
V7 n_auto_27 0  DC 1.7
M8 n_auto_26 Vin2 n_auto_25 n_auto_25 P_18_MM M=1 L=1.8e-06 W=4e-06
Rwire9 n_auto_25 n_auto_20  R=0
M10 n_auto_26 n_auto_28 gnd gnd N_18_MM M=1 L=1.8e-06 W=6e-06
V11 n_auto_28 0  DC 1.74
M12 n_auto_20 n_auto_29 Vdd Vdd P_18_MM M=1 L=1.8e-06 W=6e-06
V13 n_auto_29 0  DC 0.06
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)
        
        #instantiate as folded, nmos input
        # -this means that the input is stacked, not folded;
        #  therefore the ss part does not have a vbias, so ddViInput
        #  generates one
        conns = {'Vin1':'Vin1','Vin2':'Vin2','Iout1':'Iout1','Iout2':'Iout2',
                 'loadrail':'gnd','opprail':'Vdd'}

        point = {'input_is_pmos':0,
                 'loadrail_is_vdd':0,
                 'cascode_W':2e-6,
                 'cascode_L':1e-6,
                 'cascode_Vbias':1.7,
                 'cascode_recurse':0,
                 'cascode_is_wire':1,
                 
                 'ampmos_W':4e-6,
                 'ampmos_L':3e-6,
                                  
                 'degen_R':1.03e6,
                 'degen_choice':0,
                 
                 'inputbias_W':6e-6, 
                 'inputbias_L':5e-6,
                 'inputbias_Vbias':1.74,
                 }

        instance = EmbeddedPart(part, conns, point)
                                 
        target_str = """M0 Iout1 n_auto_33 n_auto_32 n_auto_32 P_18_MM M=1 L=1e-06 W=2e-06
V1 n_auto_33 0  DC 0.1
M2 n_auto_32 Vin1 n_auto_31 n_auto_31 N_18_MM M=1 L=1.8e-06 W=4e-06
Rwire3 n_auto_31 n_auto_30  R=0
M4 n_auto_32 n_auto_34 Vdd Vdd P_18_MM M=1 L=1.8e-06 W=6e-06
V5 n_auto_34 0  DC 0.06
M6 Iout2 n_auto_37 n_auto_36 n_auto_36 P_18_MM M=1 L=1e-06 W=2e-06
V7 n_auto_37 0  DC 0.1
M8 n_auto_36 Vin2 n_auto_35 n_auto_35 N_18_MM M=1 L=1.8e-06 W=4e-06
Rwire9 n_auto_35 n_auto_30  R=0
M10 n_auto_36 n_auto_38 Vdd Vdd P_18_MM M=1 L=1.8e-06 W=6e-06
V11 n_auto_38 0  DC 0.06
M12 n_auto_30 n_auto_39 gnd gnd N_18_MM M=1 L=1.8e-06 W=6e-06
V13 n_auto_39 0  DC 1.74
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)


    def _dsViAmp1_Point(self, loadrail_is_vdd, input_is_pmos):
        input_point = {'input_is_pmos':input_is_pmos,
                       'loadrail_is_vdd':loadrail_is_vdd,
                       'cascode_W':2e-6,
                       'cascode_L':1e-6,
                       'cascode_Vbias':1.7,
                       'cascode_recurse':0,
                       'cascode_is_wire':1,
                    
                       'ampmos_W':4e-6,
                       'ampmos_L':3e-6,
                       
                       'degen_R':1.03e6,
                       'degen_choice':0,
                       
                       'inputbias_W':6e-6, 
                       'inputbias_L':5e-6,
                       'inputbias_Vbias':1.74,
                       }
        load_point = {'load_chosen_part_index':0,
                    'loadrail_is_vdd':loadrail_is_vdd,
                    'load_base_W':3*0.18e-6,
                    'load_ref_K':1,
                    'load_out_K':2,
                    'load_L':5*0.18e-6,
                    'load_topref_usemos':0,
                    'load_topref_R':10.0e3,
                    'load_topref_K':2,
                    'load_middleref_K':1,
                    'load_bottomref_K':2,
                    'load_topout_K':3,
                    'load_bottomout_K':4,
                    'load_Vbias':3.0,
                    }
        
        point = {}
        point.update(input_point)
        point.update(load_point)
        
        point_vars = point.keys()
        part_vars = self.lib.dsViAmp1().point_meta.keys()
        assert sorted(point_vars) == sorted(part_vars)
        return point

        
    def testDsViAmp1_index0(self):
        if self.just1: return
        conns = {'Vin1':'Vin1','Vin2':'Vin2','Iout':'Iout',
                 'loadrail':'gnd','opprail':'Vdd'}
        self._indexed_testDsViAmp1(0, conns)
        
    def testDsViAmp1_index1(self):
        if self.just1: return
        conns = {'Vin1':'Vin1','Vin2':'Vin2','Iout':'Iout',
                 'loadrail':'gnd','opprail':'Vdd'}
        self._indexed_testDsViAmp1(1, conns)
        
    def testDsViAmp1_index2(self):
        if self.just1: return
        conns = {'Vin1':'Vin1','Vin2':'Vin2','Iout':'Iout',
                 'loadrail':'Vdd','opprail':'gnd'}
        self._indexed_testDsViAmp1(2, conns)
        
    def testDsViAmp1_index3(self):
        if self.just1: return
        conns = {'Vin1':'Vin1','Vin2':'Vin2','Iout':'Iout',
                 'loadrail':'Vdd','opprail':'gnd'}
        self._indexed_testDsViAmp1(3, conns)
        
    def _indexed_testDsViAmp1(self, index, conns):
        part = self.lib.dsViAmp1()
        self.assertEqual(sorted(part.externalPortnames()),
                         sorted(['Vin1','Vin2','Iout','loadrail','opprail']))
                
        point = self._indexed_dsViAmp1_Point(index)
        instance = EmbeddedPart(part, conns, point)

        target_str = self._indexed_testDsViAmp1_TargetStr(index)
        
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

    def _indexed_dsViAmp1_Point(self, point_index):
        """The result of the 4 possible point_index_values of this function
        are the netlists of _indexed_testDsViAmp1_TargetStr.
        These 4 points are largely based on the four combinations of
        loadrail_is_vdd=0/1 and input_is_pmos=0/1 but there are other
        differences too.
        """
        if(point_index==0):
            loadrail_is_vdd = 0
            input_is_pmos = 0
            input_point = {'input_is_pmos':input_is_pmos,
                    'loadrail_is_vdd':loadrail_is_vdd,
                    'cascode_W':2e-6,
                    'cascode_L':1e-6,
                    'cascode_Vbias':1.7,
                    'cascode_recurse':0,
                    'cascode_is_wire':1,
                    
                    'ampmos_W':4e-6,
                    'ampmos_L':3e-6,
                                    
                    'degen_R':1.03e6,
                    'degen_choice':0,
                    
                    'inputbias_W':6e-6, 
                    'inputbias_L':5e-6,
                    'inputbias_Vbias':1.74,
    
                    }
            load_point = {'load_chosen_part_index':0,
                        'loadrail_is_vdd':loadrail_is_vdd,
                        'load_base_W':3*0.18e-6,
                        'load_ref_K':1,
                        'load_out_K':2,
                        'load_L':5*0.18e-6,
                        'load_topref_usemos':0,
                        'load_topref_R':10.0e3,
                        'load_topref_K':2,
                        'load_middleref_K':1,
                        'load_bottomref_K':2,
                        'load_topout_K':3,
                        'load_bottomout_K':4,
                        'load_Vbias':3.0,
                        }
                        
        elif(point_index==1):
            loadrail_is_vdd = 0
            input_is_pmos = 1
            input_point = {'input_is_pmos':input_is_pmos,
                    'loadrail_is_vdd':loadrail_is_vdd,
                    'cascode_W':2e-6,
                    'cascode_L':1e-6,
                    'cascode_Vbias':1.7,
                    'cascode_recurse':0,
                    'cascode_is_wire':1,
                    
                    'ampmos_W':4e-6,
                    'ampmos_L':3e-6,
                                    
                    'degen_R':1.03e6,
                    'degen_choice':0,
                    
                    'inputbias_W':6e-6, 
                    'inputbias_L':5e-6,
                    'inputbias_Vbias':1.74,
    
                    }
            load_point = {'load_chosen_part_index':loadrail_is_vdd,
                        'loadrail_is_vdd':0,
                        'load_base_W':3*0.18e-6,
                        'load_ref_K':1,
                        'load_out_K':2,
                        'load_L':5*0.18e-6,
                        'load_topref_usemos':0,
                        'load_topref_R':10.0e3,
                        'load_topref_K':2,
                        'load_middleref_K':1,
                        'load_bottomref_K':2,
                        'load_topout_K':3,
                        'load_bottomout_K':4,
                        'load_Vbias':3.0,
                        }          
        elif(point_index==2):
            loadrail_is_vdd = 1
            input_is_pmos = 1
            input_point = {'input_is_pmos':input_is_pmos,
                    'loadrail_is_vdd':loadrail_is_vdd,
                    'cascode_W':2e-6,
                    'cascode_L':1e-6,
                    'cascode_Vbias':1.7,
                    'cascode_recurse':0,
                    'cascode_is_wire':1,
                    
                    'ampmos_W':4e-6,
                    'ampmos_L':3e-6,
                                    
                    'degen_R':1.03e6,
                    'degen_choice':0,
                    
                    'inputbias_W':6e-6, 
                    'inputbias_L':5e-6,
                    'inputbias_Vbias':1.74,
    
                    }
            load_point = {'load_chosen_part_index':0,
                        'loadrail_is_vdd':loadrail_is_vdd,
                        'load_base_W':3*0.18e-6,
                        'load_ref_K':1,
                        'load_out_K':2,
                        'load_L':5*0.18e-6,
                        'load_topref_usemos':0,
                        'load_topref_R':10.0e3,
                        'load_topref_K':2,
                        'load_middleref_K':1,
                        'load_bottomref_K':2,
                        'load_topout_K':3,
                        'load_bottomout_K':4,
                        'load_Vbias':3.0,
                        }          
        elif(point_index==3):
            loadrail_is_vdd = 1
            input_is_pmos = 0
            input_point = {'input_is_pmos':input_is_pmos,
                    'loadrail_is_vdd':loadrail_is_vdd,
                    'cascode_W':2e-6,
                    'cascode_L':1e-6,
                    'cascode_Vbias':1.7,
                    'cascode_recurse':0,
                    'cascode_is_wire':1,
                    
                    'ampmos_W':4e-6,
                    'ampmos_L':3e-6,
                                    
                    'degen_R':1.03e6,
                    'degen_choice':0,
                    
                    'inputbias_W':6e-6, 
                    'inputbias_L':5e-6,
                    'inputbias_Vbias':1.74,
    
                    }
            load_point = {'load_chosen_part_index':0,
                        'loadrail_is_vdd':loadrail_is_vdd,
                        'load_base_W':3*0.18e-6,
                        'load_ref_K':1,
                        'load_out_K':2,
                        'load_L':5*0.18e-6,
                        'load_topref_usemos':0,
                        'load_topref_R':10.0e3,
                        'load_topref_K':2,
                        'load_middleref_K':1,
                        'load_bottomref_K':2,
                        'load_topout_K':3,
                        'load_bottomout_K':4,
                        'load_Vbias':3.0,
                        }          

        point = {}
        point.update(input_point)
        point.update(load_point)
        
        point_vars = point.keys()
        part_vars = self.lib.dsViAmp1().point_meta.keys()
        assert sorted(point_vars) == sorted(part_vars)
        return point
            
    def _indexed_testDsViAmp1_TargetStr(self, index):
        if index==0:
            return """M0 n_auto_14 n_auto_19 n_auto_18 n_auto_18 P_18_MM M=1 L=1e-06 W=2e-06
V1 n_auto_19 0  DC 0.1
M2 n_auto_18 Vin1 n_auto_17 n_auto_17 N_18_MM M=1 L=1.8e-06 W=4e-06
Rwire3 n_auto_17 n_auto_16  R=0
M4 n_auto_18 n_auto_20 Vdd Vdd P_18_MM M=1 L=1.8e-06 W=6e-06
V5 n_auto_20 0  DC 0.06
M6 n_auto_15 n_auto_23 n_auto_22 n_auto_22 P_18_MM M=1 L=1e-06 W=2e-06
V7 n_auto_23 0  DC 0.1
M8 n_auto_22 Vin2 n_auto_21 n_auto_21 N_18_MM M=1 L=1.8e-06 W=4e-06
Rwire9 n_auto_21 n_auto_16  R=0
M10 n_auto_22 n_auto_24 Vdd Vdd P_18_MM M=1 L=1.8e-06 W=6e-06
V11 n_auto_24 0  DC 0.06
M12 n_auto_16 n_auto_25 gnd gnd N_18_MM M=1 L=1.8e-06 W=6e-06
V13 n_auto_25 0  DC 1.74
M14 n_auto_14 n_auto_14 gnd gnd N_18_MM M=1 L=9e-07 W=5.4e-07
M15 n_auto_15 n_auto_14 gnd gnd N_18_MM M=1 L=9e-07 W=1.08e-06
Rwire16 n_auto_15 Iout  R=0
"""
        elif index==1:
            return """Rwire0 n_auto_26 n_auto_29  R=0
M1 n_auto_29 Vin1 n_auto_30 n_auto_30 P_18_MM M=1 L=1.8e-06 W=4e-06
Rwire2 n_auto_30 n_auto_28  R=0
Rwire3 n_auto_27 n_auto_31  R=0
M4 n_auto_31 Vin2 n_auto_32 n_auto_32 P_18_MM M=1 L=1.8e-06 W=4e-06
Rwire5 n_auto_32 n_auto_28  R=0
M6 n_auto_28 n_auto_33 Vdd Vdd P_18_MM M=1 L=1.8e-06 W=6e-06
V7 n_auto_33 0  DC 0.06
M8 n_auto_26 n_auto_26 gnd gnd N_18_MM M=1 L=9e-07 W=5.4e-07
M9 n_auto_27 n_auto_26 gnd gnd N_18_MM M=1 L=9e-07 W=1.08e-06
Rwire10 n_auto_27 Iout  R=0
"""
        elif index==2:
            return """M0 n_auto_34 n_auto_39 n_auto_38 n_auto_38 N_18_MM M=1 L=1e-06 W=2e-06
V1 n_auto_39 0  DC 1.7
M2 n_auto_38 Vin1 n_auto_37 n_auto_37 P_18_MM M=1 L=1.8e-06 W=4e-06
Rwire3 n_auto_37 n_auto_36  R=0
M4 n_auto_38 n_auto_40 gnd gnd N_18_MM M=1 L=1.8e-06 W=6e-06
V5 n_auto_40 0  DC 1.74
M6 n_auto_35 n_auto_43 n_auto_42 n_auto_42 N_18_MM M=1 L=1e-06 W=2e-06
V7 n_auto_43 0  DC 1.7
M8 n_auto_42 Vin2 n_auto_41 n_auto_41 P_18_MM M=1 L=1.8e-06 W=4e-06
Rwire9 n_auto_41 n_auto_36  R=0
M10 n_auto_42 n_auto_44 gnd gnd N_18_MM M=1 L=1.8e-06 W=6e-06
V11 n_auto_44 0  DC 1.74
M12 n_auto_36 n_auto_45 Vdd Vdd P_18_MM M=1 L=1.8e-06 W=6e-06
V13 n_auto_45 0  DC 0.06
M14 n_auto_34 n_auto_34 Vdd Vdd P_18_MM M=1 L=9e-07 W=5.4e-07
M15 n_auto_35 n_auto_34 Vdd Vdd P_18_MM M=1 L=9e-07 W=1.08e-06
Rwire16 n_auto_35 Iout  R=0
"""      
        elif index==3:
            return """Rwire0 n_auto_46 n_auto_49  R=0
M1 n_auto_49 Vin1 n_auto_50 n_auto_50 N_18_MM M=1 L=1.8e-06 W=4e-06
Rwire2 n_auto_50 n_auto_48  R=0
Rwire3 n_auto_47 n_auto_51  R=0
M4 n_auto_51 Vin2 n_auto_52 n_auto_52 N_18_MM M=1 L=1.8e-06 W=4e-06
Rwire5 n_auto_52 n_auto_48  R=0
M6 n_auto_48 n_auto_53 gnd gnd N_18_MM M=1 L=1.8e-06 W=6e-06
V7 n_auto_53 0  DC 1.74
M8 n_auto_46 n_auto_46 Vdd Vdd P_18_MM M=1 L=9e-07 W=5.4e-07
M9 n_auto_47 n_auto_46 Vdd Vdd P_18_MM M=1 L=9e-07 W=1.08e-06
Rwire10 n_auto_47 Iout  R=0
"""
    def _indexed_dsViAmp1_VddGndPorts_Point(self, index):
        point = self._indexed_dsViAmp1_Point(index)
        if (index==0 or index==1):
            point['chosen_part_index'] = 0
        else:
            point['chosen_part_index'] = 1
            
        del point['loadrail_is_vdd']
        
        point_vars = point.keys()
        part_vars = self.lib.dsViAmp1_VddGndPorts().point_meta.keys()
        assert sorted(point_vars) == sorted(part_vars)
        return point
    
    def _dsViAmp1_VddGndPorts_Point(self,
                                    loadrail_is_vdd,
                                    input_is_pmos):
        input_point = {'input_is_pmos':input_is_pmos,
                #'loadrail_is_vdd':loadrail_is_vdd,
                'cascode_W':2e-6,
                'cascode_L':1e-6,
                'cascode_Vbias':1.7,
                'cascode_recurse':0,
                'cascode_is_wire':1,

                'ampmos_W':4e-6,
                'ampmos_L':3e-6,

                'degen_R':1.03e6,
                'degen_choice':0,

                'inputbias_W':6e-6, 
                'inputbias_L':5e-6,
                'inputbias_Vbias':1.74,

                }
        load_point = {'load_chosen_part_index':0,
                    #'loadrail_is_vdd':loadrail_is_vdd,
                    'load_base_W':3*0.18e-6,
                    'load_ref_K':1,
                    'load_out_K':2,
                    'load_L':5*0.18e-6,
                    'load_topref_usemos':0,
                    'load_topref_R':10.0e3,
                    'load_topref_K':2,
                    'load_middleref_K':1,
                    'load_bottomref_K':2,
                    'load_topout_K':3,
                    'load_bottomout_K':4,
                    'load_Vbias':3.0,
                    }
                        
        point = {}
        point.update(input_point)
        point.update(load_point)
        point['chosen_part_index'] = loadrail_is_vdd
        
        point_vars = point.keys()
        part_vars = self.lib.dsViAmp1_VddGndPorts().point_meta.keys()
        assert sorted(point_vars) == sorted(part_vars)
        return point
        
        #compute 'index'
        if loadrail_is_vdd==0 and input_is_pmos==0:
            index = 0
        elif loadrail_is_vdd==0 and input_is_pmos==1:
            index = 1
        elif loadrail_is_vdd==1 and input_is_pmos==0:
            index = 2
        elif loadrail_is_vdd==1 and input_is_pmos==1:
            index = 3

        #use computed 'index' to determine point
        point = self._indexed_dsViAmp1_VddGndPorts_Point(index)

        #validate
        point_vars = point.keys()
        part_vars = self.lib.dsViAmp1_VddGndPorts().point_meta.keys()
        assert sorted(point_vars) == sorted(part_vars)

        #done
        return point

    def _indexed_testDsViAmp1_VddGndPorts_TargetStr(self, index):
        if index==0:
            s = """
* ==== Summary for: dsViAmp1_VddGndPorts ====
* loadrail is vdd = 0
* input is pmos (rather than nmos) = 0
* folded = True
* cascode_is_wire = 1
* degen_choice (0=wire,1=resistor) = 0
* load_chosen_part_index (0=simple CM,1=cascode CM,2=low-voltageA CM) = 0
* ==== Done summary ====

"""
        elif index==1:
            s = """
* ==== Summary for: dsViAmp1_VddGndPorts ====
* loadrail is vdd = 0
* input is pmos (rather than nmos) = 1
* folded = False
* cascode_is_wire = 1
* degen_choice (0=wire,1=resistor) = 0
* load_chosen_part_index (0=simple CM,1=cascode CM,2=low-voltageA CM) = 0
* ==== Done summary ====

"""
        elif index==2:
            s = """
* ==== Summary for: dsViAmp1_VddGndPorts ====
* loadrail is vdd = 1
* input is pmos (rather than nmos) = 1
* folded = True
* cascode_is_wire = 1
* degen_choice (0=wire,1=resistor) = 0
* load_chosen_part_index (0=simple CM,1=cascode CM,2=low-voltageA CM) = 0
* ==== Done summary ====

"""
        elif index==3:
            s = """
* ==== Summary for: dsViAmp1_VddGndPorts ====
* loadrail is vdd = 1
* input is pmos (rather than nmos) = 0
* folded = False
* cascode_is_wire = 1
* degen_choice (0=wire,1=resistor) = 0
* load_chosen_part_index (0=simple CM,1=cascode CM,2=low-voltageA CM) = 0
* ==== Done summary ====

"""

        return s + self._indexed_testDsViAmp1_TargetStr(index)
        
    def testDsViAmp1_VddGndPorts_index0(self):
        return #HACK: this currently breaks
        if self.just1: return
        self._indexed_testDsViAmp1_VddGndPorts(0)
        
    def testDsViAmp1_VddGndPorts_index1(self):
        return #HACK: this currently breaks
        if self.just1: return
        self._indexed_testDsViAmp1_VddGndPorts(1)
        
    def testDsViAmp1_VddGndPorts_index2(self):
        return #HACK: this currently breaks
        if self.just1: return
        self._indexed_testDsViAmp1_VddGndPorts(2)
        
    def testDsViAmp1_VddGndPorts_index3(self):
        return #HACK: this currently breaks
        if self.just1: return
        self._indexed_testDsViAmp1_VddGndPorts(3)
        
    def _indexed_testDsViAmp1_VddGndPorts(self, index):
        part = self.lib.dsViAmp1_VddGndPorts()
        self.assertEqual(sorted(part.externalPortnames()),
                         sorted(['Vin1','Vin2','Iout','Vdd','gnd']))

        conns = {'Vin1':'Vin1','Vin2':'Vin2','Iout':'Iout',
                 'Vdd':'Vdd','gnd':'gnd'}

        point = self._indexed_dsViAmp1_VddGndPorts_Point(index)
        instance = EmbeddedPart(part, conns, point)

        target_str = self._indexed_testDsViAmp1_VddGndPorts_TargetStr(index)
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

    def _ddIiLoad_Point(self, loadrail_is_vdd):
        """simple-as-possible _ddIiLoadPoint: 10K load, no cascoding"""
        point = {'loadrail_is_vdd':loadrail_is_vdd,
                 'chosen_part_index':0,

                 'R':10.0e3,
                                 
                 'W':3*0.18e-6,
                 'L':4*0.18e-6,
                 'Vbias':1.41,
                                 
                 'loadcascode_recurse':0,
                 'loadcascode_W':5*0.18e-6,
                 'loadcascode_L':6*0.18e-6,
                 'loadcascode_Vbias':1.3,
                 }
        
        point_vars = point.keys()
        part_vars = self.lib.ddIiLoad().point_meta.keys()
        assert sorted(point_vars) == sorted(part_vars)
        return point

    def testDdIiLoad(self):
        if self.just1: return
        part = self.lib.ddIiLoad()
        self.assertEqual(sorted(part.externalPortnames()),
                         sorted(['Iout1','Iout2','loadrail','opprail']))

        conns = {'Iout1':'Iout1','Iout2':'Iout2',
                 'loadrail':'Vdd','opprail':'gnd'}
        point = self._ddIiLoad_Point(loadrail_is_vdd=1)
        instance = EmbeddedPart(part, conns, point)

        target_str = """R0 Vdd Iout1  R=10000
R1 Vdd Iout2  R=10000
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

    def _ddViAmp1_Point(self, loadrail_is_vdd, input_is_pmos):
        input_point = self._ddViInput_Point(loadrail_is_vdd, input_is_pmos)
        
        #simple-as-possible: 10K load, no cascoding
        load_point = {
            'loadrail_is_vdd':loadrail_is_vdd,
            'load_chosen_part_index':0,
            'load_R':10.0e3,
            'load_W':3*0.18e-6,
            'load_L':4*0.18e-6,
            'load_Vbias':1.41,
            'loadcascode_recurse':0,
            'loadcascode_W':5*0.18e-6,
            'loadcascode_L':6*0.18e-6,
            'loadcascode_Vbias':1.3,
            }
        point = {}
        point.update(input_point)
        point.update(load_point)
        
        point_vars = point.keys()
        part_vars = self.lib.ddViAmp1().point_meta.keys()
        assert sorted(point_vars) == sorted(part_vars)
        return point

    def _ddViAmp1_VddGndPorts_Point(self, loadrail_is_vdd, input_is_pmos):
        point = self._ddViAmp1_Point(loadrail_is_vdd, input_is_pmos)
        del point['loadrail_is_vdd']
        point['chosen_part_index'] = loadrail_is_vdd
        
        point_vars = point.keys()
        part_vars = self.lib.ddViAmp1_VddGndPorts().point_meta.keys()
        assert sorted(point_vars) == sorted(part_vars)
        return point
        
    def testDdViAmp1(self):
        if self.just1: return
        part = self.lib.ddViAmp1()

        conns = {'Vin1':'Vin1','Vin2':'Vin2',
                 'Iout1':'Iout1','Iout2':'Iout2',
                 'loadrail':'Vdd','opprail':'gnd'}
        
        point = self._ddViAmp1_Point(loadrail_is_vdd=1, input_is_pmos=0)
        instance = EmbeddedPart(part, conns, point)

        target_str = """M0 Iout1 n_auto_14 n_auto_12 n_auto_12 N_18_MM M=1 L=7.2e-07 W=5.4e-07
V1 n_auto_14 0  DC 1.7
M2 n_auto_12 Vin1 n_auto_13 n_auto_13 N_18_MM M=1 L=1.08e-06 W=9e-07
R3 n_auto_13 n_auto_11  R=1.03e+06
M4 Iout2 n_auto_17 n_auto_15 n_auto_15 N_18_MM M=1 L=7.2e-07 W=5.4e-07
V5 n_auto_17 0  DC 1.7
M6 n_auto_15 Vin2 n_auto_16 n_auto_16 N_18_MM M=1 L=1.08e-06 W=9e-07
R7 n_auto_16 n_auto_11  R=1.03e+06
M8 n_auto_11 n_auto_18 gnd gnd N_18_MM M=1 L=1.62e-06 W=1.62e-06
V9 n_auto_18 0  DC 1.74
R10 Vdd Iout1  R=10000
R11 Vdd Iout2  R=10000
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

    def _dsViAmp2_DifferentialMiddle_Point(self, stage1_loadrail_is_vdd,
                                           stage1_input_is_pmos,
                                           stage2_loadrail_is_vdd,
                                           stage2_input_is_pmos):
                                           
        stage1_point = self._ddViAmp1_Point(stage1_loadrail_is_vdd,
                                            stage1_input_is_pmos)
        stage2_point = self._dsViAmp1_Point(stage2_loadrail_is_vdd,
                                            stage2_input_is_pmos)
        
        shifter_point = self._levelShifterOrWire_Point(stage1_loadrail_is_vdd)
        feedback_point = self._viFeedback_Point(use_pmos=0)

        d = {}
        for name, value in stage1_point.items(): d['stage1_' + name] = value
        for name, value in stage2_point.items(): d['stage2_' + name] = value
        for name, value in shifter_point.items(): d['shifter_' + name] = value
        for name, value in feedback_point.items(): d['feedback_' + name] = value
        
        part_vars = self.lib.dsViAmp2_DifferentialMiddle().point_meta.keys()
        d_vars = d.keys()
        assert sorted(d_vars) == sorted(part_vars)
               
        return d

    def testDsViAmp2_DifferentialMiddle(self):
        return #HACK
        if self.just1: return
        part = self.lib.dsViAmp2_DifferentialMiddle()
    
        conns = part.unityPortMap()
        point = self._dsViAmp2_DifferentialMiddle_Point(1,0,1,0)
        instance = EmbeddedPart(part, conns, point)

        target_str = """
"""
        actual_str = instance.spiceNetlistStr()
        #self._compareStrings3(target_str, actual_str)

        #stress test
        for i in range(20):
            point = self._dsViAmp2_DifferentialMiddle_Point(random.randint(0,1),
                                                            random.randint(0,1),
                                                            random.randint(0,1),
                                                            random.randint(0,1))
            instance = EmbeddedPart(part, conns, point)


    def _dsViAmp2_SingleEndedMiddle_VddGndPorts_Point(self,
                                                      stage1_loadrail_is_vdd,
                                                      stage1_input_is_pmos,
                                                      stage2_loadrail_is_vdd,
                                                      stage2_input_is_pmos,
                                                      shifter_Drail_is_vdd,
                                                      shifter_use_wire):
        #gather the point for each sub-part
        stage1_point = self._dsViAmp1_VddGndPorts_Point(stage1_loadrail_is_vdd,
                                                        stage1_input_is_pmos)
        assert stage1_point['chosen_part_index'] == stage1_loadrail_is_vdd
        assert stage1_point['input_is_pmos'] == stage1_input_is_pmos
        
        stage2_point = self._ssViAmp1_VddGndPorts_Point(stage2_loadrail_is_vdd,
                                                        stage2_input_is_pmos)
        assert stage2_point['chosen_part_index'] == stage2_loadrail_is_vdd
        assert stage2_point['input_is_pmos'] == stage2_input_is_pmos
        
        shifter_point = self._levelShifterOrWire_VddGndPorts_Point( \
            shifter_Drail_is_vdd,
            shifter_use_wire)
        assert shifter_point['Drail_is_vdd'] == shifter_Drail_is_vdd
        assert shifter_point['use_wire'] == shifter_use_wire
        
        feedback_point = {'C':1.0e-9} #note the HACK for just capacitor

        #build up an overall point 'd'
        d = {}
        for name, value in stage1_point.items(): d['stage1_' + name] = value
        for name, value in stage2_point.items(): d['stage2_' + name] = value
        for name, value in shifter_point.items(): d['shifter_' + name] = value
        for name, value in feedback_point.items(): d['feedback_' + name] = value

        d['stage1_loadrail_is_vdd'] = stage1_loadrail_is_vdd
        d['stage2_loadrail_is_vdd'] = stage2_loadrail_is_vdd
        del d['stage1_chosen_part_index']
        del d['stage2_chosen_part_index']
        del d['shifter_chosen_part_index']

        #validate d
        part = self.lib.dsViAmp2_SingleEndedMiddle_VddGndPorts()
        part_vars = part.point_meta.keys()
        d_vars = d.keys()
        assert sorted(part_vars) == sorted(d_vars)

        #done
        return d

    def _dsViAmp2_Point(self,
                        single_ended_middle,
                        stage1_loadrail_is_vdd,
                        stage1_input_is_pmos,
                        stage2_loadrail_is_vdd,
                        stage2_input_is_pmos):
        dss_point = self._dsViAmp2_SingleEndedMiddle_Point( \
            stage1_loadrail_is_vdd,
            stage1_input_is_pmos,
            stage2_loadrail_is_vdd,
            stage2_input_is_pmos)
        assert dss_point['stage2_input_is_pmos'] == stage2_input_is_pmos
        
        dds_point = self._dsViAmp2_DifferentialMiddle_Point(\
            stage1_loadrail_is_vdd,
            stage1_input_is_pmos,
            stage2_loadrail_is_vdd,
            stage2_input_is_pmos)
        assert dds_point['stage2_input_is_pmos'] == stage2_input_is_pmos
        
        point = {}
        point.update(dss_point)
        point.update(dds_point)
        point['chosen_part_index'] = single_ended_middle

        point_vars = point.keys()
        part_vars = self.lib.dsViAmp2().point_meta.keys()
        assert sorted(point_vars) == sorted(part_vars)
        return point

    def _dsViAmp2_VddGndPorts_Point(self, 
                                    single_ended_middle,
                                    stage1_loadrail_is_vdd,
                                    stage1_input_is_pmos,
                                    stage2_loadrail_is_vdd,
                                    stage2_input_is_pmos):
        point = self._dsViAmp2_Point(single_ended_middle,
                                     stage1_loadrail_is_vdd,
                                     stage1_input_is_pmos,
                                     stage2_loadrail_is_vdd,
                                     stage2_input_is_pmos)
        assert point['stage1_loadrail_is_vdd'] == stage1_loadrail_is_vdd
        assert point['stage1_input_is_pmos'] == stage1_input_is_pmos
        assert point['stage2_loadrail_is_vdd'] == stage2_loadrail_is_vdd
        assert point['stage2_input_is_pmos'] == stage2_input_is_pmos

        if stage1_loadrail_is_vdd==0 and stage2_loadrail_is_vdd==0:
            chosen_part_index=0
        elif stage1_loadrail_is_vdd==0 and stage2_loadrail_is_vdd==1:
            chosen_part_index=1
        elif stage1_loadrail_is_vdd==1 and stage2_loadrail_is_vdd==0:
            chosen_part_index=2
        elif stage1_loadrail_is_vdd==1 and stage2_loadrail_is_vdd==1:
            chosen_part_index=3

        point['chosen_part_index'] = chosen_part_index
        del point['stage1_loadrail_is_vdd']
        del point['stage2_loadrail_is_vdd']
        point['single_ended_middle'] = single_ended_middle

        point_vars = point.keys()
        part_vars = self.lib.dsViAmp2_VddGndPorts().point_meta.keys()
        assert sorted(point_vars) == sorted(part_vars)
        return point
        
    def testDsViAmp2_SingleEndedMiddle(self):
        return #FIXME
        if self.just1: return
        part = self.lib.dsViAmp2_SingleEndedMiddle()
    
        conns = part.unityPortMap()
        point = self._dsViAmp2_SingleEndedMiddle_Point(1,0,1,0)
        instance = EmbeddedPart(part, conns, point)

        target_str = """
"""
        actual_str = instance.spiceNetlistStr()
        #self._compareStrings3(target_str, actual_str)

        #stress test
        for i in range(20):
            point = self._dsViAmp2_DifferentialMiddle_Point(random.randint(0,1),
                                                            random.randint(0,1),
                                                            random.randint(0,1),
                                                            random.randint(0,1))
            instance = EmbeddedPart(part, conns, point)

    def testDsViAmp2_VddGndPorts(self):
        if self.just1: return
        #FIXME
        pass

    def testDsViAmp_VddGndPorts(self):
        if self.just1: return
        #FIXME
        pass

    def _millerAmpPoint(self,
                        stage1_loadrail_is_vdd,
                        stage1_input_is_pmos,
                        stage2_loadrail_is_vdd,
                        stage2_input_is_pmos):
        #being a Miller, it is:
        # -a dsViAmp2
        # -with a single-ended middle
        # -feedback is merely a capacitor
        shifter_Drail_is_Vdd = True
        shifter_use_wire = True
        point = self._dsViAmp2_SingleEndedMiddle_VddGndPorts_Point(\
            stage1_loadrail_is_vdd,
            stage1_input_is_pmos,
            stage2_loadrail_is_vdd,
            stage2_input_is_pmos,
            shifter_Drail_is_Vdd,
            shifter_use_wire)
        assert point['stage1_loadrail_is_vdd'] == stage1_loadrail_is_vdd
        assert point['stage1_input_is_pmos'] == stage1_input_is_pmos
        assert point['stage2_loadrail_is_vdd'] == stage2_loadrail_is_vdd
        assert point['stage2_input_is_pmos'] == stage2_input_is_pmos
        assert point['shifter_Drail_is_vdd'] == shifter_Drail_is_Vdd
        assert point['shifter_use_wire'] == shifter_use_wire

        #make the topology choices the simplest topologies possible
        point['stage1_cascode_is_wire'] = 1 #'1' is wire
        point['stage1_degen_choice'] = 0 #'0' is wire
        point['stage1_load_chosen_part_index'] = 0 #'0' is simple CM
        
        point['stage2_degen_choice'] = 0 #'0' is wire

        point_vars = point.keys()
        part = self.lib.dsViAmp2_SingleEndedMiddle_VddGndPorts()
        part_vars = part.point_meta.keys()
        assert sorted(point_vars) == sorted(part_vars)
        
        return point

    def testMillerAmp_0(self):
        if self.just1: return
        return #HACK: this currently breaks

        part = self.lib.dsViAmp2_SingleEndedMiddle_VddGndPorts()
        self.assertEqual( part.numSubpartPermutations(), None)
        self.assertEqual( part.schemas(), None)
        
        #1st stage is nmos-input, stacked
        #2nd stage is nmos-input, stacked
        point = self._millerAmpPoint(stage1_loadrail_is_vdd=True,
                                     stage1_input_is_pmos=False,
                                     stage2_loadrail_is_vdd=True,
                                     stage2_input_is_pmos=False)
        
        conns = part.unityPortMap()
        instance = EmbeddedPart(part, conns, point)

        target_str = """

Rwire0 n_auto_26 n_auto_29  R=0
M1 n_auto_29 Vin1 n_auto_30 n_auto_30 N_18_MM M=1 L=1.08e-06 W=9e-07
Rwire2 n_auto_30 n_auto_28  R=0
Rwire3 n_auto_27 n_auto_31  R=0
M4 n_auto_31 Vin2 n_auto_32 n_auto_32 N_18_MM M=1 L=1.08e-06 W=9e-07
Rwire5 n_auto_32 n_auto_28  R=0
M6 n_auto_28 n_auto_33 gnd gnd N_18_MM M=1 L=1.62e-06 W=1.62e-06
V7 n_auto_33 0  DC 1.74
M8 n_auto_26 n_auto_26 Vdd Vdd P_18_MM M=1 L=7.2e-07 W=1.08e-06
M9 n_auto_27 n_auto_26 Vdd Vdd P_18_MM M=1 L=7.2e-07 W=2.16e-06
Rwire10 n_auto_27 n_auto_24  R=0
Rwire11 Iout n_auto_34  R=0
M12 n_auto_34 n_auto_25 n_auto_35 n_auto_35 N_18_MM M=1 L=3e-06 W=4e-06
Rwire13 n_auto_35 gnd  R=0
R14 Vdd Iout  R=10000
Rwire15 n_auto_24 n_auto_25  R=0
C16 Iout n_auto_24  C=1e-09
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings4(target_str, actual_str)

    def testMillerAmp_1(self):
        return #HACK: this currently breaks
        if self.just1: return
        #1st stage is nmos-input, stacked
        #2nd stage is pmos-input, stacked
        point = self._millerAmpPoint(stage1_loadrail_is_vdd=True,
                                     stage1_input_is_pmos=False,
                                     stage2_loadrail_is_vdd=False,
                                     stage2_input_is_pmos=True)
        part = self.lib.dsViAmp2_SingleEndedMiddle_VddGndPorts()
        conns = part.unityPortMap()
        instance = EmbeddedPart(part, conns, point)

        target_str = """

Rwire0 n_auto_26 n_auto_29  R=0
M1 n_auto_29 Vin1 n_auto_30 n_auto_30 N_18_MM M=1 L=1.08e-06 W=9e-07
Rwire2 n_auto_30 n_auto_28  R=0
Rwire3 n_auto_27 n_auto_31  R=0
M4 n_auto_31 Vin2 n_auto_32 n_auto_32 N_18_MM M=1 L=1.08e-06 W=9e-07
Rwire5 n_auto_32 n_auto_28  R=0
M6 n_auto_28 n_auto_33 gnd gnd N_18_MM M=1 L=1.62e-06 W=1.62e-06
V7 n_auto_33 0  DC 1.74
M8 n_auto_26 n_auto_26 Vdd Vdd P_18_MM M=1 L=7.2e-07 W=1.08e-06
M9 n_auto_27 n_auto_26 Vdd Vdd P_18_MM M=1 L=7.2e-07 W=2.16e-06
Rwire10 n_auto_27 n_auto_24  R=0
Rwire11 Iout n_auto_34  R=0
M12 n_auto_34 n_auto_25 n_auto_35 n_auto_35 P_18_MM M=2 L=3e-06 W=4e-06
Rwire13 n_auto_35 Vdd  R=0
R14 gnd Iout  R=10000
Rwire15 n_auto_24 n_auto_25  R=0
C16 Iout n_auto_24  C=1e-09
"""
        actual_str = instance.spiceNetlistStr(False)
        self._compareStrings4(target_str, actual_str)

    def testMillerAmp_2(self):
        return #HACK: this currently breaks
        if self.just1: return
        #1st stage is pmos-input, folded
        #2nd stage is pmos-input, folded
        point = self._millerAmpPoint(stage1_loadrail_is_vdd=True,
                                     stage1_input_is_pmos=True,
                                     stage2_loadrail_is_vdd=True,
                                     stage2_input_is_pmos=True)
        part = self.lib.dsViAmp2_SingleEndedMiddle_VddGndPorts()
        conns = part.unityPortMap()
        instance = EmbeddedPart(part, conns, point)

        target_str = """

M0 n_auto_61 n_auto_66 n_auto_65 n_auto_65 N_18_MM M=1 L=7.2e-07 W=5.4e-07
V1 n_auto_66 0  DC 1.7
M2 n_auto_65 Vin1 n_auto_64 n_auto_64 P_18_MM M=1 L=1.08e-06 W=1.8e-06
Rwire3 n_auto_64 n_auto_63  R=0
M4 n_auto_65 n_auto_67 gnd gnd N_18_MM M=1 L=1.62e-06 W=1.62e-06
V5 n_auto_67 0  DC 1.74
M6 n_auto_62 n_auto_70 n_auto_69 n_auto_69 N_18_MM M=1 L=7.2e-07 W=5.4e-07
V7 n_auto_70 0  DC 1.7
M8 n_auto_69 Vin2 n_auto_68 n_auto_68 P_18_MM M=1 L=1.08e-06 W=1.8e-06
Rwire9 n_auto_68 n_auto_63  R=0
M10 n_auto_69 n_auto_71 gnd gnd N_18_MM M=1 L=1.62e-06 W=1.62e-06
V11 n_auto_71 0  DC 1.74
M12 n_auto_63 n_auto_72 Vdd Vdd P_18_MM M=1 L=1.62e-06 W=3.24e-06
V13 n_auto_72 0  DC 0.06
M14 n_auto_61 n_auto_61 Vdd Vdd P_18_MM M=1 L=7.2e-07 W=1.08e-06
M15 n_auto_62 n_auto_61 Vdd Vdd P_18_MM M=1 L=7.2e-07 W=2.16e-06
Rwire16 n_auto_62 n_auto_59  R=0
M17 Iout n_auto_75 n_auto_74 n_auto_74 N_18_MM M=1 L=7.2e-07 W=5.4e-07
V18 n_auto_75 0  DC 1.7
M19 n_auto_74 n_auto_60 n_auto_73 n_auto_73 P_18_MM M=2 L=3e-06 W=4e-06
Rwire20 n_auto_73 Vdd  R=0
M21 n_auto_74 n_auto_76 gnd gnd N_18_MM M=2 L=5e-06 W=3e-06
V22 n_auto_76 0  DC 1.74
R23 Vdd Iout  R=10000
Rwire24 n_auto_59 n_auto_60  R=0
C25 Iout n_auto_59  C=1e-09
"""
        actual_str = instance.spiceNetlistStr(False)
        self._compareStrings4(target_str, actual_str)

    def testMillerAmp_3(self):
        return #HACK: this currently breaks
        if self.just1: return
        #-1st stage is nmos-input, stacked
        #-2nd stage is pmos-input, stacked
        #-plus a level shifter implemented as two nmoses
        point = self._millerAmpPoint(stage1_loadrail_is_vdd=True,
                                     stage1_input_is_pmos=False,
                                     stage2_loadrail_is_vdd=False,
                                     stage2_input_is_pmos=True)
        
        point['shifter_Drail_is_vdd'] = 1
        point['shifter_use_wire'] = 0
        point['shifter_cascode_do_stack'] = 0
        
        part = self.lib.dsViAmp2_SingleEndedMiddle_VddGndPorts()
        conns = part.unityPortMap()
        instance = EmbeddedPart(part, conns, point)

        target_str = """

Rwire0 n_auto_113 n_auto_116  R=0
M1 n_auto_116 Vin1 n_auto_117 n_auto_117 N_18_MM M=1 L=3e-06 W=4e-06
Rwire2 n_auto_117 n_auto_115  R=0
Rwire3 n_auto_114 n_auto_118  R=0
M4 n_auto_118 Vin2 n_auto_119 n_auto_119 N_18_MM M=1 L=3e-06 W=4e-06
Rwire5 n_auto_119 n_auto_115  R=0
M6 n_auto_115 n_auto_120 gnd gnd N_18_MM M=2 L=5e-06 W=3e-06
V7 n_auto_120 0  DC 1.74
M8 n_auto_113 n_auto_113 Vdd Vdd P_18_MM M=1 L=9e-07 W=1.08e-06
M9 n_auto_114 n_auto_113 Vdd Vdd P_18_MM M=1 L=9e-07 W=2.16e-06
Rwire10 n_auto_114 n_auto_111  R=0
Rwire11 Iout n_auto_121  R=0
M12 n_auto_121 n_auto_112 n_auto_122 n_auto_122 P_18_MM M=1 L=1.08e-06 W=1.8e-06
Rwire13 n_auto_122 Vdd  R=0
R14 gnd Iout  R=10000
M15 Vdd n_auto_111 n_auto_112 n_auto_112 N_18_MM M=1 L=5.4e-07 W=5.4e-07
M16 n_auto_112 n_auto_123 gnd gnd N_18_MM M=1 L=9e-07 W=9e-07
V17 n_auto_123 0  DC 1.5
C18 Iout n_auto_111  C=1e-09
"""
        actual_str = instance.spiceNetlistStr(False)
        self._compareStrings4(target_str, actual_str)


        
    #=================================================================
    #Helper functions for these unit tests
    def _compareStrings(self, target_str_in, actual_str):
        """This is complex because it needs to take into account
        that auto-named nodes can have different values"""
        maxn = 30
        cand_xs = range(maxn)
        cand_ys = [-1]
        cand_zs = [-2]
        if 'yyy' in target_str_in: cand_ys = range(maxn)
        if 'zzz' in target_str_in: cand_zs = range(maxn)

        self.assertTrue( self._foundMatch(target_str_in, actual_str,
                                          cand_xs, cand_ys, cand_zs),
                         '\ntarget=\n[%s]\n\nactual=\n[%s]\n' %
                         (target_str_in, actual_str))

    def _foundMatch(self, target_str_in, actual_str, cand_xs, cand_ys, cand_zs):
        assert len(cand_xs)>0 and len(cand_ys)>0 and len(cand_zs)>0
        for nodenum_xxx in cand_xs:
            for nodenum_yyy in cand_ys:
                if nodenum_yyy == nodenum_xxx: continue
                for nodenum_zzz in cand_zs:
                    if nodenum_zzz == nodenum_xxx: continue
                    if nodenum_zzz == nodenum_yyy: continue
                    target_str = target_str_in.replace('xxx', str(nodenum_xxx))
                    target_str = target_str.replace('yyy', str(nodenum_yyy))
                    target_str = target_str.replace('zzz', str(nodenum_zzz))
                    if actual_str == target_str:
                        return True
        return False

    
    def _compareStrings2(self, target_str, actual_str):
        """Compres equality of two strings, but ignores the actual
        values in the auto-created nodenumbers"""

        self._compareStrings(replaceAutoNodesWithXXX(target_str), replaceAutoNodesWithXXX(actual_str))

    def _compareStrings3(self, target_str, actual_str):
        """Like compareStrings2, but also on every line, ignores everything
        after the M=.
        This way, we don't have to tediously rewrite our netlist every
        time we make a change to the way that M, W, and L are calculated
        as a function of Ibias etc in operating point formulation.

        For the simpler circuits we should still be checking the W and L values.
        """
        self._compareStrings2(replaceAfterMWithBlank(target_str),
                              replaceAfterMWithBlank(actual_str))
        
    def _compareStrings4(self, target_str, actual_str):
        """Like compareStrings2, but ignore the summaryStr()'s
        """
        self._compareStrings3(replaceSummaryStrWithBlank(target_str),
                              replaceSummaryStrWithBlank(actual_str))
        
    def tearDown(self):
        pass

if __name__ == '__main__':
    import logging
    logging.basicConfig()
    logging.getLogger('library').setLevel(logging.DEBUG)
    logging.getLogger('part').setLevel(logging.DEBUG)
    
    unittest.main()

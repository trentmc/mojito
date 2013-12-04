import unittest

from adts import *
from adts.Part import NodeNameFactory, flattenedTupleList, validateFunctions,\
     replaceAutoNodesWithXXX, evalFunction

from util.constants import *

class PartTest(unittest.TestCase):

    def setUp(self):
        self.just1 = False #to make True is a HACK

        #a couple atomic parts (res and cap)
        self.resistance_varmeta = ContinuousVarMeta(True, 1, 7, 'R')
        self.res_part = AtomicPart('R', ['node_a', 'node_b'],
                                   PointMeta([self.resistance_varmeta]),
                                   name = 'resistor')
    
        self.cap_part = AtomicPart('C', ['cnode_a', 'cnode_b'],
                                   PointMeta([]),
                                   name = 'capacitor')

        #DOCs
        self.sim_doc1 = SimulationDOC(Metric('operating_region',
                                             REGION_SATURATION,
                                             REGION_SATURATION, False),'region')
        self.sim_doc2 = SimulationDOC(Metric('v_od', 0.2, 5.0, False),'vgs-vt')

        self.min_R = 10**self.resistance_varmeta.min_unscaled_value
        self.func_doc1 = FunctionDOC(Metric('R_metric',self.min_R*2,
                                            100.0, False),'(R)')
        
        self.func_doc2 = FunctionDOC(Metric('R_metric',self.min_R*2,
                                            100.0, False),'(r)')
        
        #a FlexPart
        flex = FlexPart( ['flex_ext1','flex_ext2'],
                         PointMeta([self.resistance_varmeta]),
                         'res_or_cap')
        self.assertEqual(flex.part_choices, [])
        flex.addPartChoice( self.res_part,
                            {'node_a':'flex_ext1', 'node_b':'flex_ext2'},
                            {'R':'R'} )
        flex.addPartChoice( self.cap_part,
                            {'cnode_a':'flex_ext1','cnode_b':'flex_ext2'},
                            {} )
        self.flex_part = flex

        #a CompoundPart
        r1a_varmeta = ContinuousVarMeta(True, 1, 7, 'res1a')
        r1b_varmeta = ContinuousVarMeta(True, 1, 7, 'res1b')
        r2_varmeta = ContinuousVarMeta(True, 1, 7, 'res2')
        pointmeta = PointMeta([r1a_varmeta, r1b_varmeta, r2_varmeta])

        comp_part = CompoundPart(['A', 'B'], pointmeta, 'series_Rs')
        self.assertEqual(comp_part.internalNodenames(), [])
        
        internal_nodename = comp_part.addInternalNode()
        comp_part.addPart( self.res_part,
                           {'node_a':'A','node_b':internal_nodename},
                           {'R':'res1a + res1b'} )
        comp_part.addPart( self.res_part,
                           {'node_a':internal_nodename,'node_b':'B'},
                           {'R':'res2'} )
        self.compound_part = comp_part
        self.compound_internal_nodename = internal_nodename

    def testFunctionDoc(self):
        if self.just1: return

        scaled_point = {'R':self.min_R}

        self.assertFalse(self.func_doc1.resultsAreFeasible(scaled_point))
        
        scaled_point = {'R':self.min_R*5}
        self.assertTrue(self.func_doc1.resultsAreFeasible(scaled_point))

        self.assertEqual(self.func_doc1.metric.name, 'R_metric')
        self.assertEqual(self.func_doc1.function_str, '(R)')


        #
        self.assertRaises(ValueError, FunctionDOC, 'not_metric', '(r)')

        #
        metric_with_objective = Metric('R_metric', 0.0, 100.0, True)
        self.assertRaises(ValueError, FunctionDOC,
                          metric_with_objective, '(r)')

        #
        self.assertRaises(ValueError, FunctionDOC,
                          Metric('R_metric', 0.0, 100.0, False), [])


    def testSimulationDoc(self):
        if self.just1: return

        lis_results = {'lis__m42__region':0,
                       'lis__m12__vgs':5.0,
                       'lis__m12__vt':2.0,
                       'lis__m12__blah':500.0,
                       'lis__blah__vgs':10000,
                       'lis__m14__region':REGION_LINEAR,
                       'lis__m15__region':REGION_SATURATION}

        self.assertEqual(self.sim_doc1.evaluateFunction(lis_results, 'm14'),
                         REGION_LINEAR)
        self.assertFalse(self.sim_doc1.resultsAreFeasible(lis_results, 'm14'))
        
        self.assertEqual(self.sim_doc1.evaluateFunction(lis_results, 'm15'),
                         REGION_SATURATION)
        self.assertTrue(self.sim_doc1.resultsAreFeasible(lis_results, 'm15'))

        self.assertEqual(self.sim_doc2.metric.name, 'v_od')
        self.assertEqual(self.sim_doc2.function_str, 'vgs-vt')
        self.assertEqual(self.sim_doc2.evaluateFunction(lis_results, 'm12'), 5.0-2.0)
        self.assertTrue(self.sim_doc2.resultsAreFeasible(lis_results, 'm12'))
        
        lis_results['lis__m12__vt'] = 4.95
        self.assertFalse(self.sim_doc2.resultsAreFeasible(lis_results, 'm12'))

        #it can handle uppercase or lowercase device_names
        self.assertEqual(self.sim_doc1.evaluateFunction(lis_results, 'M14'),
                         REGION_LINEAR)

        #
        self.assertRaises(ValueError, SimulationDOC, 'not_metric', 'vgs')

        #
        metric_with_objective = Metric('vgs', 1.0, 2.0, True)
        self.assertRaises(ValueError, SimulationDOC, metric_with_objective,
                          'vgs-vt')

        #
        self.assertRaises(ValueError, SimulationDOC,
                          Metric('vgs', 1.0, 2.0, False), [])

        #
        self.assertRaises(ValueError, SimulationDOC,
                          Metric('vgs', 1.0, 2.0, False), 'VGS')

    def testAtomicPart(self):
        if self.just1: return
        part = self.res_part
        self.assertEqual(part.spice_symbol, 'R')
        self.assertEqual(part.model_name, '')
        self.assertEqual(part.point_meta['R'].railbinUnscaled(10), 7)
        self.assertEqual(part.point_meta['R'].spiceNetlistStr(1e5),'R=%g' % 1e5)
        
        self.assertEqual( part.externalPortnames(), ['node_a', 'node_b'])
        self.assertEqual( part.internalNodenames(), [])
        self.assertEqual( part.embeddedParts({}), [] )
        self.assertEqual( part.portNames(), ['node_a', 'node_b'])
        self.assertEqual( part.unityVarMap(), {'R':'R'} )
        self.assertEqual( part.unityPortMap(),
                          {'node_a':'node_a','node_b':'node_b'} )
        self.assertTrue(len(str(part))>0)
        self.assertTrue(len(part.str2(1))>0)
        
        part.addSimulationDOC(self.sim_doc1)
        part.addSimulationDOC(self.sim_doc2)
        self.assertEqual(part.simulation_DOCs[1].metric.name, 'v_od')
        
        part.addFunctionDOC(self.func_doc1)
        self.assertEqual(part.function_DOCs[0].metric.name, 'R_metric')

    def testFlexPart(self):
        if self.just1: return

        part = self.flex_part

        #test functionality specific to FlexPart
        self.assertEqual(len(part.part_choices), 2)
        self.assertTrue(isinstance(part.part_choices[0], EmbeddedPart))
        self.assertEqual(part.part_choices[1].part.ID, self.cap_part.ID)
        self.assertEqual(sorted(part.point_meta.keys()),
                         sorted(['chosen_part_index', 'R']))
        scaled_point = Point(True, {'chosen_part_index':1, 'R':10})
        self.assertEqual(part.chosenPart(scaled_point).part.ID, self.cap_part.ID)

        #test functionality common to all Part types
        # (though FlexPart has interesting behavior with that, so test it!)
        self.assertEqual( part.externalPortnames(), ['flex_ext1', 'flex_ext2'])
        emb_parts = part.embeddedParts(scaled_point)
        names = part.internalNodenames()
        self.assertEqual(len(emb_parts), 1)
        self.assertEqual(emb_parts[0].part.ID, self.cap_part.ID)
        self.assertEqual(names, [])
        self.assertEqual( part.portNames(), ['flex_ext1', 'flex_ext2'])
        self.assertEqual( part.unityVarMap(),
                          {'R':'R','chosen_part_index':'chosen_part_index'} )
        self.assertEqual( part.unityPortMap(),
                          {'flex_ext1':'flex_ext1','flex_ext2':'flex_ext2'} )
        self.assertTrue(len(str(part))>0)
        self.assertTrue(len(part.str2(1))>0)

        part.addSimulationDOC(self.sim_doc1)
        part.addSimulationDOC(self.sim_doc2)
        self.assertEqual(part.simulation_DOCs[1].metric.name, 'v_od')
        
        part.addFunctionDOC(self.func_doc1)
        self.assertEqual(part.function_DOCs[0].metric.name, 'R_metric')

    def testCompoundPart_and_EmbeddedPart(self):
        if self.just1: return

        part = self.compound_part
        internal_nodename = self.compound_internal_nodename

        #test functionality common to all Part types
        self.assertEqual(part.point_meta['res1a'].railbinUnscaled(10), 7)
        self.assertEqual( part.externalPortnames(), ['A', 'B'])
        self.assertEqual( part.internalNodenames(), [internal_nodename] )
        self.assertTrue( len(part.embeddedParts({})) > 0 )
        self.assertEqual( part.portNames(), ['A', 'B', internal_nodename])
        self.assertEqual( part.unityVarMap(),
                          {'res1a':'res1a', 'res1b':'res1b', 'res2':'res2'} )
        self.assertEqual( part.unityPortMap(), {'A':'A','B':'B'} )
        self.assertTrue(len(str(part))>0)
        self.assertTrue(len(part.str2(1))>0)

        part.addSimulationDOC(self.sim_doc1)
        part.addSimulationDOC(self.sim_doc2)
        self.assertEqual(part.simulation_DOCs[1].metric.name, 'v_od')
        
        part.addFunctionDOC(self.func_doc1)
        self.assertEqual(part.function_DOCs[0].metric.name, 'R_metric')

        #test functionality specific to CompoundPart
        self.assertEqual(len(part.embedded_parts), 2)
        
        emb1 = part.embedded_parts[1]
        self.assertEqual(emb1.part.name, 'resistor')
        self.assertEqual(emb1.connections['node_b'], 'B')
        self.assertEqual(emb1.functions['R'], 'res2')
        self.assertTrue( len(str(emb1)) > 0)

        #test EmbeddedPart, including SPICE netlisting
        bigemb = EmbeddedPart(part,
                              {'A':'a', 'B':'b'},
                              {'res1a':10e3, 'res1b':11e3,
                               'res2':20e3})
        self.assertEqual(bigemb.part.name, 'series_Rs')
        self.assertEqual(bigemb.connections['B'], 'b')
        self.assertEqual(len(bigemb.connections), 2)
        self.assertEqual(bigemb.functions['res1a'], 10e3)
        self.assertEqual(len(bigemb.functions), 3)
        self.assertTrue(len(str(bigemb)) > 0)

        """We want a netlist that looks like the following; the number
        following 'n_auto_' could be any number, however.
        'R0 a n_auto_2  R=21000\n'
        'R1 n_auto_2 b  R=20000\n'
        Our strategy is to replace all 'n_auto_NUM' with 'XXX'.
        """
        netlist = replaceAutoNodesWithXXX(bigemb.spiceNetlistStr())
        self.assertEqual(netlist,
                         'R0 a XXX  R=21000\n'
                         'R1 XXX b  R=20000\n')

        bb_netlist = bigemb.spiceNetlistStr(True)

    def testSwitchAndEval(self):
        if self.just1: return
        case2result = {3:'4.2', 'yo':'7+2', 'p':'1/0', 'default':'400/9'}
        self.assertEqual(switchAndEval(3, case2result), 4.2)
        self.assertEqual(switchAndEval('yo', case2result), 7+2)
        self.assertRaises(ZeroDivisionError, switchAndEval, 'p', case2result)
        self.assertEqual(switchAndEval('blah', case2result), 400/9)
        self.assertEqual(switchAndEval('default', case2result), 400/9)
        
        no_default = {3:'4.2', 'yo':'7+2', 'p':'1/0'}
        self.assertRaises(KeyError, switchAndEval, 'blah', no_default)

    def testWireFactory(self):
        if self.just1: return
        wire1 = WireFactory().build()
        wire2 = WireFactory().build()
        self.assertEqual(len(wire1.point_meta), 0) #should have no parameters
        self.assertEqual(wire1.ID, wire2.ID) #should be singleton part

    def testValidateFunctions(self):
        if self.just1: return
        unscaled_point = Point(False, {'W':10,'L':2})
        self.assertRaises(ValueError, validateFunctions,
                          {'x':'W/L'}, unscaled_point)
        
        scaled_point = Point(False, {'W':10,'L':2})
        self.assertRaises(ValueError, validateFunctions,
                          {'x':'blah W/L'}, scaled_point)
        
    def testEvalFunction(self):
        #if self.just1: return
        
        self.assertEqual(evalFunction({'W':10,'L':2}, 'W / L'), 5)

        #make sure that we don't accidentally substitite 'var'
        # into 'bigvarname'
        self.assertEqual(evalFunction({'var':10,'bigvarname':2},
                                      'var / bigvarname'), 5)

        #make sure that the fix for this doesn't just wrap () around
        # alphanumeric characteris
        self.assertEqual(evalFunction({'var':10,'bigvarname':2},
                                      'max(var, bigvarname)'), 10)

        #more tests
        p = {'x':1,'xx':10,'xxx':100,'xx_xx':1000,'_':12}
        self.assertEqual(evalFunction(p,'x+xx+xxx*2+xx_xx'), 1211)
        self.assertEqual(evalFunction(p,' x+xx+xxx*2+xx_xx'), 1211)
        self.assertEqual(evalFunction(p,'x+xx+xxx*2+xx_xx '), 1211)
        self.assertEqual(evalFunction(p,'x+    xx+xxx  *2+xx_xx '), 1211)
        self.assertEqual(evalFunction(p,'x+xx + xxx*2+xx_xx '), 1211)
        self.assertEqual(evalFunction(p,'xx_xx * x + xx_xx '), 2000)
        self.assertEqual(evalFunction(p,' _'), 12) #yes it supports just '_'
        self.assertEqual(evalFunction(p,'3'), 3)
        self.assertEqual(evalFunction(p,' 32'), 32)
        self.assertEqual(evalFunction(p,'32 '), 32)
        self.assertAlmostEqual(evalFunction(p,'3.2e5'), 3.2e5)
        self.assertAlmostEqual(evalFunction(p,'3.2e5 + 1e5'), 4.2e5)

        #'raise' tests
        self.assertRaises(ValueError, evalFunction, {'W':10,'L':2}, 'bad W / L')
        
        #special case: return a '' if the function is ''
        self.assertEqual(evalFunction({'W':10,'L':2}, ''), '')

    def testFlattenedTupleList(self):
        if self.just1: return
        self.assertEqual(flattenedTupleList([]),[])
        self.assertEqual(flattenedTupleList([(1,2),(3,4)]),[1,3,2,4])

    def testNodeNameFactory(self):
        if self.just1: return
        for i in range(500):
            name1 = NodeNameFactory().build()
            name2 = NodeNameFactory().build()
            self.assertNotEqual(name1, name2)

    def testPartCountingWithSchemas1(self):
        if self.just1: return

        #test the parts that we use in other unit tests
        self.assertEqual(self.res_part.schemas(), Schemas([Schema({})]))
        self.assertEqual(self.res_part.numSubpartPermutations(), 1)
        self.assertEqual(self.cap_part.schemas(), Schemas([Schema({})]))
        self.assertEqual(self.cap_part.numSubpartPermutations(), 1)
        self.assertEqual(self.flex_part.schemas(),
                         Schemas([Schema({'chosen_part_index':[0,1]})]))
        self.assertEqual(self.flex_part.numSubpartPermutations(), 2)
        self.assertEqual(self.compound_part.schemas(),
                         Schemas([Schema({})]))
        self.assertEqual(self.compound_part.numSubpartPermutations(), 1)

    def testPartCountingWithSchemas2(self):
        if self.just1: return

        #test using parts we create here; focus is on multiple levels of
        # hierarchy, without extra variables or external nodes to clutter it up
        #-but note that FlexParts add the 'chosen_part_index' variable,
        # which is, of course, the key to counting

        #nmos4
        nmos4 = AtomicPart('M', [], PointMeta([]), name = 'nmos4')
        self.assertEqual(nmos4.schemas(), Schemas([Schema({})]))
        self.assertEqual(nmos4.numSubpartPermutations(), 1)

        #pmos4
        pmos4 = AtomicPart('M', [], PointMeta([]), name = 'pmos4')
        self.assertEqual(pmos4.schemas(), Schemas([Schema({})]))
        self.assertEqual(pmos4.numSubpartPermutations(), 1)

        #mos4 = nmos4 or pmos4
        mos4 = FlexPart([], PointMeta([]), 'mos4')
        mos4.addPartChoice(nmos4, {}, {})
        mos4.addPartChoice(pmos4, {}, {})
        self.assertEqual(mos4.schemas(),
                         Schemas([Schema({'chosen_part_index':[0,1]})]))
        self.assertEqual(mos4.numSubpartPermutations(), 2)

        #mos3 = embeds mos4
        pm_mos3 = PointMeta([DiscreteVarMeta([0,1],'is_pmos')])
        mos3 = CompoundPart([], pm_mos3, 'mos3') 
        mos3.addPart(mos4, {}, {'chosen_part_index':'is_pmos'})
        self.assertEqual(mos3.schemas(),
                         Schemas([Schema({'is_pmos':[0,1]})]))
        self.assertEqual(mos3.numSubpartPermutations(), 2)

        #small_cm = 2 mos3's and 2 choice vars
        pm_small_cm = PointMeta([DiscreteVarMeta([0,1],'is_pmos1'),
                                 DiscreteVarMeta([0,1],'is_pmos2')])
        small_cm = CompoundPart([], pm_small_cm, 'small_cm')
        small_cm.addPart(mos3, {}, {'is_pmos':'is_pmos1'} )
        small_cm.addPart(mos3, {}, {'is_pmos':'is_pmos2'} )
        self.assertEqual(small_cm.schemas(),
                         Schemas([Schema({'is_pmos1':[0,1],'is_pmos2':[0,1]})]))
        self.assertEqual(small_cm.numSubpartPermutations(), 4) # 2*2=4

        #big_cm = 4 mos3's and 3 choice vars (not 4)
        pm_big_cm = PointMeta([DiscreteVarMeta([0,1],'is_pmos2'),
                               DiscreteVarMeta([0,1],'is_pmos3'),
                               DiscreteVarMeta([0,1],'is_pmos4')])
        big_cm = CompoundPart([], pm_big_cm, 'big_cm')
        big_cm.addPart(mos3, {}, {'is_pmos':'is_pmos2'} )
        big_cm.addPart(mos3, {}, {'is_pmos':'is_pmos3'} )
        big_cm.addPart(mos3, {}, {'is_pmos':'1-is_pmos3'} )
        big_cm.addPart(mos3, {}, {'is_pmos':'1-is_pmos4'} )
        s1 = Schema({'is_pmos2':[0,1],'is_pmos3':[0,1],'is_pmos4':[0,1]})
        self.assertEqual(big_cm.schemas(), Schemas([s1]))
        self.assertEqual(big_cm.numSubpartPermutations(), 8) # 2*2*2=8

        #cm = small_cm or big_cm
        #'cm' is the most complicated of all the parts so far.  Some
        # of its variables affect small_cm, and a different subset affects
        # big_cm.  Therefore there are _two_ schemas, each with a different
        # set of variables
        pm_cm = PointMeta([DiscreteVarMeta([0,1],'cm_var1'),
                           DiscreteVarMeta([0,1],'cm_var2'),
                           DiscreteVarMeta([0,1],'cm_var3'),
                           DiscreteVarMeta([0,1],'cm_var4')])
        cm = FlexPart([], pm_cm, 'cm')
        cm.addPartChoice(small_cm, {}, {'is_pmos1':'cm_var1',
                                        'is_pmos2':'cm_var2'})
        cm.addPartChoice(big_cm, {},   {'is_pmos2':'cm_var2',
                                        'is_pmos3':'cm_var3',
                                        'is_pmos4':'cm_var4'})
        self.assertEqual(sorted(cm.point_meta.keys()),
                         sorted(['chosen_part_index','cm_var1','cm_var2',
                                 'cm_var3','cm_var4']))
        s1 = Schema({'chosen_part_index':[0],'cm_var1':[0,1],'cm_var2':[0,1]})
        s2 = Schema({'chosen_part_index':[1],'cm_var2':[0,1],'cm_var3':[0,1],
                     'cm_var4':[0,1]})
        self.assertEqual(cm.schemas(), Schemas([s1,s2]))
        self.assertEqual(cm.numSubpartPermutations(), 12) # 4+8=12
#         print cm.schemas()

#         for emb_part in cm.part_choices:
#             print "schemasWithVarRemap for embedded_part: %s"%emb_part.part.name
#             print cm.schemasWithVarRemap(emb_part)

        #double_cm = two cm's
        #tests if can we handle the merging of two Schemas objects, in which
        # each object has >1 Schema
        pm_double_cm = PointMeta([DiscreteVarMeta([0,1],'chosen_part_index'),
                                  DiscreteVarMeta([0,1],'cm_var2'),
                                  DiscreteVarMeta([0,1],'cm_var3'),
                                  DiscreteVarMeta([0,1],'cm_var4')])
        
        
    def tearDown(self):
        pass

if __name__ == '__main__':
    #if desired, this is where logging would be set up
    
    unittest.main()

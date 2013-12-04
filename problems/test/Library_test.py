import unittest

import random
import string

from adts import *
from adts.Part import replaceAutoNodesWithXXX

from problems.Library import *
from problems.SizesLibrary import *

class LibraryTest(unittest.TestCase):

    def setUp(self):
        self.just1 = False #to make True is a HACK
        self.lib = Point18SizesLibrary()

    def testBuildVarMeta(self):
        if self.just1: return

        vm = self.lib.buildVarMeta('W')
        self.assertTrue( isinstance(vm, VarMeta) )
        self.assertEqual(vm.name, 'W')

    def testBuildPointMeta_list(self):
        if self.just1: return

        pm = self.lib.buildPointMeta(['L','W'])
        self.assertTrue( isinstance(pm, PointMeta) )
        self.assertEqual( sorted(pm.keys()), sorted(['L','W']) )
        self.assertEqual( pm['W'].name, 'W' )

    def testBuildPointMeta_dict(self):
        if self.just1: return

        pm = self.lib.buildPointMeta({'my_L':'L','my_W':'W'})
        self.assertTrue( isinstance(pm, PointMeta) )
        self.assertEqual( sorted(pm.keys()), sorted(['my_L','my_W']) )
        self.assertEqual( pm['my_W'].name, 'my_W' )
        self.assertEqual( type(pm['my_W']), type(self.lib.buildVarMeta('W')) )

    def testUpdatePointMeta(self):
        if self.just1: return

        base_point_meta = self.lib.buildPointMeta(['R'])
        extra_part = self.lib.nmos4()
        varmap = {'W':'my_W','L':'my_L','M':'my_M'}
        pm = self.lib.updatePointMeta(base_point_meta, extra_part, varmap)
        self.assertTrue( isinstance(pm, PointMeta) )
        self.assertEqual(sorted(pm.keys()),
                         sorted(['R','my_W','my_L','my_M']))
        self.assertTrue( isinstance(pm['my_L'], VarMeta ) )        
        

    def test_replaceAfterMWithBlank(self):
        if self.just1: return
        #
        target_str = """M0 1 2 3 nblah N_18_MM M=4 L=1e-06 W=4.47483e-06
"""
        without_str = """M0 1 2 3 nblah N_18_MM 
"""
        self.assertEqual(replaceAfterMWithBlank(target_str), without_str)

        #
        input_str = """M0 Iout n_auto_17 n_auto_16 n_auto_16 P_18_MM M=13 L=1e-06 W=4.85917e-06
V1 n_auto_17 0  DC 0.7
M2 n_auto_16 Vin n_auto_15 n_auto_15 N_18_MM M=11 L=1e-06 W=4.98272e-06
R3 n_auto_15 gnd  R=100
"""
        without_str = """M0 Iout n_auto_17 n_auto_16 n_auto_16 P_18_MM 
V1 n_auto_17 0  DC 0.7
M2 n_auto_16 Vin n_auto_15 n_auto_15 N_18_MM 
R3 n_auto_15 gnd  R=100
"""
        self.assertEqual(replaceAfterMWithBlank(input_str), without_str)


    def test_replaceSummaryStrWithBlank(self):
        input_str = """
blah
blah2

* ==== Summary for: ssViAmp1_VddGndPorts ====
* loadrail is vdd = False
* input is pmos (rather than nmos) = False
* ==== Done summary ====

M0 Iout n_auto_9 n_auto_8 n_auto_8 P_18_MM M=1 L=7.2e-07 W=1.08e-06
V1 n_auto_9 0  DC 0.1
"""
        without_str = """
blah
blah2


M0 Iout n_auto_9 n_auto_8 n_auto_8 P_18_MM M=1 L=7.2e-07 W=1.08e-06
V1 n_auto_9 0  DC 0.1
"""
        self.assertEqual(replaceSummaryStrWithBlank(input_str), without_str)

        self.assertEqual(replaceSummaryStrWithBlank(without_str), without_str)
        
    def tearDown(self):
        pass

if __name__ == '__main__':
    import logging
    logging.basicConfig()
    logging.getLogger('library').setLevel(logging.DEBUG)
    
    unittest.main()

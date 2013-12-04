import unittest

from adts.Point import *

class PointTest(unittest.TestCase):

    def setUp(self):
        pass
        

    def testPointMeta(self):
        pm = PointMeta([ContinuousVarMeta(False, -5, 3.0, 'axx'),
                        ContinuousVarMeta(True, -1, 1,'b'),
                        DiscreteVarMeta([-10,1000,1000.02], 'c') ] )
        self.assertEqual(sorted(pm.keys()), ['axx','b','c'])
        self.assertEqual( pm['b'].name, 'b')

        for i in range(100):
            random_point = pm.createRandomUnscaledPoint()
            self.assertTrue( -5 <= random_point['axx'] < 3.0)
            self.assertTrue( -1 <= random_point['b'] < 1.0)
            self.assertTrue( random_point['c'] in [0,1,2,3] )
            
        self.assertEqual(pm.unityVarMap(), {'axx':'axx','b':'b','c':'c'})

        min_p = pm.minValuesScaledPoint()
        self.assertEqual( min_p['axx'], -5 )
        self.assertEqual( min_p['b'], 10**(-1) )
        self.assertEqual( min_p['c'], -10 )

        unsc_p = Point(False, {'axx':-8,'b':3,'c':22})
        self.assertFalse(unsc_p.is_scaled)
        
        rb_unsc_p = pm.railbin( unsc_p )
        self.assertEqual( rb_unsc_p['axx'], -5)
        self.assertEqual( rb_unsc_p['b'], 1) 
        self.assertEqual( rb_unsc_p['c'], 2)

        self.assertTrue( Point(True, {}).is_scaled )

        sc_p = pm.scale( Point(False, {'axx':-8,'b':3,'c':22}) )
        self.assertTrue(sc_p.is_scaled)
        
        self.assertEqual( sc_p['axx'], -8)
        self.assertEqual( sc_p['b'], 10**3) 
        self.assertEqual( sc_p['c'], 1000.02)
                       
        rb_sc_p = pm.railbin( sc_p )
        self.assertEqual( rb_sc_p['axx'], -5)
        self.assertEqual( rb_sc_p['b'], 10**1) 
        self.assertEqual( rb_sc_p['c'], 1000.02)

        s = pm.spiceNetlistStr(rb_sc_p)
        self.assertTrue('axx' in s)

        pm.addVarMeta( DiscreteVarMeta([80.0,90.0],'newvar') )
        self.assertEqual(sorted(pm.keys()), ['axx','b','c','newvar'])
        p = pm.minValuesScaledPoint()
        self.assertEqual(sorted(p.keys()), ['axx','b','c','newvar'])

    def testEmptyPointMeta(self):
        pm = PointMeta({})
        self.assertEqual(len(pm), 0)
        self.assertEqual(pm.unityVarMap(), {})
        
        for i in range(100):
            random_point = pm.createRandomUnscaledPoint()
            self.assertEquals( len(random_point), 0 )

    def testUniquePointIDs(self):
        p1 = Point(False, {'a':3, 'b':42.2})
        p2 = Point(False, {'a':3, 'b':42.2})
        self.assertEqual( p1['b'], 42.2 )
        self.assertNotEqual( p1.ID, p2.ID )
            
    def tearDown(self):
        pass

if __name__ == '__main__':
    #if desired, this is where logging would be set up
    
    unittest.main()

import unittest

from adts import *

def some_function(x):
    return x+2

def function2(x):
    return x+2

class ProblemSetupTest(unittest.TestCase):

    def setUp(self):
        pass
        
    def testProblemSetup(self):
        an = FunctionAnalysis(some_function, [EnvPoint(True)], 10, 20, False)
        an2 = FunctionAnalysis(function2, [EnvPoint(True)], 10, 20, False)
        dummy_part = WireFactory().build()
        emb_part = EmbeddedPart(dummy_part, dummy_part.unityPortMap(), {})
        ps = ProblemSetup(emb_part, [an, an2])
        self.assertEqual(len(ps.analyses), 2)
        
        fm = ps.flattenedMetrics()
        fm_names = [metric.name for metric in fm]
        self.assertEqual(len(fm), 2)
        self.assertTrue(an.metric.name in fm_names)
        self.assertTrue(an2.metric.name in fm_names)
        
        self.assertRaises(ValueError, ProblemSetup, 'not_emb_part', [an])
        empty_list = []
        self.assertRaises(ValueError, ProblemSetup, emb_part, empty_list)

        self.assertEqual(ps.metric(an2.metric.name).name, an2.metric.name)
        self.assertRaises(ValueError, ps.metric, 'nonexistent_metric_name')

    def tearDown(self):
        pass

if __name__ == '__main__':
    #if desired, this is where logging would be set up
    
    unittest.main()

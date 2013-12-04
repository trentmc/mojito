import unittest

from adts import *

def some_function(x):
    return x+2

class EvalRequestTest(unittest.TestCase):

    def setUp(self):
        pass
        

    def testEvalRequest(self):
        opt_point = 'opt_point_of_an_arbitrary_object'
        rnd_point = RndPoint(True)
        env_point = EnvPoint(True)
        analysis = FunctionAnalysis(some_function, [env_point], 10, 20, False)

        er = EvalRequest(opt_point, rnd_point, analysis, env_point)
        self.assertEqual(opt_point, er.opt_point)
        self.assertEqual(rnd_point, er.rnd_point)
        self.assertEqual(analysis.ID, er.analysis.ID)
        self.assertEqual(env_point, er.env_point)

        self.assertRaises(ValueError, EvalRequest, opt_point, 'not_rnd_point',
                          analysis, env_point)
        self.assertRaises(ValueError, EvalRequest, opt_point, RndPoint(False),
                          analysis, env_point)
        self.assertRaises(ValueError, EvalRequest, opt_point, RndPoint,
                          'not_analyis', env_point)
        self.assertRaises(ValueError, EvalRequest, opt_point, RndPoint,
                          analysis, 'not_env_point')
        self.assertRaises(ValueError, EvalRequest, opt_point, RndPoint,
                          analysis, EnvPoint(False))
        
    def tearDown(self):
        pass

if __name__ == '__main__':
    #if desired, this is where logging would be set up
    
    unittest.main()

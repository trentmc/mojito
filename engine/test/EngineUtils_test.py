import unittest

import random

#FIXME: unit tests for EngineUtils still need to be written!
from adts import *
from util.ascii import *
from engine.EngineUtils import *
from engine.Ind import Ind

def f1(x):
    return x+1

def f2(x):
    return x+2

def twoMetricsPS(thr1, thr2):
    """Makes a PS from two metrics:
    -first metric is maximize past thr1
    -second metric is minimize past thr2
    """

    #to mos3, add dummy function DOC: constraint of get w > l
    an_f1 = FunctionAnalysis(f1, [EnvPoint(True)],
                             thr1, float('+Inf'), True) 
    an_f2 = FunctionAnalysis(f2, [EnvPoint(True)],
                             float('-Inf'), thr2, True) 

    analyses = [an_f1, an_f2]

    #build ps
    dummy_part = WireFactory().build()
    emb_part = EmbeddedPart(dummy_part, dummy_part.unityPortMap(), {})
    ps = ProblemSetup(emb_part, analyses)

    return ps

class DummyGenotype:
    pass


def indsFromResAndPS(res, ps):
    """Construct a list of inds, given results tuples 'res' and problem setup
    'ps'.
    """
    an_f1 = ps.analyses[0]
    e1 = an_f1.env_points[0]
    an_f2 = ps.analyses[1]
    e2 = an_f2.env_points[0]

    inds = []
    for (res1,res2) in res:
        g = DummyGenotype()
        g.unscaled_opt_point = Point(False)
        next_ind = Ind(g, ps)

        next_ind.reportSimRequest(an_f1, e1)
        next_ind.setSimResults({an_f1.metric.name:res1}, an_f1, e1)

        next_ind.reportSimRequest(an_f2, e2)
        next_ind.setSimResults({an_f2.metric.name:res2}, an_f2, e2)

        inds.append( next_ind )
    return inds

class EngineUtilsTest(unittest.TestCase):

    def setUp(self):
        self.just1 = False #to make True is a HACK
        
    def testFastNondominatedSort_empty(self):
        if self.just1: return
        F = fastNondominatedSort([], {'metname':(1,2)})
        self.assertEqual(F,[[]])        
        
    def testFastNondominatedSort_A(self):
        """Test on a synthetic dataset where we have
        -inds on 0th layer: 0,5,6 (feasible)
        -inds on 1st layer: 1,4  (feasible)
        -inds on 2nd layer: 2 (infeasible)
        -inds on 3rd layer: 3 (infeasible)
        """
        if self.just1: return

        res = [(2,1), (2,3), (1,4), (0,5), (3,4), (4,3), (3,2)] #(f1,f2) per ind
        
        ps = twoMetricsPS(1.5, 10.0)

        inds = indsFromResAndPS(res, ps)

        an_f1 = ps.analyses[0]
        an_f2 = ps.analyses[1]
        minmax_metrics = {an_f1.metric.name:(0,4), an_f2.metric.name:(1,5)}

        #test ind.isFeasible()
        self.assertTrue(inds[0].isFeasible())
        self.assertTrue(inds[1].isFeasible())
        self.assertFalse(inds[2].isFeasible())
        self.assertFalse(inds[3].isFeasible())
        self.assertTrue(inds[4].isFeasible())
        self.assertTrue(inds[5].isFeasible())
        self.assertTrue(inds[6].isFeasible())

        #test ind.constrainedDominates()
        self.assertTrue(inds[0].constrainedDominates(inds[1], minmax_metrics))
        self.assertTrue(inds[0].constrainedDominates(inds[2], minmax_metrics))
        self.assertTrue(inds[0].constrainedDominates(inds[3], minmax_metrics))
        self.assertFalse(inds[0].constrainedDominates(inds[4], minmax_metrics))
        self.assertFalse(inds[0].constrainedDominates(inds[5], minmax_metrics))
        self.assertFalse(inds[0].constrainedDominates(inds[6], minmax_metrics))

        for i in [0,1,4,5,6]:
            self.assertEqual(inds[i].constraintViolation(minmax_metrics), 0.0)
        self.assertTrue(inds[3].constraintViolation(minmax_metrics) > \
                        inds[2].constraintViolation(minmax_metrics) > 0)
                                 
        #test fastNondominatedSort()
        F = fastNondominatedSort(inds, minmax_metrics)
        self.assertEqual(len(F), 4) #4 nondominated layers
        F0_IDs = sorted([ind.ID for ind in F[0]])
        F1_IDs = sorted([ind.ID for ind in F[1]])
        F2_IDs = sorted([ind.ID for ind in F[2]])
        F3_IDs = sorted([ind.ID for ind in F[3]])
        self.assertEqual(F0_IDs, sorted([inds[0].ID, inds[6].ID, inds[5].ID]))
        self.assertEqual(F1_IDs, sorted([inds[1].ID, inds[4].ID]))
        self.assertEqual(F2_IDs, [inds[2].ID])
        self.assertEqual(F3_IDs, [inds[3].ID])
            
    def testFastNondominatedSort_B(self):
        """Tests results of gain and power that caused trouble with Pieter
        -inds on 0th layer: 0,1,4,7,8,9 (feasible)
        -inds on 1st layer: 3,5 (feasible)
        -inds on 2nd layer: 2,6
        """
        if self.just1: return

        #(maximize, minimize)
        gains = [11.293,  32.721,  10.800,  10.655,  11.625,  32.622,  10.501,
                 36.768,  10.075,  10.312]
        powers = [0.00075530,  0.00089390,  0.00164000,  0.00075530,  0.00089030,
                  0.00091880,  0.00075530,  0.00091890,  0.00042520,  0.00075520]
        res = [(gain, power) for gain,power in zip(gains,powers)]

        #gain threshold is 10.0, prnode threshold is 100e-3
        ps = twoMetricsPS(10, 100e-3)

        inds = indsFromResAndPS(res, ps)

        an_f1 = ps.analyses[0]
        an_f2 = ps.analyses[1]
        minmax_metrics = {an_f1.metric.name:(min(gains),max(gains)),
                          an_f2.metric.name:(min(powers),max(powers))}

        #all inds should be feasible
        for ind in inds:
            self.assertTrue(ind.isFeasible())
                                 
        #test fastNondominatedSort()
        F = fastNondominatedSort(inds, minmax_metrics)
        self.assertEqual(len(F), 3) #3 nondominated layers
        F0_IDs = sorted([ind.ID for ind in F[0]])
        F1_IDs = sorted([ind.ID for ind in F[1]])
        F2_IDs = sorted([ind.ID for ind in F[2]])
        self.assertEqual(F0_IDs, sorted([ inds[0].ID, inds[1].ID, inds[4].ID,
                                          inds[7].ID, inds[8].ID, inds[9].ID]))
        self.assertEqual(F1_IDs, sorted([inds[3].ID, inds[5].ID]))
        self.assertEqual(F2_IDs, sorted([inds[2].ID, inds[6].ID]))
        
    def testMergeNondominatedSort(self):
        if self.just1: return

        N = 50

        gains = [random.random() for i in range(N)]
        powers = [random.random() for i in range(N)]
        res = [(gain, power) for gain,power in zip(gains,powers)]

        ps = twoMetricsPS(0.25, 0.75)

        inds = indsFromResAndPS(res, ps)

        an_f1 = ps.analyses[0]
        an_f2 = ps.analyses[1]
        minmax_metrics = {an_f1.metric.name:(min(gains),max(gains)),
                          an_f2.metric.name:(min(powers),max(powers))}

        #validate that the same results come out of both approaches
        Fa = fastNondominatedSort(inds, minmax_metrics)
        Fb = Deb_fastNondominatedSort(inds, minmax_metrics)
        for Fa_layer, Fb_layer in zip(Fa, Fb):
            self.assertEqual(sorted([ind.ID for ind in Fa_layer]),
                             sorted([ind.ID for ind in Fb_layer]))
            
    def testUniqueIndsByPerformance(self):
        if self.just1: return
        pass
        
    def tearDown(self):
        pass

if __name__ == '__main__':

    import logging
    logging.basicConfig()
    logging.getLogger('synth').setLevel(logging.DEBUG)
    
    unittest.main()

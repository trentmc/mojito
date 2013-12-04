import unittest

from adts import *
from util.constants import BAD_METRIC_VALUE
from engine.Ind import *


def some_function(x):
    return x+2

def function2(x):
    return x-5

class IndTest(unittest.TestCase):

    def setUp(self):
        an = FunctionAnalysis(some_function, [EnvPoint(True)], 10, 20, False)
        an2 = FunctionAnalysis(function2, [EnvPoint(True)], 10, 20, False)
        dummy_part = WireFactory().build()
        emb_part = EmbeddedPart(dummy_part, dummy_part.unityPortMap(), {})
        self.ps = ProblemSetup(emb_part, [an, an2])
        self.genotype = 'dummy genotype'

    def test1(self):
        an = self.ps.analyses[0]
        an2 = self.ps.analyses[1]
        
        ind = Ind(self.genotype, self.ps)

        #check out basic attributes
        self.assertEqual(ind.genotype, self.genotype)
        self.assertEqual(sorted(ind.sim_requests_made.keys()),
                         sorted([an.ID, an2.ID]))

        metric_names = [metric.name for metric in self.ps.flattenedMetrics()]
        self.assertEqual(sorted(ind.sim_results.keys()),
                         sorted(metric_names))
        self.assertTrue(len(str(ind)) > 0)

        e = an2.env_points[0]

        #try setting a sim result (and see that error)
        self.assertRaises(ValueError, ind.setSimResults,{an2.metric.name:33.2},
                          an2, e)

        #ok, set a sim result _properly_
        self.assertFalse(ind.simRequestMade(an2, e))
        ind.reportSimRequest(an2, e)
        self.assertTrue(ind.simRequestMade(an2, e))

        self.assertEqual(ind.sim_results[an2.metric.name][e.ID], None)
        ind.setSimResults({an2.metric.name:33.2}, an2, e)
        self.assertEqual(ind.sim_results[an2.metric.name][e.ID], 33.2)

        #see that we can't report a request twice, or set a sim result twice
        self.assertRaises(ValueError, ind.reportSimRequest, an2, e)
        self.assertRaises(ValueError, ind.setSimResults,{an2.metric.name:10.5},
                          an2, e)

        #fully evaluated yet? (no)
        self.assertFalse(ind.fullyEvaluated())

        #retrieve a worst-case value; see that caching didn't happen
        self.assertEqual(ind.worstCaseMetricValue(an2.metric.name), 33.2)
        self.assertFalse(ind._cached_wc_metvals.has_key(an2.metric.name))

        #set enough sim results to be fully evaluated, and re-test
        ind.reportSimRequest(an, an.env_points[0])
        ind.setSimResults({an.metric.name:10.0}, an, an.env_points[0])
        self.assertTrue(ind.fullyEvaluated())

        #retrieve a worst-case value; see that caching did happen
        self.assertEqual(ind.worstCaseMetricValue(an2.metric.name), 33.2)
        self.assertTrue(ind._cached_wc_metvals.has_key(an2.metric.name))
        self.assertEqual(ind._cached_wc_metvals[an2.metric.name], 33.2)

    def testIsBad(self):        
        an = self.ps.analyses[0]
        an2 = self.ps.analyses[1]

        #fresh new inds are never bad
        ind = Ind(self.genotype, self.ps)
        self.assertFalse(ind.isBad())

        #set a non-bad metric value; ind should remain non-bad
        ind.reportSimRequest(an2, an2.env_points[0])
        ind.setSimResults({an2.metric.name:33.2}, an2, an2.env_points[0])
        self.assertFalse(ind.isBad())

        #set a bad metric value, making ind bad
        ind.reportSimRequest(an, an.env_points[0])
        ind.setSimResults({an.metric.name:BAD_METRIC_VALUE}, an,an.env_points[0])
        self.assertTrue(ind.isBad())
        self.assertEqual(ind.worstCaseMetricValue(an.metric.name),
                         BAD_METRIC_VALUE)
        self.assertEqual(ind.constraintViolation({}), float('Inf'))
        self.assertFalse(ind.isFeasible())

        #can it go into a string?
        self.assertTrue(len(str(ind)) > 0)

    def testForceBad(self):
        ind = Ind(self.genotype, self.ps)
        ind.forceFullyBad()
        self.assertTrue(ind.isBad())
        self.assertTrue(ind.fullyEvaluated())
        
        
    def tearDown(self):
        pass

if __name__ == '__main__':
    #if desired, this is where logging would be set up
    
    unittest.main()

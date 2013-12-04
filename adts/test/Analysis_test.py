import unittest

import os

import numpy

from adts import *
from adts.Analysis import WaveformsToNmse

def some_function(x):
    return x+3

def buildSimulatorStub(metrics_per_outfile):
    lis_measures = ['region','vgs']
    return Simulator(metrics_per_outfile, '/',0,0,0,0,lis_measures)

class AnalysisTest(unittest.TestCase):

    def setUp(self):
        pass
        
    def testFunctionAnalysis(self):
        an = FunctionAnalysis(some_function, [EnvPoint(True)], 10, 20, False)
        self.assertEqual(len(an.env_points), 1)
        self.assertEqual(an.function, some_function)
        self.assertEqual(len(an.metrics), 1)
        self.assertTrue(isinstance(an.metric, Metric))
        self.assertEqual(an.metric.name, 'metric_some_function')
        self.assertEqual(an.metric.min_threshold, 10)
        self.assertEqual(an.metric.max_threshold, 20)
        self.assertEqual(an.metric.improve_past_feasible, False)
        self.assertTrue(len(str(an)) > 0)

        self.assertRaises(ValueError, FunctionAnalysis, some_function,
                          [EnvPoint(False)], 10, 20, False)
        
        an2 = FunctionAnalysis(some_function, [EnvPoint(True)], 10, 20, False)
        self.assertNotEqual(an.ID, an2.ID)

    def testCircuitAnalysis(self):
        #These tests are configured for metric: percent DOCs met.  If it
        # changes, then change these tests as well, if needed.
        self.assertEqual(DOCs_metric_name, 'perc_DOCs_met')
        
        #build up metrics
        metrics = [Metric('gain', 10, float('Inf'), False),
                   Metric('pwrnode', 10, 20, False),
                   Metric(DOCs_metric_name, 0.9999, 1.001, False)]

        #test building up the simulator
        # -typical use
        d = {'ma0':['gain'], 'ic0':['pwrnode'], 'lis':[DOCs_metric_name]}
        sim = buildSimulatorStub(d)
        self.assertEqual(sim.metrics_per_outfile, d)
        self.assertEqual(sorted(sim.metricNames()),
                         sorted(['gain','pwrnode',DOCs_metric_name]))

        # -complain if the dict's values are not in lists
        self.assertRaises(ValueError, buildSimulatorStub,
                          {'ma0':'gain', 'ic0':'pwrnode',
                           'lis':DOCs_metric_name})
        
        # -only allow lis to have one metric DOCs_metric_name
        self.assertRaises(ValueError, buildSimulatorStub,
                          {'lis':['blah']})

        # -allow DOCs_metric_name to only come from 'lis'
        self.assertRaises(ValueError, buildSimulatorStub,
                          {'ma0':[DOCs_metric_name]})

        #test building up the analysis
        an = CircuitAnalysis([EnvPoint(True)], metrics, sim)
        self.assertEqual(len(an.env_points), 1)
        self.assertEqual(len(an.metrics), 3)

        an2 = CircuitAnalysis([EnvPoint(True)], metrics, sim) 
        self.assertNotEqual(an.ID, an2.ID)

        # -complain if dict's keys are not in the set of allowed keys
        self.assertRaises(ValueError, buildSimulatorStub, {'bad_value':'gain'})

        # -need env_point objects
        self.assertRaises(ValueError, CircuitAnalysis, ['not_env_point'],
                          metrics, sim)

        # -need env_point to be scaled
        self.assertRaises(ValueError, CircuitAnalysis, [EnvPoint(False)],
                          metrics, sim)

        # -need metric objects
        self.assertRaises(ValueError, CircuitAnalysis, [EnvPoint(True)],
                          ['not_a_metric'], sim)
        
        #add to this when we support circuit analyses more fully

    def testExtractLisResults(self):
        #build an analysis
        d = {'ma0':['gain'], 'lis':[DOCs_metric_name]}
        sim = buildSimulatorStub(d)

        #test
        # FIXME: the following directory setup is a make-it-work hack
        pwd = os.getenv('PWD')
        if pwd[-1] != '/':
            pwd += '/'
        if 'adts/test/' not in pwd:
            pwd += 'adts/test/'
        lis_file = os.path.abspath(pwd + 'test_lisfile.lis')
        success, lis_results = sim._extractLisResults(lis_file)
        self.assertTrue(success)
        self.assertEqual(lis_results,
                         {'lis__m0__region': 0, 'lis__m14__region': 0, 'lis__m13__region': 1, 'lis__m10__region': 0, 'lis__m6__vgs': -1.5269999999999999, 'lis__m8__vgs': 12.050000000000001, 'lis__m2__region': 1, 'lis__m2__vgs': 0.40579999999999999, 'lis__m4__vgs': -2.4329999999999998, 'lis__m6__region': 1, 'lis__m4__region': 0, 'lis__m0__vgs': -1.5840000000000001, 'lis__m13__vgs': 1.3740000000000001, 'lis__m8__region': 0, 'lis__m14__vgs': 1.3740000000000001, 'lis__m10__vgs': -2.4329999999999998})

        #test bad -- missing a whole 'models' section
        bad_file = os.path.abspath(pwd + 'test_lisfile_bad.lis')
        success, lis_results = sim._extractLisResults(bad_file)
        self.assertFalse(success)
        
        #test bad2 -- device names don't line up with targeted measures
        bad_file = os.path.abspath(pwd + 'test_lisfile_bad2.lis')
        success, lis_results = sim._extractLisResults(bad_file)
        self.assertFalse(success)

    def testWaveformsToNmse(self):
        
        waveforms_array = numpy.array([[1.0, 1.0, 1.0, 1.0, 1.0],
                                         [0.2, 0.4, 0.4, 0.5, 0.1]])
        nmse_calc = WaveformsToNmse(     [0.2, 0.3, 0.4, 0.5, 0.2], 1)
        wrange = 0.5 - 0.2
        expected_nmse = (0.1/wrange)**2 + (0.1/wrange)**2
        self.assertAlmostEqual(nmse_calc(waveforms_array), expected_nmse, 5)

    def tearDown(self):
        pass

if __name__ == '__main__':

    import logging
    logging.basicConfig()
    logging.getLogger('analysis').setLevel(logging.DEBUG)

    
    unittest.main()

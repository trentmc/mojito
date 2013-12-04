import unittest

import os
import shutil

from adts import *
from problems import ProblemFactory
from engine.SynthEngine import *
from engine.SynthEngine import NsgaInd
from engine.Ind import Ind

class SynthEngineTest(unittest.TestCase):

    def setUp(self):
        self.just1 = False #to make True is a HACK
        
    def testNsgaInd(self):
        if self.just1: return
        
        ps = ProblemFactory().build(1)
        genotype = 'dummy genotype'
        ind = NsgaInd(genotype, ps)

    def testProblem2(self):
        if self.just1: return
        
        problem_number = 2
        
        ps = ProblemFactory().build(problem_number)
        pop_size = 3
        ss = SynthSolutionStrategy(pop_size)
        ss.max_num_inds = 10
        ss.max_num_neutral_vary_tries = 4
        ss.do_plot = False #to make True is a HACK

        #possible cleanup from prev run
        if os.path.exists('test_outpath'):
            shutil.rmtree('test_outpath')

        #main call
        engine = SynthEngine(ps, ss, 'test_outpath', None, None)
        engine.run()
        self.assertTrue(os.path.exists('test_outpath'))
        state = loadSynthState('test_outpath/state_gen0001.db', ps)
        self.assertTrue(len(state.allInds()) == pop_size*2)
        self.assertTrue(len(state.R_per_age_layer) == 1)

        #on one problem, see if we can recover from a previous state
        if problem_number == 2:
            ss.max_num_inds = 5
            
            #possible cleanup from prev run
            if os.path.exists('test_outpath2'):
                shutil.rmtree('test_outpath2')
            
            # -recover onto a different output directory
            engine = SynthEngine(ps, ss, 'test_outpath2', None,
                                 'test_outpath/state_gen0001.db')
            engine.run()

            # -recover on an already-existing output directory
            engine = SynthEngine( ps, ss, 'test_outpath', None,
                                  'test_outpath/state_gen0001.db')
            engine.run()
            # -see that it will have deleted all prior files in that
            #  directory
            #we'd need to start from gen0002 or higher in order to
            # ensure that gen0001 is missing, but that will make the
            # unit test runtime too long.  So turn off this test for now.
            #self.assertFalse(os.path.exists('test_outpath/state_gen0001.db'))
            

            #cleanup
            shutil.rmtree('test_outpath2')

        #cleanup
        shutil.rmtree('test_outpath')
        
    def tearDown(self):
        pass

if __name__ == '__main__':

    import logging
    logging.basicConfig()
    logging.getLogger('synth').setLevel(logging.DEBUG)
    
    unittest.main()

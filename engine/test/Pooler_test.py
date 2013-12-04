import unittest

import os
import shutil

from adts import *
from problems import ProblemFactory
from engine.SynthEngine import *
from engine.SynthEngine import NsgaInd
from engine.Ind import Ind
from engine.Pooler import Pooler, PoolerStrategy

class PoolerTest(unittest.TestCase):

    def setUp(self):
        self.just1 = False #to make True is a HACK

    def test1(self):
        if self.just1: return   
        ps = ProblemFactory().build(2)
        ss = PoolerStrategy(0.5, 10, False)
        pooler = Pooler(ps, ss, '.', 'blah_db.db')
        
    def tearDown(self):
        pass

if __name__ == '__main__':

    import logging
    logging.basicConfig()
    logging.getLogger('synth').setLevel(logging.INFO)
    
    unittest.main()

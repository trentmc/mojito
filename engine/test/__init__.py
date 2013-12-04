import unittest, os
from tests import doctest, importSuite

from Ind_test import IndTest
from Pooler_test import PoolerTest
from SynthEngine_test import SynthEngineTest
from EngineUtils_test import EngineUtilsTest

TestClasses = [IndTest,
               PoolerTest,
               SynthEngineTest,
               EngineUtilsTest,
               ]

def unittest_suite():
    return unittest.TestSuite(
      [unittest.makeSuite(t,'test') for t in TestClasses]
    )    

def doctest_suite():
    return doctest.DocFileSuite(
        package='engine',
        )

allSuites = [
    'engine.test.unittest_suite',
    'engine.test.doctest_suite',
]

def test_suite():
    return importSuite(allSuites, globals())

if __name__=="__main__":
    import logging
    logging.basicConfig()
    logging.getLogger('synth').setLevel(logging.ERROR)
    
    unittest.main(defaultTest='test_suite')

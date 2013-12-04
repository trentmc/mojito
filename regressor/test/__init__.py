import unittest, os
from tests import doctest, importSuite

from Lut_test import LutTest

TestClasses = [LutTest,
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
    logging.getLogger('lut').setLevel(logging.ERROR)
    
    unittest.main(defaultTest='test_suite')

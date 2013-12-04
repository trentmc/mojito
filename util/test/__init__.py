import unittest, os
from tests import doctest, importSuite

from Constants_test import ConstantsTest
from Mathutil_test import MathutilTest

TestClasses = [
    ConstantsTest,
    MathutilTest,
    ]

def unittest_suite():
    return unittest.TestSuite(
      [unittest.makeSuite(t,'test') for t in TestClasses]
    )    

def doctest_suite():
    return doctest.DocFileSuite(
        package='util',
        )

allSuites = [
    'util.test.unittest_suite',
    'util.test.doctest_suite',
]

def test_suite():
    return importSuite(allSuites, globals())

if __name__=="__main__":
    unittest.main(defaultTest='test_suite')

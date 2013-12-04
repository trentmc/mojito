import unittest, os
from tests import doctest, importSuite

from Analysis_test import AnalysisTest
from EvalRequest_test import EvalRequestTest
from Metric_test import MetricTest
from Part_test import PartTest
from Point_test import PointTest
from ProblemSetup_test import ProblemSetupTest
from Schema_test import SchemaTest
from Var_test import VarTest

TestClasses = [ \
    AnalysisTest,
    EvalRequestTest,
    MetricTest,
    PartTest,
    PointTest,
    ProblemSetupTest,
    SchemaTest,
    VarTest,
    ]

def unittest_suite():
    return unittest.TestSuite(
      [unittest.makeSuite(t,'test') for t in TestClasses]
    )    

def doctest_suite():
    return doctest.DocFileSuite(
        package='adts',
        )

allSuites = [
    'adts.test.unittest_suite',
    'adts.test.doctest_suite',
]

def test_suite():
    return importSuite(allSuites, globals())

if __name__=="__main__":
    unittest.main(defaultTest='test_suite')

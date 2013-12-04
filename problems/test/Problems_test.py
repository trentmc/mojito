import unittest

from adts import *
from problems.Problems import *

class ProblemsTest(unittest.TestCase):

    def setUp(self):
        pass
        

    def testInstantiateEachProblem(self):
        factory = ProblemFactory()
        for problem_choice in [1,2,31,32]:
            factory.build(problem_choice)
        
    def tearDown(self):
        pass

if __name__ == '__main__':
    #if desired, this is where logging would be set up
    
    unittest.main()

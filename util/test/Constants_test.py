import unittest
        
from util.constants import *

class ConstantsTest(unittest.TestCase):

    def testIncomputable(self):
        a = Incomputable()
        self.assertRaises(ValueError, a.__cmp__, 2)
        self.assertRaises(ValueError, a.__eq__, 2)

        b = Incomputable()
        self.assertRaises(ValueError, a.__cmp__, b)
        self.assertRaises(ValueError, a.__eq__, b)

        c = 2
        self.assertRaises(TypeError, c.__cmp__, a)

        self.assertTrue(str(a) > 0)
        
              
    def testOnlyEqualityComparable(self):
        a = OnlyEqualityComparable()
        self.assertRaises(ValueError, a.__cmp__, 2)
        self.assertFalse(a == 2)

        b = OnlyEqualityComparable()
        self.assertTrue(a == b)
        self.assertFalse(a != b)

        c = 2
        self.assertRaises(TypeError, c.__cmp__, a)

        self.assertTrue(str(a) > 0)

    def testBadMetricValue(self):
        a = BAD_METRIC_VALUE
        self.assertEqual(str(BAD_METRIC_VALUE), 'BAD_METRIC_VALUE')
        self.assertRaises(ValueError, a.__cmp__, 2)
        self.assertFalse(a == 2)
        
        b = BAD_METRIC_VALUE
        self.assertTrue(a == b)
        self.assertFalse(a != b)
                      

if __name__ == '__main__':
    unittest.main()

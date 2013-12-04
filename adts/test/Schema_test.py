import unittest

from adts import *

class SchemaTest(unittest.TestCase):

    def setUp(self):
        self.just1 = False #to make True is a HACK

    def testCheckConsistency(self):
        if self.just1: return

        #the following should _not_ raise a ValueError
        Schema({'a': [0, 1], 'b': [0]}).checkConsistency()
        Schema({'a': [0, 3, 2], 'b': [0]}).checkConsistency()
        Schemas([Schema({'a': [0, 3, 2], 'b': [0]})]).checkConsistency()
        Schemas([Schema({'a': [0, 3, 2], 'b': [0]}),
                 Schema({'c': [0,1]})]).checkConsistency()

        #the following _should_ raise a ValueError
        self.assertRaises( ValueError,
                           Schema, {'a': [0, 1, 1], 'b': [0]})

    def testStr(self):
        if self.just1: return
        s = str(Schema({'foo': [0, 12], 'bar': [0]}))
        self.assertTrue( 'foo' in s )
        self.assertTrue( '12' in s )
        self.assertTrue( 'bar' in s )

        
    def testOverlap(self):
        return #we don't do this yet
        if self.just1: return

        #shouldn't be able to build the following, because
        # some schemas overlap with others (e.g. a=1,b=0)
        self.assertRaises(ValueError, Schemas, [ \
            Schema({'a': [0, 1], 'b': [0]}),
            Schema({'a': [1], 'c': [0, 1]}),
            ])
        
        self.assertRaises(ValueError, Schemas, [ \
            Schema({'a': [0, 1], 'b': [0]}),
            Schema({'a': [1], 'c': [0, 1]}),
            Schema({'b': [0], 'c': [0, 1]}),
            ])

        #also test when using append
        schemas = Schemas()
        schemas.append({'a': [0, 1], 'b': [0]})
        self.assertRaises(ValueError, schemas.append, {'a': [1], 'c': [0, 1]})

        
    def testMerge1(self):
        if self.just1: return

        #4 schemas, each occupying a corner of the a=(0,1) and b=(0,1) square
        # can merge into one schema that covers the whole square
        schemas = Schemas([ \
                Schema({'a': [0], 'b': [0]}),
                Schema({'a': [0], 'b': [1]}),
                Schema({'a': [1], 'b': [0]}),
                Schema({'a': [1], 'b': [1]}),
                ])
        target = Schemas([ \
                Schema({'a': [0,1], 'b': [0,1]}),            
                ])
        schemas.merge()
        self.assertEqual( schemas, target )
        
    def testMerge2(self):
        if self.just1: return

        #-the first 2 schemas are identical except for 'a', so that merges.
        #-the last schema should remain independent because it has different
        # variables
        schemas = Schemas([ \
                Schema({'a': [0], 'b': [0], 'c': [0, 1], 'd': [0, 1]}),
                Schema({'a': [1], 'b': [0], 'c': [0, 1], 'd': [0, 1]}),
                Schema({'a': [2], 'blah':[1]}),
                ])

        target = Schemas([ \
                Schema({'a': [0,1], 'b': [0], 'c': [0, 1], 'd': [0, 1]}),
                Schema({'a': [2], 'blah':[1]}),
                ])
        schemas.merge()
        self.assertEqual( schemas, target )
        
    def testMerge3(self):
        if self.just1: return

        #ensure that we don't get {'a': [0], 'b': [0,1,1]}
        schemas = Schemas([ \
                Schema({'a': [0], 'b': [0]}),
                Schema({'a': [0], 'b': [1]}),
                Schema({'a': [0], 'b': [1]}),
                ])
        target = Schemas([ \
                Schema({'a': [0], 'b': [0,1]}),            
                ])
        schemas.merge()
        self.assertEqual( schemas, target )
        
    def testMerge4(self):
        if self.just1: return

        #the second schema is a subset of the first
        schemas = Schemas([ \
                Schema({'a': [0], 'b': [0,1]}),
                Schema({'a': [0], 'b': [1]}),
                ])
        target = Schemas([ \
                Schema({'a': [0], 'b': [0,1]}),            
                ])
        schemas.merge()
        self.assertEqual( schemas, target )

    def testNumPermutations(self):
        if self.just1: return

        #simplest possible: 1 schema, 1 variable and 1 choice for that variable
        self.assertEqual(Schemas([Schema({'a':[0]})]).numPermutations(), 1)

        #1 schema, 1 variable and 3 choices for that variable
        self.assertEqual(Schemas([Schema({'a':[0,1,5]})]).numPermutations(), 3)

        #1 schema, 2 variables, but only 1 variable varies
        s1 = Schema({'a':[0],'b':[0,1,2]})
        self.assertEqual(Schemas([s1]).numPermutations(), 3)

        #1 schema, 2 variables where both vary, so effect is multiplicative
        s2 = Schema({'a':[1,2],'b':[3,4,5]})
        self.assertEqual(Schemas([s2]).numPermutations(), 2*3)

        #2 schemas that are wholly independent; add each contribution
        self.assertEqual(Schemas([s1, s2]).numPermutations(), 3 + 2*3)

        #2 schemas, but s3 is a subset of s1 so it has no effect
        s3 = Schema({'a':[0],'b':[0]})
        ss = Schemas([s1, s3])
        ss.merge()
        self.assertEqual(ss.numPermutations(), 3)

        #schemas with different variable groups
        s4 = Schema({'a':[0],'c':[0,1,2,3]}) 
        self.assertEqual(Schemas([s1,s4]).numPermutations(), 3+4)
        
        
    def tearDown(self):
        pass

if __name__ == '__main__':
    #if desired, this is where logging would be set up
    
    unittest.main()

import unittest

from adts import *


class EvalUtilsTest(unittest.TestCase):

    def setUp(self):
        self.just1 = False #to make True is a HACK
        
    def testGetSpiceData1Var(self):
        if self.just1: return
        
        X = getSpiceData("onevar.sw0", 11, 4, 1)
        self.assertEqual(X.shape, (1,9))
        self.assertEqual(X[0][0], 0.89981)
        self.assertEqual(X[0][5], 0.92107)
        
    def testGetSpiceData2Vars(self):
        if self.just1: return
        
        X = getSpiceData("twovar.sw0", 11, 5, 2)
        self.assertEqual(X.shape, (2,9))
        self.assertEqual(X[0][0], 0.57766)
        self.assertEqual(X[0][5], 0.2593)
        self.assertEqual(X[1][0], 0.0)
        self.assertEqual(X[1][5], 1.0)

    def testRemoveWhitespace(self):
        if self.just1: return

        self.assertEqual(removeWhitespace(""), "")
        self.assertEqual(removeWhitespace("   "), "")
        self.assertEqual(removeWhitespace("   aa"), "aa")
        self.assertEqual(removeWhitespace("aa  "), "aa")
        self.assertEqual(removeWhitespace("aa"), "aa")
        self.assertEqual(removeWhitespace("hello there"), "hellothere" )
        self.assertEqual(removeWhitespace(" hi   a bcd aa 09876~$ $   "),
                         "hiabcdaa09876~$$")

    def testFile2tokens(self):
        if self.just1: return

        self.assertEqual(file2tokens('simple_file.txt'),
                         ['this', 'is', 'a', 'test', 'file.',
                          'hello', 'world.',
                          'this', 'is', 'line', '3.',
                          'this', 'is', '=', 'line', '4.',
                          'this', 'is', 'the', 'end', 'line.'])
        self.assertEqual(file2tokens('simple_file.txt',  3),
                         ['this', 'is', 'line', '3.',
                          'this', 'is',  '=', 'line','4.',
                          'this', 'is', 'the', 'end', 'line.'])
        self.assertEqual(file2tokens('simple_file.txt',  30), [])
        
    def testString2tokens(self):
        if self.just1: return

        self.assertEqual(string2tokens("x=2, y==3, z = 4"),
                         ['x', '=', '2,', 'y', '==', '3,', 'z', '=', '4'])

    def testWhitespaceAroundEquality(self):
        if self.just1: return

        self.assertEqual(whitespaceAroundEquality(""), "")
        self.assertEqual(whitespaceAroundEquality(" hello there aa "),
                         " hello there aa ")
        
        self.assertEqual(whitespaceAroundEquality("x=2"), "x = 2")
        self.assertEqual(whitespaceAroundEquality("x==2"), "x == 2")
        self.assertEqual(whitespaceAroundEquality("x=2, y==3, z=4"),
                         "x = 2, y == 3, z = 4")

    def testSubfile2strings(self):
        if self.just1: return

        self.assertEqual(subfile2strings("simple_file.txt","foo","bar"),[])
        self.assertEqual(subfile2strings("simple_file.txt","end","bar"), [])
        self.assertEqual(subfile2strings("simple_file.txt","this","world"),
                         ["\n"])
        self.assertEqual(subfile2strings("simple_file.txt","world","end"),
                         ["this is line 3.\n", "this is=line 4.\n", "\n"])


    def testFile2str(self):
        if self.just1: return
        
    def tearDown(self):
        pass

if __name__ == '__main__':
    #if desired, this is where logging would be set up
    
    unittest.main()

import unittest

import numpy
import time

from adts import *
from regressor.Lut import *

# specify the maximum error a regressor can have
regressor_max_error=0.5

class LutTest(unittest.TestCase):

    def setUp(self):
        self.just1 = False #to make True is a HACK
        pass

    def test1d(self):
        if self.just1: return
        #create training data
        X = numpy.zeros((1,50))
        y = numpy.zeros(50)
        for i in range(50):
            x = i * 0.1
            X[0,i] = x
            y[i] = math.sin(x)

        #build the model
        lut_ss = LutStrategy()
        lut_model = LutFactory().build(X, y, lut_ss)

        #test the model
        X2 = X 
        yhat = lut_model.simulate(X2)

        # the borders of the interpolation are not really good
        for yi, yhati in zip(y[1:-1], yhat[1:-1]):
            self.assertTrue( abs(yi - yhati)/((yi + yhati + 1e-20)/2) < regressor_max_error, (yi,yhati))
            
    def test2d(self):
        if self.just1: return
        #create training data
        gridsize = 10
        X = numpy.zeros((2,gridsize**2))
        y = numpy.zeros(gridsize**2)
        sample_k = 0
        
        for i in range(gridsize):
            x_i = i * 0.1
            for j in range(gridsize):
                x_j = j * 0.1
                X[0,sample_k] = x_i
                X[1,sample_k] = x_j
                y[sample_k] = math.sin(x_i + x_j)
                sample_k=sample_k+1

        #build the model
        lut_ss = LutStrategy()
        lut_model = LutFactory().build(X, y, lut_ss)

        #test the model
        X2 = X
        yhat = lut_model.simulate(X2)
        
        for yi, yhati,x20,x21 in zip(y, yhat,X2[0],X2[1]):
            # ignore the corners
            if not ((x20 <= 0.1) or (x20 >= 4.9) or (x21 <= 0.1) or (x21 >= 4.9)):
                self.assertTrue( abs(yi - yhati)/((yi + yhati + 1e-20)/2) < regressor_max_error, (yi,yhati,x20,x21))
    
    def testSpeed3D(self):
        if self.just1: return
        self._testSpeednD(50, 5)
        
    def _testSpeednD(self,nr_points, dim):
        points = 100*numpy.random(dim, nr_points)
        vals = 100*numpy.random(nr_points)
        
        #build the model
        lut_ss = LutStrategy()
        lut_model = LutFactory().build(points, vals, lut_ss)       
        
        # test the model    
        target_points = points + 0.1
        cnt=0
        
        starttime=time.time()
        
        while cnt < 2:
            yhat = lut_model.simulate(target_points)           
            cnt=cnt+1
        
        elapsed=time.time()-starttime
        
        nb_lookups=nr_points * cnt
        
        lookups_per_sec=nb_lookups / elapsed
        
        print "%d simulations (%d-D) of %d points took %f seconds (%d lookups/sec)" % ( cnt, dim , nr_points, elapsed, lookups_per_sec)
        
    def testSingleCluster(self):
        if self.just1: return
        
        xvalues=numpy.array([[1,3,4,2,5,7,6]],'f')
        yvalues=numpy.array([2,8,16,4,32,128,64],'f')
        
        tst=LutCluster(None, xvalues,yvalues)
        self.assertEqual(tst.simulate([0.5]),1.0)
        self.assertEqual(tst.simulate([1.0]),2.0)
        self.assertEqual(tst.simulate([1.5]),3.0)
        self.assertEqual(tst.simulate([2.0]),4.0)
        self.assertEqual(tst.simulate([2.5]),6.0)
        self.assertEqual(tst.simulate([3.0]),8.0)
        self.assertEqual(tst.simulate([7.0]),128.0)
        self.assertEqual(tst.simulate([8.0]),192.0)

    def testTwoClusters(self):
        if self.just1: return
        
        xvalues=numpy.array([[1,1,4,4,2,2],[5,6,5,6,5,6]],'f')
        yvalues=numpy.array([15,16,45,46,25,26],'f')
        
        tst=LutCluster(None, xvalues,yvalues)

        # the data points should be exact
        self.assertEqual(tst.simulate([1,5]),15)
        self.assertEqual(tst.simulate([2,5]),25)
        self.assertEqual(tst.simulate([4,5]),45)
        self.assertEqual(tst.simulate([1,6]),16)
        self.assertEqual(tst.simulate([2,6]),26)
        self.assertEqual(tst.simulate([4,6]),46)
        
        # interpolation along one dimension
        self.assertEqual(tst.simulate([1.5,5]),20.0)
        self.assertEqual(tst.simulate([1.5,6]),21.0)
        
        #interpolate along two dimensions
        self.assertEqual(tst.simulate([1.5,5.5]),20.5)
        
    def testCluster1d(self):
        if self.just1: return
        #create training data
        X = numpy.zeros((1,50))
        y = numpy.zeros(50)
        for i in range(50):
            x = i * 0.1
            X[0,i] = x
            y[i] = math.sin(x)

        #build the model
        lut_ss = LutStrategy()
        lut_ss.regressor_type = 'LutCluster'
        lut_model = LutFactory().build(X, y, lut_ss)

        #test the model
        X2 = X 
        yhat = lut_model.simulate(X2)

        # the borders of the interpolation are not really good
        for yi, yhati in zip(y[1:-1], yhat[1:-1]):
            self.assertTrue( abs(yi - yhati)/((yi + yhati + 1e-20)/2) < regressor_max_error, (yi,yhati))
            
    def testCluster2d(self):
        return #FIXME: this test is not good
        if self.just1: return
        #create training data
        gridsize = 10
        X = numpy.zeros((2,gridsize**2))
        y = numpy.zeros(gridsize**2)
        sample_k = 0
        
        for i in range(gridsize):
            x_i = i * 0.1
            for j in range(gridsize):
                x_j = j * 0.1
                X[0,sample_k] = x_i
                X[1,sample_k] = x_j
                y[sample_k] = math.sin(x_i + x_j)
                sample_k=sample_k+1

        #build the model
        lut_ss = LutStrategy()
        lut_ss.regressor_type = 'LutCluster'
        lut_model = LutFactory().build(X, y, lut_ss)

        #test the model
        X2 = X
        yhat = lut_model.simulate(X2)
        
        for yi, yhati,x20,x21 in zip(y, yhat,X2[0],X2[1]):
            # ignore the corners
            if not ((x20 <= 0.1) or (x20 >= 4.9) or (x21 <= 0.1) or (x21 >= 4.9)):
                self.assertTrue( abs(yi - yhati)/((yi + yhati + 1e-20)/2) < regressor_max_error, (yi,yhati,x20,x21))
                      
    def tearDown(self):
        pass

if __name__ == '__main__':

    import logging
    logging.basicConfig()
    logging.getLogger('lut').setLevel(logging.DEBUG)
    
    unittest.main()

"""
LUT = Look-Up Table

Holds:
-LutStrategy
-LutModel
-LutFactory
"""

import math
import random

import numpy

# For the removed KD tree implementation (see simulate)
# from util.KDTree import *

from adts import *
from util.ascii import *
from util import mathutil

import logging

log = logging.getLogger('lut')

class LutStrategy:
    """
    @description
      Holds parameters specific to the strategy of building LutModel objects.
      
    @attributes
      bandwidth -- the bigger this number is, the more 'smoothing' it does,
        i.e. the more that faraway training points matter.  In (0,1.0]
    """ 
    def __init__(self):
        """        
        @return
          lut_ss -- LutStrategy object          
        """
        self.bandwidth = 0.05
        
        # indicate the regressortype to use
        self.regressor_type = 'LutModel'
        
        # self.regressor_type = 'LutCluster'
        
    def __str__(self):
        s = "LutStrategy={"
        s += ' bandwidth=%.3f' % self.bandwidth
        s += ' regressor=%s' % self.regressor_type
        s += " /LutStrategy}"  
        return s


class LutFactory:
    """
    @description
      Builds a LutModel
    """ 
    def __str__(self):
        s = "LutFactory={"
        s += " /LutFactory}"  
        return s


    def build(self, X, y, ss):
        """
        @description
          Builds a LutModel, given a target mapping of X=>y and a strategy 'ss'.
        
        @arguments
          X -- 2d array [input variable #][sample #] -- training input data
          y -- 1d array [sample #] -- training output data
        
        @return
          lut_model -- LutModel object
    
        @notes
          In constrast to most regressor factories, 
          this factory is trivial because all the work for a lookup table
          model is during simulation.
        """
        if ss.regressor_type=='LutModel':
            return LutModel(X, y, ss.bandwidth)
            
        elif ss.regressor_type=='LutCluster':
            return LutCluster(None, X, y)
            
        else:
            return LutModel(X, y, ss.bandwidth)
            

class LutModel:
    """
    @description
      Simulatable model.
      
    @attributes
      keep_I -- list of int -- indices of input vars that actually vary
      min_x -- list of float -- min val for each _varying_ input var
      max_x -- list of float -- max val for each _varying_ input var    
      training_X01 -- 2d array [0 .. # varying input variables-1][sample #] --
        the training input data, but each value is scaled to be in
        [0,1] based on the max and min value found for that input variable
      training_y -- 1d array [sample #] -- all the training output data
      bandwidth -- float -- kernel width
    """ 
    def __init__(self, X, y, bandwidth):
        """        
        @arguments
          X -- 2d array [input variable #][sample #] -- the training input data
          y -- 1d array [sample #] -- all the training output dat
          ss -- LutStrategy object
        
        @return
          lut_model -- LutModel object -- a simulatable model          
        """
        #identify the input variables that vary (ie min < max)
        full_min_x = mathutil.minPerRow(X)
        full_max_x = mathutil.maxPerRow(X)
        self.keep_I = [i
                       for i,(mn,mx) in enumerate(zip(full_min_x, full_max_x))
                       if mn < mx]
        
        #only work with input variables that vary as we
        # save min_x, max_x, training_X01/y
        self.min_x = list(numpy.take(full_min_x, self.keep_I, 0))
        self.max_x = list(numpy.take(full_max_x, self.keep_I, 0))
        
        keep_X = numpy.take(X, self.keep_I, 0)
        self.training_X01 = mathutil.scaleTo01(keep_X, self.min_x, self.max_x)
        self.training_y = y
        
# For the removed KD tree implementation (see simulate)
#         # construct the KDTree for the training data
#         self.training_tree = KDTree(self.training_X01.shape[0], 1)
#         tt=numpy.transpose(self.training_X01).astype("f")
#         self.training_tree.set_coords(tt)
#         self.bandwidth_increase = bandwidth * 0.01
#         self.min_nb_lut_indices=20
                
        self.bandwidth = bandwidth

    def __str__(self):
        s = "LutModel={"
        s += ' bandwidth=%.3f' % self.bandwidth
        s += '; # varying input variables=%d' % self.training_X01.shape[0]
        s += '; # training samples=%d' % self.full_X.shape[1]
        s += " /LutModel}"  
        return s

    def simulate(self, X):
        """
        @description
          For each input point (column) in X, compute the response
          of this model.
        
        @arguments
          X -- 2d array [input variable #][sample #] -- inputs 
        
        @return
          yhat -- 1d array [sample #] -- simulated outputs
        """
        keep_X = numpy.take(X, self.keep_I, 0)
        X01 = mathutil.scaleTo01(keep_X, self.min_x, self.max_x)
        yhat = numpy.zeros(X.shape[1])
        
        for sample_i in range(X01.shape[1]):
            sum_w, sum_output = 0.0, 0.0
            for training_sample_j in range(self.training_X01.shape[1]):
                dist = mathutil.distance(X01[:, sample_i],
                                         self.training_X01[:,training_sample_j])
                w = mathutil.epanechnikovQuadraticKernel(dist, self.bandwidth)
                sum_output += w * self.training_y[training_sample_j]
                sum_w += w
            
            if sum_w > 0:
                yhat[sample_i] = sum_output / sum_w
            else:
                yhat[sample_i] = 0.0

# It can be done with a KD tree like this 
# (using the KDtree implementation removed in rev 168)
#
#             sum_w, sum_output = 0.0, 0.0
#             point=numpy.transpose(X01[:, sample_i]).astype("f")
#             bw=self.bandwidth
#             
#             # search neighbors
#             self.training_tree.search(point, bw)
#     
#             # get indices & radii of points
#             indices=self.training_tree.get_indices()
#             
#             if len(indices) < self.min_nb_lut_indices:
#                 log.warning('Not enough LUT indices found, increasing bandwidth...')        
#                 while len(indices) < self.min_nb_lut_indices:              
#                     bw=bw + self.bandwidth_increase
#                     
#                     # search neighbors
#                     self.training_tree.search(point, bw)
#             
#                     # get indices & radii of points
#                     indices=self.training_tree.get_indices()
#                     if bw > 1:
#                         log.warning(' Bandwith too high, out of range')
#                         bw=1
#                         break
#                 
#                 log.warning(' Increased bandwidth to %f, found %d indices' %\
#                         (bw, len(indices)))
#             
#             for training_sample_j in indices:
#                 dist = mathutil.distance(X01[:, sample_i],
#                                          self.training_X01[:,training_sample_j])
#                 w = mathutil.epanechnikovQuadraticKernel(dist, bw)
#                 sum_output += w * self.training_y[training_sample_j]
#                 sum_w += w
# 
#                 
#             if sum_w > 0.0:
#                 yhat[sample_i] = sum_output / sum_w
#             else:
#                 yhat[sample_i] = 0.0
       
        return yhat

    def simulate1(self, x):
        X = numpy.reshape(x, (len(x),1))
        return self.simulate(X)[0]

class LutDataPruner:
    """Prunes data in a lookup table"""
    def __init__(self):
        pass
        
    def prune(self, X, y, Xy, thr_error, min_N, pruned_filebase, all_varnames):
        """
        @description
          Given a dataset of X=>y, prune away samples until
          we either get error > thr or # samples < min_N.  Returns
          results both as a list and into files.
        
        @arguments
          X -- 2d array -- has _all_ input data
          y -- 1d array -- has _all_ output data
          Xy -- 2d array -- has an extra row for y.  Note that the ordering
            of the rows may be different than that for X.  It will output
            the pruned_filebase using the pruned samples from this dataset.
          thr_error -- float -- 
          min_N -- int -- stop pruning if len(pruned_y) < min_N
          pruned_filebase -- string -- during pruning, periodically
            save results to pruned_filebase.hdr/.val
          all_varnames -- list of string -- list of varnames, needed
            for saving pruned_filebase.hdr
            
        @return        
          keep_I -- list of int -- the indices of the samples of X or
            y that we want to keep.  Rest have been pruned away.
          AND
          <<pruned_filebase.hdr, pruned_filebase.val>>
        """
        assert X.shape[0]+1 == Xy.shape[0] == len(all_varnames) 
        assert X.shape[1] == Xy.shape[1] == len(y)
        N = len(y)
        keep_I = range(N)

        max_error = 0
        for prune_iter in range(100000):
            log.info('=======================================================')
            log.info('LutDataPruner iteration #%d; #samples init=%d, now=%d' %
                     (prune_iter, N, len(keep_I)))
            max_error, next_keep_I = self._prune1(X, y, keep_I, thr_error)
            if len(next_keep_I) <= min_N:
                log.info('Stop pruning because we have <= min num samples')
                break
            elif max_error > thr_error:
                log.info('Stop pruning because it would exceed error threshold')
                break
            else:
                keep_I = next_keep_I

            # -periodically store data to file
            if prune_iter > 10 and prune_iter%10 == 0:
                keep_Xy = numpy.take(Xy, keep_I, 1)
                trainingDataToHdrValFiles(pruned_filebase, all_varnames,keep_Xy)
                log.info("Updated pruned output in %s.hdr, %s.val" %
                         (pruned_filebase, pruned_filebase))
                
                
        log.info('=======================================================')
        return keep_I

    def _prune1(self, X, y, keep_I, thr_error):
        """
        @description
          Strategy: keep randomly choosing samples from keep_I until we find
          one whose removal still has error < thr_error.

          If we can't find such a sample, prune next-best sample.
        
        @arguments
          X -- 2d array -- has _all_ data
          y -- 1d array -- has _all_ data
          keep_I -- list of int -- the indices of the samples of X or
            y that we want to keep.  Rest have been pruned away.
          thr_error -- float -- 
            
        @return
          new_keep_I -- list of int -- remove_I, with one more
            sample removed from
        """
        num_cands = 10000 #magic number alert

        #
        lut_factory = LutFactory()
        lut_ss = LutStrategy()

        #choose which samples we consider pruning away
        N = len(keep_I)
        num_cands = min(N, max(1, num_cands))
        cand_sample_I = random.sample(keep_I, num_cands)

        #'best' here is the sample which returns the lowest error
        best_error, best_keep_I = float('inf'), None
        for j, cand_sample_i in enumerate(cand_sample_I):
            cand_keep_I = [i for i in keep_I if i != cand_sample_i]
            model = lut_factory.build(numpy.take(X, cand_keep_I, 1),
                                      numpy.take(y, cand_keep_I), lut_ss)
            error = abs(model.simulate1(X[:,cand_sample_i]) - y[cand_sample_i])
            error = error / (max(y) - min(y)) #normalize
            
            if error < best_error:
                best_error = error
                best_keep_I = cand_keep_I

            if (j % 10) == 0 or cand_sample_i == cand_sample_I[-1]:
                log.info('  LutDataPruner cand #%i/%i; error=%8g, lowest=%8g' % 
                         (j+1, num_cands, error, best_error))

            if error < thr_error:
                log.info('  Found candidate with error < %g (cand #%d)' %
                         (thr_error, j+1))
                break

        return best_error, best_keep_I

class LutCluster:
    """ Represents a cluster of data points in the LUT point space 
        The idea is that the point space is divided into clusters along
        the 'discrete' axes. This means that a cluster is created for
        every discrete value on that axis. The cluster can contain
        sub-clusters that operate along another axis. The lowest level
        clusters contain a non-uniform set of data points in one dimension.
        
        The interpolation is done by finding the appropriate clusters,
        doing a 1D interpolation in them and then interpolating inbetween
        the clusters.
        
        This approach seems to be yielding good results and has good
        performance, also for large datasets.
    """
    
    def __init__(self, parent, X, y):
        """
        @description
            Build the cluster
            
        @arguments
            X -- 2-d array [var_i][sample_i]  -- the indices of the data values
            y -- 1-d array of float [sample_i]  -- the data values
            
        @return
          nothing
        """
        #preconditions
        assert len(y) == X.shape[1]

        #base data
        n, N = X.shape
        self.children = []
        self.level = 0
                
        # determine the level of the cluster
        if parent==None:
            # root cluster
            self.level=0
        else:
            self.level=parent.level+1
        
        # determine if this cluster is bottom level
        # i.e. are there only one variable left
        if self.level + 1 == n:
            # yes it is
            
            self.has_children=False
            
            # we save the values sorted, otherwise we'll have to do it during
            # the interpolation            
            
            # note that we save the values sorted by target value, as we
            # cannot be sure that the I=f(W) is really a function (i.e. invertible).
            # the effect will be that when we interpolate, we'll always choose
            # the smallest W available.            
            
            perm_I = numpy.argsort(y)
            
            self.xvalues = numpy.take(X[self.level,:], perm_I)
            self.yvalues = numpy.take(y, perm_I)
            
        else:
            self.has_children = True
            
            # construct the list of axis-values for this cluster
            # returns a sorted list without duplicates
            self.xvalues = mathutil.uniquifyVector(X[self.level,:])
            
            # build a cluster for each axis value
            for xvalue in self.xvalues:            
                # find the points that are contained in the new child cluster
                I = [i for i,val in enumerate(X[self.level,:]) if val==xvalue]

                # build the child
                child = LutCluster(self, numpy.take(X,I,1), numpy.take(y,I))
                
                self.children.append(child)
                
    def simulate(self, point):
        """ 
        @description
            find the predicted value for the given point based upon the 
            data present in this cluster. This is either interpolation of
            the actual data present, or choosing the best child clusters
            to interpolate between.
            
        @arguments
          point -- list -- contains the point data
            
        @return
          the interpolated value
        """
        # strip the first entry, as this will be used to select the subclusters
        target_point = point[self.level]
    
        # find the clusters that should be interpolated
        # calculate linear distance
        xdist = self.xvalues-target_point
    
        nb_xvalues = xdist.shape[0]
        
        # find the center element
        idxR = numpy.searchsorted(xdist,0);
        while idxR < nb_xvalues and xdist[idxR] < 0:
            idxR = idxR + 1
    
        # handle extrapolation
        if idxR == nb_xvalues:
            #log.warning('Extrapolation at the right side')
            idxR = nb_xvalues-1
    
        idxL = idxR-1
    
        if idxL<0:
            #corner case: is target point the first point in the dataset?
            #if target_point != self.xvalues[0]:
                #log.warning('Extrapolation at the left side')
                
            idxL = 0
            idxR = 1
        
        # sanity check
        assert(idxL>=0 and idxL<nb_xvalues and idxR>=0 and idxR<nb_xvalues)
    
        # find the x-axis values
        x1 = self.xvalues[idxL]
        x2 = self.xvalues[idxR]
        
        # check if this is a bottom level cluster
        if self.has_children:
            # it is not a bottom level cluster so recurse down
            
            y1 = self.children[idxL].simulate(point)
            y2 = self.children[idxR].simulate(point)

            return y1+(y2-y1)/(x2-x1)*(target_point-x1)
        
        else:
            # it is bottom level. The cluster contains yvalues; interpolate between them.
            return self.yvalues[idxL]+(self.yvalues[idxR]-self.yvalues[idxL]) / \
                (x2-x1)*(target_point-x1)

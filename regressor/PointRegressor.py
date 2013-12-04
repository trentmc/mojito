import numpy

class PointRegressor:
    """
    @description
      Like a regressor, but is aware of the input variable names
      and thus can simulate directly off of an input point.
    """
    def __init__(self, regressor, input_varnames, case_matters):
        """
        @arguments
          regressor -- a regressor -- has function simulate(X) where
            X is a 2d array [input var #][sample #]
          input_varnames -- list of string --
          case_matters -- bool -- does uppercase vs. lowercase matter
            for the input vars?

        @return
          new_point_regressor -- PointRegressor object -- 
        """
        self.regressor = regressor
        if not case_matters:
            input_varnames = [varname.lower() for varname in input_varnames]
        self.input_varnames = input_varnames
        self.case_matters = case_matters

        #We allocate this once, and update with each call to simulate.
        #Therefore less overhead in memory allocation.
        self._X = numpy.zeros((len(input_varnames), 1))

    def simulatePoint(self, point):
        """
        @description
          Simulates at one input point

        @arguments
          point -- dict mapping input_varname : input_value

        @return
          simulated_output_value -- float          
        """
        #make input point's varnames lowercase if case_matters == False
        if self.case_matters:
            point2 = point
        else:
            point2 = {}
            for varname, varval in point.items():
                point2[varname.lower()] = varval
        
        #set _X
        # -recall that each 'self_varname' is already lowercase, if
        #  case_matters == False
        for var_index, self_varname in enumerate(self.input_varnames):
            self._X[var_index,0] = point2[self_varname]

        #simulate with regressor
        y = self.regressor.simulate(self._X)

        #done
        return y[0]

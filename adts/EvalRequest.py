from Point import RndPoint, EnvPoint
from Analysis import Analysis

class EvalRequest:
    """
    @description
      A request for an evaluation.  Holds just enough info to uniquely
      define a simulation result.
      
    @attributes
      opt_point -- -- point in search space == genotype
      rnd_point -- scaled RndPoint object
      analysis -- Analysis object
      env_point -- scaled EnvPoint object
    """
    
    def __init__(self, opt_point, rnd_point, analysis, env_point):
        """        
        @arguments
          opt_point -- see class description
          rnd_point -- ''
          analysis -- ''
          env_point -- ''
    
        @notes
          It doesn't care if env_point is not one of the env_points in
          'analysis'. 
        """ 
        #validate inputs
        if not isinstance(rnd_point, RndPoint):
            raise ValueError('rnd_point is not a RndPoint: %s' % rnd_point)
        if not rnd_point.is_scaled:
            raise ValueError('rnd_point is not scaled')
        
        if not isinstance(analysis, Analysis):
            raise ValueError('analysis is not an Analysis: %s' % analysis)
        
        if not isinstance(env_point, EnvPoint):
            raise ValueError('env_point is not an EnvPoint: %s' % env_point)
        if not env_point.is_scaled:
            raise ValueError('env_point is not scaled')

        #set values
        self.opt_point = opt_point
        self.rnd_point = rnd_point
        self.analysis = analysis
        self.env_point = env_point

    def __str__(self):
        s = ''
        s += 'EvalRequest={'
        s += ' opt_point=%s' % self.opt_point
        s += '; rnd_point=%s' % self.rnd_point
        s += '; analysis=%s' % self.analysis
        s += '; env_point=%s' % self.env_point
        s += '/EvalRequest}'
        return s

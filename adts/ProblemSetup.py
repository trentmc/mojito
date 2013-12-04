from Part import EmbeddedPart
from Analysis import FunctionAnalysis, CircuitAnalysis

class ProblemSetup:
    """
    @description
      Holds all the information necessary to attack problem.
      At the core, it's:
      -the search space
      -the goals
      
    @attributes
      analyses -- list of Analysis objects -- hold info about goals
    """
    
    def __init__(self, embedded_part, analyses):
        """        
        @arguments
          embedded_part -- EmbeddedPart object -- describes top-level Part
            along with its connections.  Note that the 'functions'
            attribute of this embedded_part will change with every Ind;
            upon instantiation here, it's ok to set each function value
            to None.
          analyses -- list of Analysis objects
        
        @return
          ProblemSetup object        
        """
        #validate inputs
        if not isinstance(embedded_part, EmbeddedPart):
            raise ValueError("'embedded_part' was not EmbeddedPart, it was %s"%
                             str(embedded_part.__class__))
        if len(analyses) == 0:
            raise ValueError("Need >0 analyses")
        an_IDs = []
        for analysis in analyses:
            if analysis.ID in an_IDs:
                raise ValueError('found duplicate analysis ID: %s, %s' % (analysis.ID, an_IDs))
            an_IDs.append(analysis.ID)

        #set values
        self.embedded_part = embedded_part
        self.analyses = analyses

        #fast-access dict for metrics
        self._metric_name_to_metric = {}
        for analysis in analyses:
            for metric in analysis.metrics:
                self._metric_name_to_metric[metric.name] = metric

        #fast-access for flattened metrics
        self._flattened_metrics = [metric
                                   for an in self.analyses
                                   for metric in an.metrics]

    def functionAnalyses(self):
        """
        @description
          Returns the list of analyses that are FunctionAnalysis objects          
        """
        return [analysis for analysis in self.analyses
                if isinstance(analysis, FunctionAnalysis)]

    def circuitAnalyses(self):
        """
        @description
          Returns the list of analyses that are CircuitAnalysis objects          
        """
        return [analysis for analysis in self.analyses
                if isinstance(analysis, CircuitAnalysis)]

    def metric(self, metric_name):
        """
        @description
          Returns the metric corresponding to 'metric_name'
        
        @arguments
          metric_name -- string
        
        @return
          metrics -- Metric object        
        """
        if self._metric_name_to_metric.has_key(metric_name):
            return self._metric_name_to_metric[metric_name]
        else:
            raise ValueError("No metric with name '%s' found" % metric_name)

    def numMetrics(self):
        """Returns total number of metrics"""
        return len(self.flattenedMetricNames())

    def flattenedMetrics(self):
        """
        @description
          Returns list of metrics, flattened across analyses
        
        @arguments
          <<none>>
        
        @return
          metrics_list -- list of Metric
        """
        return self._flattened_metrics

    def flattenedMetricNames(self):
        """
        @description
          Returns list of metric _names_, flattened across analyses
        
        @arguments
          <<none>>
        
        @return
          metrics_list -- list of string        
        """
        metric_names = [metric.name
                        for an in self.analyses
                        for metric in an.metrics]
        return metric_names
                        
    def prettyStr(self):
        s = '\n\nProblem Setup:\n'
        s += '   Embedded_part = %s\n\n' % self.embedded_part.part.name
        num_con, num_obj = 0,0
        for analysis in self.analyses:
            s += 'Analysis ID = %d:\n' % analysis.ID
            for metric in analysis.metrics:
                s += '   ' + metric.prettyStr() + '\n'
                num_con += 1
                num_obj += metric.improve_past_feasible
            s += '\n'
        s += 'Total # constraints = %d; total # objectives = %d\n' % \
             (num_con, num_obj)
        return s
        
        
    def __str__(self):        
        s = ''
        s += 'ProblemSetup={'
        s += ' embedded_part = %s' % self.embedded_part.part.name
        s += ' # analyses=%s' % self.analyses
        s += '\nAnalyses:\n'
        for analysis in self.analyses:
            s += '\nNext analysis: \n%s' % analysis
        s += ' /ProblemSetup}'
        return s
        
 

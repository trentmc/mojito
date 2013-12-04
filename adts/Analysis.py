"""
Holds:
-Analysis (abstract parent class)
-FunctionAnalysis (child class)
-CircuitAnalysis (child class)
-Simulator class -- a key attribute of CircuitAnalysis
"""

import os
import string
import time
import types

from util.constants import BAD_METRIC_VALUE, REGION_LINEAR, REGION_SATURATION, \
     REGION_CUTOFF
from util import mathutil
from Point import EnvPoint
from Metric import Metric
import EvalUtils

import logging
log = logging.getLogger('analysis')

region_token_to_value = {'Linear'   : REGION_LINEAR,
                         'Saturati' : REGION_SATURATION,
                         'Cutoff'   : REGION_CUTOFF}
region_value_to_str = {REGION_LINEAR : 'LINEAR',
                       REGION_SATURATION : 'SATURATION',
                       REGION_CUTOFF : 'CUTOFF'}

DOCs_metric_name = 'perc_DOCs_met'

class Analysis:
    """
    @description
      One invokation of a 'simulation' or a function call.  Results
      in >=1 metrics.
      
    @attributes
      ID -- int -- unique ID for this Analysis
      env_points -- list of EnvPoint -- to be thorough, need to sim at
        all of these        
      
    @notes
      Each of the env_points coming in must be scaled.
    """
    
    # Each analysis created get a unique ID
    _ID_counter = 0L
    
    def __init__(self, env_points):
        """        
        @arguments        
          env_points -- list of EnvPoint
        
        @return
          Analysis           
        """
        #manage 'ID'
        self._ID = Analysis._ID_counter
        Analysis._ID_counter += 1
        
        #validate inputs
        if len(env_points) == 0:
            raise ValueError("Need >0 env points for each analysis")
        for env_point in env_points:
            if not env_point.is_scaled:
                raise ValueError('Env point needs to be scaled')

        #set values
        self.env_points = env_points

    ID = property(lambda s: s._ID)

    def __str__(self):
        raise NotImplementedError('Implement in child')
        
        
class FunctionAnalysis(Analysis):
    """
    @description
      An analysis used for simulating on _functions_.  Holds one metric,
      which gets defined here (at the same time).
      
    @attributes
      env_points -- list of EnvPoint 
      function -- function -- a call to function(point)
        is considered to be the 'running' of this Analysis.  It will
        will return the value of the _metric_ at that (scaled) point.
      metric -- Metric object -- describes the metric that running this
        Analysis at a scaled_point will produce a measurement of      
    """
    
    def __init__(self, function, env_points, min_metric_threshold,
                 max_metric_threshold, metric_is_objective):
        """        
        @arguments
          function -- see class description
          env_points -- see class description
          min_metric_threshold -- float/ int -- lower bound; helps define metric 
          max_metric_threshold -- float/ int -- upper bound; helps define metric
          metric_is_objective -- bool -- is metric an objective (vs.
            constraint(s) ?)
        
        @return
          FunctionAnalysis 
        """
        Analysis.__init__(self, env_points)

        self.function = function
        metric_name = 'metric_' + function.func_name
        self.metric = Metric(metric_name,
                             min_metric_threshold, max_metric_threshold,
                             metric_is_objective)

    #make it such that we can access the single metric as if it were a list
    def _metrics(self):
        return [self.metric]
    metrics = property(_metrics)
        
    def __str__(self):
        s = ''
        s += 'FunctionAnalysis={'
        s += ' function=%s' % self.function
        s += '; # env_points=%d' % len(self.env_points)
        s += '; metric=%s' % self.metric
        s += ' /FunctionAnalysis}'
        return s
        
class CircuitAnalysis(Analysis):
    """
    @description
      An analysis used for simulating on _circuits_.  Holds >1 metrics,
      which gets defined here (at the same time).
      
    @attributes
      env_points -- list of EnvPoint 
      metrics -- list of Metric objects -- describes the metrics that
        running this Analysis at a scaled_point will produce measurements of.
      simulator -- Simulator object -- knows how to call SPICE and
        retrieve corresponding output data
      
    @notes
      Each of the env_points coming in must be scaled.
    """
    
    def __init__(self, env_points, metrics, simulator):
        """        
        @arguments
          env_points -- see class description
          metrics -- list of Metric objects
          simulator -- see class description
        
        @return
          CircuitAnalysis 
        """
        #validate inputs
        if not isinstance(env_points[0], EnvPoint): raise ValueError
        if not isinstance(metrics[0], Metric): raise ValueError
        metrics_metricnames = sorted([m.name for m in metrics])
        sim_metricnames = sorted(simulator.metricNames())
        if metrics_metricnames != sim_metricnames:
            raise ValueError("These should match:\n%s\n%s" %
                             (metrics_metricnames, sim_metricnames))
        if simulator.metric_calculators is not None:
            calcs_metricnames = sorted(simulator.metric_calculators.keys())
            if metrics_metricnames != calcs_metricnames:
                raise ValueError("These should match:\n%s\n%s" %
                                 (metrics_metricnames, calcs_metricnames))
        if not isinstance(simulator, Simulator): raise ValueError

        #set values
        Analysis.__init__(self, env_points)
        self.metrics = metrics
        self.simulator = simulator

    def createFullNetlist(self, design_netlist, env_point):
        """Creates a full netlist from design_netlist and env_point.
        See Simulator:createFullNetlist() for details."""
        return self.simulator.createFullNetlist(design_netlist, env_point)
        
    def simulate(self, simfile_dir, design_netlist, env_point):
        """
        @description
          Calls self.simulator.simulate()
          
        @arguments
          simfile_dir -- string -- this is where the temporary simulation
            files will be put (the ones auto-generated here, and auto-gen by
            SPICE too)
          design_netlist -- string -- describes the design.  Cannot
            simulate on its own, however; it needs testbench code around it.
          env_point -- EnvPoint object -- holds envvar_name : envvar_value
        
        @return
           sim_results -- dict of metric_name : metric_value -- has
             there is one entry for every metric in self.analysis
             Never includes the DOCs metric
           lis_results -- dict of 'lis__device_name__measure_name' : lis_value --
             used to compute the DOCs metric
           waveforms_per_ext -- dict of file_extension : 2d_array_of_waveforms
             For each of the waveforms outputs like .tr0, .sw0
        """
        #validate inputs
        assert isinstance(simfile_dir, types.StringType)
        assert isinstance(design_netlist, types.StringType)
        assert isinstance(env_point, EnvPoint)
        if sorted(env_point.keys()) != \
           sorted(self.env_points[0].keys()):
            raise ValueError("Input 'env_point' has wrong keys: %s" %
                             env_point.keys())
        #
        return self.simulator.simulate(simfile_dir, design_netlist, env_point)

    def __str__(self):
        s = ''
        s += 'CircuitAnalysis={'
        s += '; # env_points=%d' % len(self.env_points)
        s += '; # metrics=%d' % len(self.metrics)
        s += '; metrics=%s' % self.metrics
        s += '; simulator=%s' % self.simulator
        s += ' /CircuitAnalysis}'
        return s
    
class Simulator(Analysis):
    """
    @description
      Knows how to call SPICE and retrieve corresponding output data

      Holds a lot of data specifically for yanking info out
      of a simulator output file and converting it into metric
      value information.

      Used for CircuitAnalysis objects, but quite a bit more low-level.
      
    @attributes
      metrics_per_outfile -- dict of output_filetype : list_of_metric_names --
        Tells which output files to look for, for which metrics.
        Output_filetypes can include lis; ms0, ma0, mt0; sw0, tr0; ic0.
        If we want waveforms but no metrics from a particular output file,
        it still must be included here.  E.g. have 'sw0':[] entry.
        
      cir_file_path -- string -- path where to find 'base' circuit files
        (but not the ones that are temporarily generated)
                                
      max_simulation_time -- int -- max time to spend on a simulation, in
        seconds
        
      simulator_options_string -- string -- info about simulator options
        which will be embedded directly in auto-generated .cir netlist
      models_string -- string -- info about MOS models
        which will be embedded directly in auto-generated .cir netlist
      test_fixture_string -- string --info about test fixture
        which will be embedded directly in auto-generated .cir netlist.
        Includes:
             -input waveform generation, biases, etc
             -call to an analysis
             -'.print' commands
      lis_measures -- list of string -- which values to measure in .lis.  E.g.
        ['region','vgs'].  Will measure these on every mos device.

      The following attributes are only needed when one of the output
        filetypes is a waveform file with extensions of 'tr0' or 'sw0':
      output_file_num_vars -- dict of extension_string : num_vars_int --
        number of variables expected in each waveform output file (eases parsing)
        Extension string can be .tr0, .sw0
      output_file_start_line -- dict of extension_string : start_line_int --
        where to start parsing each waveform output file.  Starts counting
        at line 0.
      number_width -- int -- number of characters taken up by a number in the
        output file (eases parsing)
        
      metric_calculators -- dict of metric_name : metric_calculator,
        where each calculator knows how to convert a 'waveforms' 2d array
        into a scalar value
    """
    def __init__(self,
                 metrics_per_outfile,
                 cir_file_path,
                 max_simulation_time,
                 simulator_options_string,
                 models_string,
                 test_fixture_string,
                 lis_measures,
                 output_file_num_vars=None,
                 output_file_start_line=None,
                 number_width=None,
                 metric_calculators=None):
        """
        @description
          Constructor.  Fills attributes based on arguments.
          See class description for details about arguments.

        """
        #validate data
        for outfile, metrics in metrics_per_outfile.items():

            if outfile not in ['lis', 'ms0', 'ma0', 'mt0', 'sw0', 'tr0', 'ic0']:
                raise ValueError
            
            if outfile == 'lis': #only DOC and pole-zero metrics allowed
                for metric in metrics:
                    if 'pole' in metric: pass
                    elif metric == DOCs_metric_name: pass
                    else: raise ValueError

            else:
                if DOCs_metric_name in metrics: raise ValueError
            
        assert isinstance(lis_measures, types.ListType)
        for metric_names in metrics_per_outfile.values():
            if not isinstance(metric_names, types.ListType): raise ValueError
        if cir_file_path[-1] != '/':
            raise ValueError("cir_file_path must end in '/'; it's: now %s" %
                             cir_file_path)

        #set values
        self.metrics_per_outfile = metrics_per_outfile
        self.cir_file_path = cir_file_path
        self.max_simulation_time = max_simulation_time
        self.simulator_options_string = simulator_options_string
        self.models_string = models_string
        self.test_fixture_string = test_fixture_string
        self.lis_measure_names = lis_measures
        self.output_file_num_vars = output_file_num_vars
        self.output_file_start_line = output_file_start_line
        self.number_width = number_width
        self.metric_calculators = metric_calculators

    def metricNames(self):
        """List of the metric names that this analysis measures"""
        names = []
        for next_names in self.metrics_per_outfile.values():
            names.extend(next_names)
        return names

    def simulate(self, simfile_dir, design_netlist, env_point):
        """
        @description
          Simulates the design netlist:
          -calls self.simulator.simulate()
          -wraps the appropriate testbench code around the design netlist
           (with appropriate env point values)
          -calls the simulator
          -yanks out the results
          
        @arguments
          simfile_dir -- string -- this is where the temporary simulation
            files will be put (the ones auto-generated here, and auto-gen by
            SPICE too)
          design_netlist -- string -- describes the design.  Cannot
            simulate on its own, however; it needs testbench code around it.
          env_point -- EnvPoint object
        
        @return
           sim_results -- dict of metric_name : metric_value -- has
             there is one entry for every metric in self.analysis.
             Never includes the DOCs metric
           lis_results -- dict of 'lis__device_name__measure_name' : lis_value --
             used to compute the DOCs metric
           waveforms_per_ext -- dict of file_extension : 2d_array_of_waveforms
             For each of the waveforms outputs like .tr0, .sw0
    
        @notes
          Currently we use os.system a lot, but subprocess.call
          is easier to use; we should consider changing (warning:
          Trent's python 2.4 doesn't properly support subprocess yet)
        """
        if len(simfile_dir) > 0 and simfile_dir[-1] != '/':
            simfile_dir = simfile_dir + '/'
            
        #Make sure no previous output files
        outbase = 'autogen_cirfile'
        os.system('rm ' + simfile_dir + outbase + '*;')
        if os.path.exists(simfile_dir + 'ps_temp.txt'):
            os.remove(simfile_dir + 'ps_temp.txt')

        #Create netlist, write it to file
        netlist = self.createFullNetlist(design_netlist, env_point)
        cirfile = simfile_dir + outbase + '.cir'
        f = open(cirfile, 'w'); f.write(netlist); f.close()

        #Call simulator; error check
        #old command = ['cd ' simfile_dir '; hspice -i ' cirfile ' -o ' outbase '; cd -'];

        #hspice
        psc = "ps ax |grep hspice|grep -v 'cd '|grep " + cirfile + \
              " 1> " + simfile_dir + "ps_temp.txt"
        command = "cd " + simfile_dir + "; hspice -i " + cirfile + \
                  " -o " + outbase + "& cd -; " + psc

        #eldo
        #psc = ['ps ax |grep eldo|grep -v ''cd ''|grep ' cirfile ' 1> ps_temp.txt'];
        #command = ['cd ' simfile_dir '; eldo -i ' cirfile ' -o ' outbase '& cd -; ' psc];

        #log.debug("Call with comand: '%s'" % command)
        status = os.system(command)

        output_filetypes = self.metrics_per_outfile.keys()
        result_files = [simfile_dir + outbase + '.' + output_filetype
                        for output_filetype in output_filetypes]
        got_results = False
        bad_result = False

        if status != 0:
          got_results = True;
          bad_result = True;
          log.error('System call with bad result.  Command was: %s' % command)

        #loop until we get results, or until timeout
        t0 = time.time()
        while not got_results:
            
            if self._filesExist(result_files):
                #log.debug('\nSuccessfully got result file')
                got_results = True
                bad_result = False
            
            elif (time.time() - t0) > self.max_simulation_time:
                log.debug('\nExceeded max sim time of %d s, so kill' %
                          self.max_simulation_time)
                got_results = True
                bad_result = True
                      
                #kill the process
                t = EvalUtils.file2tokens(simfile_dir + 'ps_temp.txt', 0)
                log.debug('ps_temp.txt was:%s' %
                          EvalUtils.file2str(simfile_dir + 'ps_temp.txt'))
                pid = t[0]
                log.debug('fid was: %s' % pid)
                if not t[0] == 'Done':
                    os.system('kill -9 %s' % pid)

            #pause for 0.25 seconds (to avoid taking cpu time while waiting)
            time.sleep(0.25) 

        #we may have had to do a timeout kill, but there still
        # may be good results
        if self._filesExist(result_files):
            #log.debug('\nSuccessfully got result file')
            got_results = True
            bad_result = False

        #retrieve results
        # -fill these:
        sim_results = {}
        
        metric_names = self.metricNames();
        
        for metric_name in metric_names:
            if metric_name != DOCs_metric_name: #don't fill this in
                sim_results[metric_name] = None
        metrics_found = []

        if bad_result:
            log.debug('Bad result: did not successfully generate simdata')
            return self._badSimResults()

        #Add metric values measured from each result file: tr0, ma0, ic0

        # -lis: from .lis file (which is like stdout)
        if 'lis' in output_filetypes:
            lis_file = simfile_dir + outbase + '.lis'
            success, lis_results = self._extractLisResults(lis_file)
            if not success:
                log.debug('Bad result: could not extract values from .lis file')
                return self._badSimResults()
                

            metrics_found.append(DOCs_metric_name)
            
            # if pz results are found
            for k in lis_results.keys():
                ks = k.split('__')
                measure_name = ks[1] + ks[2]
                if measure_name in self.metrics_per_outfile['lis']:
                    sim_results[measure_name] = lis_results[k]
                    metrics_found.append(measure_name)            
            
        else:
            lis_results = {}

        # -ms0, ma0, mt0 -- .measure outputs for dc, ac, tran respectively
        for extension in ['ms0','ma0','mt0']:
            if extension not in output_filetypes: continue
            output_file = simfile_dir + outbase + '.' + extension
            tokens = EvalUtils.file2tokens(output_file, 2)
            num_measures = len(tokens) / 2
            all_measures = {}
            for measure_i in range(num_measures):
                measure_name = tokens[measure_i]
                if measure_name in self.metrics_per_outfile[extension]:
                    try:
                        measure_value_str = tokens[num_measures + measure_i]
                        measure_value = eval(measure_value_str)
                        assert mathutil.isNumber(measure_value)
                    except:
                        log.debug("Bad result in %s: non-numeric number "
                                  "returned:'%s'" %(extension,measure_value_str))
                        return self._badSimResults()
                    sim_results[measure_name] = measure_value
                    metrics_found.append(measure_name)

        #fill in 'waveforms_per_ext' -- dict of extension_str :2d_waveforms_array
        # and 'sim_results' related to waveforms.
        # -sw0, tr0 -- waveform outputs for dc, tran respectively.  Useful in:
        #   -calculating metrics in python code rather than directly in SPICE
        #   -return waveforms for visualization
        #   -other later-in-the-flow calcs for waveforms calcs
        waveforms_per_ext = {}
        for extension in ['sw0','tr0']:
            if extension not in output_filetypes: continue
            output_file = simfile_dir + outbase + '.' + extension
            try:
                start_line = self.output_file_start_line[extension]
                num_vars = self.output_file_num_vars[extension]
                waveforms_array = EvalUtils.getSpiceData(
                    output_file, self.number_width, start_line, num_vars)
            except:
                log.debug('Bad result: could not retrieve %s waveforms' %
                          extension)
                return self._badSimResults()

            if waveforms_array.shape[0] != num_vars:
                log.debug('Bad result: # waveforms back (%d) != num vars' %
                          (waveforms_array.shape[0], num_vars))
                return self._badSimResults()

            if waveforms_array.shape[1] <= 2:
                log.debug('Bad result: <=2 points per waveform (!?)')
                return self._badSimResults()

            for metric_name, metric_calc_func in self.metric_calculators.items():
                metric_val = metric_calc_func(waveforms_array)
                if metric_val is BAD_METRIC_VALUE:
                    log.debug("Bad result in calculating %s: BAD_METRIC_VALUE "
                              "returned" % metric_name)
                    return self._badSimResults()
                    
                sim_results[metric_name] = metric_val
                metrics_found.append(metric_name)

            waveforms_per_ext[extension] = waveforms_array

        # -ic0: comes from .op sim
        if 'ic0' in output_filetypes:
            ic0_file = simfile_dir + outbase + '.ic0'
            tokens = EvalUtils.file2tokens(ic0_file, 2)
            for metric_name in self.metrics_per_outfile['ic0']:
                #find the token and value corresponding to 'metric_name'
                # and fill it
                found = False
                for token_i, token in enumerate(tokens):
                    if token == metric_name:
                        sim_results[token] = eval(tokens[token_i+2])
                        found = True
                        break
                    
                if not found:
                    log.debug('Bad result 3: did not find metric %s' %
                              metric_name)
                    return self._badSimResults()
                else:
                    metrics_found.append(metric_name)

        # -special: pole-zero (pz) measures are a function of 'gbw' and other
        # (note: problem setup may request a subset, or none, of the following)
        # (note: somewhat HACK-like because of our dependence on special
        #  names, but it will do until we have a more general way to
        #  compute some metrics as functions of other metrics w/ error check)
        pz_dict = {'pole0fr':'pole0_margin',
                   'pole1fr':'pole1_margin',
                   'pole2fr':'pole2_margin',
                   'zero0fr':'zero0_margin',
                   'zero1fr':'zero1_margin',
                   'zero2fr':'zero2_margin',
                   }
        have_pzmeasure = mathutil.listsOverlap(pz_dict.values(), metric_names)
        if have_pzmeasure:
            #all pz measures need gbw, so find it (incl. catching error cases)
            if not sim_results.has_key('gbw'):
                log.debug("Bad result: could not find gbw")
                return self._badSimResults()
            gbw = sim_results['gbw']
            if not mathutil.isNumber(gbw) or gbw <= 0.0:
                log.debug("Bad result: gbw is not a number or is <=0")
                return self._badSimResults()

            #now fill in all the pz metrics that we care about
            for pzmeasure_name, pzmetric_name in pz_dict.items():
                if pzmetric_name not in metric_names: continue
                
                if pzmeasure_name in sim_results.keys():
                    pzmeasure = sim_results[pzmeasure_name]
                    if not mathutil.isNumber(pzmeasure):
                        log.debug("Bad result: '%s' is not a number")
                        return self._badSimResults()
                    # note that we've already caught divide-by-zero above
                    sim_results[pzmetric_name] = pzmeasure / gbw
                    metrics_found.append(pzmetric_name)
                else:
                    log.debug("Bad result: '%s' not found" %pzmeasure_name)
                    return self._badSimResults()                

        #have we got all the metrics we expected?
        if sorted(metrics_found) != sorted(metric_names):
            missing = sorted(mathutil.listDiff(metric_names,
                                               metrics_found))
            log.debug('Bad result 4: missed metrics: %s' % missing)            
            return self._badSimResults()
        
        #Hooray, everything simulated ok! Return the results.
        s = 'Got fully good results: {'
        for metric_name, metric_value in sim_results.items():
            if metric_name[:4] != 'lis.':
                s += '%s=%g, ' % (metric_name, metric_value)
        s += '}'
        s += ' (plus %d lis values)' % len(lis_results)
        log.debug(s)
        return sim_results, lis_results, waveforms_per_ext


    def _extractLisResults(self, lis_file):
        """
        @description
          Helper file for simulate().

          Extracts the simulation results from a .lis file
          (e.g. for later finding out if DOCs are met)
          
        @arguments
          lis_file -- string -- should end in '.lis'
        
        @return
           success -- bool -- was extraction successful?
           lis_results -- dict of 'lis__device_name__measure_name' : lis_value
        """
        assert self.metrics_per_outfile.has_key('lis'), 'only call if want lis'
        assert lis_file[-4:] == '.lis', lis_file

        if not os.path.exists(lis_file):
            log.debug("_extractLisResults failed: couldn't find file: %s" %
                      lis_file)
            return False, {}
        
        lis_results = {}
            
        #extract subset of 'lis' file that starts with ***mosfets
        # and ends with the next ***
        lines = EvalUtils.subfile2strings(lis_file, '**** mosfets','***')
        if len(lines) == 0:
            log.debug("_extractLisResults failed: '**** mosfets' section "
                      "was not found")
            return False, {}
            

        #strip leading whitespace
        lines = [string.lstrip(line) for line in lines]

        #extract (ordered) list of transistor names            
        device_names = []
        for line in lines:
            if line[:len('element')] == 'element':
                #'token' examples are '0:m2', '0:m16', we don't want the 0: part
                tokens = EvalUtils.string2tokens(line[len('element'):])
                device_names += [token[2:] for token in tokens]
        
        #extract list of each measure of interest
        # lis_measure_values maps measure_name : list_of_values, where
        #  the order of values is same as that of transistor names
        lis_measures = {} 
        for measure_name in self.lis_measure_names:
            values = []
            for line in lines:
                if line[:len(measure_name)] == measure_name:
                    tokens = EvalUtils.string2tokens(line[len(measure_name):])
                    if measure_name == 'region':
                        values += [region_token_to_value[token]
                                   for token in tokens]
                    else:
                        values += [eval(token) for token in tokens]
            
            #validate
            if len(values) != len(device_names):
                s = 'Found %d values for measure=%s but found %d devices (%s)'% \
                    (len(values), measure_name, len(device_names), device_names)
                log.debug(s)
                return False, {}

            if measure_name == 'region':
                s = "'region' measures:"
                for device_name, value in zip(device_names, values):
                    s += device_name + '=' + region_value_to_str[value] + ', '
                log.debug(s)

            #good, so update lis_measures
            lis_measures[measure_name] = values
        
        #update lis_results
        for device_index, device_name in enumerate(device_names):
            for measure_name in self.lis_measure_names:
                lis_name = 'lis' + '__' + device_name + '__' + measure_name
                lis_value = lis_measures[measure_name][device_index]
                lis_results[lis_name] = lis_value

        #extract subset of 'lis' file that starts with '  ******   pole/zero analysis'
        # and ends with ' ***** constant factor'
        lines = EvalUtils.subfile2strings(lis_file, '  ******   pole/zero analysis',' ***** constant factor')
 
        # now fill the real values if present
        if len(lines) == 0:
            log.info("_extractLisResults failed: '**** pole/zero analysis' section "
                      "was not found")                            
        else:
            # there are pole-zero analysis results

            #strip leading whitespace
            lines = [string.lstrip(line) for line in lines]
            
            # find the start of the poles section
            poles_start_idx=0
            for line in lines:
                if line[:5] == 'poles':
                    break
                else:
                    poles_start_idx += 1
                    
            poles_stop_idx=poles_start_idx+3
            for line in lines[poles_start_idx+3:]:
                if len(line)==0 or not line[0] in ['0','1','2','3','4','5','6','7','8','9','-']:
                    break
                else:
                    poles_stop_idx += 1
                                     
            zeros_start_idx=poles_stop_idx
            for line in lines[poles_stop_idx:]:
                if line[:5] == 'zeros':
                    break
                else:
                    zeros_start_idx += 1
                    
            zeros_stop_idx=zeros_start_idx+3
            for line in lines[zeros_start_idx+3:]:
                if len(line)==0 or not line[0] in ['0','1','2','3','4','5','6','7','8','9','-']:
                    break
                else:
                    zeros_stop_idx += 1
            
            nb_poles=poles_stop_idx - poles_start_idx - 3
            nb_zeros=zeros_stop_idx - zeros_start_idx - 3
                            
            if nb_poles > 0:
            
                # the poles are extracted
                for n in range(0,nb_poles):                
                    line = lines[poles_start_idx+n+3]
                    values = EvalUtils.string2tokens(line)
                    lis_name = 'lis' + '__pole' + str(n) + '__real'
                    lis_results[lis_name] = eval(values[2])
                    lis_name = 'lis' + '__pole' + str(n) + '__imag'
                    lis_results[lis_name] = eval(values[3])
                    
                    fr=((eval(values[2])**2 + eval(values[3])**2)**0.5)
                    
                    if fr == 0:
                        lis_name = 'lis' + '__pole' + str(n) + '__fr'
                        lis_results[lis_name] = 'failed'
                        lis_name = 'lis' + '__pole' + str(n) + '__zeta'
                        lis_results[lis_name] = 'failed'
                    else:
                        lis_name = 'lis' + '__pole' + str(n) + '__fr'
                        lis_results[lis_name] = fr
                        lis_name = 'lis' + '__pole' + str(n) + '__zeta'
                        lis_results[lis_name] = eval(values[2]) / fr
                        
            if nb_zeros > 0:
                # the zeros are extracted
                for n in range(0,nb_zeros):
                    line = lines[zeros_start_idx+n+3]
                    values = EvalUtils.string2tokens(line)
                    lis_name = 'lis' + '__zero' + str(n) + '__real'
                    lis_results[lis_name] = values[2]
                    lis_name = 'lis' + '__zero' + str(n) + '__imag'
                    lis_results[lis_name] = values[3]
                    
                    fr=((eval(values[2])**2 + eval(values[3])**2)**0.5)
                    
                    if fr == 0:
                        lis_name = 'lis' + '__zero' + str(n) + '__fr'
                        lis_results[lis_name] = 'failed'
                        lis_name = 'lis' + '__zero' + str(n) + '__zeta'
                        lis_results[lis_name] = 'failed'
                    else:
                        lis_name = 'lis' + '__zero' + str(n) + '__fr'
                        lis_results[lis_name] = fr
                        lis_name = 'lis' + '__zero' + str(n) + '__zeta'
                        lis_results[lis_name] = eval(values[2]) / fr

        # nothing else to extract                
        return True, lis_results

    def _filesExist(self, filenames):
        for filename in filenames:
            if not os.path.exists(filename):
                return False
        return True

    def _badSimResults(self):
        """
        @description

          Returns (sim_results, lis_results, waveforms) where each entry in
          the tuple is 'bad'.  A bad 'sim_results' is a
          dict of metric_name : BAD_METRIC_VALUE whereas
          bad lis_results are merely an empty dict.
          
        @arguments

          <<none>>
        
        @return

          tuple -- see description
    
        @exceptions
    
        @notes

          Does not have an entry in sim_results for DOCs
        """
        sim_results = {}
        for metric_name in self.metricNames():
            if metric_name != DOCs_metric_name:
                sim_results[metric_name] = BAD_METRIC_VALUE
        return (sim_results, {}, {})

    def createFullNetlist(self, design_netlist, env_point):
        """
        @description
          Builds up a netlist having the following components:
          -call to 'include variables.inc' plus writes a variables.inc file
           that has envvars and rndvars (kept separate ease debugging)
          -the input design_netlist
          -self.test_fixture_string
             
        @arguments
          design_netlist -- string -- describes the design.
          env_point -- EnvPoint object -- 
        
        @return
          full_netlist -- string -- simulation-ready netlist
        """

        #build up s as a list of string segments, rather than a string (faster)
        s = [] 
        
        s.append('\n*SPICE netlist, auto-generated by createFullNetlist()')
        s.append('\n')

        s.append('\n*------Env and Rnd Variables---------')
        s.append('\n')
        for envvar_name, envvar_val in env_point.items():
            s.append('\n.param %s = %5.3e' % (envvar_name, envvar_val))
        #for rndvar_name, rndvar_val in rnd_point.items():
        #    s.append('.param %s = %5.3e\n' % (rndvar_name, rndvar_val))
        s.append('\n')

        s.append('\n*------Design---------' )
        s.append('\n' + design_netlist)
        s.append('\n')
        
        s.append('\n*------Test Fixture---------' )
        s.append('\n' + self.test_fixture_string)
        s.append('\n' )
 
        s.append('\n*------Simulator Options---------' )
        s.append('\n' + self.simulator_options_string)
        s.append('\n' )

        s.append('\n*------Models---------' )
        s.append('\n' + self.models_string)
        s.append('\n' )

        s.append('\n.end' )
        s.append('\n')
        s = string.join(s) #list of strings => string
        return s

    def __str__(self):
        s = ''
        s += 'Simulator={'
        #s += '; # xxx=%s' % xxx
        s += ' /Simulator}'
        return s


class WaveformsToNmse:
    """This is a class that can appear as a callable function to compute
    nmse (normalized mean-squared error)
    
    Example usage:
     calc_nmse = WaveformsToNmse(target_waveform, 1)
     nmse = calc_nmse(waveforms_array) returns a float.
    """
    
    def __init__(self, target_waveform, index_of_cand_waveform):
        self.target_waveform = target_waveform
        self.index_of_cand_waveform = index_of_cand_waveform
        self.range = max(target_waveform) - min(target_waveform)
        self.range = max(self.range, 1.0e-15) #make it >0 by small amount

    def __call__(self, waveforms_array):
        return nmse(self.target_waveform,
                    waveforms_array[self.index_of_cand_waveform],
                    self.range)

def nmse(waveform1, waveform2, denom):
    """Returns normalized sum of squared differences between
    waveform1 and waveform2.  Normalizes via (waveform1-waveform2)"""
    assert denom > 0.0
    if len(waveform1) != len(waveform2):
        log.warning('Waveforms have different lengths: %d and %d' %
                    (len(waveform1), len(waveform2)))
        return BAD_METRIC_VALUE
    return (sum( ((w1 - w2)/denom)**2
                 for (w1,w2) in zip(waveform1, waveform2)) )

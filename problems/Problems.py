import os

import numpy

from adts import *
from SizesLibrary import Point18SizesLibrary, SizesLibraryStrategy, SizesLibrary
from OpLibrary import ApproxMosModels, OpLibraryStrategy, OpLibrary
from adts.Analysis import WaveformsToNmse

import logging
log = logging.getLogger('problems')

WAVEFORM_NUMBER_WIDTH = 11

class ProblemFactory:
    """
    @description    
      ProblemFactory builds ProblemSetup objects for different problems.
    """
    
    def __init__(self):
        pass

    def problemDescriptions(self):
        """Outputs a string describing problems"""
        return """
        PROBLEM_NUM choices:
        --------------------
        31 / 32 - SS (WL / OP)
        41 / 42 - DS (WL / OP)
        51 / 52 - DSS (WL / OP)
        61 / 62 - DS and DSS (WL / OP)
        71 / 72 - DS, DSS, and DDS (WL / OP)
        81 - minimizeNmseToTargetWaveform
	1  - maximizePartCountProblem
        2  - maxPartCount_minArea_Problem
	--------------------
        Legend:
        -SS  = single-ended-in, single-ended out, 1 stage amp
        -DS  = diff-in, single-ended-out, 1 stage amp
        -DSS = diff-in, single-ended-middle, single-ended-out, 2 stage amp
        -DDS = diff-in, differential-middle, single-ended-out, 2 stage amp
        -WL  = use SizingLibrary (W and L search space)
        -OP  = use OpLibrary (operating point driven formulation search space)
        """

    def build(self, problem_choice, extra_args=None):
        """
        @description
          Builds a ProblemSetup based on the input 'problem_choice'.
        
        @arguments
          problem_choice -- int -- to select problem.  See problemDescriptions().
        
        @return
          ps -- ProblemSetup object --          
        """
        known_problem_choices = [1,2,
                                 31,32,
                                 41,42,
                                 51,52,
                                 61,62,
                                 71,72,
				 81	]
        problem = None #fill this in
        if problem_choice == 1:
            problem = self.maximizePartCount_Problem()
        elif problem_choice == 2:
            problem = self.maxPartCount_minArea_Problem()
        
        elif problem_choice == 31:
            problem = self.WL_ssViAmp1_Problem()
        elif problem_choice == 32:
            problem = self.OP_ssViAmp1_Problem()
        
        elif problem_choice == 41:
            problem = self.WL_dsViAmp_Problem(DS=True, DSS=False, DDS=False)
        elif problem_choice == 42:
            problem = self.OP_dsViAmp_Problem(DS=True, DSS=False, DDS=False)
            
        elif problem_choice == 51:
            problem = self.WL_dsViAmp_Problem(DS=False, DSS=True, DDS=False)
        elif problem_choice == 52:
            problem = self.OP_dsViAmp_Problem(DS=False, DSS=True, DDS=False)
            
        elif problem_choice == 61:
            problem = self.WL_dsViAmp_Problem(DS=True, DSS=True, DDS=False)
        elif problem_choice == 62:
            problem = self.OP_dsViAmp_Problem(DS=True, DSS=True, DDS=False)
            
        elif problem_choice == 71:
            problem = self.WL_dsViAmp_Problem(DS=True, DSS=True, DDS=True)
     	elif problem_choice == 72:
            return self.OP_dsViAmp_Problem(DS=True, DSS=True, DDS=True)     
        elif problem_choice == 72:
            problem = self.OP_dsViAmp_Problem(DS=True, DSS=True, DDS=True)	
	elif problem_choice == 81:
            (dc_sweep_start_voltage, dc_sweep_end_voltage, target_waveform) = \
                                     extra_args
            return self.minimizeNmseToTargetWaveform(dc_sweep_start_voltage,
                                                     dc_sweep_end_voltage,
                                                     target_waveform)

        elif problem_choice in known_problem_choices:
            raise ValueError('problem_choice=%d is not implemented yet' %
                             problem_choice)	    
        else:
            raise AssertionError('unknown problem choice: %d' % problem_choice)


        part = problem.embedded_part.part
        log.info("Schema for problem's part '%s': \n%s" %
                 (part.name, part.schemas()))
        schemas = part.schemas()
        schemas.merge()
        log.info("Merged schemas: %s" % schemas)
        log.info("Number of topologies for part '%s' = %d" %
                 (part.name, part.numSubpartPermutations()))

        return problem

    def maximizePartCount_Problem(self):
        """
        @description        
          This is a simple non-simulator problem which tries to maximize
          the number of atomic parts used in a dsViAmp1
        
        @arguments
          <<none>>          
        
        @return
          ps -- ProblemSetup object          
        """
        part = Point18SizesLibrary().dsViAmp1()
        
        connections = part.unityPortMap()
        functions = {}
        for varname in part.point_meta.keys():
            functions[varname] = None #these need to get set ind-by-ind
            
        embedded_part = EmbeddedPart(part, connections, functions)

        an = FunctionAnalysis(embedded_part.numAtomicParts, [EnvPoint(True)],
                              1, float('Inf'), True)
        ps = ProblemSetup(embedded_part, [an])
        
        return ps
    
    def maxPartCount_minArea_Problem(self):
        """
        @description        
          This is a simple bi-objective non-simulator problem:
          -try to maximize # atomic parts
          -try to minimize transistor area (ignore R and C areas)
          -plus meet an arbitrary functionDOC of W>L
        
        @arguments
          <<none>>          
        
        @return
          ps -- ProblemSetup object          
        """
        lib = Point18SizesLibrary()

        #to mos3, add dummy function DOC: constraint of get w > l
        metric = Metric('W_minus_L', 0.00001, float('Inf'), False)
        function = '(W-L)'
        doc = FunctionDOC(metric, function)
        
        mos3 = lib.mos3()
        mos3.addFunctionDOC(doc)

        #main problem setup...
        part = lib.dsViAmp1()
        
        connections = part.unityPortMap()
        functions = {}
        for varname in part.point_meta.keys():
            functions[varname] = None #these need to get set ind-by-ind
            
        embedded_part = EmbeddedPart(part, connections, functions)

        analyses = []

        #maximize num atomic parts
        an0 = FunctionAnalysis(embedded_part.numAtomicParts, [EnvPoint(True)],
                               10, float('Inf'), True)
        analyses.append(an0)

        #minimize area
        an1 = FunctionAnalysis(embedded_part.transistorArea, [EnvPoint(True)],
                               float('-Inf'), 120e-11, False)
        analyses.append(an1)

        #meet functionDOCs
        an2 = FunctionAnalysis(embedded_part.functionDOCsAreFeasible,
                               [EnvPoint(True)],
                               0.99, float('Inf'), False)
        analyses.append(an2)

        #build ps
        ps = ProblemSetup(embedded_part, analyses)
        
        return ps
        
        
    def WL_dsViAmp_Problem(self, DS, DSS, DDS):
        """
        @description        
          Amplifier problem, for double-ended input / single-ended output.
          Many goals, including slew rate, gain, power, area, ...
        
        @arguments        
          DS -- bool -- include 1-stage amp?
          DSS -- bool -- include 2-stage single-ended-middle amp?
          DDS -- bool -- include 2-stage differential-middle amp?
        
        @return
          ps -- ProblemSetup object
    
        @exceptions
          Need to include at least one of the stages.
        """
        #validate inputs
        if not (DS or DSS or DDS):
            raise ValueError('must include at least one of the choices')
        
        #settable parameters
        vdd = 1.8
        
        # -these values must be set based on what is set below!!
        feature_size = 0.18e-06
        nmos_modelname = 'N_18_MM'
        pmos_modelname = 'P_18_MM'
        
        #build library
        lib_ss = SizesLibraryStrategy(feature_size, nmos_modelname,
                                      pmos_modelname, vdd)
        library = SizesLibrary(lib_ss)

        #choose main part
        if DS and not DSS and not DDS:
            part = library.dsViAmp1_VddGndPorts()
        elif not DS and DSS and not DDS:
            part = library.dsViAmp2_SingleEndedMiddle_VddGndPorts()
        elif not DS and not DSS and DDS:
            part = library.dsViAmp2_DifferentialMiddle_VddGndPorts()
        elif not DS and DSS and DDS:
            part = library.dsViAmp2_VddGndPorts()
        elif DS and DSS and DDS:
            part = library.dsViAmp_VddGndPorts()
        else:
            raise ValueError("this combo of DS/DSS/DSS not supported yet")

        #build embedded part
        # -dsViAmp1_VddGndPorts has ports: Vin1, Vin2, Iout, Vdd, gnd
        
        #the keys of 'connections' are the external ports of 'part'
        #the value corresponding to each key must be in the test_fixture_strings
        # that are below
        connections = {'Vin1':'ninp', 'Vin2':'ninn', 'Iout':'nout',
                       'Vdd':'ndd', 'gnd':'gnd'}

        functions = {}
        for varname in part.point_meta.keys():
            functions[varname] = None #these need to get set ind-by-ind
            
        embedded_part = EmbeddedPart(part, connections, functions)

        #we'll be building this up
        analyses = []

        #-------------------------------------------------------
        #shared info between analyses
        # (though any of this can be analysis-specific if we'd wanted
        #  to set them there instead)
        max_simulation_time = 5 #in seconds
        
        pwd = os.getenv('PWD')
        if pwd[-1] != '/':
            pwd += '/'
        cir_file_path = pwd + 'problems/miller2/'
        
        simulator_options_string = """
.include %ssimulator_options.inc
""" % cir_file_path
        
        models_string = """
.include %smodels.inc
""" % cir_file_path
        
        #-------------------------------------------------------
        #build dc analysis
        if False:
            pass

        #-------------------------------------------------------
        #build ac analysis
        if True:
            d = {'pCload':5e-12,
                 'pVdd':vdd,
                 'pVdcin':0.9,
                 'pVout':0.9,
                 'pRfb':1.000e+09,
                 'pCfb':1.000e-03}
            ac_env_points = [EnvPoint(True, d)]
            test_fixture_string = """
Cload	nout	gnd	pCload

* biasing circuitry

Vdd		ndd		gnd	DC=pVdd
Vss		gnd		0	DC=0
Vindc		ninpdc		gnd	DC=pVdcin
Vinac		ninpdc		ninp	AC=1 SIN(0 1 10k)

* feedback loop for dc biasing of output stage

Vout	nfbinn	gnd	pVout
Efb1	nfbin	gnd	nout	nfbinn	1.0e2
Rfb	nfbin	nfbout	pRfb
Cfb	nfbout	gnd	pCfb
Efb2	ninpdc	ninn_unlim	nfbout	gnd	1.0
Efb3	ninn	gnd	volts='MAX(0,MIN(1.8,V(ninn_unlim)))'

* this measures the amount of feedback biasing there is
EFBM fbmnode gnd volts='ABS(V(nfbout))'

* simulation statements

.op
.ac	dec	50	1.0e0	10.0e9

* pole-zero analysis
.pz v(nout) Vinac

* Frequency-domain measurements
.measure ac ampl       max vdb(nout) at=0
.measure ac inampl max vdb(ninp,ninn) at=0
.measure ac gain PARAM='ampl-inampl'
.measure ac phase FIND vp(nout) WHEN vdb(nout)=0 CROSS=1
.measure ac phasemargin PARAM='phase'
.measure ac GBW WHEN vdb(nout)=0 CROSS=1
.measure ac phase0 FIND vp(nout) at=1e5

.measure ac pole1 WHEN vp(nout)=135 CROSS=1
.measure ac pole2 WHEN vp(nout)=45 CROSS=1

* power measurement
EPWR1 pwrnode gnd volts='-pVdd*I(Vdd)'


"""
            #build list of metrics
            ac_metrics = [
                Metric('perc_DOCs_met', 0.9999, 1.0, False),
                Metric('gain', 20, float('Inf'), False),
                Metric('phasemargin', 65, 180, False),
                Metric('phase0', 160, 190, False),
                Metric('gbw', 1.0e6, float('Inf'), True), #OBJECTIVE
                Metric('pole1fr', 0.0, float('Inf'), False),
                Metric('pole2fr', 0.0, float('Inf'), False),
                Metric('pole2_margin', 1.0, float('Inf'), False),                
                Metric('pwrnode', float('-Inf'), 100.0e-3, True), #OBJECTIVE
                Metric('fbmnode', float('-Inf'), 50.0e-3, False)
                ]

            #if we use a .lis output like 'region' or 'vgs' even once in
            # order to constrain DOCs via perc_DOCs_met, list it here
            # (if you forget a measure, it _will_ complain)
            doc_measures = ['region'] 
            sim = Simulator(
                {
#                 'ma0':['gain','phasemargin','phase0','gbw','pole1','pole2'],
                'ma0':['gain','phasemargin','phase0','gbw'],
                'ic0':['pwrnode','fbmnode'],
                'lis':['perc_DOCs_met','pole1fr','pole2fr','pole2_margin']
                },
                cir_file_path,
                max_simulation_time,
                simulator_options_string,
                models_string,
                test_fixture_string,
                doc_measures)
            ac_an = CircuitAnalysis(ac_env_points, ac_metrics, sim)
            analyses.append(ac_an)
            
        #-------------------------------------------------------
        #add area analysis
        if DS and not (DSS or DDS):
            max_area = 3.0e-10
        else:
            max_area = 5.0e-10
            
        max_area = 1
        area_an = FunctionAnalysis(
            embedded_part.transistorArea,
            [EnvPoint(True)], float('-Inf'), max_area, False) #OBJECTIVE
        analyses.append(area_an)
        
        #-------------------------------------------------------
        #add function DOCs analysis
        funcDOCs_an = FunctionAnalysis(embedded_part.functionDOCsAreFeasible,
                                       [EnvPoint(True)],
                                       0.99, float('Inf'), False)
        analyses.append(funcDOCs_an)
        
        #-------------------------------------------------------
        #build transient analysis
        if False:
            tran_env_points = [EnvPoint(True)]
            test_fixture_string = """
*input waveform case 1
VIN0 n_vin0 n_vss PWL(0.0 0.65 1.0e-3 0.75)

VDD  n_vdd n_vss DC 1.8V
VGND n_vss 0 DC 0.0V

*for input waveform case 1 and case 2
*.tran tstep    tstop   <tstart> <tmaxstep>

*proper version: (101 points)
.tran  0.01e-3  1.0e-3  0.0      0.01e-3

*HACK to-be-fast version (21 points)
*.tran  0.05e-3  1.0e-3  0.0      0.05e-3

*what to print
.print tran V(n_vin0)
.print tran V(n_vout0)
"""
            #FIXME: add more metrics?
            tran_metrics = [Metric('slewrate',0.0,float('Inf'),False)]
            
            doc_measures = []
            output_file_num_vars = {'tr0':None} #FIXME
            output_file_start_line = {'tr0':None} #FIXME
            metric_calculators = {'slewrate':None} #FIXME
            sim = Simulator({'tr0':'slewrate'},
                            cir_file_path,
                            max_simulation_time,
                            simulator_options_string,
                            models_string,
                            test_fixture_string,
                            doc_measures,
                            output_file_num_vars,
                            output_file_start_line,
                            WAVEFORM_NUMBER_WIDTH,
                            metric_calculators)            
            tran_an = CircuitAnalysis(tran_env_points, tran_metrics, sim,
                                      'tran')
            analyses.append(tran_an)

        #-------------------------------------------------------
        #finally, build PS and return
        ps = ProblemSetup(embedded_part, analyses)
        return ps

    def OP_dsViAmp_Problem(self, DS, DSS, DDS):
        """
        @description        
          Amplifier problem, for double-ended input / single-ended output.
          Many goals, including slew rate, gain, power, area, ...
        
          Operating point driven
          
        @arguments        
          DS -- bool -- include 1-stage amp?
          DSS -- bool -- include 2-stage single-ended-middle amp?
          DDS -- bool -- include 2-stage differential-middle amp?
        
        @return
          ps -- ProblemSetup object
    
        @exceptions
          Need to include at least one of the stages.
        """
        #validate inputs
        if not (DS or DSS or DDS):
            raise ValueError('must include at least one of the choices')
        
        #settable parameters
        vdd = 1.8
        
        # -these values must be set based on what is set below!!
        feature_size = 0.18e-06
        nmos_modelname = 'N_18_MM'
        pmos_modelname = 'P_18_MM'
        
        #build library
        lib_ss = OpLibraryStrategy(feature_size, nmos_modelname,
                                   pmos_modelname, vdd, self.approxMosModels())
        library = OpLibrary(lib_ss)

        #choose main part
        if DS and not DSS and not DDS:
            part = library.dsViAmp1_VddGndPorts()
        elif not DS and DSS and not DDS:
            part = library.dsViAmp2_SingleEndedMiddle_VddGndPorts()
        elif not DS and not DSS and DDS:
            part = library.dsViAmp2_DifferentialMiddle_VddGndPorts()
        elif not DS and DSS and DDS:
            part = library.dsViAmp2_VddGndPorts()
#         elif DS and DSS and DDS:
        elif DS and DSS: # FIXME: DDS is not ready yet
            part = library.dsViAmp_VddGndPorts()
        else:
            raise ValueError("this combo of DS/DSS/DSS not supported yet")

        #build embedded part
        # -dsViAmp1_VddGndPorts has ports: Vin1, Vin2, Iout, Vdd, gnd
        
        #the keys of 'connections' are the external ports of 'part'
        #the value corresponding to each key must be in the test_fixture_strings
        # that are below
        connections = {'Vin1':'ninp', 'Vin2':'ninn', 'Iout':'nout',
                       'Vdd':'ndd', 'gnd':'gnd'}

        functions = {}
        for varname in part.point_meta.keys():
            functions[varname] = None #these need to get set ind-by-ind
            
        embedded_part = EmbeddedPart(part, connections, functions)

        #we'll be building this up
        analyses = []

        #-------------------------------------------------------
        #shared info between analyses
        # (though any of this can be analysis-specific if we'd wanted
        #  to set them there instead)        
        max_simulation_time = 5 #in seconds
        
        pwd = os.getenv('PWD')
        if pwd[-1] != '/':
            pwd += '/'
        cir_file_path = pwd + 'problems/miller2/'
        
        simulator_options_string = """
.include %ssimulator_options.inc
""" % cir_file_path
        
        models_string = """
.include %smodels.inc
""" % cir_file_path
        
        #-------------------------------------------------------
        #build dc analysis
        if False:
            pass

        #-------------------------------------------------------
        #build ac analysis
        if True:
            d = {'pCload':1e-12,
                 'pVdd':vdd,
                 'pVdcin':1.5,
                 'pVout':0.9,
                 'pRfb':1.000e+09,
                 'pCfb':1.000e-03,
                 'pTemp':25,
                 }
            ac_env_points = [EnvPoint(True, d)]
            test_fixture_string = """
Cload	nout	gnd	pCload

* biasing circuitry

Vdd		ndd		gnd	DC=pVdd
Vss		gnd		0	DC=0
Vindc		ninpdc		gnd	DC=pVdcin
Vinac		ninpdc		ninp	AC=1 SIN(0 1 10k)

* feedback loop for dc biasing of output stage

Vout	nfbinn	gnd	pVout
Efb1	nfbin	gnd	nout	nfbinn	1.0e2
Rfb	nfbin	nfbout	pRfb
Cfb	nfbout	gnd	pCfb

Efb2	ninpdc	ninn_unlim	nfbout	gnd	1.0
Efb3	ninn	gnd	volts='MAX(0,MIN(1.8,V(ninn_unlim)))'

* this measures the amount of feedback biasing there is
EFBM fbmnode gnd volts='ABS(V(nfbout))'

* simulation statements

.op
.ac	dec	50	1.0e0	10.0e9

* pole-zero analysis
.pz v(nout) Vinac

* Frequency-domain measurements
.measure ac ampl       max vdb(nout) at=0
.measure ac inampl max vdb(ninp,ninn) at=0
.measure ac gain PARAM='ampl-inampl'
.measure ac phase FIND vp(nout) WHEN vdb(nout)=0 CROSS=1
.measure ac phasemargin PARAM='phase'
.measure ac GBW WHEN vdb(nout)=0 CROSS=1
.measure ac phase0 FIND vp(nout) at=1e5

.measure ac pole1 WHEN vp(nout)=135 CROSS=1
.measure ac pole2 WHEN vp(nout)=45 CROSS=1

* power measurement
EPWR1 pwrnode gnd volts='-pVdd*I(Vdd)'


"""
            #build list of metrics
            ac_metrics = [
                Metric('perc_DOCs_met', 0.9999, 1.0, False),
                Metric('gain', 20, float('Inf'), True), #OBJECTIVE
                Metric('phasemargin', 65, 180, False),
                Metric('phase0', 160, 190, False),
                Metric('gbw', 1.0e6, float('Inf'), True), #OBJECTIVE
                Metric('pole1fr', 0.0, float('Inf'), False),
                Metric('pole2fr', 0.0, float('Inf'), False),
                Metric('pole2_margin', 1.0, float('Inf'), False),
                Metric('pwrnode', float('-Inf'), 100.0e-3, False),
                Metric('fbmnode', float('-Inf'), 50.0e-3, False)
                ]

            #if we use a .lis output like 'region' or 'vgs' even once in
            # order to constrain DOCs via perc_DOCs_met, list it here
            # (if you forget a measure, it _will_ complain)
            doc_measures = ['region'] 
            sim = Simulator(
                {
#                 'ma0':['gain','phasemargin','phase0','gbw','pole1','pole2'],
                'ma0':['gain','phasemargin','phase0','gbw'],
                'ic0':['pwrnode','fbmnode'],
                'lis':['perc_DOCs_met','pole1fr','pole2fr','pole2_margin']
                },
                cir_file_path,
                max_simulation_time,
                simulator_options_string,
                models_string,
                test_fixture_string,
                doc_measures)
            ac_an = CircuitAnalysis(ac_env_points, ac_metrics, sim)
            analyses.append(ac_an)
            
        #-------------------------------------------------------
        #add area analysis
        area_an = FunctionAnalysis(
            embedded_part.transistorArea, [EnvPoint(True)],
            float('-Inf'), 1, True) #OBJECTIVE
        analyses.append(area_an) 
        
        #-------------------------------------------------------
        #add function DOCs analysis
        funcDOCs_an = FunctionAnalysis(embedded_part.functionDOCsAreFeasible,
                                       [EnvPoint(True)],
                                       0.99, float('Inf'), False)
        analyses.append(funcDOCs_an)
        
        #-------------------------------------------------------
        #build transient analysis
        if False:
            tran_env_points = ac_env_points
            test_fixture_string = """
Cload	nout	gnd	pCload

* biasing circuitry

Vdd		ndd		gnd	DC=pVdd
Vss		gnd		0	DC=0
Vindc		ninpdc		gnd	DC=pVdcin
Vintran 	ninpdc 		ninp 	DC=0 PULSE(
+ -0.1 0.1 1NS 0 0 50NS 100NS)

* feedback loop for dc biasing of output stage

Vout	nfbinn	gnd	pVout
Efb1	nfbin	gnd	nout	nfbinn	1.0e2
Rfb	nfbin	nfbout	pRfb
Cfb	nfbout	gnd	pCfb
Efb2	ninpdc	ninn	nfbout	gnd	1.0

* simulation statements

.op
.tran 100p 500n

* Time-domain measurements
.param pRiseDelta=1
.measure tran time1 when V(nout)='pVout+0.5*pRiseDelta' CROSS=1
.measure tran time2 when V(nout)='pVout-0.5*pRiseDelta' CROSS=2
.measure tran time3 when V(nout)='pVout+0.5*pRiseDelta' CROSS=2
.measure tran time4 when V(nout)='pVout-0.5*pRiseDelta' CROSS=3
.measure tran 'srneg' param='pRiseDelta/(time4-time3)'
.measure tran 'srpos' param='pRiseDelta/(time1-time2)'

.measure tran outmax MAX v(nout)
.measure tran outmin MIN v(nout)

"""
            #FIXME: add more metrics?
            tran_metrics = [
                Metric('srneg',-1e6,float('Inf'),False),
                Metric('srpos',-1e6,float('Inf'),False),
                Metric('outmax',-10,float('Inf'),False),
                Metric('outmin',-10,float('Inf'),False),       
                ]
         
            doc_measures = []           
                                      
            sim = Simulator(
                {
                'ma0':['srneg','srpos','outmax','outmin'],
                },
                cir_file_path,
                max_simulation_time,
                simulator_options_string,
                models_string,
                test_fixture_string,
                doc_measures)
            tran_an = CircuitAnalysis(tran_env_points, tran_metrics, sim)
                                                  
            analyses.append(tran_an)

        #-------------------------------------------------------
        #finally, build PS and return
        ps = ProblemSetup(embedded_part, analyses)
        return ps
        
                
    def WL_ssViAmp1_Problem(self):
        """
        @description        
          Amplifier problem, for single ended input / single-ended output.
          Many goals, including slew rate, gain, power, area, ...
        
        @arguments
          <<none>>          
        
        @return
          ps -- ProblemSetup object
        """
        #settable parameters
        vdd = 1.8
        
        # -these values must be set based on what is set below!!
        feature_size = 0.18e-06
        nmos_modelname = 'N_18_MM'
        pmos_modelname = 'P_18_MM'
        
        #build library
        lib_ss = SizesLibraryStrategy(feature_size, nmos_modelname,
                                      pmos_modelname, vdd)
        library = SizesLibrary(lib_ss)
        
        #build embedded part
        # -ssViAmp1_VddGndPorts has ports: Vin, Iout, Vdd, gnd
        part = library.ssViAmp1_VddGndPorts()

        #the keys of 'connections' are the external ports of 'part'
        #the value corresponding to each key must be in the test_fixture_strings
        # that are below
        connections = {'Vin':'ninp', 'Iout':'nout',
                       'Vdd':'ndd', 'gnd':'gnd'}

        functions = {}
        for varname in part.point_meta.keys():
            functions[varname] = None #these need to get set ind-by-ind
            
        embedded_part = EmbeddedPart(part, connections, functions)

        #we'll be building this up
        analyses = []

        #-------------------------------------------------------
        #shared info between analyses
        # (though any of this can be analysis-specific if we'd wanted
        #  to set them there instead)
        pwd = os.getenv('PWD')
        if pwd[-1] != '/':
            pwd += '/'
        cir_file_path = pwd + 'problems/ssvi1/'
        max_simulation_time = 5 #in seconds
        simulator_options_string = """
.include %ssimulator_options.inc
""" % cir_file_path
        
        models_string = """
.include %smodels.inc
""" % cir_file_path

        #-------------------------------------------------------
        #build ac analysis
        if True:
            d = {
                 'pCload':5e-12,
                 'pVdd':vdd,
                 'pVdcin':0.9,
                 'pVout':0.9,
                 'pRfb':1.000e+09,
                 'pCfb':1.000e-03}
            ac_env_points = [EnvPoint(True, d)]
            test_fixture_string = """
Cload	nout	gnd	pCload

* biasing circuitry

Vdd		ndd		gnd	DC=pVdd
Vss		gnd		0	DC=0
Vindc		ninpdc		gnd	DC=pVdcin
Vinac		ninpdc		ninp1	AC=1
Vintran 	ninp1 		ninpx 	DC=0 PWL(
+ 0     0
+ 0.1n   -0.2
+ 10.0n  -0.2 
+ 10.1n  0.2 
+ 30.0n  0.2
+ 30.1n  -.2 )

* feedback loop for dc biasing 
Vout_ref	nvout_ref	gnd	pVout
Efb1	nfbin	gnd	nout	nvout_ref	1.0e2
Rfb	nfbin	nfbout	pRfb
Cfb	nfbout	gnd	pCfb
Efb2	n1	gnd	nfbout	gnd	1.0
Efb3	ninp_unlim	n1	ninpx	gnd	1.0
Efb4	ninp	gnd	volts='MAX(-1.8,MIN(1.8,V(ninp_unlim)))'

* this measures the amount of feedback biasing there is
EFBM fbmnode gnd volts='ABS(V(ninp)-V(ninpdc))'

* simulation statements

.op
*.DC TEMP 25 25 10
.ac	dec	50	1.0e0	10.0e9
* pole-zero analysis
.pz v(nout) Vinac

.probe ac V(nout)
.probe ac V(ninp)
.probe ac V(*)

*.tran 100p 50n
.probe tran V(nout)
.probe tran V(ninp)
.probe tran V(*)

* Frequency-domain measurements
.measure ac ampl       max vdb(nout) at=0
.measure ac inampl max vdb(ninp) at=0
.measure ac gain PARAM='ampl-inampl'
.measure ac phase FIND vp(nout) WHEN vdb(nout)=0 CROSS=1
.measure ac phasemargin PARAM='phase+180'
.measure ac GBW WHEN vdb(nout)=0 CROSS=1
.measure ac phase0 FIND vp(nout) at=1e5



* power measurement
EPWR1 pwrnode gnd volts='-pVdd*I(Vdd)'

"""
            ac_metrics = [
                          Metric('perc_DOCs_met', 0.9999, 1.0, False),
                          Metric('gain', 10, float('Inf'), True),
                          Metric('phase0', -10, 10, False),
                          Metric('phasemargin', 65, 180, False),
                          Metric('gbw', 10.0e6, float('Inf'), False),
                          Metric('pwrnode', float('-Inf'), 100.0e-3, True),
                          Metric('fbmnode', float('-Inf'), 50.0e-3, False),
                          ]
        
            #if we use a .lis output like 'region' or 'vgs' even once in
            # order to constrain DOCs via perc_DOCs_met, list it here
            # (if you forget a measure, it _will_ complain)
            doc_measures = ['region'] 
            sim = Simulator({'ma0':['gain','phase0','phasemargin','gbw'],
                             'ic0':['pwrnode','fbmnode'],
                             'lis':['perc_DOCs_met']},
                            cir_file_path,
                            max_simulation_time,
                            simulator_options_string,
                            models_string,
                            test_fixture_string,
                            doc_measures)
                            
            ac_an = CircuitAnalysis(ac_env_points, ac_metrics, sim)
            analyses.append(ac_an)
            
        #-------------------------------------------------------
        #add area analysis
#         area_an = FunctionAnalysis(embedded_part.transistorArea, [EnvPoint(True)],
#                                    float('-Inf'), 1, True)
#         analyses.append(area_an) 
#         
        #-------------------------------------------------------
        #add function DOCs analysis
        funcDOCs_an = FunctionAnalysis(embedded_part.functionDOCsAreFeasible,
                                       [EnvPoint(True)],
                                       0.99, float('Inf'), False)
        analyses.append(funcDOCs_an)
        
        #-------------------------------------------------------
        #finally, build PS and return
        ps = ProblemSetup(embedded_part, analyses)
        return ps
        
    def OP_ssViAmp1_Problem(self):
        """
        @description        
          Amplifier problem, for single ended input / single-ended output.
          Many goals, including slew rate, gain, power, area, ...
        
          Operating point driven
          
        @arguments
          <<none>>          
        
        @return
          ps -- ProblemSetup object
        """
        #settable parameters
        vdd = 1.8
        
        # -these values must be set based on what is set below!!
        feature_size = 0.18e-06
        nmos_modelname = 'N_18_MM'
        pmos_modelname = 'P_18_MM'
        
        #build library
        lib_ss = OpLibraryStrategy(feature_size, nmos_modelname,
                                   pmos_modelname, vdd, self.approxMosModels())
        library = OpLibrary(lib_ss)
        
        #build embedded part
        # -ssViAmp1_VddGndPorts has ports: Vin, Iout, Vdd, gnd
        part = library.ssViAmp1_VddGndPorts_Fixed()

        #the keys of 'connections' are the external ports of 'part'
        #the value corresponding to each key must be in the test_fixture_strings
        # that are below
        connections = {'Vin':'ninp', 'Iout':'nout',
                       'Vdd':'ndd', 'gnd':'gnd'}

        functions = {}
        for varname in part.point_meta.keys():
            functions[varname] = None #these need to get set ind-by-ind
            
        embedded_part = EmbeddedPart(part, connections, functions)

        #we'll be building this up
        analyses = []

        #-------------------------------------------------------
        #shared info between analyses
        # (though any of this can be analysis-specific if we'd wanted
        #  to set them there instead)
        pwd = os.getenv('PWD')
        if pwd[-1] != '/':
            pwd += '/'
        cir_file_path = pwd + 'problems/ssvi1/'
        max_simulation_time = 5 #in seconds
        simulator_options_string = """
.include %ssimulator_options.inc
""" % cir_file_path
        
        models_string = """
.include %smodels.inc
""" % cir_file_path

        #-------------------------------------------------------
        #build ac analysis
        if True:
            d = {
                 'pCload':5e-12,
                 'pVdd':vdd,
                 'pVdcin':0.9,
                 'pVout':0.9,
                 'pRfb':1.000e+09,
                 'pCfb':1.000e-03,
                 'pTemp':25,
                 }
            d2 = {
                 'pCload':5e-12,
                 'pVdd':vdd,
                 'pVdcin':0.9,
                 'pVout':0.9,
                 'pRfb':1.000e+09,
                 'pCfb':1.000e-03,
                 'pTemp':50,
                 }
            ac_env_points = [EnvPoint(True, d),EnvPoint(True, d2)]
            test_fixture_string = """
Cload	nout	gnd	pCload

* biasing circuitry

Vdd		ndd		gnd	DC=pVdd
Vss		gnd		0	DC=0
Vindc		ninpdc		gnd	DC=pVdcin
Vinac		ninpdc		ninp1	AC=1
Vintran 	ninp1 		ninpx 	DC=0 PWL(
+ 0     0
+ 0.1n   -0.2
+ 10.0n  -0.2 
+ 10.1n  0.2 
+ 30.0n  0.2
+ 30.1n  -.2 )

* feedback loop for dc biasing 
Vout_ref	nvout_ref	gnd	pVout
Efb1	nfbin	gnd	nout	nvout_ref	1.0e2
Rfb	nfbin	nfbout	pRfb
Cfb	nfbout	gnd	pCfb
Efb2	n1	gnd	nfbout	gnd	1.0
Efb3	ninp_unlim	n1	ninpx	gnd	1.0
Efb4	ninp	gnd	volts='MAX(0,MIN(pVdd,V(ninp_unlim)))'

* this measures the amount of feedback biasing there is
EFBM fbmnode gnd volts='ABS(V(ninp)-V(ninpdc))'

* simulation statements

.op

* temperature analysis
.temp pTemp

*.DC TEMP 25 25 10
.ac	dec	50	1.0e0	10.0e9
* pole-zero analysis
.pz v(nout) Vinac

.probe ac V(nout)
.probe ac V(ninp)
.probe ac V(*)

*.tran 100p 50n
.probe tran V(nout)
.probe tran V(ninp)
.probe tran V(*)

* Frequency-domain measurements
.measure ac ampl       max vdb(nout) at=0
.measure ac inampl max vdb(ninp) at=0
.measure ac gain PARAM='ampl-inampl'
.measure ac phase FIND vp(nout) WHEN vdb(nout)=0 CROSS=1
.measure ac phasemargin PARAM='phase+180'
.measure ac GBW WHEN vdb(nout)=0 CROSS=1
.measure ac phase0 FIND vp(nout) at=1e5

* power measurement
EPWR1 pwrnode gnd volts='-pVdd*I(Vdd)'

"""
            ac_metrics = [
                          Metric('perc_DOCs_met', 0.9999, 1.0, False),
                          Metric('gain', 10, float('Inf'), True),
                          Metric('phase0', -10, 10, False),
                          Metric('phasemargin', 65, 180, False),
                          Metric('gbw', 10.0e6, float('Inf'), False),
                          Metric('pwrnode', float('-Inf'), 100.0e-3, True),
                          Metric('fbmnode', float('-Inf'), 50.0e-3, False),
                          ]
   
            #if we use a .lis output like 'region' or 'vgs' even once in
            # order to constrain DOCs via perc_DOCs_met, list it here
            # (if you forget a measure, it _will_ complain)
            doc_measures = ['region'] 
            sim = Simulator({'ma0':['gain','phase0','phasemargin','gbw'],
                             'ic0':['pwrnode','fbmnode'],
                             'lis':['perc_DOCs_met']},
                            cir_file_path,
                            max_simulation_time,
                            simulator_options_string,
                            models_string,
                            test_fixture_string,
                            doc_measures)
                            
            ac_an = CircuitAnalysis(ac_env_points, ac_metrics, sim)
            analyses.append(ac_an)
        #-------------------------------------------------------
        #build transient analysis
        if True:
            tran_env_points = ac_env_points
            test_fixture_string = """
Cload	nout	gnd	pCload

* biasing circuitry

Vdd		ndd		gnd	DC=pVdd
Vss		gnd		0	DC=0
Vindc		ninpdc		gnd	DC=pVdcin
Vinac		ninpdc		ninp1	AC=1
Vintran 	ninp1 		ninpx 	DC=0 PWL(
+ 0     0
+ 0.01n   -0.2
+ 100.0n  -0.2 
+ 100.01n  0.2 
+ 200.0n  0.2
+ 200.01n  -.2 )

* feedback loop for dc biasing 
Vout_ref	nvout_ref	gnd	pVout
Efb1	nfbin	gnd	nout	nvout_ref	1.0e2
Rfb	nfbin	nfbout	pRfb
Cfb	nfbout	gnd	pCfb
Efb2	n1	gnd	nfbout	gnd	1.0
Efb3	ninp_unlim	n1	ninpx	gnd	1.0
Efb4	ninp	gnd	volts='MAX(0,MIN(pVdd,V(ninp_unlim)))'

* simulation statements

.op

* temperature analysis
.temp pTemp

.tran 100p 300n

.measure tran srneg deriv v(nout) when v(nout)='pVout*0.95' CROSS=3
.measure tran srpos deriv v(nout) when v(nout)='pVout*1.05' CROSS=1

.measure tran outmax find V(nout) at=199.9n 
.measure tran outmin find V(nout) at=99.9n

.measure tran 'outswing' param='outmax-outmin'

*.probe tran V(*)

"""
            #FIXME: add more metrics?
            tran_metrics = [
            # FIXME: measurements cannot have the same name accross
            #        different metrics
            #
            #        gives problems in Ind.py(201)setSimResults()
            #        because self.sim_results[metric_name][env_point.ID]
            #        is expected to be empty.
            
#                Metric('perc_DOCs_met', 0, 1.0, False), 
                Metric('srneg',-float('Inf'),0,False),
                Metric('srpos',0,float('Inf'),False),
                Metric('outmax',-10,10,False),
                Metric('outmin',-10,10,False),       
                Metric('outswing',1.0,float('Inf'),False),       
                ]
         
            doc_measures = []           
                                      
            sim = Simulator(
                {
                'mt0':['srneg','srpos','outmax','outmin','outswing'],
                #'lis':['perc_DOCs_met'],
                },
                cir_file_path,
                max_simulation_time,
                simulator_options_string,
                models_string,
                test_fixture_string,
                doc_measures)
            tran_an = CircuitAnalysis(tran_env_points, tran_metrics, sim)
                                                  
            analyses.append(tran_an)
                        
        #-------------------------------------------------------
        #add area analysis
#         area_an = FunctionAnalysis(embedded_part.transistorArea,
#                                    [EnvPoint(True)],
#                                    float('-Inf'), 1, True)
#         analyses.append(area_an) 
       
        #-------------------------------------------------------
        #add function DOCs analysis
        funcDOCs_an = FunctionAnalysis(embedded_part.functionDOCsAreFeasible,
                                       [EnvPoint(True)],
                                       0.99, float('Inf'), False)
        analyses.append(funcDOCs_an)
        
        #-------------------------------------------------------
        #finally, build PS and return
        ps = ProblemSetup(embedded_part, analyses)
        return ps

    def approxMosModels(self):
        """Returns an ApproxMosModels, currently hardcoded
        to look at 'miller2/nmos_results/nmos_results.*'
        """
        pwd = os.getenv('PWD')
        if pwd[-1] != '/':
            pwd += '/'
        file_path = pwd + 'problems/miller2/'
        nmos_basefile = file_path + 'nmos_data'
        pmos_basefile = file_path + 'pmos_data'
        return ApproxMosModels(nmos_basefile, pmos_basefile)


      
    def minimizeNmseToTargetWaveform(self,
                                     dc_sweep_start_voltage,
                                     dc_sweep_end_voltage,
                                     target_waveform):
        """
        @description        
          We are looking for a bunch of weak learners              
        
        @arguments
          dc_sweep_start_voltage -- float -- input start voltage
          dc_sweep_end_voltage -- float -- input end voltage
          target_waveform -- 1d array -- the target waveform
            desired.  Also specifies the number of values to use in the
            input dc sweep.
               
        @return
          ps -- ProblemSetup object
    
        @exceptions
          Need to include at least one of the stages.
        """
        
        #settable parameters
        vdd = 1.8
        
        # -these values must be set based on what is set below!!
        feature_size = 0.18e-06
        nmos_modelname = 'N_18_MM'
        pmos_modelname = 'P_18_MM'
        
        #build library
        lib_ss = SizesLibraryStrategy(feature_size, nmos_modelname,
                                      pmos_modelname, vdd)
        library = SizesLibrary(lib_ss)

        # part

        part = library.mos4()
           
        #build part
 
        #connections = part.unityPortMap()
        connections = {'G':'ninp', 'D':'nout',
                       'S':'ndd', 'B':'gnd'}
        functions = {}
        for varname in part.point_meta.keys():
            functions[varname] = None #these need to get set ind-by-ind
            
        embedded_part = EmbeddedPart(part, connections, functions)

        #we'll be building this up
        analyses = []

        #-------------------------------------------------------
        #shared info between analyses
        # (though any of this can be analysis-specific if we'd wanted
        #  to set them there instead)
        max_simulation_time = 1.5 #in seconds
        
        pwd = os.getenv('PWD')
        if pwd[-1] != '/':
            pwd += '/'
        cir_file_path = pwd + 'problems/try/'
        
        simulator_options_string = """
.include %ssimulator_options.inc
""" % cir_file_path
        
        models_string = """
.include %smodels.inc
""" % cir_file_path
        
        #-------------------------------------------------------
        #build dc analysis
        if True:
            d = {'pVdd':vdd,
		 'pVinac':0 
                 }
            dc_env_points = [EnvPoint(True, d)]

            step_voltage = (dc_sweep_end_voltage - dc_sweep_start_voltage) / \
                           float(len(target_waveform))
            
            test_fixture_string = """


* biasing circuitry
Vdd		ndd		gnd	DC=pVdd
Vindc		ninpdc		gnd	DC=5
Vinac		ninpdc		ninp	AC=pVinac

* simulation statements

.dc	Vindc	%f	%f	%f		

* output the voltage waveforms 'vinp' (input) and 'nout' (output)
.print dc V(ninp)
.print dc V(nout)

* DC output measurment
*.measure dc maxvout max V(nout) at=0
*.options POST=1 brief
""" % (dc_sweep_end_voltage, dc_sweep_start_voltage, step_voltage)
            
            calc_nmse = WaveformsToNmse(target_waveform, 1)
            metric_calculators = {'nmse':calc_nmse}
            
            #build list of metrics
            dc_metrics = [
                #'maxvout' is just for testing
                #Metric('maxvout', 0, 1.8, True),

                #"minimize nmse", with arbitrary feasibility threshold of 1000.0
                Metric('nmse', float('-Inf'), 1000.0, True),	    
               ]

            #for ninp, nout in .print commands
            output_file_num_vars = {'sw0':2} 

            #set this by: examine .sw0 file, and supply which line the numbers
            # start at.  Start counting at 0.
            # One output var => 4.
            # Two output vars => 5.
            # ...
            output_file_start_line = {'sw0':5}
            
            sim = Simulator(
                {
                #'ms0':['maxvout'],
                'sw0':['nmse'],
                },
                cir_file_path,
                max_simulation_time,
                simulator_options_string,
                models_string,
                test_fixture_string,
                [],
                output_file_num_vars,
                output_file_start_line,
                WAVEFORM_NUMBER_WIDTH,
                metric_calculators,
                )
            dc_an = CircuitAnalysis(dc_env_points, dc_metrics, sim)
            analyses.append(dc_an)
            
        #-----------------------	
            
        #-------------------------------------------------------
        #add area analysis

        #area_an = FunctionAnalysis(embedded_part.transistorArea,
        #                           [EnvPoint(True)],
        #                           float('-Inf'), 1, True)
        #analyses.append(area_an)
             
        #-------------------------------------------------------
        #finally, build PS and return
        ps = ProblemSetup(embedded_part, analyses)
        return ps
    	

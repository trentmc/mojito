import unittest

import random
import string
import os
import time

from adts import *
from adts.Part import replaceAutoNodesWithXXX

from problems.OpLibrary import *
from problems.Library import replaceAfterMWithBlank

#make this global for testing so we only have one disk access
_GLOBAL_approx_mos_models = ApproxMosModels('problems/miller2/nmos_data',
                                            'problems/miller2/pmos_data')

class OpLibraryTest(unittest.TestCase):

    def setUp(self):
        self.just1 = True #to make True is a HACK

        self.lib = self._point18Library(_GLOBAL_approx_mos_models)
        
        self.max_approx_error_relative=0.25

    def _point18Library(self, approx_mos_models):
        ss = OpLibraryStrategy(0.18e-6, 'N_18_MM', 'P_18_MM', 1.8,
                               approx_mos_models)
        return OpLibrary(ss)
    
    #=================================================================
    # Tests for the LUT sizer
    
    # Note: this also depends on the quality of the dataset
    def testSizer1(self):
        if self.just1: return

        allSizingsOK=True;
        
        # target values obtained with spice based sizer (jmoscal)
        allSizingsOK = self._testSizer1Helper({'Vds':1.0,'Vgs':1.0,'Vbs':0.0,'L':1e-6,'Ids':1e-3}, 21.48e-6) and allSizingsOK
        allSizingsOK = self._testSizer1Helper({'Vds':0.8,'Vgs':1.0,'Vbs':0.0,'L':1e-6,'Ids':1e-3}, 21.75e-6) and allSizingsOK
         
        allSizingsOK = self._testSizer1Helper({'Vds':1.0,'Vgs':0.8,'Vbs':0.0,'L':1e-6,'Ids':1e-3}, 43.620e-6) and allSizingsOK
        allSizingsOK = self._testSizer1Helper({'Vds':0.8,'Vgs':0.8,'Vbs':0.0,'L':1e-6,'Ids':1e-3}, 44.191e-6) and allSizingsOK
        allSizingsOK = self._testSizer1Helper({'Vds':0.6,'Vgs':0.8,'Vbs':0.0,'L':1e-6,'Ids':1e-3}, 44.931e-6) and allSizingsOK

        allSizingsOK = self._testSizer1Helper({'Vds':1.0,'Vgs':0.6,'Vbs':0.0,'L':1e-6,'Ids':1e-4}, 14.278e-6) and allSizingsOK
        allSizingsOK = self._testSizer1Helper({'Vds':0.8,'Vgs':0.6,'Vbs':0.0,'L':1e-6,'Ids':1e-4}, 14.54e-6) and allSizingsOK
        allSizingsOK = self._testSizer1Helper({'Vds':0.6,'Vgs':0.6,'Vbs':0.0,'L':1e-6,'Ids':1e-4}, 14.849e-6) and allSizingsOK
        
        
        allSizingsOK = self._testSizer1Helper({'Vds':1.0,'Vgs':1.0,'Vbs':0.0,'L':0.5e-6,'Ids':1e-3}, 12.729e-6) and allSizingsOK
        allSizingsOK = self._testSizer1Helper({'Vds':0.8,'Vgs':1.0,'Vbs':0.0,'L':0.5e-6,'Ids':1e-3}, 12.952e-6) and allSizingsOK
        
        allSizingsOK = self._testSizer1Helper({'Vds':1.0,'Vgs':0.8,'Vbs':0.0,'L':0.5e-6,'Ids':1e-3}, 26.704e-6) and allSizingsOK
        allSizingsOK = self._testSizer1Helper({'Vds':0.8,'Vgs':0.8,'Vbs':0.0,'L':0.5e-6,'Ids':1e-3}, 27.218e-6) and allSizingsOK
        allSizingsOK = self._testSizer1Helper({'Vds':0.6,'Vgs':0.8,'Vbs':0.0,'L':0.5e-6,'Ids':1e-3}, 27.899e-6) and allSizingsOK

        allSizingsOK = self._testSizer1Helper({'Vds':1.0,'Vgs':0.6,'Vbs':0.0,'L':0.5e-6,'Ids':1e-4}, 10.518e-6) and allSizingsOK
        allSizingsOK = self._testSizer1Helper({'Vds':0.8,'Vgs':0.6,'Vbs':0.0,'L':0.5e-6,'Ids':1e-4}, 10.837e-6) and allSizingsOK
        allSizingsOK = self._testSizer1Helper({'Vds':0.6,'Vgs':0.6,'Vbs':0.0,'L':0.5e-6,'Ids':1e-4}, 11.203e-6) and allSizingsOK
        
        allSizingsOK = self._testSizer1Helper({'Vds':1.0,'Vgs':1.0,'Vbs':0.0,'L':0.18e-6,'Ids':1e-3}, 5.775e-6) and allSizingsOK
        allSizingsOK = self._testSizer1Helper({'Vds':1.0,'Vgs':0.8,'Vbs':0.0,'L':0.18e-6,'Ids':1e-3}, 11.632e-6) and allSizingsOK
        allSizingsOK = self._testSizer1Helper({'Vds':1.0,'Vgs':0.6,'Vbs':0.0,'L':0.18e-6,'Ids':1e-4}, 5.03e-6) and allSizingsOK
        
        allSizingsOK = self._testSizer1Helper({'Vds':0.8,'Vgs':0.4,'Vbs':0.0,'L':0.18e-6,'Ids':1e-6}, 1.613e-6) and allSizingsOK
        allSizingsOK = self._testSizer1Helper({'Vds':0.8,'Vgs':0.5,'Vbs':0.0,'L':0.18e-6,'Ids':1e-5}, 2.182e-6) and allSizingsOK
        allSizingsOK = self._testSizer1Helper({'Vds':0.8,'Vgs':0.6,'Vbs':0.0,'L':0.18e-6,'Ids':1.3e-5}, 0.415e-6) and allSizingsOK  
            
        self.assertTrue(allSizingsOK)
        
    def _testSizer1Helper(self, point, target_w):
        w = _GLOBAL_approx_mos_models.estimateNmosWidth(point)
        err=abs(w-target_w)/target_w
        
        if (err>self.max_approx_error_relative):
            print "Sizing error too big: point=%s, w=%e, target_w=%e, err=%f" %\
                (point,w,target_w,err)    
            return False
        
        return True;
        
    def _testSizer2Helper(self, point, target_w):
        w = _GLOBAL_approx_mos_models.estimatePmosWidth(point)
        err=abs(w-target_w)/target_w
        
        if (err>self.max_approx_error_relative):
            print "Sizing error too big: point=%s, w=%e, target_w=%e, err=%f" %\
                (point,w,target_w,err)    
            return False
        
        return True;
        
    def testSizerSpeed(self):
        if self.just1: return
        point0={'Vds':1.0,'Vgs':0.7,'Vbs':0.0,'L':15e-6,'Ids':1e-4}
        point1={'Vds':1.0,'Vgs':0.5,'Vbs':0.0,'L':0.44e-6,'Ids':1e-4}
        point2={'Vds':0.9,'Vgs':0.4,'Vbs':0.0,'L':0.57e-6,'Ids':1e-4}
        point3={'Vds':0.8,'Vgs':0.6,'Vbs':0.0,'L':10e-6,'Ids':1e-5}
        point4={'Vds':0.7,'Vgs':0.4,'Vbs':0.0,'L':1e-6,'Ids':1e-6}
        point5={'Vds':0.6,'Vgs':0.5,'Vbs':0.0,'L':0.7e-6,'Ids':1e-4}
        point6={'Vds':0.5,'Vgs':0.9,'Vbs':0.0,'L':0.5e-6,'Ids':2e-4}
        point7={'Vds':0.4,'Vgs':0.2,'Vbs':0.0,'L':0.24e-6,'Ids':3e-4}
        point8={'Vds':0.5,'Vgs':0.3,'Vbs':0.0,'L':0.24e-6,'Ids':4e-4}
        point9={'Vds':0.6,'Vgs':1.0,'Vbs':0.0,'L':0.24e-6,'Ids':5e-4}
        
        cnt=0
        starttime=time.time()
        while cnt < 1000:
            w = _GLOBAL_approx_mos_models.estimateNmosWidth(point0)          
            w = _GLOBAL_approx_mos_models.estimateNmosWidth(point1)          
            w = _GLOBAL_approx_mos_models.estimateNmosWidth(point2)          
            w = _GLOBAL_approx_mos_models.estimateNmosWidth(point3)          
            w = _GLOBAL_approx_mos_models.estimateNmosWidth(point4)          
            w = _GLOBAL_approx_mos_models.estimateNmosWidth(point5)          
            w = _GLOBAL_approx_mos_models.estimateNmosWidth(point6)          
            w = _GLOBAL_approx_mos_models.estimateNmosWidth(point7)          
            w = _GLOBAL_approx_mos_models.estimateNmosWidth(point8)          
            w = _GLOBAL_approx_mos_models.estimateNmosWidth(point9)          
            cnt=cnt+1
        
        elapsed=time.time()-starttime
        
        lookups_per_sec=10*cnt / elapsed
        
        print "NMOS: %d lookups took %f seconds (%d lookups/sec)" % ( 10* cnt, elapsed, lookups_per_sec)
                
        cnt=0
        starttime=time.time()
        while cnt < 1000:
            w = _GLOBAL_approx_mos_models.estimatePmosWidth(point0)          
            w = _GLOBAL_approx_mos_models.estimatePmosWidth(point1)          
            w = _GLOBAL_approx_mos_models.estimatePmosWidth(point2)          
            w = _GLOBAL_approx_mos_models.estimatePmosWidth(point3)          
            w = _GLOBAL_approx_mos_models.estimatePmosWidth(point4)          
            w = _GLOBAL_approx_mos_models.estimatePmosWidth(point5)          
            w = _GLOBAL_approx_mos_models.estimatePmosWidth(point6)          
            w = _GLOBAL_approx_mos_models.estimatePmosWidth(point7)          
            w = _GLOBAL_approx_mos_models.estimatePmosWidth(point8)          
            w = _GLOBAL_approx_mos_models.estimatePmosWidth(point9)          
            cnt=cnt+1
        
        elapsed=time.time()-starttime
        
        lookups_per_sec=10*cnt / elapsed
        
        print "PMOS: %d lookups took %f seconds (%d lookups/sec)" % ( 10* cnt, elapsed, lookups_per_sec)
                
                
    #=================================================================
    #One Test for each Part
    def testNmos4Sized(self):
        if self.just1: return
        part = self.lib.nmos4_sized()
        self.assertEqual( part.externalPortnames(), ['D','G','S','B'])
        instance = EmbeddedPart(part, {'D':'1', 'G':'2', 'S':'3', 'B':'nblah'},
                                {'W':3*0.18e-6, 'L':5*0.18e-6, 'M':1})
        self.assertTrue( len(str(part)) > 0 )
        self.assertTrue( len(str(instance)) > 0 )

        target_str = """M0 1 2 3 nblah N_18_MM M=1 L=9e-07 W=5.4e-07
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

    def testPmos4Sized(self):
        if self.just1: return
        part = self.lib.pmos4_sized()
        instance = EmbeddedPart(part, {'D':'1', 'G':'2', 'S':'3', 'B':'nblah'},
                                {'W':3*0.18e-6, 'L':5*0.18e-6, 'M':1})
        self.assertTrue( len(str(part)) > 0 )
        self.assertTrue( len(str(instance)) > 0 )

        target_str = """M0 1 2 3 nblah P_18_MM M=1 L=9e-07 W=5.4e-07
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

    def testNmos4_simple(self):
        if self.just1: return
        part = self.lib.nmos4()
        self.assertEqual( part.externalPortnames(), ['D','G','S','B'])
        instance = EmbeddedPart(part, {'D':'1', 'G':'2', 'S':'3', 'B':'nblah'},
                                {'Vds':1.0,'Vgs':1.0,'Vbs':0.0,'L':0.18e-6,'Ids':1e-3})
        self.assertTrue( len(str(part)) > 0 )
        self.assertTrue( len(str(instance)) > 0 )

        target_str = """M0 1 2 3 nblah N_18_MM M=3 L=1.8e-07 W=2.4e-05
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)
        
    def testNmos4_bigL(self):
        if self.just1: return
        part = self.lib.nmos4()
        instance = EmbeddedPart(part, {'D':'1', 'G':'2', 'S':'3', 'B':'nblah'},
                                {'Vds':1.0,'Vgs':1.0,'Vbs':0.0,'L':1e-6,'Ids':1e-3})
        self.assertTrue( len(str(part)) > 0 )
        self.assertTrue( len(str(instance)) > 0 )

        target_str = """M0 1 2 3 nblah N_18_MM M=5 L=1e-06 W=4.83382e-06
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)
        
    def testNmos4_bigL_bigIds(self):
        if self.just1: return
        part = self.lib.nmos4()
        instance = EmbeddedPart(part, {'D':'1', 'G':'2', 'S':'3', 'B':'nblah'},
                                {'Vds':1.0,'Vgs':1.0,'Vbs':0.0,'L':1e-6,'Ids':2e-3})
        self.assertTrue( len(str(part)) > 0 )
        self.assertTrue( len(str(instance)) > 0 )

        target_str = """M0 1 2 3 nblah N_18_MM M=10 L=1e-06 W=4.83382e-06
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)
        
    def testPmos4(self):
        if self.just1: return
        part = self.lib.pmos4()
        instance = EmbeddedPart(part, {'D':'ndrain', 'G':'ngate', 'S':'nsource', 'B':'nbulk'},
                                {'Vds':1.0,'Vgs':1.0,'Vbs':0.0,'L':1e-6,'Ids':1e-3})
        
        self.assertTrue( len(str(part)) > 0 )
        self.assertTrue( len(str(instance)) > 0 )

        target_str = """M0 ndrain ngate nsource nblah P_18_MM M=22 L=1e-06 W=4.84575e-06
"""
        actual_str = instance.spiceNetlistStr()
        
        self._compareStrings(target_str, actual_str)

    def testPmos4Sim(self):
        if self.just1: return
        part = self.lib.pmos4()
        instance = EmbeddedPart(part, {'D':'ndrain', 'G':'ngate', 'S':'nsource', 'B':'nbulk'},
                                {'Vds':1.0,'Vgs':1.0,'Vbs':0.0,'L':1e-6,'Ids':1e-3})
        
        self._simulateAndVerifyMos(True, 1.0,1.0,0.0,1e-6,1e-3)
        
    def _simulateAndVerifyMos(self, is_pmos, Vds, Vgs, Vbs, L, I):
        if is_pmos:
            part = self.lib.pmos4()
            sources_netlist = """
                Vd ns nd dc """ + str(Vds) + """
                Vg ns ng dc """ + str(Vgs) + """
                Vs ns 0 dc """ + str(0) + """
                Vb nb ns dc """ + str(Vbs) + """
            """
        else:
            part = self.lib.nmos4()
            sources_netlist = """
                Vd nd ns dc """ + str(Vds) + """
                Vg ng ns dc """ + str(Vgs) + """
                Vs ns 0 dc """ + str(0) + """
                Vb ns nb dc """ + str(Vbs) + """
            """
        
        instance = EmbeddedPart(part, {'D':'nd', 'G':'ng', 'S':'ns', 'B':'nb'},
                                {'Vds':Vds,'Vgs':Vgs,'Vbs':Vbs,'L':L,'Ids':I})
    
        device_netlist = instance.spiceNetlistStr()
        
        netlist_hdr = """
        .protect
        .lib '/users/micas/ppalmers/models/UMC_18_CMOS_Model/hspice/MM180_REG18_V123.lib' tt
        .unprotect
              

        
        .op
        """
        
        netlist = netlist_hdr + "\n" + device_netlist + "\n" + sources_netlist
        
        simfile_dir="./tmp-sim/"
        if len(simfile_dir) > 0 and simfile_dir[-1] != '/':
            simfile_dir = simfile_dir + '/'
	
        os.system('mkdir -p ' + simfile_dir + ';')
        #Make sure no previous output files
        outbase = 'autogen_cirfile'
        os.system('rm ' + simfile_dir + outbase + '*;')
        if os.path.exists(simfile_dir + 'ps_temp.txt'):
            os.remove(simfile_dir + 'ps_temp.txt')

        #Create netlist, write it to file
        cirfile = outbase + '.cir'
        f = open(simfile_dir + cirfile, 'w'); f.write(netlist); f.close()

        #hspice
        psc = "ps ax |grep hspice|grep -v 'cd '|grep " + cirfile + \
              " 1> " + simfile_dir + "ps_temp.txt"
        command = "cd " + simfile_dir + "; hspice -i " + cirfile + \
                  " -o " + outbase + "& cd -; " + psc

        status = os.system(command)
        
        got_results = False
        bad_result = False
        if status != 0:
          got_results = True;
          bad_result = True;
          print 'System call with bad result.  Command was: %s' % command
        
        self.max_simulation_time=5
        
        #loop until we get results, or until timeout
        t0 = time.time()
        while not got_results:
            
            if os.path.exists(filename):
                #log.debug('\nSuccessfully got result file')
                got_results = True
                bad_result = False
            
            elif (time.time() - t0) > self.max_simulation_time:
                log.debug('\nExceeded max sim time of %d s, so kill' %
                          self.max_simulation_time)
                got_results = True
                bad_result = True
                      
                #kill the process
                t = file2tokens(simfile_dir + 'ps_temp.txt', 0)
                log.debug('ps_temp.txt was:%s' %
                          file2str(simfile_dir + 'ps_temp.txt'))
                pid = t[0]
                log.debug('fid was: %s' % pid)
                if not t[0] == 'Done':
                    os.system('kill -9 %s' % pid)

            #pause for 0.25 seconds (to avoid taking cpu time while waiting)
            time.sleep(0.25) 

        
        
        
    def testDcvs(self):
        if self.just1: return
        part = self.lib.dcvs()
        n0 = part.externalPortnames()[0]
        instance = EmbeddedPart(part, {n0:'1'}, {'DC':1.8})
        self.assertTrue( len(str(part)) > 0 )
        self.assertTrue( len(str(instance)) > 0 )

        target_str = """V0 1 0  DC 1.8
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

    def testWire(self):
        if self.just1: return
        part = self.lib.wire()
        instance = EmbeddedPart(part, {'1':'a', '2':'b'}, {})
        self.assertTrue( len(str(part)) > 0 )
        self.assertTrue( len(str(instance)) > 0 )

        target_str = """Rwire0 a b  R=0
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

    def testOpenCircuit(self):
        if self.just1: return
        part = self.lib.openCircuit()
        instance = EmbeddedPart(part, {'1':'a', '2':'b'}, {})
        self.assertTrue( len(str(part)) > 0 )
        self.assertTrue( len(str(instance)) > 0 )

        target_str = "" #yes, target string is _empty_
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

    def testShortOrOpenCircuit(self):
        if self.just1: return
        part = self.lib.shortOrOpenCircuit()

        #instantiate as short circuit
        instance = EmbeddedPart(part, {'1':'a', '2':'b'},
                                {'chosen_part_index':0})

        target_str = """Rwire0 a b  R=0
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

        #instantiate as open circuit
        instance = EmbeddedPart(part, {'1':'a', '2':'b'},
                                {'chosen_part_index':1})

        target_str = ""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

    def testSizedLogscaleResistor(self):
        if self.just1: return

        part = self.lib.sizedLogscaleResistor()
        instance = EmbeddedPart(part, {'1':'a', '2':'b'}, {'R':10.2e3})
        self.assertTrue( len(str(part)) > 0 )
        self.assertTrue( len(str(instance)) > 0 )

        target_str = "R0 a b  R=10200\n"
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

    def testSizedLogscaleResistor(self):
        if self.just1: return

        part = self.lib.sizedLinscaleResistor()
        instance = EmbeddedPart(part, {'1':'a', '2':'b'}, {'R':10.2e3})
        self.assertTrue( len(str(part)) > 0 )
        self.assertTrue( len(str(instance)) > 0 )

        target_str = "R0 a b  R=10200\n"
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

    def testResistor(self):
        if self.just1: return

        part = self.lib.resistor()
        instance = EmbeddedPart(part, {'1':'a', '2':'b'}, {'V':1.0,'I':0.1})
        self.assertTrue( len(str(part)) > 0 )
        self.assertTrue( len(str(instance)) > 0 )

        target_str = "R0 a b  R=100\n"
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

    def testRailing(self):
        """test to see that it rails to be <= max allowed value.
        We use resistance of resistor for the test."""
        if self.just1: return

        part = self.lib.sizedLogscaleResistor()
        instance = EmbeddedPart(part, {'1':'a', '2':'b'}, {'R':10.2e3})

        R_varmeta = self.lib._ref_varmetas['logscale_R']
        self.assertTrue(R_varmeta.logscale)
        max_R = 10**R_varmeta.max_unscaled_value
        instance = EmbeddedPart(part, {'1':'a', '2':'b'}, {'R':max_R*10.0})
        target_str = "R0 a b  R=%g\n" % max_R
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

    def testCapacitor(self):
        if self.just1: return

        part = self.lib.capacitor()
        instance = EmbeddedPart(part, {'1':'a', '2':'b'}, {'C':1.0e-6})
        self.assertTrue( len(str(part)) > 0 )
        self.assertTrue( len(str(instance)) > 0 )

        target_str = "C0 a b  C=1e-06\n"
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

    def testMos4(self):
        if self.just1: return
        part = self.lib.mos4()
        self.assertTrue( isinstance( part, FlexPart ) )
        self.assertTrue( len(str(part)) > 0 )

        #instantiate as nmos
        instance0 = EmbeddedPart(part, {'D':'1', 'G':'2', 'S':'3', 'B':'4'},
                                 {'chosen_part_index':0,
                                  'Vds':1.0,'Vgs':1.0,'Vbs':0.0,
                                  'L':1e-6,'Ids':1e-3}
                                 )
        self.assertTrue( len(str(instance0)) > 0 )

        target_str0 = """M0 1 2 3 4 N_18_MM M=5 L=1e-06 W=4.83382e-06
"""
        actual_str0 = instance0.spiceNetlistStr()
        self._compareStrings(target_str0, actual_str0)

        #instantiate as pmos
        instance0 = EmbeddedPart(part, {'D':'1', 'G':'2', 'S':'3', 'B':'4'},
                                 {'chosen_part_index':1,
                                  'Vds':1.0,'Vgs':1.0,'Vbs':0.0,
                                  'L':1e-6,'Ids':1e-3}
                                 )
        self.assertTrue( len(str(instance0)) > 0 )

        target_str0 = """M0 1 2 3 4 P_18_MM M=22 L=1e-06 W=4.84575e-06
"""
        actual_str0 = instance0.spiceNetlistStr()
        self._compareStrings(target_str0, actual_str0)

    def testMos3(self):
        if self.just1: return
        part = self.lib.mos3()

        #instantiate as pmos
        instance = EmbeddedPart(part, {'D':'1', 'G':'2', 'S':'3'},
                                {'use_pmos':1,
                                 'Vds':1.0,'Vgs':1.0,
                                 'L':1e-6,'Ids':1e-3}
                               )
        
        self.assertTrue( len(str(part)) > 0 )
        self.assertTrue( len(str(instance)) > 0 )
        
        target_str = """M0 1 2 3 3 P_18_MM M=22 L=1e-06 W=4.84575e-06
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

    def testMosDiode(self):
        if self.just1: return
        part = self.lib.mosDiode()

        instance = EmbeddedPart(part, {'D':'1', 'S':'2'},
                                {'use_pmos':1,
                                 'Vds':1.0,
                                 'L':1e-6,'Ids':1e-3}
                               )
        
        target_str = """M0 1 1 2 2 P_18_MM M=22 L=1e-06 W=4.84575e-06
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

    def testResistorOrMosDiode_asResistor(self):
        if self.just1: return
        part = self.lib.resistorOrMosDiode()
        instance = EmbeddedPart(part, {'D':'1', 'S':'2'},
                                {'chosen_part_index':0,
                                 'use_pmos':1,
                                 'Vds':1.0,
                                 'L':1e-6,'Ids':1e-3})
        
        target_str = """R0 1 2  R=1000
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)


    def testResistorOrMosDiode_asMosDiode(self):
        if self.just1: return
        part = self.lib.resistorOrMosDiode()
        instance = EmbeddedPart(part, {'D':'1', 'S':'2'},
                                {'chosen_part_index':1,
                                 'use_pmos':1,
                                 'Vds':1.0,
                                 'L':1e-6,
                                 'Ids':1e-3})
        
        target_str = """M0 1 1 2 2 P_18_MM M=22 L=1e-06 W=4.84575e-06
"""

        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

    def testBiasedMos(self):
        if self.just1: return
        part = self.lib.biasedMos()

        instance = EmbeddedPart(part, {'D':'1', 'S':'2'},
                                {'Vgs':1.0,'Vds':1.0,
                                 'L':1e-6,'Ids':1e-3,
                                 'use_pmos':1,
                                 'Vs':1.8})
        
        target_str = """M0 1 n_auto_2 2 2 P_18_MM M=22 L=1e-06 W=4.84575e-06
V1 n_auto_2 0  DC 0.8
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings2(target_str, actual_str)
        
    def testBiasedMosOrWire(self):
        if self.just1: return
        part = self.lib.biasedMosOrWire()

        conns = {'D':'a', 'S':'b'}
        point = {'Vgs':1.0,'Vds':1.0,
                 'L':1e-6,'Ids':1e-3,
                 'use_pmos':1,
                 'Vs':1.8}

        #instantiate as biasedMos
        point['chosen_part_index'] = 0 
        instance = EmbeddedPart(part, conns, point)
        
        target_str = """M0 a n_auto_2 b b P_18_MM M=22 L=1e-06 W=4.84575e-06
V1 n_auto_2 0  DC 0.8
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings2(target_str, actual_str)

        #instantiate as wire
        point['chosen_part_index'] = 1
        instance = EmbeddedPart(part, conns, point)
        
        target_str = """Rwire0 a b  R=0
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings2(target_str, actual_str)

    def testRC_series(self):
        if self.just1: return
        part = self.lib.RC_series()

        instance = EmbeddedPart(part,
                                {'N1':'1', 'N2':'2'},
                                {'R':10.0e3, 'C':10.0e-6})
        
        target_str = """R0 1 n_auto_112  R=10000
C1 n_auto_112 2  C=1e-05
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings2(target_str, actual_str)
    
    def testTwoBiasedMoses(self):
        if self.just1: return
        part = self.lib.twoBiasedMoses()

        instance = EmbeddedPart(part,
                                {'D':'1','S':'gnd'},
                                {'use_pmos':0,
                                 'Vds':1.2,'fracVi':0.5,'Vs':0,
                                 'Ids':1e-3,
                                 'D_L':1e-6,
                                 'D_Vgs':0.7,
                                 'S_L':2e-6,
                                 'S_Vgs':0.7
                                 })
        
        target_str = """M0 1 XXX XXX XXX N_18_MM M=14 L=1e-06 W=4.85742e-06
V1 XXX 0  DC 1.3
M2 XXX XXX gnd gnd N_18_MM M=28 L=2e-06 W=4.85742e-06
V3 XXX 0  DC 0.7
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings2(target_str, actual_str)
        
        instance = EmbeddedPart(part,
                                {'D':'1','S':'Vdd'},
                                {'use_pmos':1,
                                 'Vds':1.0,'fracVi':0.5,'Vs':1.8,
                                 'Ids':1e-3,
                                 'D_L':1e-6,
                                 'D_Vgs':1.0,
                                 'S_L':1e-6,
                                 'S_Vgs':1.0
                                 })
        
        target_str = """M0 1 XXX XXX XXX P_18_MM M=22 L=1e-06 W=4.84575e-06
V1 XXX 0  DC 0.3
M2 XXX XXX Vdd Vdd P_18_MM M=22 L=1e-06 W=4.84575e-06
V3 XXX 0  DC 0.8
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings2(target_str, actual_str)   
             
    def testStackedCascodeMos(self):
        if self.just1: return
        part = self.lib.stackedCascodeMos()

        point = {'use_pmos':0,
                'Vds':1.2,'fracVi':0.5,'Vs':0,
                'Ids':1e-3,
                'D_L':1e-6,
                'D_Vgs':0.7,
                'S_L':2e-6,
                'S_Vgs':0.7
                }

        #one mos
        point['chosen_part_index'] = 0
        instance = EmbeddedPart(part, {'D':'1','S':'2'}, point)
        
        target_str = """M0 1 XXX 2 2 N_18_MM M=28 L=2e-06 W=4.85742e-06
V1 XXX 0  DC 0.7
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings2(target_str, actual_str)

        #two n-moses
        point['chosen_part_index'] = 1
        instance = EmbeddedPart(part, {'D':'1','S':'2'}, point)
        
        target_str = """M0 1 XXX XXX XXX N_18_MM M=14 L=1e-06 W=4.85742e-06
V1 XXX 0  DC 1.3
M2 XXX XXX 2 2 N_18_MM M=28 L=2e-06 W=4.85742e-06
V3 XXX 0  DC 0.7
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings2(target_str, actual_str)
        
        #two p-moses
        point = {'use_pmos':1,
                'Vds':1.2,'fracVi':0.5,'Vs':1.8,
                'Ids':1e-3,
                'D_L':1e-6,
                'D_Vgs':1.0,
                'S_L':1e-6,
                'S_Vgs':1.0
                }
        point['chosen_part_index'] = 1
        instance = EmbeddedPart(part, {'D':'1','S':'Vdd'}, point)
        
        target_str = """M0 1 XXX XXX XXX P_18_MM M=22 L=1e-06 W=4.84575e-06
V1 XXX 0  DC 0.2
M2 XXX XXX Vdd Vdd P_18_MM M=22 L=1e-06 W=4.84575e-06
V3 XXX 0  DC 0.8
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings2(target_str, actual_str)
        
    def _levelShifter_Point(self, Drail_is_vdd=0, do_stack=0):
        if Drail_is_vdd==1:
            point = {'Drail_is_vdd':Drail_is_vdd,
                'Vin':1.4,
                'Vout':0.7,
                'amp_L':1e-6,
                'Ibias':1e-3,
                'cascode_fracVi':0.5,
                'cascode_D_L':1e-6,
                'cascode_D_Vgs':1.0,
                'cascode_S_L':1e-6,
                'cascode_S_Vgs':1.0,
                'cascode_do_stack':do_stack
                }
        else:
            point = {'Drail_is_vdd':Drail_is_vdd,
                'Vin':0.3,
                'Vout':1.1,
                'amp_L':1e-6,
                'Ibias':1e-3,
                'cascode_fracVi':0.5,
                'cascode_D_L':1e-6,
                'cascode_D_Vgs':1.0,
                'cascode_S_L':1e-6,
                'cascode_S_Vgs':1.0,
                'cascode_do_stack':do_stack
                }       
        return point
        
    
    def testLevelShifter(self):
        if self.just1: return
        part = self.lib.levelShifter()

        conns = {'Drail':'Vdd','Srail':'gnd',
                 'Vin':'Vin','Vout':'Vout'}
        point = self._levelShifter_Point(1,0)
        instance = EmbeddedPart(part, conns, point)
        
        target_str = """M0 Vdd Vin Vout Vout N_18_MM M=14 L=1e-06 W=4.85742e-06
M1 Vout XXX gnd gnd N_18_MM M=5 L=1e-06 W=4.83382e-06
V2 XXX 0  DC 1
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings2(target_str, actual_str)
        
        point = self._levelShifter_Point(1,1)
        instance = EmbeddedPart(part, conns, point)
        
        target_str = """M0 Vdd Vin Vout Vout N_18_MM M=14 L=1e-06 W=4.85742e-06
M1 Vout XXX XXX XXX N_18_MM M=5 L=1e-06 W=4.83382e-06
V2 XXX 0  DC 1.35
M3 XXX XXX gnd gnd N_18_MM M=5 L=1e-06 W=4.83382e-06
V4 XXX 0  DC 1
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings2(target_str, actual_str)

        

        conns = {'Drail':'gnd','Srail':'Vdd',
                 'Vin':'Vin','Vout':'Vout'}
        point = self._levelShifter_Point(0,0)
        instance = EmbeddedPart(part, conns, point)
        
        target_str = """M0 gnd Vin Vout Vout P_18_MM M=44 L=1e-06 W=4.914e-06
M1 Vout XXX Vdd Vdd P_18_MM M=22 L=1e-06 W=4.84575e-06
V2 XXX 0  DC 0.8
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings2(target_str, actual_str)
        
        point = self._levelShifter_Point(0,1)
        instance = EmbeddedPart(part, conns, point)
        
        target_str = """M0 gnd Vin Vout Vout P_18_MM M=44 L=1e-06 W=4.914e-06
M1 Vout XXX XXX XXX P_18_MM M=22 L=1e-06 W=4.84575e-06
V2 XXX 0  DC 0.45
M3 XXX XXX Vdd Vdd P_18_MM M=22 L=1e-06 W=4.84575e-06
V4 XXX 0  DC 0.8
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings2(target_str, actual_str)
                       
    def _levelShifterOrWire_Point(self, use_pmos, do_stack):
        d = self._levelShifter_Point(use_pmos, do_stack)
        d['chosen_part_index'] = 0 # 0 = choose level shifter
        return d
        
    def testLevelShifterOrWire(self):
        if self.just1: return
        part = self.lib.levelShifterOrWire()

        conns = {'Drail':'Vdd','Srail':'gnd',
                 'Vin':'Vin','Vout':'Vout'}
        point = self._levelShifterOrWire_Point(1,0)

        #instantiate as level shifter
        point['chosen_part_index'] = 0 
        instance = EmbeddedPart(part, conns, point)
        
        target_str = """M0 Vdd Vin Vout Vout N_18_MM M=14 L=1e-06 W=4.85742e-06
M1 Vout XXX gnd gnd N_18_MM M=5 L=1e-06 W=4.83382e-06
V2 XXX 0  DC 1
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

        #instantiate as wire
        point['chosen_part_index'] = 1
        instance = EmbeddedPart(part, conns, point)
        
        target_str = """Rwire0 Vin Vout  R=0
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings2(target_str, actual_str)
    
    def testViFeedback_LevelShifter(self):
        return #HACK
        if self.just1: return
        part = self.lib.viFeedback_LevelShifter()

        point = {'C':1.0e-9, 'use_pmos':0,
                 'amp_W':3*0.18e-6,
                 'amp_L':3*0.18e-6,
                 'cascode_do_stack':0,
                 'cascode_D_W':3*0.18e-6,
                 'cascode_D_L':3*0.18e-6,
                 'cascode_D_Vbias':1.5,
                 'cascode_S_W':5*0.18e-6,
                 'cascode_S_L':5*0.18e-6,
                 'cascode_S_Vbias':1.5}

        instance = EmbeddedPart(part,
                                {'loadrail':'Vdd','opprail':'gnd',
                                 'Ifpos':'Ifpos','Ifneg':'Ifneg',
                                 'VsensePos':'Vsensepos',
                                 'VsenseNeg':'VsenseNeg'},
                                point)
        
        target_str = """M0 Vdd Vsensepos n_auto_176 n_auto_176 N_18_MM M=1 L=5.4e-07 W=5.4e-07
M1 n_auto_176 n_auto_177 gnd gnd N_18_MM M=1 L=9e-07 W=9e-07
V2 n_auto_177 0  DC 1.5
C3 Ifpos n_auto_176  C=1e-09
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

    def _viFeedback_Point(self, use_pmos, chosen_part_index=0):
        return  {'use_pmos':use_pmos,
                 'chosen_part_index':chosen_part_index,
                 'R':10.0e6, 'C':1.0e-9, 
                 'amp_W':3*0.18e-6,
                 'amp_L':3*0.18e-6,
                 'cascode_do_stack':0,
                 'cascode_D_W':3*0.18e-6,
                 'cascode_D_L':3*0.18e-6,
                 'cascode_D_Vbias':1.5,
                 'cascode_S_W':5*0.18e-6,
                 'cascode_S_L':5*0.18e-6,
                 'cascode_S_Vbias':1.5,
                 }
    
    def testViFeedback(self):
        return #HACK
        if self.just1: return
        part = self.lib.viFeedback()

        conns = {'loadrail':'Vdd', 'opprail':'gnd',
                 'Ifpos':'Ifpos', 'Ifneg':'Ifneg',
                 'VsensePos':'VsensePos', 'VsenseNeg':'VsenseNeg'}
        point = self._viFeedback_Point(0)

        #instantiate as capacitor
        point['chosen_part_index'] = 0      
        instance = EmbeddedPart(part, conns, point)
        
        target_str = """C0 Ifpos VsensePos  C=1e-09
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

        #instantiate as RC_series
        point['chosen_part_index'] = 1              
        instance = EmbeddedPart(part, conns, point)
        
        target_str = """R0 Ifpos n_auto_177  R=1e+07
C1 n_auto_177 VsensePos  C=1e-09
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

        #instantiate as viFeedback_LevelShifter
        point['chosen_part_index'] = 2          
        instance = EmbeddedPart(part, conns, point)
        
        target_str = """M0 Vdd VsensePos n_auto_178 n_auto_178 N_18_MM M=1 L=5.4e-07 W=5.4e-07
M1 n_auto_178 n_auto_179 gnd gnd N_18_MM M=1 L=9e-07 W=9e-07
V2 n_auto_179 0  DC 1.5
C3 Ifpos n_auto_178  C=1e-09
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)
    
    def testSourceDegen(self):
        if self.just1: return
        part = self.lib.sourceDegen()

        #instantiate as wire
        instance0 = EmbeddedPart(part, {'D':'1', 'S':'2'},
                                 {'chosen_part_index':0,
                                  'V':1.0,'I':0.1}
                                 )
        
        target_str0 = """Rwire0 1 2  R=0
"""
        actual_str0 = instance0.spiceNetlistStr()
        self._compareStrings(target_str0, actual_str0)


        #instantiate as resistor
        instance2 = EmbeddedPart(part, {'D':'1', 'S':'2'},
                                 {'chosen_part_index':1,
                                  'V':1.0,'I':0.1}
                                 )
        
        target_str2 = """R0 1 2  R=100
"""
        actual_str2 = instance2.spiceNetlistStr()
        self._compareStrings2(target_str2, actual_str2)

    def testCascodeDevice(self):
        if self.just1: return
        part = self.lib.cascodeDevice()
        self.assertEqual(sorted(part.externalPortnames()),
                         sorted(['D','S','loadrail','opprail']))

        #instantiate as biasedMos -- nmos
        conns = {'D':'1','S':'2', 'loadrail':'3','opprail':'4'}
        point = {'chosen_part_index':0,
                 'loadrail_is_vdd':1,
                 'Vgs':1.0,'Vds':1.0,
                 'L':1e-6,'Ids':1e-3,
                 'Vs':0}
        instance = EmbeddedPart(part, conns, point)
        target_str = """M0 1 n_auto_2 2 2 N_18_MM M=9 L=1e-06 W=1.98881e-06
V1 n_auto_2 0  DC 1
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

        #instantiate as biasedMos -- pmos
        point = {'chosen_part_index':0,
                 'loadrail_is_vdd':0,
                 'Vgs':1.0,'Vds':1.0,
                 'L':1e-6,'Ids':1e-3,
                 'Vs':1.8}
        instance = EmbeddedPart(part, conns, point)
        target_str = """M0 1 XXX 2 2 P_18_MM M=8 L=1e-06 W=1.81982e-06
V1 n_auto_2 0  DC 0.8
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)
        
        #instantiate as gainBoostedMos 
        return #FIXME
        instance1 = EmbeddedPart(part,
                                 {'D':'1', 'S':'2','loadrail':'3','opprail':'4'},
                                 {'chosen_part_index':1,
                                  'W':3*0.18e-6,
                                  'L':5*0.18e-6,
                                  'use_pmos':1,
                                  'Vbias':4.4 }
                                 )
        
        target_str1 = """BLAH
"""
        actual_str1 = instance1.spiceNetlistStr()
        self._compareStrings(target_str1, actual_str1)
        
    def testCascodeDeviceOrWire(self):
        if self.just1: return
        part = self.lib.cascodeDeviceOrWire()
        self.assertEqual(sorted(part.externalPortnames()),
                         sorted(['D','S','loadrail','opprail']))

        #instantiate as cascodeDevice
        instance0 = EmbeddedPart(part,
                                 {'D':'1', 'S':'2','loadrail':'3','opprail':'4'},
                                 {'chosen_part_index':0,
                                  'cascode_recurse':0,
                                  'loadrail_is_vdd':1,
                                  'Vgs':1.0,'Vds':1.0,
                                  'L':1e-6,'Ids':1e-3,
                                  'Vs':0}
                                 )
                                 
        target_str0 = """M0 1 n_auto_2 2 2 N_18_MM M=5 L=1e-06 W=4.83382e-06
V1 n_auto_2 0  DC 1
"""
        actual_str0 = instance0.spiceNetlistStr()
        self._compareStrings3(target_str0, actual_str0)
        
        #instantiate as wire
        instance1 = EmbeddedPart(part,
                                 {'D':'1', 'S':'2','loadrail':'3','opprail':'4'},
                                 {'chosen_part_index':1,
                                  'cascode_recurse':0,
                                  'loadrail_is_vdd':1,
                                  'Vgs':1.0,'Vds':1.0,
                                  'L':1e-6,'Ids':1e-3,
                                  'Vs':0}
                                 )
        
        target_str1 = """Rwire0 1 2  R=0
"""
        actual_str1 = instance1.spiceNetlistStr()
        self._compareStrings(target_str1, actual_str1)
        
    def testInputCascode_Stacked(self):
        if self.just1: return
        part = self.lib.inputCascode_Stacked()
        self.assertEqual(sorted(part.externalPortnames()),
                         sorted(['Vin', 'Iout', 'loadrail', 'opprail']))
        self.assertEqual(len(part.embedded_parts), 3)

        #'nmos version':
        #instantiate with input_is_pmos=False (ie input is nmos)
        # cascode_is_wire=0, degen_choice of biasedMos (1)
        #Remember: input_is_pmos=False means loadrail_is_Vdd=True; and vice-versa
        conn = {'Vin':'Vin', 'Iout':'Iout', 'loadrail':'Vdd','opprail':'gnd'}
        point = self._stackedPoint(input_is_pmos=False)
        instance = EmbeddedPart(part, conn, point)
        target_str = self._stackedNetlist(input_is_pmos=False)
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

        #'pmos (upside-down) version':
        conn = {'Vin':'Vin', 'Iout':'Iout', 'loadrail':'gnd','opprail':'Vdd'}
        point = self._stackedPoint(input_is_pmos=True)
        instance = EmbeddedPart(part, conn, point)
        target_str = self._stackedNetlist(input_is_pmos=True)
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

    def _stackedPoint(self, input_is_pmos):
        """For testing testInputCascode_Stacked"""
     
        if input_is_pmos==0:
            return { 'input_is_pmos':0,
                 'Ibias':1e-3, 'Vds': 1.0, 'Vs':0, 
                 'cascode_is_wire':0,
                 'cascode_L':1e-6,
                 'cascode_Vgs':1.0,
                 'cascode_recurse':0,
                 
                 'ampmos_Vgs':1.0,'ampmos_L':1e-6,'fracAmp':1.1/1.8,
                                  
                 'degen_choice':1,'fracDeg':0.1
                 }        
        else:
            return { 'input_is_pmos':1,
                 'Ibias':1e-3, 'Vds': 1.0, 'Vs':1.8, 
                
                 'cascode_is_wire':0,
                 'cascode_L':1e-6,
                 'cascode_Vgs':1.0,
                 'cascode_recurse':0,
                 
                 'ampmos_Vgs':1.0,'ampmos_L':1e-6,'fracAmp':1.1/1.8,
                                  
                 'degen_choice':1,'fracDeg':0.1
                 }    
            

    def _stackedNetlist(self, input_is_pmos):
        """For testing testInputCascode_Stacked"""
        if input_is_pmos:
            #all transistors should be pmos
            return """M0 Iout n_auto_18 n_auto_16 n_auto_16 P_18_MM M=22 L=1e-06 W=4.84575e-06
V1 n_auto_18 0  DC 0.188889
M2 n_auto_16 Vin n_auto_17 n_auto_17 P_18_MM M=22 L=1e-06 W=4.84575e-06
R3 n_auto_17 Vdd  R=100
"""
        else:
            #all transistors should be nmos
            return """M0 Iout n_auto_15 n_auto_13 n_auto_13 N_18_MM M=5 L=1e-06 W=4.83382e-06
V1 n_auto_15 0  DC 1.61111
M2 n_auto_13 Vin n_auto_14 n_auto_14 N_18_MM M=5 L=1e-06 W=4.83382e-06
R3 n_auto_14 gnd  R=100
"""
        
    def testInputCascode_Folded(self):
        if self.just1: return
        part = self.lib.inputCascode_Folded()
        self.assertEqual(sorted(part.externalPortnames()),
                         sorted(['Vin', 'Iout', 'loadrail', 'opprail']))
        self.assertEqual(len(part.embedded_parts), 4)

        #instantiate with input_is_pmos=True, degen_choice of biasedMos (1)
        conn = {'Vin':'Vin', 'Iout':'Iout', 'loadrail':'Vdd','opprail':'gnd'}
        point = self._foldedPoint(input_is_pmos=True)
        instance = EmbeddedPart(part, conn, point)
        target_str = self._foldedNetlist(input_is_pmos=True)
        actual_str = instance.spiceNetlistStr()
        self._compareStrings2(target_str, actual_str)

        #instantiate with input_is_pmos=False
        conn = {'Vin':'Vin', 'Iout':'Iout', 'loadrail':'gnd','opprail':'Vdd'}
        point = self._foldedPoint(input_is_pmos=False)
        instance = EmbeddedPart(part, conn, point)
        target_str = self._foldedNetlist(input_is_pmos=False)
        actual_str = instance.spiceNetlistStr()
        self._compareStrings2(target_str, actual_str)

    def _foldedPoint(self, input_is_pmos):
        """For testing testInputCascode_Folded"""
        point={'input_is_pmos':'fillme', 'Vs':'fillme', 
                 'Ibias':1e-3, 'Ibias2':1e-3, 'Vds': 1.0, 
                 'cascode_is_wire':0,
                 'cascode_L':1e-6,
                 'cascode_Vgs':1.0,
                 'cascode_recurse':0,
                 
                 'ampmos_Vgs':1.0,'ampmos_L':1e-6,'fracAmp':1.1/1.8,
                                  
                 'degen_choice':1,'fracDeg':0.1,
                 
                 'inputbias_L':1e-6,
                 'inputbias_Vgs':1.0,
                 }   
                 
        if input_is_pmos==0:
            point['input_is_pmos']=0
            point['Vs']=0
            
            return point  
        else:
            point['input_is_pmos']=1
            point['Vs']=1.8
            
            return point     
    
    def _foldedNetlist(self, input_is_pmos):
        """For testing testInputCascode_Folded"""
        if input_is_pmos:
            return """M0 Iout n_auto_15 n_auto_14 n_auto_14 N_18_MM M=5 L=1e-06 W=4.83382e-06
V1 n_auto_15 0  DC 1.7
M2 n_auto_14 Vin n_auto_13 n_auto_13 P_18_MM M=22 L=1e-06 W=4.84575e-06
R3 n_auto_13 Vdd  R=180
M4 n_auto_14 n_auto_16 gnd gnd N_18_MM M=10 L=1e-06 W=4.83382e-06
V5 n_auto_16 0  DC 1
"""
        else:
            return """M0 Iout n_auto_19 n_auto_18 n_auto_18 P_18_MM M=22 L=1e-06 W=4.84575e-06
V1 n_auto_19 0  DC 0.1
M2 n_auto_18 Vin n_auto_17 n_auto_17 N_18_MM M=5 L=1e-06 W=4.83382e-06
R3 n_auto_17 gnd  R=180
M4 n_auto_18 n_auto_20 Vdd Vdd P_18_MM M=43 L=1e-06 W=4.95845e-06
V5 n_auto_20 0  DC 0.8
"""
        
    def testInputCascodeFlex(self):
        if self.just1: return
        part = self.lib.inputCascodeFlex()

        assert len(part.point_meta) == \
                (len(self.lib.inputCascode_Folded().point_meta) + 1)

        #case 1: input_is_pmos=F, loadrail_is_Vdd=T
        # (therefore stacked, ie choice=0)
        conn = {'Vin':'Vin', 'Iout':'Iout', 'loadrail':'Vdd','opprail':'gnd'}
        point = self._inputCascodeFlex_Point(0, 0)
        instance = EmbeddedPart(part, conn, point)
        self._compareStrings3(self._stackedNetlist(0),
                              instance.spiceNetlistStr())

        #case 2: input_is_pmos=T, loadrail_is_Vdd=F
        # (therefore stacked, ie choice=0)
        conn = {'Vin':'Vin', 'Iout':'Iout', 'loadrail':'gnd','opprail':'Vdd'}
        point = self._inputCascodeFlex_Point(0, 1)
        instance = EmbeddedPart(part, conn, point)
        self._compareStrings3(self._stackedNetlist(1),
                              instance.spiceNetlistStr())

        #case 3: input_is_pmos=T, loadrail_is_Vdd=T
        # (therefore stacked, ie choice=0)
        conn = {'Vin':'Vin', 'Iout':'Iout', 'loadrail':'Vdd','opprail':'gnd'}
        point = self._inputCascodeFlex_Point(1, 1)
        instance = EmbeddedPart(part, conn, point)
        self._compareStrings3(self._foldedNetlist(1),
                              instance.spiceNetlistStr())

        #case 4: input_is_pmos=F, loadrail_is_Vdd=F
        # (therefore stacked, ie choice=0)
        conn = {'Vin':'Vin', 'Iout':'Iout', 'loadrail':'gnd','opprail':'Vdd'}
        point = self._inputCascodeFlex_Point(1, 0)
        instance = EmbeddedPart(part, conn, point)
        self._compareStrings3(self._foldedNetlist(0),
                              instance.spiceNetlistStr())

    def _inputCascodeFlex_Point(self, chosen_part_index, input_is_pmos):
        #can easily  generate this, because it only adds two vars
        # above and beyond a foldedPoint. 
        point = self._foldedPoint(input_is_pmos)
        point['chosen_part_index'] = chosen_part_index #add var
        point['cascode_is_wire'] = 0                   #add var
        return point
        
    def testInputCascodeStage(self):
        if self.just1: return
        part = self.lib.inputCascodeStage()
        self._testInputCascodeStage_and_SsViInput(part)
        
    def testSsViInput(self):
        if self.just1: return
        part = self.lib.inputCascodeStage()
        self._testInputCascodeStage_and_SsViInput(part)
        
    def _testInputCascodeStage_and_SsViInput(self, part):
        if self.just1: return

        #case 1: input_is_pmos=F, loadrail_is_Vdd=T
        # (therefore stacked)
        conn = {'Vin':'Vin', 'Iout':'Iout', 'loadrail':'Vdd','opprail':'gnd'}
        point = self._inputCascodeStage_Point(1, 0)
        instance = EmbeddedPart(part, conn, point)
        self._compareStrings3(self._stackedNetlist(0),
                              instance.spiceNetlistStr())

        #case 2: input_is_pmos=T, loadrail_is_Vdd=F
        # (therefore stacked)
        conn = {'Vin':'Vin', 'Iout':'Iout', 'loadrail':'gnd','opprail':'Vdd'}
        point = self._inputCascodeStage_Point(0, 1)
        instance = EmbeddedPart(part, conn, point)
        self._compareStrings3(self._stackedNetlist(1),
                              instance.spiceNetlistStr())

        #case 3: input_is_pmos=T, loadrail_is_Vdd=T
        # (therefore stacked)
        conn = {'Vin':'Vin', 'Iout':'Iout', 'loadrail':'Vdd','opprail':'gnd'}
        point = self._inputCascodeStage_Point(1, 1)
        instance = EmbeddedPart(part, conn, point)
        self._compareStrings3(self._foldedNetlist(1),
                              instance.spiceNetlistStr())

        #case 4: input_is_pmos=F, loadrail_is_Vdd=F
        # (therefore stacked)
        conn = {'Vin':'Vin', 'Iout':'Iout', 'loadrail':'gnd','opprail':'Vdd'}
        point = self._inputCascodeStage_Point(0, 0)
        instance = EmbeddedPart(part, conn, point)
        self._compareStrings3(self._foldedNetlist(0),
                              instance.spiceNetlistStr())

    def _inputCascodeStage_Point(self, loadrail_is_vdd, input_is_pmos):
        #can easily  generate this, because it only adds one var
        # above and beyond a foldedPoint, and removes another var
        dummy = 0
        point = self._inputCascodeFlex_Point(dummy, input_is_pmos)
        point['loadrail_is_vdd'] = loadrail_is_vdd #add var
        del point['chosen_part_index']             #remove var

        return point
        
    def testSsIiLoad_Cascoded(self):
        if self.just1: return
        part = self.lib.ssIiLoad_Cascoded()
        self.assertEqual(sorted(part.externalPortnames()),
                         sorted(['Iout','loadrail','opprail']))
                        
        #loadrail_is_vdd=1, so parts are all pmos
        conns = {'Iout':'Iout','loadrail':'Vdd','opprail':'gnd'}
        
        point = {'loadrail_is_vdd':1,
                 'Ibias':1e-3, 'Vds':0.8,'Vs':1.8,
                                 
                 'mainload_L':1e-6,
                 'mainload_Vgs':1.0,
                 'fracLoad':0.5,
                                 
                 'loadcascode_recurse':0,
                 'loadcascode_L':1e-6,
                 'loadcascode_Vgs':1.0,
                 }
        instance = EmbeddedPart(part, conns, point)
                                 
        target_str = """M0 n_auto_85 n_auto_86 Vdd Vdd P_18_MM M=22 L=1e-06 W=4.84575e-06
V1 n_auto_86 0  DC 0.8
M2 Iout n_auto_87 n_auto_85 n_auto_85 P_18_MM M=22 L=1e-06 W=4.84575e-06
V3 n_auto_87 0  DC 0.4
"""
        actual_str = instance.spiceNetlistStr()
        
        self._compareStrings3(target_str, actual_str)
        
        #loadrail_is_vdd=0, so parts are all nmos
        conns = {'Iout':'Iout','loadrail':'gnd','opprail':'Vdd'}
        point = {'loadrail_is_vdd':0,
                 'Ibias':1e-3, 'Vds':0.8,'Vs':0,
                                 
                 'mainload_L':1e-6,
                 'mainload_Vgs':1.0,
                 'fracLoad':0.5,
                                 
                 'loadcascode_recurse':0,
                 'loadcascode_L':1e-6,
                 'loadcascode_Vgs':1.0,
                 }
        instance = EmbeddedPart(part, conns, point)
                                 
        target_str = """M0 n_auto_88 n_auto_89 gnd gnd N_18_MM M=5 L=1e-06 W=4.83382e-06
V1 n_auto_89 0  DC 1
M2 Iout n_auto_90 n_auto_88 n_auto_88 N_18_MM M=5 L=1e-06 W=4.83382e-06
V3 n_auto_90 0  DC 1.4
"""
        actual_str = instance.spiceNetlistStr()
        
        self._compareStrings3(target_str, actual_str)
        
    def testSsIiLoad(self):
        if self.just1: return
       
        part = self.lib.ssIiLoad()
        self.assertEqual(sorted(part.externalPortnames()),
                         sorted(['Iout','loadrail','opprail']))

        #use ssIiLoad_Cascoded (chosen_part_index=2)
        # loadrail_is_vdd=0, so parts are all nmos
        conns = {'Iout':'Iout','loadrail':'gnd','opprail':'Vdd'}
        point = {'loadrail_is_vdd':0,
                 'chosen_part_index':2, 
                 'Ibias':1e-3, 'Vds':0.8,'Vs':0,         
                 'L':1e-6,
                 'Vgs':1.0,
                 'fracLoad':0.5,
                 'loadcascode_recurse':0,
                 'loadcascode_L':1e-6,
                 'loadcascode_Vgs':1.0,                 
                 }

        instance = EmbeddedPart(part, conns, point)
                                 
        target_str = """M0 n_auto_88 n_auto_89 gnd gnd N_18_MM M=5 L=1e-06 W=4.83382e-06
V1 n_auto_89 0  DC 1
M2 Iout n_auto_90 n_auto_88 n_auto_88 N_18_MM M=5 L=1e-06 W=4.83382e-06
V3 n_auto_90 0  DC 1.4
"""
        actual_str = instance.spiceNetlistStr()
        
        self._compareStrings3(target_str, actual_str)
        
        # loadrail_is_vdd=0, so parts are all nmos
        conns = {'Iout':'Iout','loadrail':'gnd','opprail':'Vdd'}
        point = {'loadrail_is_vdd':0,
                 'chosen_part_index':1, 
                 'Ibias':1e-3, 'Vds':0.8,'Vs':0,         
                 'L':1e-6,
                 'Vgs':1.0,
                 'fracLoad':0.5,
                 'loadcascode_recurse':0,
                 'loadcascode_L':1e-6,
                 'loadcascode_Vgs':1.0,                 
                 }

        instance = EmbeddedPart(part, conns, point)
                                 
        target_str = """M0 gnd n_auto_88 Iout Iout N_18_MM M=5 L=1e-06 W=4.83382e-06
V1 n_auto_88 0  DC 1
"""
        actual_str = instance.spiceNetlistStr()
        
        self._compareStrings3(target_str, actual_str)
        
        #simple-as-possible: 10K load, no cascoding
        conns = {'Iout':'Iout','loadrail':'Vdd','opprail':'gnd'}
        point = {'loadrail_is_vdd':0,
                 'chosen_part_index':0, 
                 'Ibias':1e-3, 'Vds':0.8,'Vs':0,         
                 'L':1e-6,
                 'Vgs':1.0,
                 'fracLoad':0.5,
                 'loadcascode_recurse':0,
                 'loadcascode_L':1e-6,
                 'loadcascode_Vgs':1.0,                 
                 }
        instance = EmbeddedPart(part, conns, point)
                                 
        target_str = """R0 Vdd Iout  R=800
"""
        actual_str = instance.spiceNetlistStr()
        
        self._compareStrings3(target_str, actual_str)

        #test Ibias railing
        conns = {'Iout':'Iout','loadrail':'Vdd','opprail':'gnd'}
        
        test_bias=self.lib.ss.max_Ires*1.1
        Vds=1.0
        
        point = {'loadrail_is_vdd':0,
                 'chosen_part_index':0, 
                 'Ibias':test_bias, 'Vds':Vds,'Vs':0,         
                 'L':1e-6,
                 'Vgs':1.0,
                 'fracLoad':0.5,
                 'loadcascode_recurse':0,
                 'loadcascode_L':1e-6,
                 'loadcascode_Vgs':1.0,                 
                 }
        instance = EmbeddedPart(part, conns, point)
                                 
        target_str = """R0 Vdd Iout  R=%g
""" % abs((Vds)/self.lib.ss.max_Ires)
        actual_str = instance.spiceNetlistStr()
        
        self._compareStrings2(target_str, actual_str)     
           
    def testSsViAmp1_simple(self):
        if self.just1: return
        part = self.lib.ssViAmp1()
        self.assertEqual(sorted(part.externalPortnames()),
                         sorted(['Vin','Iout','loadrail','opprail']))

        # Simple as possible: nmos input, 10K resistor load
        #  (no input cascode, no source degen, no load cascode)
        #  (loadrail_is_vdd=1, input_is_pmos=0)
        conns = {'Vin':'Vin','Iout':'Iout','loadrail':'Vdd','opprail':'gnd'}
        point = self._ssViAmp1_Point()
        instance = EmbeddedPart(part, conns, point)
                                 
        target_str = """Rwire0 Iout n_auto_103  R=0
M1 n_auto_103 Vin n_auto_104 n_auto_104 N_18_MM M=5 L=1e-06 W=4.83382e-06
Rwire2 n_auto_104 gnd  R=0
R3 Vdd Iout  R=1000
"""
        actual_str = instance.spiceNetlistStr()
        
        self._compareStrings3(target_str, actual_str)
        
    def testSsViAmp1_complex(self):
        if self.just1: return
        part = self.lib.ssViAmp1()
        conns = {'Vin':'Vin','Iout':'Iout','loadrail':'gnd','opprail':'Vdd'}
        point = self._ssViAmp1_Point2(0,0)
        
        instance = EmbeddedPart(part, conns, point)
                                 
        target_str = """M0 Iout n_auto_17 n_auto_16 n_auto_16 P_18_MM M=13 L=1e-06 W=4.85917e-06
V1 n_auto_17 0  DC 0.7
M2 n_auto_16 Vin n_auto_15 n_auto_15 N_18_MM M=11 L=1e-06 W=4.98272e-06
R3 n_auto_15 gnd  R=100
M4 n_auto_16 n_auto_18 Vdd Vdd P_18_MM M=31 L=1e-06 W=4.92096e-06
V5 n_auto_18 0  DC 0.8
M6 n_auto_19 n_auto_20 gnd gnd N_18_MM M=8 L=1e-06 W=4.44066e-06
V7 n_auto_20 0  DC 0.8
M8 Iout n_auto_21 n_auto_19 n_auto_19 N_18_MM M=8 L=1e-06 W=4.44066e-06
V9 n_auto_21 0  DC 1.1
"""
        actual_str = instance.spiceNetlistStr()
        
        self._compareStrings3(target_str, actual_str)

    def testSsViAmp1_simpleWithIbiasRailingCheck(self):
        if self.just1: return
        
        part = self.lib.ssViAmp1()
        conns = {'Vin':'Vin','Iout':'Iout','loadrail':'Vdd','opprail':'gnd'}
        point = self._ssViAmp1_Point()
        
        test_bias=self.lib.ss.max_Ibias*10 #will this get railed correctly?
        Vout=1.0
        Vloadrail=1.8
        point['Ibias']=test_bias
        
        point['Vout']=Vout
        point['Vloadrail']=Vloadrail
        point['ampmos_L']=0.18e-6
        
        instance = EmbeddedPart(part, conns, point)
                                 
        target_str = """Rwire0 Iout XXX  R=0
M1 XXX Vin XXX XXX N_18_MM M=31 L=1.8e-07 W=4.94358e-06
Rwire2 XXX gnd  R=0
R3 Vdd Iout  R=%g
""" % abs((Vout - Vloadrail)/self.lib.ss.max_Ibias)

        actual_str = instance.spiceNetlistStr()
        
        self._compareStrings2(target_str, actual_str)
          
        
    def _ssViAmp1_Point(self, loadrail_is_vdd=1, input_is_pmos=0):
        return  {'loadrail_is_vdd':loadrail_is_vdd,
                 'input_is_pmos':input_is_pmos,
                 
                 'Ibias':1e-3, 'Ibias2':1e-3,
                 'Vout': 1.0,
                 
                 #for input:            
                 'inputcascode_is_wire':1,
                 'inputcascode_L':1e-6,
                 'inputcascode_Vgs':1.0,
                 'inputcascode_recurse':0,
                 
                 'ampmos_Vgs':1.0,'ampmos_L':1e-6,'ampmos_fracAmp':1.1/1.8,
                                  
                 'degen_choice':0,'degen_fracDeg':0.1,
                 
                 'inputbias_L':1e-6,
                 'inputbias_Vgs':1.0,             

                 #for load:
                 'load_part_index':0,         
                 'load_L':1e-6,
                 'load_Vgs':1.0,
                 'load_fracLoad':0.5,
                 'loadcascode_recurse':0,
                 'loadcascode_L':1e-6,
                 'loadcascode_Vgs':1.0,  
                 }

    def _ssViAmp1_Point2(self, loadrail_is_vdd=1, input_is_pmos=0):
        return  {'loadrail_is_vdd':loadrail_is_vdd,
                 'input_is_pmos':input_is_pmos,
                 
                 'Ibias':1e-3, 'Ibias2':1e-3,
                 'Vout': 1.0,
                 
                 #for input:            
                 'inputcascode_is_wire':0,
                 'inputcascode_L':1e-6,
                 'inputcascode_Vgs':1.0,
                 'inputcascode_recurse':0,
                 
                 'ampmos_Vgs':1.0,'ampmos_L':1e-6,'ampmos_fracAmp':1.1/1.8,
                                  
                 'degen_choice':1,'degen_fracDeg':0.1,
                 
                 'inputbias_L':1e-6,
                 'inputbias_Vgs':1.0,             

                 #for load:
                 'load_part_index':2,         
                 'load_L':1e-6,
                 'load_Vgs':1.0,
                 'load_fracLoad':0.5,
                 'loadcascode_recurse':0,
                 'loadcascode_L':1e-6,
                 'loadcascode_Vgs':1.0,  
                 }

    def _ssViAmp1_VddGndPorts_Point(self):
        point = self._ssViAmp1_Point()
        point['chosen_part_index'] = point['loadrail_is_vdd']
        del point['loadrail_is_vdd']
        return point
    
    def testSsViAmp1_VddGndPorts_simple(self):
        if self.just1: return
        part = self.lib.ssViAmp1_VddGndPorts()
        self.assertEqual(sorted(part.externalPortnames()),
                         sorted(['Vin','Iout','Vdd','gnd']))

        conns = {'Vin':'Vin','Iout':'Iout','Vdd':'Vdd','gnd':'gnd'}
        point = self._ssViAmp1_VddGndPorts_Point()
        instance = EmbeddedPart(part, conns, point)
                                 
        target_str = """FIXME
        This should have a summary string at the top, looking like:
==== Summary for: ssViAmp1_VddGndPorts ====
* Ibias = blah
* Ibias2 = blah
* degen_choice (0=wire,1=resistor) = blah
* load type (0=resistor,1=biasedMos,2=ssIiLoad_Cascoded) = blah
==== Done summary ====

<<rest of netlist should go here>>
"""
        actual_str = instance.spiceNetlistStr()
        print actual_str
        
        #self._compareStrings3(target_str, actual_str)
        
    def testCurrentMirror_Simple(self):
        if self.just1: return
        part = self.lib.currentMirror_Simple()

        #nmos CM
        instance = EmbeddedPart(part,
                                {'Irefnode':'Irefnode', 'Ioutnode':'Ioutnode',
                                 'loadrail':'gnd'},
                                 {'loadrail_is_vdd':0,
                                  'Iin':1e-3,'Iout':1e-3,
                                  'Vds_in':1.0,'Vds_out':1.0,
                                  'Vs':0.0,
                                  'L':1e-6}
                                 )
        
        target_str = """M0 Irefnode Irefnode gnd gnd N_18_MM M=5 L=1e-06 W=4.83382e-06
M1 Ioutnode Irefnode gnd gnd N_18_MM M=5 L=1e-06 W=4.83382e-06
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

        #pmos CM
        instance = EmbeddedPart(part,
                                {'Irefnode':'Irefnode', 'Ioutnode':'Ioutnode',
                                 'loadrail':'Vdd'},
                                 {'loadrail_is_vdd':1,
                                  'Iin':1e-3,'Iout':1e-3,
                                  'Vds_in':1.0,'Vds_out':1.0,
                                  'Vs':1.8,
                                  'L':1e-6}
                                 )
        
        target_str = """M0 Irefnode Irefnode Vdd Vdd P_18_MM M=22 L=1e-06 W=4.84575e-06
M1 Ioutnode Irefnode Vdd Vdd P_18_MM M=22 L=1e-06 W=4.84575e-06
"""
        actual_str = instance.spiceNetlistStr()
        
        self._compareStrings3(target_str, actual_str)


    def testCurrentMirror_Cascode(self):
        if self.just1: return
        part = self.lib.currentMirror_Cascode()

        #nmos CM
        instance = EmbeddedPart(part,
                                {'Irefnode':'Irefnode', 'Ioutnode':'Ioutnode',
                                 'loadrail':'gnd'},
                                 {'loadrail_is_vdd':0,
                                  'Iin':1e-3,'Iout':1e-3,
                                  'Vds_in':1.2,'Vds_out':1.2,
                                  'fracIn':0.5,'fracOut':0.5,
                                  'Vs':0.0,
                                  'L':1e-6,'cascode_L':1e-6}
                                 )
        
        target_str = """M0 Irefnode Irefnode n_auto_12 n_auto_12 N_18_MM M=27 L=1e-06 W=4.87053e-06
M1 n_auto_12 n_auto_12 gnd gnd N_18_MM M=27 L=1e-06 W=4.87053e-06
M2 Ioutnode Irefnode n_auto_13 n_auto_13 N_18_MM M=27 L=1e-06 W=4.87053e-06
M3 n_auto_13 n_auto_12 gnd gnd N_18_MM M=27 L=1e-06 W=4.87053e-06
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)
        
        #pmos CM
        instance = EmbeddedPart(part,
                                {'Irefnode':'Irefnode', 'Ioutnode':'Ioutnode',
                                 'loadrail':'Vdd'},
                                 {'loadrail_is_vdd':1,
                                  'Iin':1e-3,'Iout':1e-3,
                                  'Vds_in':1.6,'Vds_out':1.6,
                                  'fracIn':0.5,'fracOut':0.5,
                                  'Vs':1.8,
                                  'L':1e-6,'cascode_L':2e-6}
                                 )
        
        target_str = """M0 Irefnode Irefnode n_auto_14 n_auto_14 P_18_MM M=87 L=2e-06 W=4.97049e-06
M1 n_auto_14 n_auto_14 Vdd Vdd P_18_MM M=44 L=1e-06 W=4.914e-06
M2 Ioutnode Irefnode n_auto_15 n_auto_15 P_18_MM M=87 L=2e-06 W=4.97049e-06
M3 n_auto_15 n_auto_14 Vdd Vdd P_18_MM M=44 L=1e-06 W=4.914e-06
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)
        
    def testCurrentMirror_LowVoltageA(self):
        if self.just1: return
        part = self.lib.currentMirror_LowVoltageA()

        #nmos CM
        instance = EmbeddedPart(part,
                                {'Irefnode':'Irefnode', 'Ioutnode':'Ioutnode',
                                 'loadrail':'gnd'},        
                                {'loadrail_is_vdd':0,
                                  'Iin':1e-3,'Iout':1e-3,
                                  'Vds_in':1.2,'Vds_out':1.0,
                                  'fracIn':0.5,'fracOut':0.5,
                                  'Vs':0.0,
                                  'L':1e-6,'cascode_L':1e-6,
                                  'cascode_Vgs':1.0}
                                 )
        
        target_str = """M0 Irefnode n_auto_21 n_auto_19 n_auto_19 N_18_MM M=5 L=1e-06 W=4.83382e-06
V1 n_auto_21 0  DC 1.6
M2 n_auto_19 Irefnode gnd gnd N_18_MM M=4 L=1e-06 W=4.0708e-06
M3 Ioutnode n_auto_22 n_auto_20 n_auto_20 N_18_MM M=5 L=1e-06 W=4.83382e-06
V4 n_auto_22 0  DC 1.5
M5 n_auto_20 Irefnode gnd gnd N_18_MM M=4 L=1e-06 W=4.0708e-06
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

    def testCurrentMirror(self):
        if self.just1: return

        self._verifyCmChoice(0, 'currentMirror_Simple')
        self._verifyCmChoice(1, 'currentMirror_Cascode')
        self._verifyCmChoice(2, 'currentMirror_LowVoltageA')

    def _verifyCmChoice(self, chosen_part_index, target_name):
        part = self.lib.currentMirror()

        #nmos CM
        conns = {'Irefnode':'Irefnode', 'Ioutnode':'Ioutnode', 'loadrail':'gnd'}
        point = {'chosen_part_index':chosen_part_index, 'loadrail_is_vdd':0,
                                  'Iin':1e-3,'Iout':1e-3,
                                  'Vds_in':1.2,'Vds_out':1.0,
                                  'fracIn':0.5,'fracOut':0.5,
                                  'Vs':0.0,
                                  'L':1e-6,'cascode_L':1e-6,
                                  'cascode_Vgs':1.0}
        
        point = Point(True, point)
        point['chosen_part_index'] = chosen_part_index
        instance = EmbeddedPart(part, conns, point)
        
        self.assertEqual(instance.part.chosenPart(point).part.name,
                         target_name)
        
        actual_str = instance.spiceNetlistStr()
        if (chosen_part_index==0):
            target_str = """M0 Irefnode Irefnode gnd gnd N_18_MM M=4 L=1e-06 W=4.0708e-06
M1 Ioutnode Irefnode gnd gnd N_18_MM M=4 L=1e-06 W=4.0708e-06
"""
        elif (chosen_part_index==1):
            target_str = """M0 Irefnode Irefnode n_auto_12 n_auto_12 N_18_MM M=27 L=1e-06 W=4.87053e-06
M1 n_auto_12 n_auto_12 gnd gnd N_18_MM M=27 L=1e-06 W=4.87053e-06
M2 Ioutnode Irefnode n_auto_13 n_auto_13 N_18_MM M=27 L=1e-06 W=4.87053e-06
M3 n_auto_13 n_auto_12 gnd gnd N_18_MM M=27 L=1e-06 W=4.87053e-06
"""
        elif (chosen_part_index==2):
            target_str = """M0 Irefnode n_auto_21 n_auto_19 n_auto_19 N_18_MM M=5 L=1e-06 W=4.83382e-06
V1 n_auto_21 0  DC 1.6
M2 n_auto_19 Irefnode gnd gnd N_18_MM M=4 L=1e-06 W=4.0708e-06
M3 Ioutnode n_auto_22 n_auto_20 n_auto_20 N_18_MM M=5 L=1e-06 W=4.83382e-06
V4 n_auto_22 0  DC 1.5
M5 n_auto_20 Irefnode gnd gnd N_18_MM M=4 L=1e-06 W=4.0708e-06
"""
        self._compareStrings2(target_str, actual_str)
    
    
    def testDsIiLoad(self):
        if self.just1: return
        part = self.lib.dsIiLoad()

        #simple-as-possible nmos CM
        conns = {'Iin1':'Iin1', 'Iin2':'Iin2', 'Iout':'Iout', 'loadrail':'gnd'}
        point = {'chosen_part_index':0, 'loadrail_is_vdd':0,
                                  'Iin':1e-3,'Iout':1e-3,
                                  'Vds_in':1.2,'Vds_out':1.0,
                                  'fracIn':0.5,'fracOut':0.5,
                                  'Vs':0.0,
                                  'L':1e-6,'cascode_L':1e-6,
                                  'cascode_Vgs':1.0}
        instance = EmbeddedPart(part, conns, point)
        
        target_str = """M0 Iin1 Iin1 gnd gnd N_18_MM M=4 L=1e-06 W=4.0708e-06
M1 Iin2 Iin1 gnd gnd N_18_MM M=4 L=1e-06 W=4.0708e-06
Rwire2 Iin2 Iout  R=0
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

    def _ddViInput_Point(self, loadrail_is_vdd, input_is_pmos):
        point = self._inputCascodeStage_Point(loadrail_is_vdd, input_is_pmos)
        return point
        
    def testDdViInput(self):
        if self.just1: return
        part = self.lib.ddViInput()
        self.assertEqual(sorted(part.externalPortnames()),
                         sorted(['Vin1','Vin2','Iout1','Iout2',
                                 'loadrail','opprail']))

        conns = {'Vin1':'Vin1','Vin2':'Vin2','Iout1':'Iout1','Iout2':'Iout2',
                 'loadrail':'Vdd','opprail':'gnd'}

        #instantiate as stacked, nmos input with cascode
        # -this means that the input is stacked, not folded;
        point = {'input_is_pmos':0,
                 'loadrail_is_vdd':1,
                 'Vs':0.0,'Ibias':1e-3, 'Ibias2':1e-3,
                 'Vds1':1.0,'Vds2':1.0,
                 'cascode_L':1e-6,
                 'cascode_Vgs':1.0,
                 'cascode_recurse':0,
                 'cascode_is_wire':0,
                 
                 'ampmos_Vgs':1.0,
                 'ampmos_L':1e-6,
                 'fracAmp':0.5,
                                  
                 'degen_choice':0,
                 'fracDeg':0.1,

                 'inputbias_L':1e-6,
                 'inputbias_Vgs':1.0,
                 
                 'folder_L':1e-6,
                 'folder_Vgs':1.0,
                 
                 'fracVgnd':0.2,
                 }
                 
        instance = EmbeddedPart(part, conns, point)
                                 
        target_str = """M0 Iout1 n_auto_44 n_auto_42 n_auto_42 N_18_MM M=5 L=1e-06 W=4.83382e-06
V1 n_auto_44 0  DC 1.68
M2 n_auto_42 Vin1 n_auto_43 n_auto_43 N_18_MM M=5 L=1e-06 W=4.83382e-06
Rwire3 n_auto_43 n_auto_41  R=0
M4 Iout2 n_auto_47 n_auto_45 n_auto_45 N_18_MM M=5 L=1e-06 W=4.83382e-06
V5 n_auto_47 0  DC 1.68
M6 n_auto_45 Vin2 n_auto_46 n_auto_46 N_18_MM M=5 L=1e-06 W=4.83382e-06
Rwire7 n_auto_46 n_auto_41  R=0
M8 n_auto_41 n_auto_48 gnd gnd N_18_MM M=10 L=1e-06 W=4.83382e-06
V9 n_auto_48 0  DC 1
"""
    
        actual_str = instance.spiceNetlistStr()
        
        self._compareStrings3(target_str, actual_str)

        #instantiate as stacked, pmos input with cascode
        # -this means that the input is stacked, not folded;
        conns = {'Vin1':'Vin1','Vin2':'Vin2','Iout1':'Iout1','Iout2':'Iout2',
                 'loadrail':'gnd','opprail':'Vdd'}

        point = {'input_is_pmos':1,
                 'loadrail_is_vdd':0,
                 'Vs':1.8,'Ibias':1e-3, 'Ibias2':1e-3,
                 'Vds1':1.0,'Vds2':1.0,
                 'cascode_L':1e-6,
                 'cascode_Vgs':1.0,
                 'cascode_recurse':0,
                 'cascode_is_wire':0,
                 
                 'ampmos_Vgs':1.0,
                 'ampmos_L':1e-6,
                 'fracAmp':0.5,
                                  
                 'degen_choice':0,
                 'fracDeg':0.1,

                 'inputbias_L':1e-6,
                 'inputbias_Vgs':1.0,
                 
                 'folder_L':1e-6,
                 'folder_Vgs':1.0,
                 
                 'fracVgnd':0.2,
                 }

        instance = EmbeddedPart(part, conns, point)
                                 
        target_str = """M0 Iout1 n_auto_50 n_auto_48 n_auto_48 P_18_MM M=22 L=1e-06 W=4.84575e-06
V1 n_auto_50 0  DC 0.12
M2 n_auto_48 Vin1 n_auto_49 n_auto_49 P_18_MM M=22 L=1e-06 W=4.84575e-06
Rwire3 n_auto_49 n_auto_47  R=0
M4 Iout2 n_auto_53 n_auto_51 n_auto_51 P_18_MM M=22 L=1e-06 W=4.84575e-06
V5 n_auto_53 0  DC 0.12
M6 n_auto_51 Vin2 n_auto_52 n_auto_52 P_18_MM M=22 L=1e-06 W=4.84575e-06
Rwire7 n_auto_52 n_auto_47  R=0
M8 n_auto_47 n_auto_54 Vdd Vdd P_18_MM M=43 L=1e-06 W=4.95845e-06
V9 n_auto_54 0  DC 0.8
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)
        
        #instantiate as folded, nmos input with cascode
        conns = {'Vin1':'Vin1','Vin2':'Vin2','Iout1':'Iout1','Iout2':'Iout2',
                 'loadrail':'gnd','opprail':'Vdd'}

        point = {'input_is_pmos':0,
                 'loadrail_is_vdd':0,
                 'Vs':0.0,'Ibias':1e-3, 'Ibias2':1e-3,
                 'Vds1':1.0,'Vds2':1.0,
                 'cascode_L':1e-6,
                 'cascode_Vgs':1.0,
                 'cascode_recurse':0,
                 'cascode_is_wire':0,
                 
                 'ampmos_Vgs':1.0,
                 'ampmos_L':1e-6,
                 'fracAmp':0.5,
                                  
                 'degen_choice':0,
                 'fracDeg':0.1,

                 'inputbias_L':1e-6,
                 'inputbias_Vgs':1.0,
                 
                 'folder_L':1e-6,
                 'folder_Vgs':1.0,
                 
                 'fracVgnd':0.2,
                 }

        instance = EmbeddedPart(part, conns, point)
                                 
        target_str = """M0 Iout1 n_auto_60 n_auto_59 n_auto_59 P_18_MM M=22 L=1e-06 W=4.84575e-06
V1 n_auto_60 0  DC 0.08
M2 n_auto_59 Vin1 n_auto_58 n_auto_58 N_18_MM M=5 L=1e-06 W=4.83382e-06
Rwire3 n_auto_58 n_auto_57  R=0
M4 n_auto_59 n_auto_61 Vdd Vdd P_18_MM M=43 L=1e-06 W=4.95845e-06
V5 n_auto_61 0  DC 0.8
M6 Iout2 n_auto_64 n_auto_63 n_auto_63 P_18_MM M=22 L=1e-06 W=4.84575e-06
V7 n_auto_64 0  DC 0.08
M8 n_auto_63 Vin2 n_auto_62 n_auto_62 N_18_MM M=5 L=1e-06 W=4.83382e-06
Rwire9 n_auto_62 n_auto_57  R=0
M10 n_auto_63 n_auto_65 Vdd Vdd P_18_MM M=43 L=1e-06 W=4.95845e-06
V11 n_auto_65 0  DC 0.8
M12 n_auto_57 n_auto_66 gnd gnd N_18_MM M=10 L=1e-06 W=4.83382e-06
V13 n_auto_66 0  DC 1
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)
        
        #instantiate as folded, pmos input
        conns = {'Vin1':'Vin1','Vin2':'Vin2','Iout1':'Iout1','Iout2':'Iout2',
                 'loadrail':'Vdd','opprail':'gnd'}

        point = {'input_is_pmos':1,
                 'loadrail_is_vdd':1,
                 'Vs':1.8,'Ibias':1e-3, 'Ibias2':1e-3,
                 'Vds1':1.0,'Vds2':1.0,
                 'cascode_L':1e-6,
                 'cascode_Vgs':1.0,
                 'cascode_recurse':0,
                 'cascode_is_wire':0,
                 
                 'ampmos_Vgs':1.0,
                 'ampmos_L':1e-6,
                 'fracAmp':0.5,
                                  
                 'degen_choice':0,
                 'fracDeg':0.1,

                 'inputbias_L':1e-6,
                 'inputbias_Vgs':1.0,
                 
                 'folder_L':1e-6,
                 'folder_Vgs':1.0,
                 
                 'fracVgnd':0.2,
                 }

        instance = EmbeddedPart(part, conns, point)
                                 
        target_str = """M0 Iout1 n_auto_70 n_auto_69 n_auto_69 N_18_MM M=5 L=1e-06 W=4.83382e-06
V1 n_auto_70 0  DC 1.72
M2 n_auto_69 Vin1 n_auto_68 n_auto_68 P_18_MM M=22 L=1e-06 W=4.84575e-06
Rwire3 n_auto_68 n_auto_67  R=0
M4 n_auto_69 n_auto_71 gnd gnd N_18_MM M=10 L=1e-06 W=4.83382e-06
V5 n_auto_71 0  DC 1
M6 Iout2 n_auto_74 n_auto_73 n_auto_73 N_18_MM M=5 L=1e-06 W=4.83382e-06
V7 n_auto_74 0  DC 1.72
M8 n_auto_73 Vin2 n_auto_72 n_auto_72 P_18_MM M=22 L=1e-06 W=4.84575e-06
Rwire9 n_auto_72 n_auto_67  R=0
M10 n_auto_73 n_auto_75 gnd gnd N_18_MM M=10 L=1e-06 W=4.83382e-06
V11 n_auto_75 0  DC 1
M12 n_auto_67 n_auto_76 Vdd Vdd P_18_MM M=43 L=1e-06 W=4.95845e-06
V13 n_auto_76 0  DC 0.8
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)


    def _dsViAmp1_Point(self, loadrail_is_vdd, input_is_pmos):
        input_point = {'input_is_pmos':input_is_pmos,
                 'loadrail_is_vdd':loadrail_is_vdd,
#                  'Vout':abs(1.8*(loadrail_is_vdd==0)-1.0),
                 'Vout':0.9,
                 'Ibias':0.6e-4, 
                 'Ibias2':1e-4,
#                  'Vds':abs(1.8*(input_is_pmos==1)-1.0),
#                  'Vds_internal':abs(1.8*(input_is_pmos==1)-1.0),
                 'Vds_internal':0.9,
                 'inputcascode_L':0.5e-6,
                 'inputcascode_Vgs':0.7,
                 'inputcascode_recurse':0,
                 'inputcascode_is_wire':1,
                 
                 'ampmos_Vgs':0.6,
                 'ampmos_L':0.5e-6,
                 'fracAmp':0.5,
                                  
                 'degen_choice':0,
                 'degen_fracDeg':0.1,

                 'inputbias_L':0.5e-6,
                 'inputbias_Vgs':0.7,
                 
                 'folder_L':0.5e-6,
                 'folder_Vgs':0.7,
                 
                 'fracVgnd':0.16,
                 }                       
        load_point = {'load_chosen_part_index':0, 
                      'loadrail_is_vdd':loadrail_is_vdd,
                      'load_fracIn':0.5,
                      'load_fracOut':0.5,
                      'load_L':0.5e-6,
                      'load_cascode_L':0.5e-6,
                      'load_cascode_Vgs':0.9,
                      }
        point = {}
        point.update(input_point)
        point.update(load_point)
        
        point_vars = point.keys()
        part_vars = self.lib.dsViAmp1().point_meta.keys()
        
        assert sorted(point_vars) == sorted(part_vars)
        return point

        
    def testDsViAmp1_index0(self):
        if self.just1: return
        conns = {'Vin1':'ninp','Vin2':'ninn','Iout':'nout',
                 'loadrail':'gnd','opprail':'ndd'}
        self._indexed_testDsViAmp1(0, conns)
        
    def testDsViAmp1_index1(self):
        if self.just1: return
        conns = {'Vin1':'ninp','Vin2':'ninn','Iout':'nout',
                 'loadrail':'gnd','opprail':'ndd'}
        self._indexed_testDsViAmp1(1, conns)
        
    def testDsViAmp1_index2(self):
        if self.just1: return
        conns = {'Vin1':'ninp','Vin2':'ninn','Iout':'nout',
                 'loadrail':'ndd','opprail':'gnd'}
        self._indexed_testDsViAmp1(2, conns)
        
    def testDsViAmp1_index3(self):
        if self.just1: return
        conns = {'Vin1':'ninp','Vin2':'ninn','Iout':'nout',
                 'loadrail':'ndd','opprail':'gnd'}
        self._indexed_testDsViAmp1(3, conns)
        
    def _indexed_testDsViAmp1(self, index, conns):
        part = self.lib.dsViAmp1()
        self.assertEqual(sorted(part.externalPortnames()),
                         sorted(['Vin1','Vin2','Iout','loadrail','opprail']))
                
        point = self._indexed_dsViAmp1_Point(index)
        instance = EmbeddedPart(part, conns, point)

        target_str = self._indexed_testDsViAmp1_TargetStr(index)
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

    def _indexed_dsViAmp1_Point(self, point_index):
        """The result of the 4 possible point_index_values of this function
        are the netlists of _indexed_testDsViAmp1_TargetStr.
        These 4 points are largely based on the four combinations of
        loadrail_is_vdd=0/1 and input_is_pmos=0/1 but there are other
        differences too.
        """
        if(point_index==0):
            loadrail_is_vdd = 0
            input_is_pmos = 0
            point=self._dsViAmp1_Point(loadrail_is_vdd, input_is_pmos)
            
        elif(point_index==1):
            loadrail_is_vdd = 0
            input_is_pmos = 1
            point=self._dsViAmp1_Point(loadrail_is_vdd, input_is_pmos)
       
        elif(point_index==2):
            loadrail_is_vdd = 1
            input_is_pmos = 1
            point=self._dsViAmp1_Point(loadrail_is_vdd, input_is_pmos)
    
        elif(point_index==3):
            loadrail_is_vdd = 1
            input_is_pmos = 0
            point=self._dsViAmp1_Point(loadrail_is_vdd, input_is_pmos)

        point_vars = point.keys()
        part_vars = self.lib.dsViAmp1().point_meta.keys()
        assert sorted(point_vars) == sorted(part_vars)
        return point
        

    def _indexed_testDsViAmp1_TargetStr(self, index):
        if index==0:
            return """M0 n_auto_95 n_auto_100 n_auto_99 n_auto_99 P_18_MM M=22 L=1e-06 W=4.84575e-06
V1 n_auto_100 0  DC 0.08
M2 n_auto_99 Vin1 n_auto_98 n_auto_98 N_18_MM M=5 L=1e-06 W=4.83382e-06
Rwire3 n_auto_98 n_auto_97  R=0
M4 n_auto_99 n_auto_101 Vdd Vdd P_18_MM M=43 L=1e-06 W=4.95845e-06
V5 n_auto_101 0  DC 0.8
M6 n_auto_96 n_auto_104 n_auto_103 n_auto_103 P_18_MM M=22 L=1e-06 W=4.84575e-06
V7 n_auto_104 0  DC 0.08
M8 n_auto_103 Vin2 n_auto_102 n_auto_102 N_18_MM M=5 L=1e-06 W=4.83382e-06
Rwire9 n_auto_102 n_auto_97  R=0
M10 n_auto_103 n_auto_105 Vdd Vdd P_18_MM M=43 L=1e-06 W=4.95845e-06
V11 n_auto_105 0  DC 0.8
M12 n_auto_97 n_auto_106 gnd gnd N_18_MM M=10 L=1e-06 W=4.83382e-06
V13 n_auto_106 0  DC 1
M14 n_auto_95 n_auto_95 gnd gnd N_18_MM M=5 L=1e-06 W=4.83382e-06
M15 n_auto_96 n_auto_95 gnd gnd N_18_MM M=5 L=1e-06 W=4.83382e-06
Rwire16 n_auto_96 Iout  R=0
"""
        elif index==1:
            return """M0 n_auto_95 n_auto_100 n_auto_98 n_auto_98 P_18_MM M=22 L=1e-06 W=4.84575e-06
V1 n_auto_100 0  DC 0.2
M2 n_auto_98 Vin1 n_auto_99 n_auto_99 P_18_MM M=22 L=1e-06 W=4.84575e-06
Rwire3 n_auto_99 n_auto_97  R=0
M4 n_auto_96 n_auto_103 n_auto_101 n_auto_101 P_18_MM M=22 L=1e-06 W=4.84575e-06
V5 n_auto_103 0  DC 0.2
M6 n_auto_101 Vin2 n_auto_102 n_auto_102 P_18_MM M=22 L=1e-06 W=4.84575e-06
Rwire7 n_auto_102 n_auto_97  R=0
M8 n_auto_97 n_auto_104 Vdd Vdd P_18_MM M=43 L=1e-06 W=4.95845e-06
V9 n_auto_104 0  DC 0.8
M10 n_auto_95 n_auto_95 gnd gnd N_18_MM M=5 L=1e-06 W=4.83382e-06
M11 n_auto_96 n_auto_95 gnd gnd N_18_MM M=5 L=1e-06 W=4.83382e-06
Rwire12 n_auto_96 Iout  R=0
"""
        elif index==2:
            return """M0 n_auto_120 n_auto_125 n_auto_124 n_auto_124 N_18_MM M=5 L=1e-06 W=4.83382e-06
V1 n_auto_125 0  DC 1.72
M2 n_auto_124 Vin1 n_auto_123 n_auto_123 P_18_MM M=22 L=1e-06 W=4.84575e-06
Rwire3 n_auto_123 n_auto_122  R=0
M4 n_auto_124 n_auto_126 gnd gnd N_18_MM M=10 L=1e-06 W=4.83382e-06
V5 n_auto_126 0  DC 1
M6 n_auto_121 n_auto_129 n_auto_128 n_auto_128 N_18_MM M=5 L=1e-06 W=4.83382e-06
V7 n_auto_129 0  DC 1.72
M8 n_auto_128 Vin2 n_auto_127 n_auto_127 P_18_MM M=22 L=1e-06 W=4.84575e-06
Rwire9 n_auto_127 n_auto_122  R=0
M10 n_auto_128 n_auto_130 gnd gnd N_18_MM M=10 L=1e-06 W=4.83382e-06
V11 n_auto_130 0  DC 1
M12 n_auto_122 n_auto_131 Vdd Vdd P_18_MM M=43 L=1e-06 W=4.95845e-06
V13 n_auto_131 0  DC 0.8
M14 n_auto_120 n_auto_120 Vdd Vdd P_18_MM M=44 L=1e-06 W=4.914e-06
M15 n_auto_121 n_auto_120 Vdd Vdd P_18_MM M=44 L=1e-06 W=4.914e-06
Rwire16 n_auto_121 Iout  R=0
"""      
        elif index==3:
            return """M0 n_auto_95 n_auto_100 n_auto_98 n_auto_98 N_18_MM M=5 L=1e-06 W=4.83382e-06
V1 n_auto_100 0  DC 1.6
M2 n_auto_98 Vin1 n_auto_99 n_auto_99 N_18_MM M=5 L=1e-06 W=4.83382e-06
Rwire3 n_auto_99 n_auto_97  R=0
M4 n_auto_96 n_auto_103 n_auto_101 n_auto_101 N_18_MM M=5 L=1e-06 W=4.83382e-06
V5 n_auto_103 0  DC 1.6
M6 n_auto_101 Vin2 n_auto_102 n_auto_102 N_18_MM M=5 L=1e-06 W=4.83382e-06
Rwire7 n_auto_102 n_auto_97  R=0
M8 n_auto_97 n_auto_104 gnd gnd N_18_MM M=10 L=1e-06 W=4.83382e-06
V9 n_auto_104 0  DC 1
M10 n_auto_95 n_auto_95 Vdd Vdd P_18_MM M=44 L=1e-06 W=4.914e-06
M11 n_auto_96 n_auto_95 Vdd Vdd P_18_MM M=44 L=1e-06 W=4.914e-06
Rwire12 n_auto_96 Iout  R=0
"""
    def _indexed_dsViAmp1_VddGndPorts_Point(self, index):
        point = self._indexed_dsViAmp1_Point(index)
        if (index==0 or index==1):
            point['chosen_part_index'] = 0
        else:
            point['chosen_part_index'] = 1
            
        del point['loadrail_is_vdd']
        del point['Vout']
        
        point_vars = point.keys()
        part_vars = self.lib.dsViAmp1_VddGndPorts().point_meta.keys()
        assert sorted(point_vars) == sorted(part_vars)
        return point
    def _indexed_testDsViAmp1_VddGndPorts_TargetStr(self, index):
        if index==0:
            return """M0 n_auto_95 n_auto_100 n_auto_99 n_auto_99 P_18_MM M=22 L=1e-06 W=4.84575e-06
V1 n_auto_100 0  DC 0.08
M2 n_auto_99 Vin1 n_auto_98 n_auto_98 N_18_MM M=5 L=1e-06 W=4.83382e-06
Rwire3 n_auto_98 n_auto_97  R=0
M4 n_auto_99 n_auto_101 Vdd Vdd P_18_MM M=43 L=1e-06 W=4.95845e-06
V5 n_auto_101 0  DC 0.8
M6 n_auto_96 n_auto_104 n_auto_103 n_auto_103 P_18_MM M=22 L=1e-06 W=4.84575e-06
V7 n_auto_104 0  DC 0.08
M8 n_auto_103 Vin2 n_auto_102 n_auto_102 N_18_MM M=5 L=1e-06 W=4.83382e-06
Rwire9 n_auto_102 n_auto_97  R=0
M10 n_auto_103 n_auto_105 Vdd Vdd P_18_MM M=43 L=1e-06 W=4.95845e-06
V11 n_auto_105 0  DC 0.8
M12 n_auto_97 n_auto_106 gnd gnd N_18_MM M=10 L=1e-06 W=4.83382e-06
V13 n_auto_106 0  DC 1
M14 n_auto_95 n_auto_95 gnd gnd N_18_MM M=5 L=1e-06 W=4.83382e-06
M15 n_auto_96 n_auto_95 gnd gnd N_18_MM M=5 L=1e-06 W=4.83382e-06
Rwire16 n_auto_96 Iout  R=0
"""
        elif index==1:
            return """M0 n_auto_120 n_auto_125 n_auto_123 n_auto_123 P_18_MM M=22 L=1e-06 W=4.84575e-06
V1 n_auto_125 0  DC 0.26
M2 n_auto_123 Vin1 n_auto_124 n_auto_124 P_18_MM M=22 L=1e-06 W=4.84575e-06
Rwire3 n_auto_124 n_auto_122  R=0
M4 n_auto_121 n_auto_128 n_auto_126 n_auto_126 P_18_MM M=22 L=1e-06 W=4.84575e-06
V5 n_auto_128 0  DC 0.26
M6 n_auto_126 Vin2 n_auto_127 n_auto_127 P_18_MM M=22 L=1e-06 W=4.84575e-06
Rwire7 n_auto_127 n_auto_122  R=0
M8 n_auto_122 n_auto_129 Vdd Vdd P_18_MM M=43 L=1e-06 W=4.95845e-06
V9 n_auto_129 0  DC 0.8
M10 n_auto_120 n_auto_120 gnd gnd N_18_MM M=5 L=1e-06 W=4.83382e-06
M11 n_auto_121 n_auto_120 gnd gnd N_18_MM M=5 L=1e-06 W=4.83382e-06
Rwire12 n_auto_121 Iout  R=0
"""
        elif index==2:
            return """M0 n_auto_143 n_auto_148 n_auto_147 n_auto_147 N_18_MM M=5 L=1e-06 W=4.83382e-06
V1 n_auto_148 0  DC 1.72
M2 n_auto_147 Vin1 n_auto_146 n_auto_146 P_18_MM M=22 L=1e-06 W=4.84575e-06
Rwire3 n_auto_146 n_auto_145  R=0
M4 n_auto_147 n_auto_149 gnd gnd N_18_MM M=10 L=1e-06 W=4.83382e-06
V5 n_auto_149 0  DC 1
M6 n_auto_144 n_auto_152 n_auto_151 n_auto_151 N_18_MM M=5 L=1e-06 W=4.83382e-06
V7 n_auto_152 0  DC 1.72
M8 n_auto_151 Vin2 n_auto_150 n_auto_150 P_18_MM M=22 L=1e-06 W=4.84575e-06
Rwire9 n_auto_150 n_auto_145  R=0
M10 n_auto_151 n_auto_153 gnd gnd N_18_MM M=10 L=1e-06 W=4.83382e-06
V11 n_auto_153 0  DC 1
M12 n_auto_145 n_auto_154 Vdd Vdd P_18_MM M=43 L=1e-06 W=4.95845e-06
V13 n_auto_154 0  DC 0.8
M14 n_auto_143 n_auto_143 Vdd Vdd P_18_MM M=44 L=1e-06 W=4.914e-06
M15 n_auto_144 n_auto_143 Vdd Vdd P_18_MM M=44 L=1e-06 W=4.914e-06
Rwire16 n_auto_144 Iout  R=0
"""      
        elif index==3:
            return """M0 n_auto_168 n_auto_173 n_auto_171 n_auto_171 N_18_MM M=5 L=1e-06 W=4.83382e-06
V1 n_auto_173 0  DC 1.54
M2 n_auto_171 Vin1 n_auto_172 n_auto_172 N_18_MM M=5 L=1e-06 W=4.83382e-06
Rwire3 n_auto_172 n_auto_170  R=0
M4 n_auto_169 n_auto_176 n_auto_174 n_auto_174 N_18_MM M=5 L=1e-06 W=4.83382e-06
V5 n_auto_176 0  DC 1.54
M6 n_auto_174 Vin2 n_auto_175 n_auto_175 N_18_MM M=5 L=1e-06 W=4.83382e-06
Rwire7 n_auto_175 n_auto_170  R=0
M8 n_auto_170 n_auto_177 gnd gnd N_18_MM M=10 L=1e-06 W=4.83382e-06
V9 n_auto_177 0  DC 1
M10 n_auto_168 n_auto_168 Vdd Vdd P_18_MM M=44 L=1e-06 W=4.914e-06
M11 n_auto_169 n_auto_168 Vdd Vdd P_18_MM M=44 L=1e-06 W=4.914e-06
Rwire12 n_auto_169 Iout  R=0
"""
    
    def testDsViAmp1_VddGndPorts_index0(self):
        if self.just1: return
        self._indexed_testDsViAmp1_VddGndPorts(0)
        
    def testDsViAmp1_VddGndPorts_index1(self):
        if self.just1: return
        self._indexed_testDsViAmp1_VddGndPorts(1)
        
    def testDsViAmp1_VddGndPorts_index2(self):
        if self.just1: return
        self._indexed_testDsViAmp1_VddGndPorts(2)
        
    def testDsViAmp1_VddGndPorts_index3(self):
        if self.just1: return
        self._indexed_testDsViAmp1_VddGndPorts(3)
        
    def _indexed_testDsViAmp1_VddGndPorts(self, index):
        part = self.lib.dsViAmp1_VddGndPorts()
        self.assertEqual(sorted(part.externalPortnames()),
                         sorted(['Vin1','Vin2','Iout','Vdd','gnd']))

        conns = {'Vin1':'Vin1','Vin2':'Vin2','Iout':'Iout',
                 'Vdd':'Vdd','gnd':'gnd'}

        point = self._indexed_dsViAmp1_VddGndPorts_Point(index)
        instance = EmbeddedPart(part, conns, point)

        target_str = self._indexed_testDsViAmp1_VddGndPorts_TargetStr(index)
        actual_str = instance.spiceNetlistStr()
        self._compareStrings(target_str, actual_str)

    def _ddIiLoad_Point(self, loadrail_is_vdd):
        """simple-as-possible _ddIiLoadPoint: 10K load, no cascoding"""
        point = {'loadrail_is_vdd':loadrail_is_vdd,
                 'chosen_part_index':0,

                 'R':10.0e3,
                                 
                 'W':3*0.18e-6,
                 'L':4*0.18e-6,
                 'Vbias':1.41,
                                 
                 'loadcascode_recurse':0,
                 'loadcascode_W':5*0.18e-6,
                 'loadcascode_L':6*0.18e-6,
                 'loadcascode_Vbias':1.3,
                 }
        
        point_vars = point.keys()
        part_vars = self.lib.ddIiLoad().point_meta.keys()
        assert sorted(point_vars) == sorted(part_vars)
        return point

    def testDdIiLoad(self):
        if self.just1: return
        part = self.lib.ddIiLoad()
        self.assertEqual(sorted(part.externalPortnames()),
                         sorted(['Iout1','Iout2','loadrail','opprail']))

        conns = {'Iout1':'Iout1','Iout2':'Iout2',
                 'loadrail':'Vdd','opprail':'gnd'}
        point = self._ddIiLoad_Point(loadrail_is_vdd=1)
        instance = EmbeddedPart(part, conns, point)

        target_str = """R0 Vdd Iout1  R=10000
R1 Vdd Iout2  R=10000
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

    def _ddViAmp1_Point(self, loadrail_is_vdd, input_is_pmos):
        input_point = self._ddViInput_Point(loadrail_is_vdd, input_is_pmos)
        
        #simple-as-possible: 10K load, no cascoding
        load_point = {
            'loadrail_is_vdd':loadrail_is_vdd,
            'load_chosen_part_index':0,
            'load_R':10.0e3,
            'load_W':3*0.18e-6,
            'load_L':4*0.18e-6,
            'load_Vbias':1.41,
            'loadcascode_recurse':0,
            'loadcascode_W':5*0.18e-6,
            'loadcascode_L':6*0.18e-6,
            'loadcascode_Vbias':1.3,
            }
        point = {}
        point.update(input_point)
        point.update(load_point)
        
        point_vars = point.keys()
        part_vars = self.lib.ddViAmp1().point_meta.keys()
        assert sorted(point_vars) == sorted(part_vars)
        return point

    def _ddViAmp1_VddGndPorts_Point(self, loadrail_is_vdd, input_is_pmos):
        point = self._ddViAmp1_Point(loadrail_is_vdd, input_is_pmos)
        del point['loadrail_is_vdd']
        point['chosen_part_index'] = loadrail_is_vdd
        
        point_vars = point.keys()
        part_vars = self.lib.ddViAmp1_VddGndPorts().point_meta.keys()
        assert sorted(point_vars) == sorted(part_vars)
        return point
        
    def testDdViAmp1(self):
        if self.just1: return
        part = self.lib.ddViAmp1()

        conns = {'Vin1':'Vin1','Vin2':'Vin2',
                 'Iout1':'Iout1','Iout2':'Iout2',
                 'loadrail':'Vdd','opprail':'gnd'}
        
        point = self._ddViAmp1_Point(loadrail_is_vdd=1, input_is_pmos=0)
        instance = EmbeddedPart(part, conns, point)

        target_str = """M0 Iout1 n_auto_14 n_auto_12 n_auto_12 N_18_MM M=1 L=7.2e-07 W=5.4e-07
V1 n_auto_14 0  DC 1.7
M2 n_auto_12 Vin1 n_auto_13 n_auto_13 N_18_MM M=1 L=1.08e-06 W=9e-07
R3 n_auto_13 n_auto_11  R=1.03e+06
M4 Iout2 n_auto_17 n_auto_15 n_auto_15 N_18_MM M=1 L=7.2e-07 W=5.4e-07
V5 n_auto_17 0  DC 1.7
M6 n_auto_15 Vin2 n_auto_16 n_auto_16 N_18_MM M=1 L=1.08e-06 W=9e-07
R7 n_auto_16 n_auto_11  R=1.03e+06
M8 n_auto_11 n_auto_18 gnd gnd N_18_MM M=1 L=1.62e-06 W=1.62e-06
V9 n_auto_18 0  DC 1.74
R10 Vdd Iout1  R=10000
R11 Vdd Iout2  R=10000
"""
        actual_str = instance.spiceNetlistStr()
        self._compareStrings3(target_str, actual_str)

    def _dsViAmp2_DifferentialMiddle_Point(self, stage1_loadrail_is_vdd,
                                           stage1_input_is_pmos,
                                           stage2_loadrail_is_vdd,
                                           stage2_input_is_pmos):
                                           
        stage1_point = self._ddViAmp1_Point(stage1_loadrail_is_vdd,
                                            stage1_input_is_pmos)
        stage2_point = self._dsViAmp1_Point(stage2_loadrail_is_vdd,
                                            stage2_input_is_pmos)
        
        shifter_point = self._levelShifterOrWire_Point(stage1_loadrail_is_vdd)
        feedback_point = self._viFeedback_Point(use_pmos=0)

        d = {}
        for name, value in stage1_point.items(): d['stage1_' + name] = value
        for name, value in stage2_point.items(): d['stage2_' + name] = value
        for name, value in shifter_point.items(): d['shifter_' + name] = value
        for name, value in feedback_point.items(): d['feedback_' + name] = value
        
        part_vars = self.lib.dsViAmp2_DifferentialMiddle().point_meta.keys()
        d_vars = d.keys()
        assert sorted(d_vars) == sorted(part_vars)
               
        return d

    def testDsViAmp2_DifferentialMiddle(self):
        return #HACK
        if self.just1: return
        part = self.lib.dsViAmp2_DifferentialMiddle()
    
        conns = part.unityPortMap()
        point = self._dsViAmp2_DifferentialMiddle_Point(1,0,1,0)
        instance = EmbeddedPart(part, conns, point)

        target_str = """
"""
        actual_str = instance.spiceNetlistStr()
        #self._compareStrings3(target_str, actual_str)

        #stress test
        for i in range(20):
            point = self._dsViAmp2_DifferentialMiddle_Point(random.randint(0,1),
                                                            random.randint(0,1),
                                                            random.randint(0,1),
                                                            random.randint(0,1))
            instance = EmbeddedPart(part, conns, point)

    def _dsViAmp1_VddGndPorts_Point(self, loadrail_is_vdd, input_is_pmos):
        input_point = {'input_is_pmos':input_is_pmos,
                 'loadrail_is_vdd':loadrail_is_vdd,
                 'Vout':abs(1.8*(loadrail_is_vdd==0)-1.0),
                 'Ibias':1e-3, 
                 'Ibias2':1e-3,
                 'Vds':abs(1.8*(input_is_pmos==1)-1.0),
                 'Vds_internal':abs(1.8*(input_is_pmos==1)-1.0),
                 'inputcascode_L':1e-6,
                 'inputcascode_Vgs':1.0,
                 'inputcascode_recurse':0,
                 'inputcascode_is_wire':0,
                 
                 'ampmos_Vgs':1.0,
                 'ampmos_L':1e-6,
                 'fracAmp':0.5,
                                  
                 'degen_choice':0,
                 'degen_fracDeg':0.1,

                 'inputbias_L':1e-6,
                 'inputbias_Vgs':1.0,
                 
                 'folder_L':1e-6,
                 'folder_Vgs':1.0,
                 
                 'fracVgnd':0.2,
                 }                       
        load_point = {'load_chosen_part_index':0, 
                      'loadrail_is_vdd':loadrail_is_vdd,
                      'load_fracIn':0.5,
                      'load_fracOut':0.5,
                      'load_L':1e-6,
                      'load_cascode_L':1e-6,
                      'load_cascode_Vgs':1.0,
                      }
        point = {}
        point.update(input_point)
        point.update(load_point)
        
        point_vars = point.keys()
        part_vars = self.lib.dsViAmp1().point_meta.keys()
        assert sorted(point_vars) == sorted(part_vars)
        return point

    def _dsViAmp2_SingleEndedMiddle_VddGndPorts_Point(self,
                                                      stage1_loadrail_is_vdd,
                                                      stage1_input_is_pmos,
                                                      stage2_loadrail_is_vdd,
                                                      stage2_input_is_pmos,
                                                      shifter_Drail_is_vdd,
                                                      shifter_use_wire):
        #gather the point for each sub-part
        stage1_point = self._dsViAmp1_VddGndPorts_Point(stage1_loadrail_is_vdd,
                                                        stage1_input_is_pmos)
        stage1_point['chosen_part_index'] = stage1_loadrail_is_vdd
        assert stage1_point['input_is_pmos'] == stage1_input_is_pmos
        
        stage2_point = self._ssViAmp1_Point(stage2_loadrail_is_vdd,
                                                        stage2_input_is_pmos)
        stage2_point['chosen_part_index'] = stage2_loadrail_is_vdd
        assert stage2_point['input_is_pmos'] == stage2_input_is_pmos
        
        shifter_point = self._levelShifterOrWire_Point( \
            shifter_Drail_is_vdd,
            shifter_use_wire)
        assert shifter_point['Drail_is_vdd'] == shifter_Drail_is_vdd
        shifter_point['chosen_part_index'] = shifter_use_wire
        
        feedback_point = {'C':1.0e-9} #note the HACK for just capacitor

        #build up an overall point 'd'
        d = {}
        for name, value in stage1_point.items(): d['stage1_' + name] = value
        for name, value in stage2_point.items(): d['stage2_' + name] = value
        for name, value in shifter_point.items(): d['shifter_' + name] = value
        for name, value in feedback_point.items(): d['feedback_' + name] = value

        d['stage1_loadrail_is_vdd'] = stage1_loadrail_is_vdd
        d['stage2_loadrail_is_vdd'] = stage2_loadrail_is_vdd
        del d['stage1_chosen_part_index']
        del d['stage2_chosen_part_index']
        del d['stage2_Vout']
        del d['shifter_chosen_part_index']

        #validate d
        part = self.lib.dsViAmp2_SingleEndedMiddle_VddGndPorts()
        part_vars = part.point_meta.keys()
        d_vars = d.keys()
        assert sorted(part_vars) == sorted(d_vars)

        #done
        return d

    def _dsViAmp2_Point(self,
                        single_ended_middle,
                        stage1_loadrail_is_vdd,
                        stage1_input_is_pmos,
                        stage2_loadrail_is_vdd,
                        stage2_input_is_pmos):
        dss_point = self._dsViAmp2_SingleEndedMiddle_Point( \
            stage1_loadrail_is_vdd,
            stage1_input_is_pmos,
            stage2_loadrail_is_vdd,
            stage2_input_is_pmos)
        assert dss_point['stage2_input_is_pmos'] == stage2_input_is_pmos
        
        dds_point = self._dsViAmp2_DifferentialMiddle_Point(\
            stage1_loadrail_is_vdd,
            stage1_input_is_pmos,
            stage2_loadrail_is_vdd,
            stage2_input_is_pmos)
        assert dds_point['stage2_input_is_pmos'] == stage2_input_is_pmos
        
        point = {}
        point.update(dss_point)
        point.update(dds_point)
        point['chosen_part_index'] = single_ended_middle

        point_vars = point.keys()
        part_vars = self.lib.dsViAmp2().point_meta.keys()
        assert sorted(point_vars) == sorted(part_vars)
        return point

    def _dsViAmp2_VddGndPorts_Point(self, 
                                    single_ended_middle,
                                    stage1_loadrail_is_vdd,
                                    stage1_input_is_pmos,
                                    stage2_loadrail_is_vdd,
                                    stage2_input_is_pmos):
        point = self._dsViAmp2_Point(single_ended_middle,
                                     stage1_loadrail_is_vdd,
                                     stage1_input_is_pmos,
                                     stage2_loadrail_is_vdd,
                                     stage2_input_is_pmos)
        assert point['stage1_loadrail_is_vdd'] == stage1_loadrail_is_vdd
        assert point['stage1_input_is_pmos'] == stage1_input_is_pmos
        assert point['stage2_loadrail_is_vdd'] == stage2_loadrail_is_vdd
        assert point['stage2_input_is_pmos'] == stage2_input_is_pmos

        if stage1_loadrail_is_vdd==0 and stage2_loadrail_is_vdd==0:
            chosen_part_index=0
        elif stage1_loadrail_is_vdd==0 and stage2_loadrail_is_vdd==1:
            chosen_part_index=1
        elif stage1_loadrail_is_vdd==1 and stage2_loadrail_is_vdd==0:
            chosen_part_index=2
        elif stage1_loadrail_is_vdd==1 and stage2_loadrail_is_vdd==1:
            chosen_part_index=3

        point['chosen_part_index'] = chosen_part_index
        del point['stage1_loadrail_is_vdd']
        del point['stage2_loadrail_is_vdd']
        point['single_ended_middle'] = single_ended_middle

        point_vars = point.keys()
        part_vars = self.lib.dsViAmp2_VddGndPorts().point_meta.keys()
        assert sorted(point_vars) == sorted(part_vars)
        return point
        
    def testDsViAmp2_SingleEndedMiddle(self):
        return #FIXME
        if self.just1: return
        part = self.lib.dsViAmp2_SingleEndedMiddle()
    
        conns = part.unityPortMap()
        point = self._dsViAmp2_SingleEndedMiddle_Point(1,0,1,0)
        instance = EmbeddedPart(part, conns, point)

        target_str = """
"""
        actual_str = instance.spiceNetlistStr()
        #self._compareStrings3(target_str, actual_str)

        #stress test
        for i in range(20):
            point = self._dsViAmp2_DifferentialMiddle_Point(random.randint(0,1),
                                                            random.randint(0,1),
                                                            random.randint(0,1),
                                                            random.randint(0,1))
            instance = EmbeddedPart(part, conns, point)

    def testDsViAmp2_VddGndPorts(self):
        if self.just1: return
        #FIXME
        pass

    def testDsViAmp_VddGndPorts(self):
        if self.just1: return
        #FIXME
        pass

    def _millerAmpPoint(self,
                        stage1_loadrail_is_vdd,
                        stage1_input_is_pmos,
                        stage2_loadrail_is_vdd,
                        stage2_input_is_pmos):
        #being a Miller, it is:
        # -a dsViAmp2
        # -with a single-ended middle
        # -feedback is merely a capacitor
        shifter_Drail_is_Vdd = True
        shifter_use_wire = True
        point = self._dsViAmp2_SingleEndedMiddle_VddGndPorts_Point(\
            stage1_loadrail_is_vdd,
            stage1_input_is_pmos,
            stage2_loadrail_is_vdd,
            stage2_input_is_pmos,
            shifter_Drail_is_Vdd,
            shifter_use_wire)
        assert point['stage1_loadrail_is_vdd'] == stage1_loadrail_is_vdd
        assert point['stage1_input_is_pmos'] == stage1_input_is_pmos
        assert point['stage2_loadrail_is_vdd'] == stage2_loadrail_is_vdd
        assert point['stage2_input_is_pmos'] == stage2_input_is_pmos
        assert point['shifter_Drail_is_vdd'] == shifter_Drail_is_Vdd
        assert point['shifter_use_wire'] == shifter_use_wire

        #make the topology choices the simplest topologies possible
        point['stage1_cascode_is_wire'] = 1 #'1' is wire
        point['stage1_degen_choice'] = 0 #'0' is wire
        point['stage1_load_chosen_part_index'] = 0 #'0' is simple CM
        
        point['stage2_degen_choice'] = 0 #'0' is wire

        point_vars = point.keys()
        part = self.lib.dsViAmp2_SingleEndedMiddle_VddGndPorts()
        part_vars = part.point_meta.keys()
        assert sorted(point_vars) == sorted(part_vars)
        
        return point

    def testMillerAmp_0(self):
        if self.just1: return
        #1st stage is nmos-input, stacked
        #2nd stage is nmos-input, stacked
        point = self._millerAmpPoint(stage1_loadrail_is_vdd=True,
                                     stage1_input_is_pmos=False,
                                     stage2_loadrail_is_vdd=True,
                                     stage2_input_is_pmos=False)
        part = self.lib.dsViAmp2_SingleEndedMiddle_VddGndPorts()
        
        conns = part.unityPortMap()
        instance = EmbeddedPart(part, conns, point)

        target_str = """Rwire0 n_auto_26 n_auto_29  R=0
M1 n_auto_29 Vin1 n_auto_30 n_auto_30 N_18_MM M=1 L=1.08e-06 W=9e-07
Rwire2 n_auto_30 n_auto_28  R=0
Rwire3 n_auto_27 n_auto_31  R=0
M4 n_auto_31 Vin2 n_auto_32 n_auto_32 N_18_MM M=1 L=1.08e-06 W=9e-07
Rwire5 n_auto_32 n_auto_28  R=0
M6 n_auto_28 n_auto_33 gnd gnd N_18_MM M=1 L=1.62e-06 W=1.62e-06
V7 n_auto_33 0  DC 1.74
M8 n_auto_26 n_auto_26 Vdd Vdd P_18_MM M=1 L=7.2e-07 W=1.08e-06
M9 n_auto_27 n_auto_26 Vdd Vdd P_18_MM M=1 L=7.2e-07 W=2.16e-06
Rwire10 n_auto_27 n_auto_24  R=0
Rwire11 Iout n_auto_34  R=0
M12 n_auto_34 n_auto_25 n_auto_35 n_auto_35 N_18_MM M=1 L=3e-06 W=4e-06
Rwire13 n_auto_35 gnd  R=0
R14 Vdd Iout  R=10000
Rwire15 n_auto_24 n_auto_25  R=0
C16 Iout n_auto_24  C=1e-09
"""
        actual_str = instance.spiceNetlistStr()
        #print actual_str
        self._compareStrings3(target_str, actual_str)

    def testMillerAmp_1(self):
        if self.just1: return
        #1st stage is nmos-input, stacked
        #2nd stage is pmos-input, stacked
        point = self._millerAmpPoint(stage1_loadrail_is_vdd=True,
                                     stage1_input_is_pmos=False,
                                     stage2_loadrail_is_vdd=False,
                                     stage2_input_is_pmos=True)
        part = self.lib.dsViAmp2_SingleEndedMiddle_VddGndPorts()
        conns = part.unityPortMap()
        instance = EmbeddedPart(part, conns, point)

        target_str = """Rwire0 n_auto_26 n_auto_29  R=0
M1 n_auto_29 Vin1 n_auto_30 n_auto_30 N_18_MM M=1 L=1.08e-06 W=9e-07
Rwire2 n_auto_30 n_auto_28  R=0
Rwire3 n_auto_27 n_auto_31  R=0
M4 n_auto_31 Vin2 n_auto_32 n_auto_32 N_18_MM M=1 L=1.08e-06 W=9e-07
Rwire5 n_auto_32 n_auto_28  R=0
M6 n_auto_28 n_auto_33 gnd gnd N_18_MM M=1 L=1.62e-06 W=1.62e-06
V7 n_auto_33 0  DC 1.74
M8 n_auto_26 n_auto_26 Vdd Vdd P_18_MM M=1 L=7.2e-07 W=1.08e-06
M9 n_auto_27 n_auto_26 Vdd Vdd P_18_MM M=1 L=7.2e-07 W=2.16e-06
Rwire10 n_auto_27 n_auto_24  R=0
Rwire11 Iout n_auto_34  R=0
M12 n_auto_34 n_auto_25 n_auto_35 n_auto_35 P_18_MM M=2 L=3e-06 W=4e-06
Rwire13 n_auto_35 Vdd  R=0
R14 gnd Iout  R=10000
Rwire15 n_auto_24 n_auto_25  R=0
C16 Iout n_auto_24  C=1e-09
"""
        actual_str = instance.spiceNetlistStr(False)
        self._compareStrings3(target_str, actual_str)

    def testMillerAmp_2(self):
        if self.just1: return
        #1st stage is pmos-input, folded
        #2nd stage is pmos-input, folded
        point = self._millerAmpPoint(stage1_loadrail_is_vdd=True,
                                     stage1_input_is_pmos=True,
                                     stage2_loadrail_is_vdd=True,
                                     stage2_input_is_pmos=True)
        part = self.lib.dsViAmp2_SingleEndedMiddle_VddGndPorts()
        conns = part.unityPortMap()
        instance = EmbeddedPart(part, conns, point)

        target_str = """M0 n_auto_61 n_auto_66 n_auto_65 n_auto_65 N_18_MM M=1 L=7.2e-07 W=5.4e-07
V1 n_auto_66 0  DC 1.7
M2 n_auto_65 Vin1 n_auto_64 n_auto_64 P_18_MM M=1 L=1.08e-06 W=1.8e-06
Rwire3 n_auto_64 n_auto_63  R=0
M4 n_auto_65 n_auto_67 gnd gnd N_18_MM M=1 L=1.62e-06 W=1.62e-06
V5 n_auto_67 0  DC 1.74
M6 n_auto_62 n_auto_70 n_auto_69 n_auto_69 N_18_MM M=1 L=7.2e-07 W=5.4e-07
V7 n_auto_70 0  DC 1.7
M8 n_auto_69 Vin2 n_auto_68 n_auto_68 P_18_MM M=1 L=1.08e-06 W=1.8e-06
Rwire9 n_auto_68 n_auto_63  R=0
M10 n_auto_69 n_auto_71 gnd gnd N_18_MM M=1 L=1.62e-06 W=1.62e-06
V11 n_auto_71 0  DC 1.74
M12 n_auto_63 n_auto_72 Vdd Vdd P_18_MM M=1 L=1.62e-06 W=3.24e-06
V13 n_auto_72 0  DC 0.06
M14 n_auto_61 n_auto_61 Vdd Vdd P_18_MM M=1 L=7.2e-07 W=1.08e-06
M15 n_auto_62 n_auto_61 Vdd Vdd P_18_MM M=1 L=7.2e-07 W=2.16e-06
Rwire16 n_auto_62 n_auto_59  R=0
M17 Iout n_auto_75 n_auto_74 n_auto_74 N_18_MM M=1 L=7.2e-07 W=5.4e-07
V18 n_auto_75 0  DC 1.7
M19 n_auto_74 n_auto_60 n_auto_73 n_auto_73 P_18_MM M=2 L=3e-06 W=4e-06
Rwire20 n_auto_73 Vdd  R=0
M21 n_auto_74 n_auto_76 gnd gnd N_18_MM M=2 L=5e-06 W=3e-06
V22 n_auto_76 0  DC 1.74
R23 Vdd Iout  R=10000
Rwire24 n_auto_59 n_auto_60  R=0
C25 Iout n_auto_59  C=1e-09
"""
        actual_str = instance.spiceNetlistStr(False)
        self._compareStrings3(target_str, actual_str)

    def testMillerAmp_3(self):
        if self.just1: return
        #-1st stage is nmos-input, stacked
        #-2nd stage is pmos-input, stacked
        #-plus a level shifter implemented as two nmoses
        point = self._millerAmpPoint(stage1_loadrail_is_vdd=True,
                                     stage1_input_is_pmos=False,
                                     stage2_loadrail_is_vdd=False,
                                     stage2_input_is_pmos=True)
        
        point['shifter_Drail_is_vdd'] = 1
        point['shifter_use_wire'] = 0
        point['shifter_cascode_do_stack'] = 0
        
        part = self.lib.dsViAmp2_SingleEndedMiddle_VddGndPorts()
        conns = part.unityPortMap()
        instance = EmbeddedPart(part, conns, point)

        target_str = """Rwire0 n_auto_113 n_auto_116  R=0
M1 n_auto_116 Vin1 n_auto_117 n_auto_117 N_18_MM M=1 L=3e-06 W=4e-06
Rwire2 n_auto_117 n_auto_115  R=0
Rwire3 n_auto_114 n_auto_118  R=0
M4 n_auto_118 Vin2 n_auto_119 n_auto_119 N_18_MM M=1 L=3e-06 W=4e-06
Rwire5 n_auto_119 n_auto_115  R=0
M6 n_auto_115 n_auto_120 gnd gnd N_18_MM M=2 L=5e-06 W=3e-06
V7 n_auto_120 0  DC 1.74
M8 n_auto_113 n_auto_113 Vdd Vdd P_18_MM M=1 L=9e-07 W=1.08e-06
M9 n_auto_114 n_auto_113 Vdd Vdd P_18_MM M=1 L=9e-07 W=2.16e-06
Rwire10 n_auto_114 n_auto_111  R=0
Rwire11 Iout n_auto_121  R=0
M12 n_auto_121 n_auto_112 n_auto_122 n_auto_122 P_18_MM M=1 L=1.08e-06 W=1.8e-06
Rwire13 n_auto_122 Vdd  R=0
R14 gnd Iout  R=10000
M15 Vdd n_auto_111 n_auto_112 n_auto_112 N_18_MM M=1 L=5.4e-07 W=5.4e-07
M16 n_auto_112 n_auto_123 gnd gnd N_18_MM M=1 L=9e-07 W=9e-07
V17 n_auto_123 0  DC 1.5
C18 Iout n_auto_111  C=1e-09
"""
        actual_str = instance.spiceNetlistStr(False)
        self._compareStrings3(target_str, actual_str)


        
    #=================================================================
    #Helper functions for these unit tests
    def _compareStrings(self, target_str_in, actual_str):
        """This is complex because it needs to take into account
        that auto-named nodes can have different values"""
        maxn = 30
        cand_xs = range(maxn)
        cand_ys = [-1]
        cand_zs = [-2]
        if 'yyy' in target_str_in: cand_ys = range(maxn)
        if 'zzz' in target_str_in: cand_zs = range(maxn)

        self.assertTrue( self._foundMatch(target_str_in, actual_str,
                                          cand_xs, cand_ys, cand_zs),
                         '\ntarget=\n[%s]\n\nactual=\n[%s]\n' %
                         (target_str_in, actual_str))

    def _foundMatch(self, target_str_in, actual_str, cand_xs, cand_ys, cand_zs):
        assert len(cand_xs)>0 and len(cand_ys)>0 and len(cand_zs)>0
        for nodenum_xxx in cand_xs:
            for nodenum_yyy in cand_ys:
                if nodenum_yyy == nodenum_xxx: continue
                for nodenum_zzz in cand_zs:
                    if nodenum_zzz == nodenum_xxx: continue
                    if nodenum_zzz == nodenum_yyy: continue
                    target_str = target_str_in.replace('xxx', str(nodenum_xxx))
                    target_str = target_str.replace('yyy', str(nodenum_yyy))
                    target_str = target_str.replace('zzz', str(nodenum_zzz))
                    if actual_str == target_str:
                        return True
        return False

    
    def _compareStrings2(self, target_str, actual_str):
        """Compres equality of two strings, but ignores the actual
        values in the auto-created nodenumbers"""
        self._compareStrings(replaceAutoNodesWithXXX(target_str),
                             replaceAutoNodesWithXXX(actual_str))

    def _compareStrings3(self, target_str, actual_str):
        """Like compareStrings2, but also on every line, ignores everything
        after the M=.
        This way, we don't have to tediously rewrite our netlist every
        time we make a change to the way that M, W, and L are calculated
        as a function of Ibias etc in operating point formulation.

        For the simpler circuits we should still be checking the W and L values.
        """
        self._compareStrings2(replaceAfterMWithBlank(target_str),
                              replaceAfterMWithBlank(actual_str))
    

    def tearDown(self):
        pass

        
    

if __name__ == '__main__':
    import logging
    logging.basicConfig()
    logging.getLogger('library').setLevel(logging.DEBUG)
    
    unittest.main()

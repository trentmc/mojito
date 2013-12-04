"""
A 'Pooler' continually yanks databases from many ongoing synth engine runs
and pools them all into one bigger DB.
"""

import cPickle as pickle
import os
import string
import time

from adts import *
from EngineUtils import AgeLayeredPop, \
     uniqueIndsByPerformance, SynthState, loadSynthState, \
     fastNondominatedSort, minMaxMetrics

import logging
log = logging.getLogger('pooler')

class PoolerStrategy: 
    """
    @description
      Holds 'magic numbers' related to strategy of running Pooler
      
    @attributes
      loop_wait_time -- int -- how often to wait between loops (in seconds)
      max_pool_size -- int -- max num inds in the pooled DB.  Suggest
        to set it to be about 'popsize' of one run
      just_one_iter -- bool -- just do one iteration of pooling
        (ie do 'aggregation').
    """

    def __init__(self, loop_wait_time, max_pool_size, just_one_iter):
        self.loop_wait_time = loop_wait_time
        self.max_pool_size = max_pool_size
        self.just_one_iter = just_one_iter

    def __str__(self):
        s = "PoolerStrategy={"
        s += ' loop_wait_time=%d seconds' % self.loop_wait_time
        s += '; max_pool_size=%d inds' % self.max_pool_size
        s += '; just_one_iter=%s' % self.just_one_iter
        s += " /PoolerStrategy}"  
        return s 

class Pooler:
    """
    @description
      Enables parallel computing with multiple concurrent SynthEngines.

      How:
      -Special case: do just one round of aggregation and dump into
      specified output file.
      -Usual case: Continually yanks databases from many ongoing SynthEngine
      runs and pools them all into one bigger DB, which can then be run
      by SynthEngines.

      Features:
      -Allows many asynchronous engines to run, without
       them depending on each other
      -Pooler does not rely on all (or any) of them being ok
      -A pooler can be stopped and started anytime.
      
    @attributes
      ps -- ProblemSetup object -- must be the same as that
        which the SynthEngine sees
      ss -- None OR PoolerStrategy object -- if None, then it
       will only do one round of pooling (i.e. 'aggregate'), otherwise
       it will do normal pooling.
      db_dirs_file -- string -- file which has list of db_dirs.  This
        is read in periodically, which means that the user
        can change its contents if he wants to add more db_dirs (or
        remove db_dirs)
      pooled_db_file -- string -- name of the file that stores the pooled
        data of all the dbs
    """

    def __init__(self, ps, ss, db_dirs_file, pooled_db_file):
        """        
        @arguments
          ps -- see class descriptoin
          ss -- ''
          db_dirs_file -- ''
          pooled_db_file -- ''
        
        @return
           Pooler object
        """
        self.ps = ps
        self.ss = ss
        
        self.db_dirs_file = os.path.abspath(db_dirs_file)
        assert os.path.exists(self.db_dirs_file), self.db_dirs_file

        self.pooled_db_file = os.path.abspath(pooled_db_file)
            

    def run(self):
        """
        @description

          Runs the Pooler, which basically puts it into a continuous loop of:
          1. read db_dirs_file to get latest set of dbs to go for
          2. read each db in
          3. pool all the db results into one big db
          4. save the pooled file
          5. wait a while
          6. goto 1
        
        @arguments
          <<none>>
        
        @return
           <<none>> but it continually generates pooled_db_file
        """
        log.info('======================================================')
        log.info("Begin.")
        log.info(str(self.ss) + "\n")
        log.info('db_dirs_file=%s' % self.db_dirs_file)
        log.info('pooled_db_file=%s' % self.pooled_db_file)
        
        while True:
            self.run__OneIteration()
            if self.ss.just_one_iter:
                log.info('Done aggregation.')
                break
            
    def run__OneIteration(self):
        """Run one iteration of Pooler"""

        log.info('======================================================')
        log.info('Begin new Pooler iteration')

        #1. read db_dirs_file to get latest set of dbs to go for
        f = open(self.db_dirs_file, 'r')
        lines_list = f.readlines()
        f.close()
        db_dirs = string.join(lines_list).split()
        log.info('Will try to read from these db_dirs: %s' % db_dirs)

        #2. read each db in (it's ok if a db doesn't exist)
        #3. pool all the db results into one big db
        all_inds = []
        num_dbs_found = 0
        synth_ss = None #set this using the first decent db we find
        for db_dir in db_dirs:
            #try to retrieve a db file; catch possible problems.
            if len(db_dir)>0 and db_dir[-1] != '/':
                db_dir = db_dir + '/'
            log.info('Try retrieving from db_dir=%s ...' % db_dir)
            if not os.path.exists(db_dir):
                log.info('  Could not find db_dir, so ignoring it')
                continue
            db_file = self._newestStateGenFile(db_dir)
            if db_file is None:
                log.info('  No relevant dbs in db_dir yet')
                continue
            try:
                synth_state = loadSynthState(db_file, self.ps)
            except:
                log.info('  Could not loadSynthState from db_file=%s' % db_file)
                continue

            #retrieved a db file, so add to all_inds
            num_dbs_found += 1
            inds = synth_state.allInds()
            log.info('  Found %d inds in %s' % (len(inds), db_file))
            max_num_inds_from_db = max(1, self.ss.max_pool_size / 3)
            if synth_ss is None:
                synth_ss = synth_state.ss
            inds_from_db = self._bestInds(inds, max_num_inds_from_db,
                                          synth_ss.metric_weights)
            all_inds.extend(inds_from_db)
            log.info('  Added %d of those inds to pooled_inds (pruned some)' %
                     len(inds_from_db))

        # -no info to work with, so try later
        log.info('Num dbs found = %d' % num_dbs_found)
        if num_dbs_found == 0:
            time.sleep(max(self.ss.loop_wait_time, 60))
            return

        #4. save the pooled file
        # -DO prune it down to the best inds
        log.info('Prune down pooled_inds via fast nondominated sort...')
        target_num_best = self.ss.max_pool_size
        pooled_inds = self._bestInds(all_inds, target_num_best,
                                     synth_ss.metric_weights)
        log.info('Done prune')
        synth_state = SynthState(self.ps, synth_ss,
                                 AgeLayeredPop([pooled_inds]))

        # -we may have trouble saving to the file if another process
        #  is accessing it, so just keep retrying until good
        while True:
            log.info('Try saving %d pruned-pooled inds to file %s' %
                     (len(pooled_inds), self.pooled_db_file))
            try:
                synth_state.save(self.pooled_db_file)
                log.info('Successfully saved')
                break
            except:
                time.sleep(3)
                pass

        #5. wait a while
        log.info('Done pooler iteration; pause for %s seconds' %
                 self.ss.loop_wait_time)
        time.sleep(self.ss.loop_wait_time)

        #6. then repeat!

    def _bestInds(self, inds, target_num_best, metric_weights):
        """
        @description

        Returns 'target_num_best' inds.
        
        How:
        -unique-ifies inds
        -does nondominated sort to get 'F'
        -takes the inds from the best layers of F first
        """
        num_before = len(inds)
        inds = uniqueIndsByPerformance(inds)
        log.info('From %d inds, %d inds are unique' % (num_before, len(inds)))
        
        minmax = minMaxMetrics(self.ps, inds)
        F = fastNondominatedSort(inds, minmax, max_num_inds=target_num_best,
                                 metric_weights=metric_weights)
        best_inds = []
        for layer_i, layer_inds in enumerate(F):
            best_inds.extend(layer_inds)
            if len(best_inds) >= target_num_best:
                best_inds[target_num_best:] = []
                break
        #could prune the last level more intelligently, ie based on crowding
        # but don't bother here
        return best_inds

    def _newestStateGenFile(self, db_dir):
        """
        @description
          Returns the name of the newest 'state_genXXX'db' file in 'db_dir'.
          (Returns None if no state_gen files are found.)
        """
        max_ctime = float('-Inf')
        newest_filename = None
        for filename in os.listdir(db_dir):
            if not 'state_gen' in filename: continue
            ctime = os.path.getctime(db_dir + filename)
            if ctime > max_ctime:
                max_ctime = ctime
                newest_filename = db_dir + filename
        return newest_filename

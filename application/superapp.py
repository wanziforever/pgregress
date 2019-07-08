"""Different testing scenario means different testing execution control
procedure, it is hard to forecast scenarios in future, so what we need
to do is providing a flexible way to implement new scenario logic to the
system. here we use the application and profile binding way to let a
specified application to run a specified profile. this has a limitation
that one profile should contain one kind of testcase.
"""

from dbserver import DBServer
from dbserver import get_installation_bin_path
from dbserver import get_installation_lib_path
#from utils.file import create_directory
import time
import datetime
import logging
import threading
import os
import config
import subprocess

_PORT = config.port
_DBNAME = config.dbname
_INSTALLDIR = config.installation
logger = logging.getLogger('SuperApp')

class SuperApp(object):
    """test progress coordination, one profile bind to one Application
       there are two kinds of Applications, this Application is for multisession.

    :type profile: :class:`Profile`
    :param profile: profile which bind to this application
    """
    def __init__(self, profile, checker):
        self.profile = profile
        self.checker = checker
        self._maint_session = None
        self._sessions = {}
        self.server = None
        self._clear_logs()
        self._start_time = None
        self._end_time = None
        self._fail_reason = {}
 

    def _clear_logs(self):
        """clear the postmaster log"""
        logfile = "%s/postmaster.log" % self.checker._logs_dir
        if not os.path.exists(logfile):
            # here i didn't check it is a file or a dir
            return
        logger.info("Cleanup the existed postmaster log")
        open(logfile, 'w').close()


    def _check_DB_ready(self):
        """whether PostgreSQL is accepting message

        although the process of the database server may be up, but it
        maybe cannot accept message, this function use psql to send
        message to check whether the server is really can handle message

        :rtype: Boolen
        :returns: whether the database server is running and can accept
                  message (means psql can connect to)
        """
        logger.info('TestMode:installcheck, check the PG server is running......')

        child = subprocess.run('ps -ef |grep postgres', shell=True, stdout=subprocess.PIPE)
        if child.returncode != 0:
            logger.info('Postgremaster process is NOT running, please confirm your DB is started!')
            exit()
        else:
            bin_path = get_installation_bin_path()
            psql = os.path.join(bin_path, 'psql')
            lib_path = get_installation_lib_path()
            logger.debug('DBServer::is_ready() bin: %s, lib: %s'
                         % (psql, lib_path))
            #env = {'LD_LIBRARY_PATH': lib_path,'HG_BASE':_INSTALLDIR}
            env = {'LD_LIBRARY_PATH': lib_path,'PGPASSWORD':'highgo123'}
            cmd = " ".join([
                psql, '-U', str(config.user), '-p', str(_PORT), str(_DBNAME), '<', '/dev/null'
                ])
            child = subprocess.run(
                cmd, shell=True, env=env, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
                )

            if child.returncode != 0:
                logger.debug("psql connect fail for reason %s"
                             % child.stderr)
                logger.info('DB server cannot be connected, please confirm your DB is ready!')
                exit()
        logger.info('PG server is ready,start to run test......')


    def _make_PGServer(self,data_path):
        """initialize a database instance, and start the database service

        ..note:
          before start the service, some parameters in configuration should
          be added or changed, they are mainly used to turn on enough logs
        """
        logger.info('TestMode:check,try to start a PG server......')
        DBServer.initDB(data_path)
        DBServer.set_dbconf(data_path,
                            port=_PORT,
                            log_autovacuum_min_duration='0',
                            log_checkpoints='on',
                            #log_line_prefix="'%m [%p] %q%a '",
                            log_lock_waits = 'on',
                            log_temp_files = '128kB',
                            max_prepared_transactions = '2')
        logger.info('TestMode:check,DONE to config file......')

        self.server = DBServer.start(data_path, self.checker._logs_dir)
        
        while not self.server.is_ready():
            logger.debug("keep trying to start the PostgreSQL service")
            time.sleep (1)

        logger.info('PG server is ready,start to run test......')

    def _clear_PGServer(self,data_path):
        #DBServer.stopDB(self.server,data_path)
        logger.info('TestMode:check,try to stop PG server......')
        DBServer.stopDB(data_path, self.checker._logs_dir)
        DBServer.removeDB(data_path)
        if DBServer.check_database_data_exist(data_path):
            raise Exception("fail to remove the DB data")
       
        logger.info('PG server is cleared')

    def _start_profile_prompt(self):
        now = datetime.datetime.now()
        print("+----------------------------------------")
        print(" Profile for %s" % self.profile.path)
        print(" Start at %s" % now.strftime("%Y-%m-%d %H:%M:%S"))
        print("----------------------------------------+")
        self._start_time = now

    def _end_profile_prompt(self):
        now = datetime.datetime.now()
        print("+----------------------------------------")
        print(" Profile for %s" % self.profile.path)
        print(" End at %s" % now.strftime("%Y-%m-%d %H:%M:%S"))
        print("----------------------------------------+")
        self._end_time = now

    def _start_batch_prompt(self,batch):
        now = datetime.datetime.now()
        print("----------start batch of test------------")
        print(" Start at %s" % now.strftime("%Y-%m-%d %H:%M:%S"))
        for test in batch.tests():
            print("  %s" % test.name())
        print("-----------------------------------------")

    def _end_batch_prompt(self,batch,results):
        now = datetime.datetime.now()
        print("----------end batch of test--------------")
        print(" End at %s" % now.strftime("%Y-%m-%d %H:%M:%S"))
        tests = batch.tests()
        for i in range(batch.len()):
            result = "ok" if results[i] is True else "fail"
            print("  %s ... %s" % (batch[i].name(), result))
        print("-----------------------------------------")


    def _start_testcase_prompt(self,testcase):
        now = datetime.datetime.now()
        print("+----------------------------------------")
        print(" TestRunner for %s" % testcase.name())
        print(" Start at %s" % now.strftime("%Y-%m-%d %H:%M:%S"))
        print("----------------------------------------+")


    def _end_testcase_prompt(self,testcase,result):
        now = datetime.datetime.now()
        print("+----------------------------------------")
        #print(" TestRunner for %s" % testcase)
        print(" Case end at %s" % now.strftime("%Y-%m-%d %H:%M:%S"))
        result = "ok" if result else "fail"
        print("  %s ... %s" % (testcase.name(), result))
        print("----------------------------------------+")


    def run(self,test_mode):
        """base the profile configration, start the test
        """

        self._start_profile_prompt()
        self.checker._check_directories()
       

        if test_mode == 'check':
            data_path = './tmp_instance/data'
            self._make_PGServer(data_path)
        else:
            data_path = config.data_path
            self._check_DB_ready()

        if self.profile.use_schedule():
            schedule = self.profile.schedule()
            batch = schedule.next_batch()

            while batch:
                if batch.len() > 1:
                    self._start_batch(batch)
                else:
                    self._start_test(batch.tests()[0])
                batch = schedule.next_batch()
        else:

            case = self.profile.next_case()
            while case:
                self._start_test(case)
                case = self.profile.next_case()

        logger.debug("cases run out!")
 
        if test_mode == 'check':
            self._clear_PGServer(data_path)

        self._end_profile_prompt()
        logger.info("calculate the report data")
        self.checker._reportdata_gen(self._start_time,self._end_time)


    def _start_batch(self, batch):
        """execute a batch of test cases parallelly

        if there is on one test case in the batch, just run it singlly
        """
        print("super application function, cutomzied class will re-write it")


    def _start_test(self, testcase):
        """run the test case singly, one by one
        """
        print("application function, cutomzied class will re-write it")

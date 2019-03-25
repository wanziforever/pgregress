"""Different testing scenario means different testing execution control
procedure, it is hard to forecast scenarios in future, so what we need
to do is providing a flexible way to implement new scenario logic to the
system. here we use the application and profile binding way to let a
specified application to run a specified profile. this has a limitation
that one profile should contain one kind of testcase.
"""

from dbserver import DBServer
#from utils.file import create_directory
import time
import logging
import threading
import os
import config
from report import ProfileReport

_DATA_PATH = './tmp_instance/data'
_LOG_PATH = './tmp_instance/log'
_PORT = config.port
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
        logger.info("clear the postmaster log before test start")
        open(logfile, 'w').close()

    def _make_PGServer(self):
        """initialize a database instance, and start the database service

        ..note:
          before start the service, some parameters in configuration should
          be added or changed, they are mainly used to turn on enough logs
        """
        DBServer.initDB(_DATA_PATH)
        DBServer.set_dbconf(_DATA_PATH,
                            port=_PORT,
                            log_autovacuum_min_duration='0',
                            log_checkpoints='on',
                            log_line_prefix="'%m [%p] %q%a '",
                            log_lock_waits = 'on',
                            log_temp_files = '128kB',
                            max_prepared_transactions = '2')

        self.server = DBServer.start(_DATA_PATH, self.checker._logs_dir)
        
        while not self.server.is_ready():
            logger.debug("trying to start the PostgreSQL service")
            time.sleep (1)

        logger.debug('PG server is ready to accept message')

    def _clear_PGServer(self):
        self.server.stop(_DATA_PATH)
        DBServer.removeDB(_DATA_PATH)
        if DBServer.check_database_data_exist(_DATA_PATH):
            raise Exception("fail to remove the DB data")

    def _start_profile_prompt(self):
        import datetime
        now = datetime.datetime.now()
        print("+----------------------------------------")
        print(" Profile for %s" % self.profile.path)
        print(" Start at %s" % now.strftime("%Y-%m-%d %H:%M:%S"))
        print("----------------------------------------+")
        self._start_time = now

    def _end_profile_prompt(self):
        import datetime
        now = datetime.datetime.now()
        print("+----------------------------------------")
        print(" Profile for %s" % self.profile.path)
        print(" End at %s" % now.strftime("%Y-%m-%d %H:%M:%S"))
        print("----------------------------------------+")
        self._end_time = now
        
    def run(self):
        """base the profile configration, start the test
        """
        print("application run function, cutomzied class will re-write it")

    def _start_batch(self, batch):
        """execute a batch of test cases parallelly

        if there is on one test case in the batch, just run it singlly
        """
        print("super application function, cutomzied class will re-write it")


    def _start_test(self, testcase):
        """run the test case singly, one by one
        """
        print("application function, cutomzied class will re-write it")

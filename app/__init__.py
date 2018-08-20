"""Different testing scenario means different testing execution control
procedure, it is hard to forecast scenarios in future, so what we need
to do is providing a flexible way to implement new scenario logic to the
system. here we use the application and profile binding way to let a
specified application to run a specified profile. this has a limitation
that one profile should contain one kind of testcase.
"""

from dbserver import DBServer
from utils.file import create_directory
import time
import logging
import threading
import os

logger = logging.getLogger('application')
_DATA_PATH = './tmp_instance/data'
_LOG_PATH = './tmp_instance/log'

def capture_runner_output(proc, logfile, to_screen=True):
    """ this is called by a new thread, so that it can capture the log
    with blocking the main thread

    :type proc: :class:`subprocess.Popen`
    :param proc: the return by subprocess.Popen function call
    
    :type logfile: str
    :param logfile: the log file absoute path
    
    :type to_screen: bool
    :param to_screen: indicate whether duplicated the log to screen

    ..note:
      currently not taking care of the thread end running staffing
    """
    logger.debug("capture log to %s" % logfile)
    runner_logger = logging.getLogger("Runner")
    with open(logfile, 'w') as fd:
        for line in iter(proc.stdout.readline, ''):
            if to_screen:
                runner_logger.info(line.strip())
            fd.write('%s' % line)
            # flush the data to disk in real time
            fd.flush()

class Application(object):
    """test progress coordination, one profile bind to one Application

    :type profile: :class:`Profile`
    :param profile: profile which bind to this application
    """
    def __init__(self, profile):
        self.profile = profile
        self._outputs_dir = os.path.join(profile.path, 'outputs')
        self._results_dir = os.path.join(self._outputs_dir, 'results')
        self._logs_dir = os.path.join(self._outputs_dir, 'logs')
        self._maint_session = None
        self._sessions = {}
        self.server = None

        self._make_directories()
        self._clear_logs()

    def _make_directories(self):
        """prepare the required directories
        """
        if self._outputs_dir:
            create_directory(self._outputs_dir)

        if self._results_dir:
            create_directory(self._results_dir)

        if self._logs_dir:
            create_directory(self._logs_dir)

    def _clear_logs(self):
        """clear the postmaster log"""
        logfile = "%s/postmaster.log" % self._logs_dir
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
                            port=5433,
                            log_autovacuum_min_duration='0',
                            log_checkpoints='on',
                            log_line_prefix="'%m [%p] %q%a '",
                            log_lock_waits = 'on',
                            log_temp_files = '128kB',
                            max_prepared_transactions = '2')

        self.server = DBServer.start(_DATA_PATH, self._logs_dir)
        
        while not self.server.is_ready():
            logger.debug("trying to start the PostgreSQL service")
            time.sleep (1)

        logger.debug('PG server is ready to accept message')

    def _clear_PGServer(self):
        self.server.stop()
        DBServer.removeDB(_DATA_PATH)
        
    def run(self):
        case = self.profile.next_case()
        while case:
            logger.debug("processing case \n%s" % str(case))
            
            self._start_test(case)
            
            case = self.profile.next_case()

        logger.debug("cases run out!")

    def _start_test(self, testcase):
        from runner import TestRunner
        
        self._make_PGServer()

        self._testrunner_start_prompt(testcase)
        
        # here why we want to run the testcase in a seperate process is
        # to capture the pure output of the testcase runner. run testcase
        # in the same process with app will mix all the output of app or
        # the other module.
        # and also i want the test runner to be more independent, i can
        # run seperately in a umltiprocess or just run serately in shell

        # here is a multiprocess solution, but it's found that it is not
        # a easy thing to capture the output of the new process, it does
        # not support stdout/stderr redirect to PIPE
        # import multiprocessing
        # p = multiprocessing.Process(target=TestRunner(testcase).run)
        # p.start()
        # p.join()


        # here try the subprocess way, here i use run method ofsubprocess
        # it is easy to use, but it only can wait until the tool finish,
        # then print the output, for complext case (timeout test), it is
        # not a good experience, so will change to Popen and communicate
        # method instead.
        import subprocess
        child = subprocess.Popen(
            ['python', '-u', 'runner/testrunner.py', testcase],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            universal_newlines=True
            )
        
        case_name = os.path.basename(os.path.splitext(testcase)[0])
        result_file = os.path.join(self._results_dir, case_name+".out")
        # Popen communicate is not good, since it will block until the
        # the runner finish and then we can get the output, here we use
        # a thread to monitor the runner tool, and print the stdout
        # content to screen and result file in real time
        t = threading.Thread(target=capture_runner_output,
                             args=(child, result_file))
        t.start()
        child.wait()
        
        self._testrunner_end_prompt(testcase)
        
        # self._capture_outputs(testcase,
        #                       child.stdout.decode('ascii'),
        #                       child.stderr.decode("ascii"))
        
        self._clear_PGServer()

    def _testrunner_start_prompt(self, testcase):
        import datetime
        now = datetime.datetime.now()
        print("+----------------------------------------")
        print(" TestRunner for %s" % testcase)
        print(" Start at %s" % now.strftime("%Y-%m-%d %H:%M:%S"))
        print("----------------------------------------+")

    def _testrunner_end_prompt(self, testcase):
        import datetime
        now = datetime.datetime.now()
        print("+----------------------------------------")
        #print(" TestRunner for %s" % testcase)
        print(" End at %s" % now.strftime("%Y-%m-%d %H:%M:%S"))
        print("----------------------------------------+")

    def _capture_outputs(self, testcase, out, err):
        case_name = os.path.basename(os.path.splitext(testcase)[0])
        result_file = os.path.join(self._results_dir, case_name+".out")
        
        logger.debug("save the case result to file %s" % result_file)
        with open(result_file, 'w') as fd:
            fd.write(out)

        if not err:
            return 

        with open(result_file, 'a') as fd:
            fd.write(err)
        

    def _diff(self):
        pass

    def _capture_logs(self):
        pass

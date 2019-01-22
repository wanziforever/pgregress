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

logger = logging.getLogger('application')
_DATA_PATH = './tmp_instance/data'
_LOG_PATH = './tmp_instance/log'
_PORT = config.port

RUNNER_LOG_TO_SCREEN = config.runner_output_to_streen

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
    runner_logger = logging.getLogger("MultiRunner")
    with open(logfile, 'w') as fd:
        for line in iter(proc.stdout.readline, ''):
            if to_screen:
                runner_logger.info(line.strip())
            fd.write('%s' % line)
            # flush the data to disk in real time
            fd.flush()

class Application(object):
    """test progress coordination, one profile bind to one Application
       there are two kinds of Applications, this Application is for multisession.

    :type profile: :class:`Profile`
    :param profile: profile which bind to this application
    """
    def __init__(self, profile, checker):
        self.profile = profile
        self.checker = checker
        '''
        self._outputs_dir = os.path.join(profile.path, 'outputs')
        self._results_dir = os.path.join(self._outputs_dir, 'results')
        self._expected_dir = os.path.join(profile.path, 'expected')
        self._logs_dir = os.path.join(self._outputs_dir, 'logs')
        self._report_file_html = os.path.join(self._outputs_dir, "report.html")
        self._report_file_text = os.path.join(self._outputs_dir, "report.txt")
        self._report = ProfileReport(self.profile.name)
        '''
        self._maint_session = None
        self._sessions = {}
        self.server = None
        self._clear_logs()
        self._start_time = None
        self._end_time = None
        self._fail_reason = {}
 
    '''
    def _check_directories(self):
        """prepare the required directories
        """
        if self._outputs_dir:
            create_directory(self._outputs_dir)

        if self._results_dir:
            create_directory(self._results_dir)

        if self._logs_dir:
            create_directory(self._logs_dir)

        if self._expected_dir:
            if not os.path.exists(self._expected_dir):
                raise Exception("cannot find the expected directory")
    '''       

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
        self._start_profile_prompt()
        self.checker._check_directories()

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
        self._end_profile_prompt()

    def _start_batch(self, batch):
        """execute a batch of test cases parallelly

        if there is on one test case in the batch, just run it singlly
        """
        def start_prompt():
            import datetime
            now = datetime.datetime.now()
            print("----------start batch of test------------")
            print(" Start at %s" % now.strftime("%Y-%m-%d %H:%M:%S"))
            for test in batch.tests():
                print("  %s" % test.name())
            print("-----------------------------------------")

        def end_prompt(results):
            import datetime
            now = datetime.datetime.now()
            print("----------end batch of test--------------")
            print(" End at %s" % now.strftime("%Y-%m-%d %H:%M:%S"))
            tests = batch.tests()
            for i in range(batch.len()):
                result = "ok" if results[i] is True else "fail"
                print("  %s ... %s" % (batch[i].name(), result))
            print("-----------------------------------------")

        start_prompt()

        self._make_PGServer()

        import subprocess
        processes = []
        env = os.environ.copy()

        for case in batch.tests():
            child = subprocess.Popen(
                ['python3', '-u', 'runner/testrunner.py', case.path()],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True, env=env
                )
        
            result_file = os.path.join(self.checker._results_dir,
                                       case.name()+".out")

            t = threading.Thread(target=capture_runner_output,
                                 args=(child, result_file,
                                       RUNNER_LOG_TO_SCREEN))
            t.start()
            processes.append(child)

        for child in processes:
            child.wait()

        diff_results = self.checker._make_many_diff(batch.tests())
        
        self._clear_PGServer()

        end_prompt(diff_results)

        '''
        for i in range(batch.len()):
            if diff_results[i] is False:
                self._report.add_case_info(batch[i].name(),
                                           diff_results[i],
                                           '目标结果比对错误')
            else:
                self._report.add_case_info(batch[i].name(),
                                           diff_results[i], '')
        ''' 

    def _start_test(self, testcase):
        """run the test case singly, one by one
        """
        logger.debug("processing case \n%s" % str(testcase))

        def start_prompt():
            import datetime
            now = datetime.datetime.now()
            print("+----------------------------------------")
            print(" TestRunner for %s" % testcase.name())
            print(" Start at %s" % now.strftime("%Y-%m-%d %H:%M:%S"))
            print("----------------------------------------+")

        def end_prompt(result):
            import datetime
            now = datetime.datetime.now()
            print("+----------------------------------------")
            #print(" TestRunner for %s" % testcase)
            print(" Case end at %s" % now.strftime("%Y-%m-%d %H:%M:%S"))
            result = "ok" if result else "fail"
            print("  %s ... %s" % (testcase.name(), result))
            print("----------------------------------------+")
            

        self._make_PGServer()
        
        start_prompt()
        
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
            ['python3', '-u', 'runner/testrunner.py', testcase.path()],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            universal_newlines=True
            )
        
        result_file = os.path.join(self.checker._results_dir,
                                   testcase.name()+".out")
        # Popen communicate is not good, since it will block until the
        # the runner finish and then we can get the output, here we use
        # a thread to monitor the runner tool, and print the stdout
        # content to screen and result file in real time
        t = threading.Thread(target=capture_runner_output,
                             args=(child, result_file,
                                   RUNNER_LOG_TO_SCREEN))
        t.start()
        child.wait()

        diff_result = self.checker._make_diff(testcase)

        self._clear_PGServer()
        
        end_prompt(diff_result)
       
        '''
        if diff_result is False:
            self._report.add_case_info(testcase.name(),
                                       diff_result,
                                       '目标结果比对错误')
        else:
            self._report.add_case_info(testcase.name(),
                                       diff_result, '')
        '''

    def _capture_outputs(self, testcase, out, err):
        case_name = os.path.basename(os.path.splitext(testcase)[0])
        result_file = os.path.join(self.checker._results_dir, case_name+".out")
        
        logger.debug("save the case result to file %s" % result_file)
        with open(result_file, 'w') as fd:
            fd.write(out)

        if not err:
            return 

        with open(result_file, 'a') as fd:
            fd.write(err)



'''

   def _make_many_diff(self, manycases):
        """have a verify of specified test cases

        :type manycases: list of :class:`testcase.TestCaseDesc`
        :param manycase: specified test cases to make diff

        :rtype: list of Boolean
        :returns: the diff results of specified test cases
        """
        results = []
        for case in manycases:
            results.append(self._make_diff(case))
            
        return results
    
    def _make_diff(self, case):
        """have a verify of specified test cases

        the verification will only use the simple diff command.
        verification support multiple version of result compare

        :type case: :class:`testcase.TestCaseDesc`
        :param case: specified test case to make diff

        :rtype: Boolean
        :returns: the diff result of specified test case
        """
        expected = os.path.join(self.checker._expected_dir, case.name()+".out")
        result = os.path.join(self.checker._results_dir, case.name()+".out")
        print("** case %s, make diff" % case.name())
        print("result:", result)
        print("expect:", expected)
        
        if not os.path.exists(expected):
            return False
        if not os.path.exists(result):
            return False

        import subprocess
        complete = subprocess.run(['diff', expected, result],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)

        if complete.returncode == 0:
            return True
            
        return False
    def report_gen(self):
        self._report.set_start_time(
            self._start_time.strftime("%Y-%m-%d %H:%M:%S")
            )
        self._report.set_end_time(
            self._end_time.strftime("%Y-%m-%d %H:%M:%S")
            )
        self._report.generate_report_html(self._report_file_html)
        self._report.generate_report_text(self._report_file_text)
'''

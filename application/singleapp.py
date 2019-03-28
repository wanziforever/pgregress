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
from application.superapp import SuperApp

logger = logging.getLogger('SingleApp')
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
    runner_logger = logging.getLogger("SingleRunner")
    with open(logfile, 'w') as fd:
        for line in iter(proc.stdout.readline, ''):
            if to_screen:
                runner_logger.info(line.strip())
            fd.write('%s' % line)
            # flush the data to disk in real time
            fd.flush()

class Application(SuperApp):
    """test progress coordination, one profile bind to one Application
       there are two kinds of Applications, this Application is for multisession.

    :type profile: :class:`Profile`
    :param profile: profile which bind to this application
    """
    def __init__(self, profile, checker):
        #super(SingleApp,self).__init__(profile,checker)       
        SuperApp.__init__(self,profile,checker)       
        
 
    def run(self):
        """base the profile configration, start the test
        """
        SuperApp._start_profile_prompt(self)
        self.checker._check_directories()

        if self.profile.use_schedule():
            schedule = self.profile.schedule()
            batch = schedule.next_batch()

            while batch:
                if batch.len() > 1:
                    self._start_batch(batch)
                else:
                    self._make_PGServer()
                    self._start_test(batch.tests()[0])
                    self._clear_PGServer()
                batch = schedule.next_batch()
        else:

            #for serial scheduled testcases, use one instance to run
            SuperApp._make_PGServer(self)
            case = self.profile.next_case()
            while case:
                self._start_test(case)
                case = self.profile.next_case()
            SuperApp._clear_PGServer(self)

        logger.debug("cases run out!")
        SuperApp._end_profile_prompt(self)
        logger.info("calculate the report data")
        self.checker._reportdata_gen(self._start_time,self._end_time)

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

        SuperApp._make_PGServer(self)
        import subprocess
        processes = []
        env = os.environ.copy()
        psql = os.path.join(config.installation,'bin/','psql')

        for case in batch.tests():
            child = subprocess.Popen(
                [psql, '-d',config.dbname,'-f', case.path()],
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
        
        SuperApp._clear_PGServer(self)

        end_prompt(diff_results)

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
            

        #self._make_PGServer()
        
        start_prompt()
        
        # here try the subprocess way, here i use run method ofsubprocess
        # it is easy to use, but it only can wait until the tool finish,
        # then print the output, for complext case (timeout test), it is
        # not a good experience, so will change to Popen and communicate
        # method instead.
        import subprocess
        psql = os.path.join(config.installation,'bin/','psql')

        child = subprocess.Popen(
            [psql, '-d',config.dbname,'-f', testcase.path()],
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

        end_prompt(diff_result)

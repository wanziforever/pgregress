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


logger = logging.getLogger('scriptapp')
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
    runner_logger = logging.getLogger("ScriptRunner")
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
        #super(ScriptApp,self).__init__(profile,checker)
        super().__init__(profile,checker)

    def _start_batch(self, batch):
        """execute a batch of test cases parallelly

        if there is on one test case in the batch, just run it singlly
        """

        super()._start_batch_prompt(batch)

        #super()._make_PGServer()

        import subprocess
        processes = []
        env = os.environ.copy()

        for case in batch.tests():
            child = subprocess.Popen(
                ['python3', '-u', 'runner/testrunner.py','-p', case.path()],
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
        
        #super()._clear_PGServer()

        super()._end_batch_prompt(batch,diff_results)


    def _start_test(self, testcase):
        """run the test case singly, one by one
        """
        logger.debug("processing case \n%s" % str(testcase))

        #super()._make_PGServer()
        
        super()._start_testcase_prompt(testcase)
        
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
            ['python3', '-u', 'runner/testrunner.py','-p', testcase.path()],
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

        #super()._clear_PGServer()
        
        super()._end_testcase_prompt(testcase,diff_result)

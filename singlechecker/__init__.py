import os
import logging
import subprocess
from report import ProfileReport
from utils.file import create_directory

logger = logging.getLogger("Checker")

class Checker(object):
    """
    This class is used to check the difference between profile's result and expected result, 
    then generate the report file.
    """
    def __init__(self,profile):
        self._path = profile.path
        self._outputs_dir = os.path.join(profile.path, 'outputs')
        self._results_dir = os.path.join(self._outputs_dir, 'results')
        self._expected_dir = os.path.join(profile.path, 'expected')
        self._logs_dir = os.path.join(self._outputs_dir, 'logs')
        self._report_html = os.path.join(self._outputs_dir, "report.html")
        self._report_txt = os.path.join(self._outputs_dir, "report.txt")
        self._report = ProfileReport(profile.name)
        self._check_directories()


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


    def _make_many_diff(self,manycases):
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
        expected = os.path.join(self._expected_dir, case.name()+".out")
        result = os.path.join(self._results_dir, case.name()+".out")
        print("** case %s, make diff" % case.name())
        print("result:", result)
        print("expect:", expected)
        
        if not os.path.exists(expected):
            return False
        if not os.path.exists(result):
            return False

        complete = subprocess.run(['diff', expected, result],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)

        if complete.returncode == 0:
            self._report.add_case_info(case,'True','目标结果对比成功')
            return True
            
        self._report.add_case_info(case,'False','目标结果对比错误')
        return False

    def _report_gen(self,start_time,end_time):
        self._report.set_start_time(
            start_time.strftime("%Y-%m-%d %H:%M:%S")
            )
        self._report.set_end_time(
            end_time.strftime("%Y-%m-%d %H:%M:%S")
            )
        self._report.generate_report_html(self._report_html)
        self._report.generate_report_text(self._report_txt)

import os
import logging
from testcase import TestCase

logger = logging.getLogger('profile')

def convert_abs_path(path):
    if path.startswith('/'):
        return path
    else:
        return os.path.realpath(os.path.join(os.getcwd(), path))

class Profile(object):
    """a test case holder, this is mainly used for a test case management,
    equal to a feather holding some test cases

    Args:
        path: str, the profile directory which to hold its test cases
        instruction: str, the profile instrction description strings
        cases: TestCase, the test case which is holded under this profile
        
    """
    def __init__(self, directory):
        self.path = convert_abs_path(directory)
        self.introduction = ""
        self._fill_instruction()
        self.cases = []
        self._build()
        self._current_case_pos = -1

    def _fill_instruction(self):
        """
        find a instruction file under the profile directory, if no file
        exist, just return empty
        """
        introduction_path = os.path.join(self.path, "introduction")
        if not os.path.exists(introduction_path):
            logger.info('there is no introduction for profile')
            self.instruction = ''
            return

        with open(introduction_path, 'r') as fd:
            self.introduction = fd.read()

    def next_case(self):
        if self._current_case_pos + 1 >= len(self.cases):
            return None
        self._current_case_pos += 1
        return self.cases[self._current_case_pos]

    def _build(self):
        """find all the test case under the profile directory"""
        for filename in os.listdir(self.path):
            if not filename.endswith('.spec'):
                continue
            testcase = TestCase(self, filename)
            testcase.build()
            self.cases.append(testcase)

    def is_end(self):
        if self._current_case_pos + 1 >= len(self.cases):
            return True
        return False

    def show(self):
        logger.info("profile location: %s" % self.path)
        logger.info("instruction: %s" % self.introduction)
        logger.info("cases: ")
        for case in self.cases:
            logger.info(case)

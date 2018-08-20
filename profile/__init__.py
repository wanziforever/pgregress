import os
import logging

logger = logging.getLogger('profile')

def convert_abs_path(path):
    if path.startswith('/'):
        return path
    else:
        return os.path.realpath(os.path.join(os.getcwd(), path))

class Profile(object):
    """a test case holder, this is mainly used for a test case management,
    equal to a feather holding some test cases

    :type path: str
    :param path: the profile directory which to hold its test cases
    
    :type instruction: str
    :param instruction: the profile instrction description strings
    """
    def __init__(self, directory):
        self.path = convert_abs_path(directory)
        self.introduction = ""
        self._fill_instruction()
        self._cases = []
        self._build()
        self._current_case_pos = -1

    def _fill_instruction(self):
        """find a instruction file under the profile directory, if no file
        exist, just return empty
        """
        introduction_path = os.path.join(self.path, "introduction")
        if not os.path.exists(introduction_path):
            logger.info('there is no introduction for profile')
            self.instruction = ''
            return

        with open(introduction_path, 'r') as fd:
            self.introduction = fd.read()

    def reset(self):
        self._current_case_pos = -1

    def next_case(self):
        """get the next case in the profile, the object will hold a pointer
        to the current case, if you want to reset to the beginning, just call
        reset() function
        """
        if self._current_case_pos + 1 >= len(self._cases):
            return None
        self._current_case_pos += 1
        return self._cases[self._current_case_pos]

    def _build(self):
        """find all the test case under the profile directory"""
        for filename in os.listdir(self.path):
            if not filename.endswith('.spec'):
                continue

            # not doing case build here, the build was moved to the
            # testRunner, since runner will be possibly a seperate
            # tool run in a serpate process, so only pass the case
            # absolusly path in command line is better then passing
            # case data in json which is too complict as a command
            # line argument
            #testcase = TestCase(self, filename)
            #testcase.build()
            
            full_case_path = os.path.join(self.path, filename)
            self._cases.append(full_case_path)

    def is_end(self):
        if self._current_case_pos + 1 >= len(self._cases):
            return True
        return False

    def show(self):
        logger.info("profile location: %s" % self.path)
        logger.info("instruction: %s" % self.introduction)
        logger.info("cases: ")
        for case in self._cases:
            logger.info(case)

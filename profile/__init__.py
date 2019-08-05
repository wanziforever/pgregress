import os
import logging
from utils.schedule import ScheduleCase

logger = logging.getLogger('profile')

def convert_abs_path(path):
    if path.startswith('/'):
        return path
    else:
        return os.path.realpath(os.path.join(os.getcwd(), path))

class Profile(object):
    """a test case holder, this is mainly used for a test case management,
    equal to a feather holding some test cases

    :type directory: str
    :param directory: the path of the profile directory

    :type use_schedule: Boolean
    :param use_schedule: whether use the schedule file as the test case
                         execution sequence management
    """
    def __init__(self, directory, use_schedule=True):
        self.path = convert_abs_path(directory)
        self.name = os.path.basename(self.path)
        self.introduction = ""
        self._fill_instruction()
        self._cases = []
        self._current_case_pos = -1
        self._schedule = None
        self._ptype = ""
        self._get_ptype()
        self._use_schedule = use_schedule
        self._build()

    def use_schedule(self):
        return self._use_schedule

    def schedule(self):
        return self._schedule

    def _get_ptype(self):
        """find the ptype file under the profile directory, if no file
        exit,set value to self._ptype, return empty
        """
        ptype_path = os.path.join(self.path, "ptype")
        if not os.path.exists(ptype_path):
            logger.error("there is no ptype file for this profile")
            exit()
        else:
            with open(ptype_path,'r') as fd:
                self._ptype = fd.read().strip()    
                logger.info("The session type for this profile is: %s" % self._ptype)

    def _fill_instruction(self):
        """find a instruction file under the profile directory, if no file
        exist, just return empty
        """
        introduction_path = os.path.join(self.path, "introduction")
        if not os.path.exists(introduction_path):
            logger.info('there is no introduction for profile')
            self.introduction = 'no introduction file'
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
        """build the testcase under the profile
        
        there are two mode of build method, one is base on schedule file,
        one is loop all the cases in the profile directory

        the schedule way is introduced after the loop all method, schedule
        made the testcase executed parallelled and execution sequence can
        be controled, this is the recommended way.
        """
        if self._use_schedule:
            schedule_file = os.path.join(self.path, "schedule")
            self._schedule = ScheduleCase(schedule_file)
            self._schedule.parse()
            return

        # old loop all method
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

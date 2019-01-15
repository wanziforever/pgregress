"""parse the test profile schedule file, provide interface to get the
scheduled testcase
"""

import sys
import os

import logging
from testcase import TestCaseDesc

logger = logging.getLogger("schedule")

class TestBatch(object):
    """a batch of tests
    
    :type tests: list of :class:`testcase.TestCaseDesc`
    :param tests: the test cases absolute path list in a batch
    """
    def __init__(self, tests=[]):
        self._tests = []
        for t in tests:
            if not self._validate_test(t):
                continue
            self._tests.append(t)

    def add(self, test):
        if not isinstance(test, TestCaseDesc):
            raise Exception('TestBatch only support adding TestCaseDesc')
        if not self._validate_test(test):
            return
        self._tests.append(test)
            
    def len(self):
        return len(self._tests)

    def tests(self):
        return self._tests
    
    def _validate_test(self, test):
        if not os.path.exists(test.path()):
            logger.warn("test file %s not exist, will ignore it" % test)
            return False
        return True

    def __str__(self):
        return " ".join(self._tests)

    def __getitem__(self, number):
        return self._tests[number]


class ScheduleCase(object):
    def __init__(self, schedule_file):
        self._file = schedule_file
        self._raw_data = ''
        with open(self._file, 'r') as fd:
            self._raw_data = fd.read()
        self._batches = []
        self._current_batches_idx = -1

    def show(self):
        print("there are %d batches of tests" % len(self._batches))
        for batch in self._batches:
            print(batch)

    def parse(self):
        """parse the schedule data file
        """
        if not self._raw_data:
            raise Exception("schedule not read file")
        
        print("PARSE  the schedulecase...... START!")
        for line in self._raw_data.splitlines():
            line = line.strip()
            # currently didnot need to support `ignore`
            if not line.startswith('test:'):
                continue
            _, tests_str = line.split(':')
            # all tests were seperated by blank
            names = tests_str.split()
            d = os.path.dirname(self._file)
            tb = TestBatch()
            for name in names:
                tb.add(TestCaseDesc(name, d))

            self._batches.append(tb)
        print(" PARSE  the schedulecase......DONE!")

    def next_batch(self):
        self._current_batches_idx += 1
        if self._current_batches_idx >= len(self._batches):
            return None
        return self._batches[self._current_batches_idx]
    

if __name__ == "__main__":
    if len(sys.argv) != 2:
        logger.error("ERROR: should take a schedule file path!")
        exit(1)
        
    logging.basicConfig(level=logging.DEBUG)
    schedule_file = sys.argv[1]
    s = ScheduleCase(schedule_file)
    s.parse()
    batch = s.next_batch()
    while batch:
        print(batch)
        batch = s.next_batch()
        

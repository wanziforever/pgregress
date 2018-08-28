import os
import json
import logging
from .case_parser import parse_testcase_structure

logger = logging.getLogger("TestCase")

class TestCaseDesc(object):
    """TestCase simple description

    :type name: str
    :param name: the name identifier of the test case

    :type path: str
    :param path: the directory of the test located
    """
    def __init__(self, name, directory):
        self._name = name
        self._directory = directory

    def name(self):
        return self._name

    def path(self):
        path = os.path.join(self._directory, self._name+".spec")
        return path

    def __str__(self):
        return self._name

    def __repr__(self):
        return "%s: %s" % (self._name, self.path())
        

class TestCase(object):
    """Test case constructor, parse the test case spec file content,
    and output content with command one my one which will be executed
    by command execution tool.

    :type path: str
    :param path: the absoluste path of the testcase
    """
    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(os.path.splitext(self.path)[0])
        self._file_content = ''
        self._command_pos = -1
        self._structure = None
        self._commands_sequence = []
        self._setups = []
        self._teardowns = []
        self._sessions = {}
        self._permutations = []
        # here is just a cache, also can do a list search each form the
        # sessions  each time
        self._step_mapping = {}

    def build(self):
        if self._structure is not None:
            return
        self._read_file_content()
        self._structure = parse_testcase_structure(self._file_content)
        self._build_internals()
        self._build_implicit_permutations()

    def _build_scenarios(self):
        index = 0
        for perm in self._permutations:
            sqls = self._build_commands_sequence(perm)
            self._scenarios.append({
                'name': 'scenario'+str(index),
                'commands': sqls
                })

    def _build_internals(self):
        """extract the data from the raw structures, and this will make
        other functions easyly to use the structure data"""
        if self._structure is None:
            return

        self._setups = list(self._structure['setup'])
        self._teardowns = list(self._structure['teardown'])
        self._sessions = dict(self._structure['sessions'])
        self._permutations = list(self._structure['permutations'])

    def __str__(self):
        """reurn two types of case description, one is builded version,
        one is unbuilded
        """
        if self._structure is None:
            return "caseName: %s, structure: unbuilded" % self.name
        
        setup_num = len(self._setups)
        teardown_num = len(self._teardowns)
        session_num = len(self._sessions.keys())
        permutation_num = len(self._permutations)
        
        return ("caseName: %s; "
                "structure: %d setup clauses, %d teardown clauses, "
                "%d sessions, %d permutations" %
                (self.name, setup_num, teardown_num, session_num,
                 permutation_num))

    def show(self):
        logger.info(self.__str__())

    def _read_file_content(self):
        with open(self.path, 'r') as fd:
            self._file_content = fd.read()
            
    def _build_implicit_permutations(self):
        """build implicit permutations, if there is no permutations provided
        in the testcase spec. the permutations will covered all the
        possibilities for crossing combination of all the sessions.

        ..note:
          if there is permutations in the testcase spec, that means the case
          just only support serveral specific permutations, and only these
          permutations will be tested.
        """
        if self._permutations:
            return
        # till now, cannot work out the real algorithm for all the combination
        # of session steps, here just for going through the test tool
        # functionalities, we just use a simple algorithm instead. and will
        # develop deeper in future

        # the simple algorithm is just sequence all the steps ordered by its
        # owned session. yes, i know the session level combination will not
        # make sense for crossing execution lock detect, but now it is only
        # a temp solution.
        import itertools
        if not self._sessions:
            return
        sessions = []
        for tag, data in self._sessions.items():
            sessions.append(data)

        session_permutations = list(itertools.permutations(sessions))

        for permutation in session_permutations:
            tags = []
            for item in permutation:
                for step in (item['steps']):
                    tags.append(step['tag'])
            self._permutations.append(tags)

    def _build_step_mapping(self):
        pass

    def get_session_by_step(self, step):
        """two solutions, can buld a cache for step to session mapping,
        and also can search the session from the structure each time.
        since it is not a performance sensitive application, for easy
        implementation, just do structure search each time, and this
        will reduce a cache variable usage, made program easy to read
        and maintain"""
        return 'session'

    def _get_command_by_step(self, step):
        pass

    def setups(self):
        """get the test case level setup sql commands
        """
        return self._setups

    def teardowns(self):
        return self._teardowns

    def sessions(self):
        return self._sessions

    def permutations(self):
        return self._permutations

    def permutation_num(self):
        return len(self._permutations)

    def session_num(self):
        return len(self._sessions.keys())

    def session_tags(self):
        return self._sessions.keys()

    def session_setups(self):
        results = []
        for tag, session in self._sessions.items():
            if 'setup' in session:
                results.append({
                    'session_tag': tag,
                    'sqls': session['setup'],
                    })
        return results

    def session_teardowns(self):
        results = []
        for tag, session in self._sessions.items():
            if 'teardown' in session:
                results.append({
                    'session_tag': tag,
                    'sqls': session['teardown'],
                    })
        return results

    def next_permutation_steps(self):
        for permutation in self._permutations:
            yield self._permutation_tag_to_steps(permutation)

    def _permutation_tag_to_steps(self, permutation):
        results = []
        for step in permutation:
            found = False
            for tag, session in self._sessions.items():
                for s in session['steps']:
                    if step != s['tag']:
                        continue
                    results.append({
                        'session_tag': tag,
                        'sqls': s['sqls'],
                        'step_tag': s['tag']
                        })
                    found = True
            if found == False:
                raise Exception("cannot find the step %s in sessions", step)
                    
        return results

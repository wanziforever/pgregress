from utils.sql import parse_sqls
from utils.connection import SQLBlockExecutorHelper

class SQLBlock(object):
    """define a whole sql block words

    there is no such block definition in c type code, but psycopg2 has
    different handling with multiple sqls execution , so we want a workaround
    to let the sql block handling to be the same with c type code, for detail
    difference, please refers to runner class.
    
    :type words: str
    :param words: sql block words
    """
    def __init__(self, words):
        self._sqls = []
        self._sqls = parse_sqls(words)
        self._raw_sql = words

    def get_sqls(self):
        return self._sqls

    def num(self):
        return len(self._sqls)

    def __repr__(self):
        return " ".join(self._sqls)

    def __getitem__(self, index):
        return self._sqls[index]

    def raw(self):
        return self._raw_sql


class StepModule(object):
    """define a class corresponsing to the testcase step section

    :type tag: str
    :param tag: the step tag name
    """
    def __init__(self, tag):
        self._tag = tag
        self._session_tag = None
        self._sqlblock = None
        self._sqlhelper = None

    def _build_sqlhelper(self):
        if self._sqlblock is None:
            raise Exception("StepModule::build_sqlhelper() no sqlblock set")
        self._sqlhelper = SQLBlockExecutorHelper(self._sqlblock)

    def reset(self):
        if self._sqlhelper:
            self._sqlhelper.reset()

    def set_sql_block(self, block):
        """set the step related sql block

        :type block: :class:`testcase.SQLBLOCK`
        :param block: sql block info of the step
        """
        self._sqlblock = block
        self._build_sqlhelper()

    def set_session(self, session_tag):
        self._session_tag = session_tag

    def session(self):
        return self._session_tag

    def tag(self):
        return self._tag

    def sql(self):
        return self._sqlblock

    def raw_sql(self):
        return self._sqlblock.raw()

    def sqlhelper(self):
        return self._sqlhelper

    def __repr__(self):
        return ("STEP: %s; SQL: %s" % (self._tag, self._sqlblock))


class SessionModule(object):
    """define a class corresponsing to the testcase session section

    :type tag: str
    :param tag: the session tag name
    """
    def __init__(self, tag):
        self._tag = tag
        self._setup_module = None
        self._teardown_module = None
        self._step_modules = []

    def set_setup(self, module):
        """set the setup module for session

        :type module: :class:`SetupModule`
        :param module: the setup module in the session
        """
        self._setup_module = module

    def set_teardown(self, module):
        """set the teardown module for session

        :type module: :class:`TearDownModule`
        :param module: the teardown module in the session
        """
        self._teardown_module = module

    def add_step(self, module):
        """add a step module for the session

        :type module: :class:`StepModule`
        :param module: the step will be added to the session
        """
        self._step_modules.append(module)

    def reset(self):
        if self._setup_module:
            self._setup_module.reset()
        if self._teardown_module:
            self._teardown_module.reset()

        for step in self._step_modules:
            step.reset()

    def steps(self):
        return self._step_modules

    def setup(self):
        return self._setup_module

    def teardown(self):
        return self._teardown_module

    def tag(self):
        return self._tag

    def step_tags(self):
        return [step.tag() for step in self._step_modules]
    

class SetupModule(object):
    def __init__(self):
        self._sqlblock = None
        self._session_tag = None
        self._sqlhelper = None

    def _build_sqlhelper(self):
        if self._sqlblock is None:
            raise Exception("SetupModule::build_sqlhelper() no sqlblock set")
        self._sqlhelper = SQLBlockExecutorHelper(self._sqlblock)

    def reset(self):
        if self._sqlhelper is not None:
            self._sqlhelper.reset()

    def set_sql_block(self, block):
        """set the sql block for the steup module
        
        :type block: :class:`testcase.SQLBLOCK`
        :param block: sql block info of the step
        """
        if not isinstance(block, SQLBlock):
            raise Exception(
                "setupModule::set_sql_block(), SQLBlock required"
                )
        self._sqlblock = block
        self._build_sqlhelper()

    def set_session(self, session_tag):
        self._session_tag = session_tag

    def session(self):
        return self._session_tag

    def sql(self):
        return self._sqlblock

    def sqlhelper(self):
        return self._sqlhelper
        

class TearDownModule(object):
    def __init__(self):
        self._sqlblock = None
        self._session_tag = None
        self._sqlhelper = None

    def _build_sqlhelper(self):
        if self._sqlblock is None:
            raise Exception(
                "TearDownModule::build_sqlhelper() no sqlblock set"
                )
        self._sqlhelper = SQLBlockExecutorHelper(self._sqlblock)

    def reset(self):
        if self._sqlhelper is not None:
            self._sqlhelper.reset()

    def set_sql_block(self, block):
        """set the sql block for the teardown module

        :type block: :class:`testcase.SQLBLOCK`
        :param block: sql block info of the step
        """
        if not isinstance(block, SQLBlock):
            raise Exception(
                "TearDownModule::set_sql_block(), SQLBlock required"
                )
        self._sqlblock = block
        self._build_sqlhelper()

    def set_session(self, session_tag):
        self._session_tag = session_tag

    def session(self):
        return self._session_tag

    def sql(self):
        return self._sqlblock

    def sqlhelper(self):
        return self._sqlhelper
    

class Permutation(object):
    def __init__(self, steps=[]):
        self._step_tags = list(steps)

    def add_step_tag(self, tag):
        """add a step to a permutation

        :type tag: str
        :param tag: the step tag name in the permutation
        """
        self._step_tags.append(tag)

    def step_tags(self):
        return self._step_tags

    def __repr__(self):
        return " ".join(self._step_tags)

    def num_of_steps(self):
        return len(self._step_tags)

def new_permutation_class():
    return Permutation()

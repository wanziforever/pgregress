from dbserver import DBServer
import time
import logging

from utils.connection import PGConnectionManager

logger = logging.getLogger('application')
_DATA_PATH = './tmp_instance'

class Application(object):
    """test progress coordination, one profile bind to one Application

    Args:
      profile: Profile, 
    """
    def __init__(self, profile):
        self.profile = profile
        self._maint_session = None
        self._sessions = {}
        self.server = None

    def _make_PGServer(self):
        DBServer.initDB(_DATA_PATH)
        DBServer.set_dbconf(_DATA_PATH, port=5433)
        self.server = DBServer.start(_DATA_PATH)

        DBServer.set_dbconf(_DATA_PATH,
                            log_autovacuum_min_duration='0',
                            log_checkpoints='on',
                            log_line_prefix="'%m [%p] %q%a '",
                            log_lock_waits = 'on',
                            log_temp_files = '128kB',
                            max_prepared_transactions = '2')
        
        while not self.server.is_ready():
            logger.debug("trying to start the PostgreSQL service")
            time.sleep (1)

        logger.debug('PG server is ready to accept message')

    def _clear_PGServer(self):
        self.server.stop()
        DBServer.removeDB(_DATA_PATH)
        
    def run(self):
        case = self.profile.next_case()
        while case:
            logger.debug("processing case \n%s" % str(case))
            
            self._start_test(case)
            
            case = self.profile.next_case()

        logger.debug("cases run out!")

    def _start_test_setup(self, testcase):
        logger.debug("LOADING SETUP SQLS")
        # fetch sqls from testcase, and send it to maint session
        print(testcase.setups())
        for sql in testcase.setups():
            self._maint_session.execute(sql)

    def _start_test_session_setup(self, testcase):
        logger.debug("LOADING SESSION SETUP SQLS")
        for setup in testcase.session_setups():
            session_tag = setup['session_tag']
            dbsession = self._get_session_by_tag(session_tag)
            if dbsession is None:
                raise Exception("cannot find session by tag %s"
                                % session_tag)
            for sql in setup['sqls']:
                dbsession.execute(sql)

    def _start_test_permutations(self, testcase):
        round_num = 1
        for steps in testcase.next_permutation_steps():
            logger.debug("ROUND %d START" % round_num)
            self._start_test_setup(testcase)
            self._start_test_session_setup(testcase)

            logger.debug('LOADING PERMUTATION STEPS')
            for step in steps:
                session_tag = step['session_tag']
                dbsession = self._get_session_by_tag(session_tag)
                if dbsession is None:
                    raise Exception("cannot find session by tag %s"
                                    % session_tag)
                for sql in step['sqls']:
                    dbsession.execute(sql)

            self._start_test_session_teardown(testcase)
            self._start_test_teardown(testcase)
            round_num += 1

    def _start_test_session_teardown(self, testcase):
        logger.debug("LOADING SESSION TEARDOWN SQLS")
        # fetch session teardown sqls from test case
        for setup in testcase.session_teardowns():
            session_tag = setup['session_tag']
            dbsession = self._get_session_by_tag(session_tag)
            if dbsession is None:
                raise Exception("cannot find session by tag %s"
                                % session_tag)
            for sql in setup['sqls']:
                dbsession.execute(sql)

    def _start_test_teardown(self, testcase):
        logger.debug("LOADING TEARDOWN SQLS")
        # fetch sqls from teardown, and send it to maint session
        for sql in testcase.teardowns():
            self._maint_session.execute(sql)

    def _start_test(self, testcase):
        self._make_PGServer()
        self._make_maint_session()
        self._make_test_sessions(testcase.session_tags())

        self._start_test_permutations(testcase)

        self._clear_test_sessions()
        self._clear_maint_session()
        self._clear_PGServer()

    def _make_maint_session(self):
        import config
        self._maint_session = PGConnectionManager.new_connection(
            config.dbname, config.user, config.password,
            config.host, config.port)
        self._maint_session.set_name('Maint')
        self._maint_session.execute("SET client_min_messages = warning;")

    def _clear_test_sessions(self):
        for tag, conn in self._sessions.items():
            logger.debug("conn(%s) has been cleared")

    def _clear_maint_session(self):
        logger.debug("Maint conn has been cleared")

    def _get_session_by_tag(self, tag):
        return self._sessions.get(tag, None)

    def _make_test_sessions(self, tags):
        import config
        for tag in tags:
            self._sessions[tag] = PGConnectionManager.new_connection(
                config.dbname, config.user, config.password,
                config.host, config.port)
            
            self._sessions[tag].set_name(tag)
            self._sessions[tag].execute(
                "SET client_min_messages = warning;"
                )

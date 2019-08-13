#!/usr/bin/env python3

"""Test Simulation tool implementation

a very special implementation from the c code, is when there are multiple
sql clause in a step (maybe in a begin ... end paragragh), we need to
seperate the sub sql clauses, and execute it one by one by our code, in c
version code, it is not. because python psycopg2 will only get the last
result which generated by the sql paragragh, and c code will not have the
problem it can access the low level c code like the geResult() to loop every
result and get all the result together, and print them all.

the parsing of sql paragragh will made runner more complex, but it is a
"SHOULD DO", we need to be compliant with c code as possible as we can.

although we can execute the sql in the "sql paragragh" one by one, and get
the output result one by one, but we need to hold the result, until the whole
paragragh end, and print the result together, this requirement is also for
compliant with the c code.

"""

__author__      = "denny wang (denny.wangliang@gmail.com)"
__copyright__   = "Copyright 2018, Highgo LLC"

import os
import sys

sys.path.append('.')
from utils.connection import PGConnectionManager, SQLBlockExecutorHelper
from testcase import TestCase
from utils.sql import parse_sqls
from testcase.modules import SQLBlock
import time
import logging
import datetime
import xml.dom.minidom
import config
import subprocess

from exc import (
    WaitDataTimeoutException,
    WaitDataErrorException,
    WaitDataLockedException
    )

logging.basicConfig(level=logging.INFO)
#logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("TestRunner")
#sys.path.append('../')

STEP_NOBLOCK = 0x1
STEP_RETRY = 0x2

def parse_keywords_list(keywords_list):
    '''
    keywords_list: type:list,the shell commands block
    '''
    commands = []

    xmlpath=os.path.abspath("keywords.xml")
    dom = xml.dom.minidom.parse(xmlpath)
    root = dom.documentElement
    operation_list = root.getElementsByTagName('operation')
 
    for item in keywords_list:
        item = item.split()
        for operation in operation_list:
            if operation.getAttribute('keyword') == item[0]:
                func = operation.getAttribute("script")
                item[0]=str(func)
                commands.append(item)
    return commands

def exec_keywords(keywords_list):
    command_list = parse_keywords_list(keywords_list)
    if len(command_list) == 0:
        logger.info('There is no Shell commands, continue SQL commands')
    else:
        for cmd in command_list:
            length = len(cmd)
            i = 0
            exec_cmd = 'python '
            while i<length:
                exec_cmd = exec_cmd + cmd[i] + ' '
                i = i+1
            child = subprocess.run(exec_cmd,shell=True,
                                   stdout=sys.stdout,
                                   stderr=subprocess.STDOUT)
            if child.returncode !=0:
                logger.info('the shell command:%s is failed' % exec_cmd)
                exit(1)



class TestRunner(object):
    """Test case running tool

    Given a test case path, the tool will parse the case structure data,
    and call connection tool to execute the case command, a output will
    be saved to testcase profile directory.

    Test case data have following structures:
      setup: hold sqls to setup the environment before running the case

    One test case support many permutation to be executed, each permutation
    should be run entirely clean environment, so for each permutation, we
    need to do the environment setup, and also SHOULD do environment tear
    down(teardown is important and this will make the next setup successful),

    Support dryrun mode, which will not setup any real db connections, it
    just print the step sequence for some debuging use.

    :type case_path: str
    :param case_path: absolute path of the test case data file
    """
    def __init__(self, case_path):
        self._testcase = TestCase(case_path)
        self._maint_session = None
        self._sessions = {}
        self._waitings = []
        self._backend_pids = []
        self._errorsteps = {} # {step: errormsg}

    #def run(self, dry_run=False):
    def run(self):
        """TestRunner execution interface, it will control the testcase
        running main procedure. it also can run a dry run.

        procedures:
          >>> parse the testcase raw data file to a structure
          >>> setup maintainance and test running db connections, the
          >>> maintainance session will execute environment related
          >>> commands or some management operations
          >>> collect something which is useful for later use
          >>> start the permutation executions
          >>> clear the maintainace and test running db connections

        :type case_type: String
        : rse_keywords_listparam case_type: Tell the function which kind of case is running,spec or spt
        ..note:
          all the sqls in setup and teardown section will have a list type
          sqls in step is a string type, refer to the description of parser
          file for detail reason
        """
        self._testcase.build()

        if len(self._testcase._keywords)!=0:
            exec_keywords(self._testcase.keywords())       

        if len(self._testcase._sessions)!=0:
            self._make_maint_session()
            self._load_setup_sqls()
            self._make_test_sessions()

            self._collect_backend_pids()
            
            self._start_permutations()

            self._clear_test_sessions()
            self._load_teardown_sqls()
            self._clear_maint_session()

    def _clear_tmp_data(self):
        self._waitings = []
        self._errorsteps = {}
        self._testcase.reset()

    def _load_setup_sqls(self):
        """get the sqls from testcase setup module, and execute them
        """
        logger.debug("LOADING SETUP SQLS")
        for setup in self._testcase.setups():
            helper = setup.sqlhelper()
            helper.execute(self._maint_session)
            output = helper.output()
            if output:
                print(output)

    def _load_teardown_sqls(self):
        """get the sqls from testcase teardown module, and execute them
        """
        logger.debug("LOADING TEARDOWN SQLS")
        for teardown in self._testcase.teardowns():
            helper = teardown.sqlhelper()
            helper.execute(self._maint_session)
            output = helper.output()
            if output:
                print(output)

    def _load_session_setup_sqls(self):
        """get the sqls from each session level setup module, and execute
        them in its session, all the steps for each session should be
        run after session setup.
        """
        logger.debug("LOADING SESSION SETUP SQLS")
        for setup in self._testcase.session_setups():
            session_tag = setup.session()
            dbsession = self._get_session_by_tag(session_tag)
            if dbsession is None:
                raise Exception("cannot find session by tag %s"
                                % session_tag)
            
            helper = setup.sqlhelper()
            helper.execute(dbsession)
            output = helper.output()
            if output:
                print(output)

    def _load_session_teardown_sqls(self):
        """get the sqls from each session level teardown model, and execute
        them in its session, teardown operations should be run after each
        session test run.
        """
        logger.debug("LOADING SESSION TEARDOWN SQLS")
        # fetch session teardown sqls from test case
        for teardown in self._testcase.session_teardowns():
            session_tag = teardown.session()
            dbsession = self._get_session_by_tag(session_tag)
            if dbsession is None:
                raise Exception("cannot find session by tag %s"
                                % session_tag)
            helper = teardown.sqlhelper()
            helper.execute(dbsession)
            output = helper.output()
            if output:
                print(output)

    def _start_dry_run(self):
        """only print the sqls for setup, teardown, permutation in sequence
        no actual database dependence will be used.
        """
        print("----------DRY RUN MOD----------")

        print(str(self._testcase))
        round_num = 1
        
        for steps in self._testcase.next_permutation_steps():
            print("starting permutation: %s"
                  % " ".join([step.tag() for step in steps]))
            print("==LOADING SETUP SQLS==")
            for setup in self._testcase.setups():
                print("Session(%s): %s" % ("Maint", setup.sql()))

            print("==LOADING SESSION SETUP SQLS==")
            for setup in self._testcase.session_setups():
                print("Session(%s): %s" % (setup.session(), setup.sql()))

            print('==LOADING PERMUTATION STEPS SQlS==')
            for step in steps:
                print("Session(%s): %s" % (step.session(), step.sql()))

            print("==LOADING SESSION TEARDOWN SQLS==")
            for teardown in self._testcase.session_teardowns():
                print("Session(%s): %s" % (teardown.session(), teardown.sql()))

            print("==LOADING TEARDOWN SQLS==")
            for teardown in self._testcase.teardowns():
                print("Session(%s): %s" % ("Maint", teardown.sql()))

            print()
            round_num += 1

    def _start_permutations(self):
        """run the steps for each permutation, look up session by the
        step tag, and run step sqls in its session.

        each permutation require a entirely new environment, the means
        the setup and teardown model should be run for every permutation
        """
        round_num = 1
        print("Parsed test spec with %d sessions"
              % len(self._sessions.keys()))
        for steps in self._testcase.next_permutation_steps():
            print()
            print("starting permutation: %s"
                  % " ".join([step.tag() for step in steps]))
            self._clear_tmp_data()
            self._load_session_setup_sqls()

            logger.debug('LOADING PERMUTATION STEPS SQLS')
            for step in steps:
                oldstep = self._complete_previous_steps(step)
                # _complete_previous_steps has possiblity to make some change of
                # current waiting list, and may make some waiting sessions to get
                # through, here need to release them
                if oldstep:
                    # clear the old error step message to just monitor the very
                    # recent step error message
                    self._try_complete_waiting_steps(STEP_NOBLOCK | STEP_RETRY)
                    self._report_multiple_error_messages(oldstep)
                #for shell command, run linux commands
                if step._session_tag == 'shell':
                    print("step %s: %s" % (step.tag(), step.command()))
                    exec_keywords(step._cmdlist) 
                else:
                    self._run_step_sqls(step)

            self._final_complete_waiting_steps()

            self._load_session_teardown_sqls()

            round_num += 1

    def _run_step_sqls(self, step):
        """ execute one step sqls, firstly need to know which session the
        sqls need to executed in.

        the sql execution has possiblity to be blocked by something, for
        example, by last step, for some interval data lock, if it is blocked
        by something, we call it a waiting step. we have a waiting list to
        hold all the current waiting steps.

        if a step become a waiting step, all the later step in the same
        session should also be hold. Here, the case designer should notice
        this as expected design, and try to release the lock in next steps
        (the blocking step normally should not followed by the steps in
        same session).
        
        the waiting step can go through when the some lock was released, and
        we need always to check the case and let it go through, removed from
        waiting list, so that the later step in the session can be executed.

        permutation step will be run in async mode, and try to get the result
        in the nonblocking way, we will mark the step as waiting or not, so
        that we avoid to be hold there, and cannot get to next step which
        will release the lock.

        :type step: dict
        :param step: structure hold a entirely test case step related data
        """

        oldstep = self._complete_previous_steps(step)
        # _complete_previous_steps has possiblity to make some change of
        # current waiting list, and may make some waiting sessions to get
        # through, here need to release them
        if oldstep:
            # clear the old error step message to just monitor the very
            # recent step error message
            self._try_complete_waiting_steps(STEP_NOBLOCK | STEP_RETRY)
            self._report_multiple_error_messages(oldstep)

        session_tag = step.session()
        dbsession = self._get_session_by_tag(session_tag)
        if dbsession is None:
            raise Exception(
                "cannot find session by tag %s" % session_tag
                )

        helper = step.sqlhelper()
        wait = False
        #while not helper.is_completed():
        #    dbsession.sendSQL(helper)
        #    wait = self._try_complete_step(step, STEP_NOBLOCK)
        #    if wait:
        #        break
        helper.sendSQL(dbsession, self._check_lock)
        
        try:
            wait = self._new_try_complete_step(step, STEP_NOBLOCK)
        except WaitDataTimeoutException as e:
            raise
        
        # after execute a step, check wether it can make some waiting
        # steps to go through
        self._try_complete_waiting_steps(STEP_NOBLOCK | STEP_RETRY)
        self._report_multiple_error_messages(step)

        if wait:
            self._waitings.append(step)

    def _complete_previous_steps(self, step):
        """Check whether the session that needs to perform the next step is
        still blocked on an earlier step.  If so, wait for it to finish.
        
        (In older versions of this tool, we allowed precisely one session
        to be waiting at a time.  If we reached a step that required that
        session to execute the next command, we would declare the whole
        permutation invalid, cancel everything, and move on to the next
        one.  Unfortunately, that made it impossible to test the deadlock
        detector using this framework, unless the number of processes
        involved in the deadlock was precisely two.  We now assume that if
        we reach a step that is still blocked, we need to wait for it to
        unblock itself.)

        ..above paragraph was pasted from C version code

        :type step: dict
        :param step: structure hold a entirely test case step related data

        :rtype: dict
        :returns: the previous step in the same session which is blocking
        """
        oldstep = None
        for wait_step  in self._waitings:
            if step.session() != wait_step.session():
                continue
            # normally the waiting list only have one entry for one
            # session, but we just keep the below code in the for
            # loop in case more session found
            oldstep = wait_step
            self._new_try_complete_step(oldstep, STEP_RETRY)

            self._waitings.remove(oldstep)

        return oldstep
                
    def _try_complete_waiting_steps(self, flags):
        """check all the existing waiting steps whether some of them can
        go through. use NOBLOCK mode, the check cannot hange to wait step
        to complete.
        """
        # originally we use for loop, but when we remove a element, it seems
        # not working as we expected, so we just mark the to_delete item, and
        # remove it at last
        to_del = []

        for step in self._waitings:
            wait = False
            wait = self._new_try_complete_step(step, flags)

            if wait:
                # still waiting, just keep it in the wait list
                continue
            
            else:
                # the step has completed either succeed, or fail
                #self._waitings.remove(step)
                to_del.append(step)
                # if the tag in the errorsteps, it means the complete with
                # fail, if not in errorsteps, should a empty error entry to
                # errorsteps for error combination report(align with c code)
                tag = step.tag()
                if tag not in self._errorsteps:
                    self._errorsteps[step.tag()] = ''

        for step in to_del:
            self._waitings.remove(step)

    def _final_complete_waiting_steps(self):
        """check all the existing waiting steps whether some of them can
        go through. since it is the final complete, use RETRY mode to wait
        for all waiting step to complete
        """
        for step in self._waitings:
            wait = False
            wait = self._new_try_complete_step(step, STEP_RETRY)
            self._report_error_message(step)
                
    def _try_complete_step(self, step, flags):
        """try to complete a step whether it is a locked or unlocked for
        unlocked, the getResult will return the result very soon, and for
        locked, it is a little complex, if the flags indicate nonblocked,
        try to lookup the maint session to see whether it is due to lock
        or some other reason to hold, if it is surely due to lock, just
        return True to indicate the step is locked and wait to unlock by
        the other session. for the case it is hang there not due to a lock,
        and it is wait for 60 seconds, and try to cancel the last step, if
        still no response and it take about 75 seconds, just quit.

        a retry mode should be support, we normally call this function
        firstly when just send the sql, and to see whether the sql is
        blocked, after that go to other session, then we still need to
        come back to complete this step, this time, we call the retry.

        .. note:
           here is problem is that although you provide a nonblock flag in
           the function parameter, if it is hang not for a lock, it will
           still block there for 60 or 75 seconds, this is an original
           design, since it is enough to handle the requirement, no change
           to be done here.

        .. note:
           there may be a very complex sql clause in a step (like begin
           blablabla ... commit), and the sql will be devided into sub
           sqls which need to be executed one by one, but only print the
           whole complex sql clause once, so add a new STEP type IN_SQLBLOCK
           which indicate the current step is a sub sql step, and try to
           see whether the whole sql has been printed

        :type step: dict
        :param step: structure hold a entirely test case step related data

        :type flags: bitarray
        :param flags: bits indicate the NONBLOCKED and RETRY mode

        :rtype: Boolen
        :returns: indicate whether the step is lock blocked, others cases
                  return False
        """
        session_tag = step.session()
        dbsession = self._get_session_by_tag(session_tag)
        block_time = 1 # block 100ms
        start_time = time.time()
        canceled = False
        timeout = False
        sqlhelper = step.sqlhelper()
        while True:
            try:
                timeout = dbsession.getResult(sqlhelper, block_time)
            except Exception as e:
                # failure is also a complete branch, and print complete
                self._errorsteps[step.tag()] = str(e)
                #return False
                break

            # the getResult may return a empty result, this is different
            # from the timeout case, for timeout it return False
            if timeout is True:
                break

            # getResult timeout case
            if flags & STEP_NOBLOCK:
                if self._check_lock(dbsession.get_backend_pid()):
                    if not (flags & STEP_RETRY):
                        print("step %s: %s <waiting ...>" % (step.tag(), step.sql()))
                    return True
                
            now = time.time()
            if now - start_time > 60 and not canceled:
                dbsession.cancel_backend()
                canceled = True

            if now - start_time > 75:
                raise Exception("step %s timeout after 75 seconds"
                                % step.tag())
                        
        if flags & STEP_RETRY:
            print("step %s: <... completed>" % step.tag())

        else:
            # very triky STEP_IN_SQLBLOCK and printed flag
            # check for sqlblocks print workaround

            print("step %s: %s" % (step.tag(), step.sql()))

        print(sqlhelper.get_result().output())
        
        return False

    def _new_try_complete_step(self, step, flags):
        session_tag = step.session()
        dbsession = self._get_session_by_tag(session_tag)
        sqlhelper = step.sqlhelper()
        while True:
            try:
                sqlhelper.try_complete_current_execution(
                    dbsession, self._check_lock
                    )
                break
            except WaitDataLockedException as e:
                if flags & STEP_NOBLOCK:
                    if not (flags & STEP_RETRY):
                        print("step %s: %s <waiting ...>" %
                              (step.tag(), step.raw_sql()))
                    return True
            except WaitDataTimeoutException as e:
                raise
            except WaitDataErrorException as e:
                self._errorsteps[step.tag()] = str(e)
                break

        if flags & STEP_RETRY:
            print("step %s: <... completed>" % step.tag())
        else:
            print("step %s: %s" % (step.tag(), step.raw_sql()))

        output = sqlhelper.output()
        if output:
            print(output)
        
        return False

    def _check_lock(self, pid):
        """send a Maint prepare message to get the lock status for session
        execute the internal lock check function to check whether the pid
        specified is locked, if it is locked, the function will return True,

        ..note:
          pg_isolation_test_session_is_blocked function is involved in 9.6

        :type pid: str or int
        :param pid: the process id or backend id need to check block status
        """
        # join operation need string type list
        pids = [str(x) for x in self._backend_pids]
        sql = (
            "SELECT pg_catalog.pg_isolation_test_session_is_blocked"
            "({pid}, '{{{pids}}}')"
            ).format(pid=pid, pids=','.join(pids))

        result = self._maint_session.execute(sql)
        
        rows = result.rows
        return rows[0][0]

    def _make_maint_session(self):
        """setup the maintainance db connection which is used for setup
        sqls and some management work.
        """
        import config
        self._maint_session = PGConnectionManager.new_connection(
            config.dbname, config.user, config.password,
            config.host, config.port)
        self._maint_session.set_name('Maint')
        # we need to set the autocommit exeplicitly for maint session,
        # in PG code, we cannot see the autocommit setting, because the
        # PQConnect is used, and PGConnect is defalutly autocommit.
        self._maint_session.autocommit(True)
        sql = "SET client_min_messages = warning;"
        self._maint_session.execute(sql)

    def _clear_test_sessions(self):
        """kill the test related db connections
        """
        for tag, conn in self._sessions.items():
            if tag != 'shell':
                logger.debug("conn(%s) has been cleared" % tag)
                conn.close()

    def _clear_maint_session(self):
        """kill the maintainance related db connection
        """
        logger.debug("Maint conn has been cleared")
        self._maint_session.close()

    def _get_session_by_tag(self, tag):
        """each step was binded to a session, use the step session tag
        to find its sessions which was setup earlier.

        :type tag: str
        :param tag: session tag which is configured in case file

        :rtype: :class: `utils.connection.PGAsyncConnection`
        :returns: a database connection which has been bind given tag.
        """
        return self._sessions.get(tag, None)

    def _make_test_sessions(self):
        """setup sessions which are used for permutation test run,
        session number should meet the testcase requirement, and each
        session should identified with the sesstion tag.
        """
        tags = self._testcase.session_tags()
        import config
        for tag in tags:
            if tag == "shell":
                self._sessions[tag] = tag
            else:
                self._sessions[tag] = PGConnectionManager.new_async_connection(
                    config.dbname, tag, 'highgo123',
                    config.host, config.port)
                # the test session are all async connection, and there is no
                # autocommit property, since the default is autocommit
                # self._sessions[tag].autocommit(True)
                self._sessions[tag].set_name(tag)

                sql = "SET client_min_messages = warning;"
                
                self._sessions[tag].execute(sql)

    def _collect_backend_pids(self):
        """get all the backend pid related to permutation sessions and
        maint session, the backed pids are used as parameters to check
        session lock.
        """
        self._backend_pids = []
        if self._maint_session:
            backendpid = self._maint_session.get_backend_pid()
            if backendpid:
                self._backend_pids.append(backendpid)

        for tag, conn in self._sessions.items():
            if tag != 'shell':
                backendpid = conn.get_backend_pid()
                if backendpid:
                    self._backend_pids.append(backendpid)

    def _report_error_message(self, step):
        """a error report method only report the target step error mssage

        :type step: dict
        :param step: session step data which is parsed from testcase data
        """
        tag = step.tag()
        if tag in self._errorsteps:
            print(self._errorsteps[tag])
            del self._errorsteps[tag]
        

    def _report_multiple_error_messages(self, step):
        """report the errors during the step processing

        since the error maybe happened during two session block case,
        so we try to print all the errors received from database backend
        for all the steps which has relations.

        :type step: dict
        :param step: session step data which is parsed from testcase data

        ..note:
          to compliant with C version code, if there is only the error for
          specified step, just call the _report_error_message
        """
        tag = step.tag()
        extratags = [etag for etag in self._errorsteps.keys() if etag != tag]

        if len(extratags) == 0:
            self._report_error_message(step)
            return
        
        all_tags = [tag]
        all_tags.extend(extratags)

        if tag in self._errorsteps:
            if self._errorsteps[tag]:
                print("error in steps %s: %s"
                      % (" ".join(all_tags), self._errorsteps[tag]))
            del self._errorsteps[tag]

        for etag in extratags:
            if self._errorsteps[etag]:
                print("error in steps %s: %s"
                      % (" ".join(all_tags), self._errorsteps[etag]))
            del self._errorsteps[etag]


def usage():
    """ show the usage of the tool, including the arguments

    -d means the dry run mode, the case path should a absolute path
    """
    print("%s [-d] <case_path>")
    
# provide a main for a dry run test
if __name__ == "__main__":
    import sys
    case_path = ''
    if len(sys.argv) == 2:
        case_path = sys.argv[1]
    else:
        usage()
        exit(1)
    TestRunner(case_path).run()

    '''
    # Maggie redefine this part, in the new code, the is_dry_run is abandoned
    is_dry_run = False
    if len(sys.argv) == 2:
        case_path = sys.argv[1]
    elif len(sys.argv) == 3:
        case_path = sys.argv[2]
        if sys.argv[1] == '-d':
            is_dry_run = True
        else:
            usage()
            exit(1)
    else:
        usage()
        exit(1)

    if is_dry_run:
        TestRunner(case_path).run(dry_run=True)
    else:
        TestRunner(case_path).run()
    '''

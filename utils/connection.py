import psycopg2
import logging
import select
import datetime
import time

from exc import (
    WaitDataTimeoutException,
    WaitDataErrorException,
    WaitDataLockedException
    )

logger = logging.getLogger('connection')

"""
We divide the PostgreSQL connection into two types of connection, libpq
dosen't have such case, we use the same libpq connection structure to
handle the sync and async function calls. but psycopg2 have the limitation
that the connection which is created without async=1 parameter will not
support async function calls.
"""

class ExecutionResult(object):
    def __init__(self, descriptions=[], rows=[]):
        self.descriptions = descriptions
        self.rows = rows

    def is_empty(self):
        return len(self.descriptions) == 0 and len(self.rows) == 0

    def output(self):
        """print the result to screen, the result is got from database

        :type descriptions: list
        :param descriptions: the column names in the result

        :type rows: list of lists
        :param rows: entry rows for the result of a db query
          
        """
        def convert_result(value):
            """currently python has different value print as c style, below
            is the convertion to do:
            * python style False/True to C style f/t
            * python style None to C style `[nil]`(blank)
            """
            if value is False:
                return 'f'
            if value is True:
                return 't'
            if value is None:
                return ''
            if isinstance(value, float):
                # ugly convertion, but no choice, c version code output a
                # floag with no .0 suffix for integer like value
                value = str(value)
                if value.endswith('.0'):
                    return value[:-2]
            elif isinstance(value, datetime.date):
                return value.strftime('%m-%d-%Y')

            return value
                
        #if not descriptions or not rows:
        #    return
        if self.descriptions is None or self.rows is None:
            return ""

        if self.is_empty():
            return ""

        outputs = []
        line = ""
        
        for desc in self.descriptions:
            line += ("%-15s" % desc)

        if line != "":
            outputs.append(line)
            
        outputs.append("")

        for row in self.rows:
            line = ""
            for t in row:
                t = convert_result(t)
                line += ("%-15s" % t)
            outputs.append(line)

        pstr = "\n".join(outputs)
        return pstr
        

class SQLBlockExecutionStatus(object):
    INITIALIZED = 0
    INPROGRESS = 1
    COMPLETED = 2
    BLOCKED = 3
    FAILED = 4
    

INITIALIZE_SLOTS = 20
class SQLBlockExecutorHelper(object):
    """this is a exectutor helper for a sqlblock, ad sqlblock always have
    many sub sqls, and the helper will track the exection status, hold the
    temp result when doing middle of the sqls.
    """
    def __init__(self, sqlblock):
        self._sqlblock = sqlblock
        #self._status = SQLBlockExecutionStatus.INITIALIZED
        self._num_of_sqls = self._sqlblock.num()
        self._pos = -1
        self._results = [ExecutionResult()] * INITIALIZE_SLOTS
        self._errors = [''] * INITIALIZE_SLOTS
        self._warns = [''] * INITIALIZE_SLOTS

    #def start(self):
    #    if self._status == SQLBlockExecutionStatus.INITIALIZED:
    #        self._status = SQLBlockExecutionStatus.INPROGRESS

    def next_sql(self, showonly=False):
        if self.is_completed():
            return None
        if showonly:
            self._pos += 1
            sql = self._sqlblock[self._pos]
            sql = self.simecolonCompletion(sql)
            self._pos -= 1
            return sql
        
        self._pos += 1
        sql = self._sqlblock[self._pos]
        sql = self.simecolonCompletion(sql)
        return sql

    def current_sql(self):
        if self._pos == -1:
            return None
        sql = self._sqlblock[self._pos]
        sql = self.simecolonCompletion(sql)
        return sql

    def status(self):
        return self._status

    def is_completed(self):
        return self._pos >= self._num_of_sqls - 1

    def pos(self):
        return self._pos

    def set_error(self, error):
        self._errors[self._pos] = error

    def set_result(self, result):
        if not isinstance(result, ExecutionResult):
            raise Exception("the result should be a ExecutionResult class")
        self._results[self._pos] = result

    def get_result(self):
        return self._results[self._pos]

    def output(self):
        results = []
        for i in range(self._pos+1):
            executionresult = self._results[i]
            if executionresult is None:
                continue
            if executionresult.is_empty():
                continue
            result = executionresult.output()
            results.append(result)
            
        return "\n".join(results)

    def get_error(self):
        return self._errors[self._pos]

    def set_warn(self, warn):
        self._warns[self._pos] = warn

    def get_warn(self):
        return self._warns[self._pos]

    def __repr__(self):
        lines = []
        counter = 0
        for sql in self._sqlblock.get_sqls():
            lines.append("%d-%s" %(counter, sql))
            counter += 1

        lines.append("current pos is %s" % self._pos)

        return "\n".join(lines)

    def show(self):
        return self.__repr__()

    def simecolonCompletion(self, sql):
        """add simecolon to a sql when it is not end with simecolon
        
        :type sql: str
        "param sql" the sql going to do completion
        """
        if sql.endswith(';'):
            return sql
        return sql + ';'

    def reset(self):
        self._pos = -1
        self._results = [ExecutionResult()] * INITIALIZE_SLOTS
        self._errors = [''] * INITIALIZE_SLOTS
        self._warns = [''] * INITIALIZE_SLOTS

    def execute(self, session):
        while not self.is_completed():
            sql = self.next_sql()
            result = session.execute(sql)
            self.set_result(result)

    def sendSQL(self, session, check_lock):
        """execute the sql in the sqlblock one by one, until the waiting lock
        case 
        :type check_lock: function
        :param check_lock: the function used to check whether current session
                           is locked
        """
        if self.is_completed():
            self.reset()
            
        while not self.is_completed():
            sql = self.next_sql()
            session.sendSQL(sql)
            try:
                self.try_complete_current_execution(session, check_lock)
            except Exception as e:
                return
            
        self._status = SQLBlockExecutionStatus.COMPLETED

    def try_complete_current_execution(self, session, check_lock):

        if not callable(check_lock):
            raise Exception(
                "SQLHelper::sendSQLUtilWait() need a check_lock function"
                )
        # already called this function for current sql execution
        if self.get_error():
            raise WaitDataErrorException(self.get_error())

        block_time = 0.02 # block 100ms
        descriptions, rows = [], []
        start_time = time.time()
        while True:
            try:
                executionresult = session.getResult(block_time)
                break
            except WaitDataErrorException as e:
                self.set_error(str(e))
                raise
            except WaitDataTimeoutException as e:
                if check_lock(session.get_backend_pid()):
                    self._status = SQLBlockExecutionStatus.BLOCKED
                    raise WaitDataLockedException(str(e))
                now = time.time()
                if now - start_time > 60:
                    session.cancel_backend()
                    
                if now - start_time > 75:
                    raise WaitDataTimeoutException("sql %s timeout" % sql)

                continue
            except Exception as e:
                # there is tricky workarround for handling try_complete
                # function already get the result when doing sendSQL, and
                # then getting again will raise a
                # 'PGAsyncConnection::getResult() cursor is None or closed'
                # exception, here just ignore the exception
                return

        self.set_result(executionresult)


class PGConnection(object):
    """PostgresSQL sync mode connection class which provide some basic
    functionalities. some were wrapper of psycopg2, and some are re-designed
    and re-implemented.

    :type conn: :class:`psycopg2.extensions.connection`
    :param conn: the connection which connecting to the postgresql
    """
    def __init__(self, conn):
        self._conn = conn
        self.name = 'unknown'
        self._backend_pid = self._conn.get_backend_pid()

    def close(self):
        pass

    def is_avaliable(self):
        return True

    def set_name(self, name):
        """
        :type name: str
        :param name: the name assigned to this connection, not required
        """
        self.name = name

    def execute(self, sql):
        """execute the sql clause

        :type sql: str
        :param sql: the sql clause to be executed
        """
        logger.debug(
            'PGConnection::execute() Conn(%s): %s' % (self.name, sql)
            )
        cursor = self._conn.cursor()
        cursor.execute(sql)
        try:
            dbrows = cursor.fetchall()
        except Exception as e:
            logger.debug(
                "there is no response for sql %s" % sql)
            return ExecutionResult([], [])

        descriptions = [desc[0] for desc in cursor.description]
        rows = [list(row) for row in dbrows]
        return ExecutionResult(descriptions, rows)

    def sendSQL(self):
        raise Exception("sync connection cannot support sendSQL async call")

    def autocommit(self, flag):
        """default sync connection don't use autocommit, psycopg2 has
        interface to simmulate a autocommit.

        :type flag: Boolen
        :param flag: what need to set to autocommit
        """
        if flag is not True and flag is not False:
            raise Exception("PGConnection::autocommit() should accept "
                            "True or False flag")
        self._conn.autocommit = flag

    def close(self):
        self._conn.close()

    def get_backend_pid(self):
        """retrieve the backend related process id

        :rtype: int
        :returns: the backend process id
        """
        # sql = "SELECT pg_backend_pid();"
        # _, rows = self.execute(sql)
        # return rows[0][0]
        return self._backend_pid

    def cancel_backend(self):
        """interface to cancel the current work for this session, psycopg
        has no such interface to do so, so we just implement it.
        """
        sql = ("select pg_cancel_backend({0})").format(self._backend_pid)
        _, rows = self.execute(sql)
        #print("PGConnection::cancel_backend", rows)

def wait_async(conn):
    """wait for the connection to be ready for next operation

    this is used for a async connection, since async mode connection will
    not block any function call, and after the function call, it maybe
    not finish doing its work, we need to wait for the work completion
    """
    while 1:
        state = conn.poll()
        if state == psycopg2.extensions.POLL_OK:
            break
        elif state == psycopg2.extensions.POLL_WRITE:
            select.select([], [conn.fileno()], [])
        elif state == psycopg2.extensions.POLL_READ:
            select.select([conn.fileno()], [], [])
        else:
            raise psycopg2.OperationalError("poll() returned %s" % state)
            
class PGAsyncConnection(object):
    """PostgresSQL sync mode connection class which provide some basic
    functionalities. some were wrapper of psycopg2, and some are re-designed
    and re-implemented.

    :type conn: :class:`psycopg2.extensions.connection`
    :param conn: the connection which connecting to the postgresql
    """
    def __init__(self, conn):
        cursor = conn.cursor()
        self._conn = conn
        self.name = 'unknown'
        self._async_cursor = None
        self._backend_pid = self._conn.get_backend_pid()

    def close(self):
        pass

    def set_name(self, name):
        self.name = name

    def execute(self, sql):
        """although this connection is async, but for some sync context,
        sync style execute sql command need to be supported

        :type sql: str
        :param sql: the sql clause to be executed
        """
        logger.debug(
            'PGConnection::execute() Conn(%s): %s' % (self.name, sql)
            )
        self._async_cursor = self._conn.cursor()
        self._async_cursor.execute(sql)

        wait_async(self._conn)
    
        try:
            dbrows = self._async_cursor.fetchall()
        except Exception as e:
            return ExecutionResult([], [])

        descriptions = [desc[0] for desc in self._async_cursor.description]
        rows = [list(row) for row in dbrows]
        self._async_cursor.close()

        return ExecutionResult(descriptions, rows)

    def sendSQL(self, sql):
        """send sql in async to postgresql server, nothing will be returned
        for this function, use getResult method to get the result, notice
        that you need to do poll() before getResult

        :type sql: str
        :param sql: the sql clause to be executed
        """
        # print("sendSQL sql", sql)

        logger.debug('PGConnection::sendSQL() Conn(%s): %s' % (self.name, sql))
        
        self._async_cursor = self._conn.cursor()
        self._async_cursor.execute(sql)
        
        return

    def autocommit(self, flag):
        raise Exception("autocommit is always True for async connection")

    def close(self):
        self._conn.close()

    def getResult(self, seconds=0):
        """a async get result function, if the response is not ready, just
        wait for specified seconds at most, when seconds=0, it will be
        a blocked call.

        ..note:
          actually this function is mainly merged from C version code,
          part of the isolationtester.c::try_complete_step(), there is
          a problem that is not very accurate. when there is some data
          arrived(not all data), the select will returned, but now poll
          status is no OK, so go on to select more data, but the timeout
          time is still the same with the first time, if some times of
          of such case happened, every select wait for same timeout,
          the total timeout will be more than expected timeout. there
          is a solution that before every select, minor the duration
          of last select occupied time, this seems to be more complex,
          and will have very little impact with the tool execution
          context. most of the time, the function is called just after
          the sendSQL(), if lock happen, no data will be received, and
          the timeout will be accurate.

        :type second: int
        :param second: seconds the function will wait for , 0 means wait
                       forever, normally use a very little number for a
                       async wait
        :rtype: list of tuples
        :returns: descriptions and rows, (None, None) for timeout 
        """
        if self._async_cursor is None or self._async_cursor.closed:
            raise Exception(
                "PGAsyncConnection::getResult() cursor is None or closed"
                )
        
        is_timeout = False
        while 1:
            if is_timeout:
                raise WaitDataTimeoutException()
            try:
                state = self._conn.poll()
            except Exception as e:
                diag = e.diag
                # only raise the primary error message
                errormsg = "%s:  %s" % (diag.severity, diag.message_primary)
                raise WaitDataErrorException(errormsg)
            
            if state == psycopg2.extensions.POLL_OK:
                break
            else:
                t = select.select([self._conn.fileno()], [], [], seconds)
                if t == ([], [], []): # timeout case, triple empty list
                    is_timeout = True
                else:
                    continue

        descriptions = []
        if hasattr(self._async_cursor, "description") \
           and self._async_cursor.description is not None:
            descriptions = [desc[0] for desc in self._async_cursor.description]
            
        try:
            dbrows = self._async_cursor.fetchall()
        except Exception as e:
            #print("we got some exception for fetchall", str(e))
            return ExecutionResult(descriptions, [])
        
        rows = [list(row) for row in dbrows]

        self._async_cursor.close()
        return ExecutionResult(descriptions, rows)
        
    # def get_backend_id(self):
    #     """get the connection related server backend process id
    # 
    #     ..note:
    #       actually, after finish this implementation for a while, i
    #       suddently found that there is connection native interface
    #       called get_backend_pid() will support this feature, and
    #       just implement like `self._conn.get_backend_pid()` will be
    #       ok, but anyway, what i implement can work well, i will not
    #       change it until some problems found.
    #     """
    #     sql = "SELECT pg_backend_pid();"
    #     _, rows = self.execute(sql)
    #     return rows[0][0]

    # above get_backend_pid is a old implementation, below is the new
    def get_backend_pid(self):
        return self._backend_pid

    def cancel_backend(self):
        logger.debug(
            'PGConnection::cancel_backend() Conn(%s)' % (self.name)
            )
        sql = ("select pg_cancel_backend({0})").format(self._backend_pid)
        self._async_cursor = self._conn.cursor()
        self._async_cursor.execute(sql)

        # because it is a caancel operation , so the next wait poll will
        # fail with exception
        #     psycopg2.extensions.QueryCanceledError: canceling
        #     statement due to user request
        # so that we should not call wait_async again here, and also not
        # try to fetch data, so just comments some lines of code

        # wait_async(self._conn)
        #
        # try:
        #     dbrows = self._async_cursor.fetchall()
        # except Exception as e:
        #     return None, None
        #
        # descriptions = [desc[0] for desc in self._async_cursor.description]
        # rows = [list(row) for row in dbrows]
        # self._async_cursor.close()
        # 
        # return descriptions, rows

class PGConnectionManager(object):
    """Connection Management, providing the connection creation interface
    """
    def __init__(self):
        pass
    
    @staticmethod
    def new_connection(database, user, password, host, port):
        """create a postgresql sync mode connection

        :type database: str
        :param database: database name which want to connect to

        :type user: str
        :param user: the username for login the database

        :type password: str
        :param password: the password for login the database

        :type host: str
        :param host: database server host name or ip address

        :type port: int
        :param port: port number of the database service

        :rtype: :class:`utils.connection.PGConnection`
        :returns: Connection object providing sync sql execution function
        """
        conn = psycopg2.connect(database=database, user=user,
                                password=password, host=host, port=port)
        return PGConnection(conn)
        
    @staticmethod
    def new_async_connection(database, user, password, host, port):
        """create a postgresql async mode connection

        :type database: str
        :param database: database name which want to connect to

        :type user: str
        :param user: the username for login the database

        :type password: str
        :param password: the password for login the database

        :type host: str
        :param host: database server host name or ip address

        :type port: int
        :param port: port number of the database service

        :rtype: :class:`utils.connection.PGAsyncConnection`
        :returns: Connection object providing async sql execution function
        """
        conn = psycopg2.connect(database=database, user=user,
                                password=password, host=host,
                                port=port, async_=1)
        wait_async(conn)
        return PGAsyncConnection(conn)

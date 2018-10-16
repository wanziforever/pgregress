"""database server definition, the server is the target testing server
"""

import os
import re
import logging
import time
import subprocess
import threading
import config

logger = logging.getLogger('DBServer')
_PORT = config.port
_DBNAME = config.dbname

def get_installation_bin_path():
    import config
    return os.path.join(config.installation, 'bin')

def get_installation_lib_path():
    import config
    return os.path.join(config.installation, 'lib')

def set_parameter_in_conf_file(conf, name, value):
    """the function will change a value of a parameter

    if the parameter is not commented out, just change it on position,
    if it is commented out, just simply add it to the end of config file

    ..note:
       for simple, the code will not uncomment the parameter

    :type conf: str
    :param conf: the path of the configuration file
    
    :type name: str
    :param name: parameter name to change or add
    
    :type value: int/str
    :param value: parameter value to change or add
    """
    logger.debug("set parameter %s with value %s" % (name, value))
    lines = []
    with open(conf, 'r') as fd:
        lines = fd.readlines()

    re_name = re.compile(name)
    newlines = []
    find = False
    for line in lines:
        line = line.strip()
        newline = ''
        if not line.startswith(name):
            newlines.append(line)
            continue

        find = True
        _, oldvalue = line.split('=')
        newline = "%s=%s" % (name, str(value))
        newlines.append(newline)
        logger.debug(
            "find exist parameter %s with value %s" % (name, oldvalue)
            )
        
    if not find:
        newlines.append("%s=%s" % (name, str(value)))

    with open(conf, 'w') as fd:
        fd.write("\n".join(newlines))

def capture_server_output(proc, logfile):
    """ this is called by a new thread, so that it can capture the log
    with blocking the main thread

    ..note:
      currently not taking care of the thread end running staffing

    :type proc: :class:`subprocess.Popen`
    :param proc: return by subprocess.Popen function call
    
    :type logfile: str
    :param logfile: the log absolute file path
    """
    logger.debug("capture log to %s" % logfile)
    with open(logfile, 'a') as fd:
        for line in iter(proc.stdout.readline, ''):
            fd.write('%s' % line)

class DBServer(object):
    """database server instance management
    
    ..note:
      two static methods is used to initialize a database data, after
      call start to start a database service, return a server real
      object.

    :type data_path: str
    :param data_path: the directory for the database data location
    
    :type pid: int
    :param pid: the database init process id
    """
    def __init__(self, popen, port):
        self._popen = popen
        self._port = port
        if not self.is_running():
            logger.debug("the DBServer fail to start")
            logger.debug(
                'PostgreSQL Init process fail for %s' % self.exit_code()
                )
            raise Exception("DBServer fail to start")

    @staticmethod
    def set_dbconf(data_path, **params):
        """currently we don't have a place to set the config params for
        a case, let's design it in future, and now i just simply set it
        hard code here, now i only want to change the port

        :type data_path: str
        :param data_path: the directory of the database data store
        
        :type params: dict
        :param params: the parameters and values to change or add
        """
        new_port = _PORT
        conf_file = os.path.join(data_path, 'postgresql.conf')
        for name, value in params.items():
            set_parameter_in_conf_file(conf_file, name, value)

    @staticmethod
    def initDB(data_path):
        """initialize the data store for a database

        :type data_path: str
        :param data_path: the directory of the database data store
        """
        bin_path = get_installation_bin_path()
        initdb = os.path.join(bin_path, 'initdb')
        lib_path = get_installation_lib_path()
        logger.debug("DBServer::initDB() bin: %s, lib: %s"
                     % (initdb, lib_path))
        env = {'LD_LIBRARY_PATH': lib_path}
        child = subprocess.run(
            [initdb, '-D', data_path, '--no-clean', '--no-sync',
             '--debug', '--no-locale'],
            env=env, stdout=subprocess.PIPE,
            universal_newlines=True,
            stderr=subprocess.PIPE)
        if child.returncode != 0:
            logger.debug(child.args)
            logger.debug(child.stdout)
            logger.debug(child.stderr)
            # logger.error(child.stderr)
            raise Exception(
                "fail to do initdb for (%s)" % child.stderr
                )
        logger.debug(
            'database initialize successfully under %s' % data_path
            )
        logger.debug(child.stdout)

    @staticmethod
    def get_postmaster_status(data_path):
        """read the data directory postmaster.pid file to check the
        status of the postgres, and check wether the pid is a active
        process.

        ..note:
          if the postmaster.pid file is not exist, just return None, None

        :type data_path: str
        :param data_path: the database instance data directory path

        :rtype: list
        :returns: process id and its status(running or dead)
        """
        postmaster_file = os.path.join(data_path, 'postmaster.pid')
        if not os.path.exists(postmaster_file):
            return
        pid = 0
        with open(postmaster_file, 'r') as fd:
            pid = int(fd.read().split()[0])

        try:
            os.kill(pid, 0)
        except OSError:
            return pid, 'dead'
        
        return 1231, 'running'
    
    @staticmethod
    def start(data_path, log_path=None):
        """start the postgresql server

        :type data_path: str
        :param data_path: the data path that server will start base on

        :type log_path: str
        :param log_path: the log file absolute path

        :rtype: :class:`DBServer`
        :returns: a server instance who will accept the test
        """
        logger.debug('starting a PostgreSQL server instance')
        bin_path = get_installation_bin_path()
        postgres = os.path.join(bin_path, 'postgres')
        lib_path = get_installation_lib_path()
        logger.debug(
            "DBServer::start() bin: %s, lib: %s" % (postgres, lib_path)
            )

        if log_path:
            logger.debug("log directory: %s" % log_path)
            
        env = {'LD_LIBRARY_PATH': lib_path}

        child = None
        postgres_cmd = [postgres, '-D', data_path, '-F', '-d', '5']
        child = subprocess.Popen(postgres_cmd,
                                 universal_newlines=True,
                                 env=env, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT)

        if log_path:
            t = threading.Thread(target=capture_server_output,
                                 args=(child, "%s/postmaster.log"%log_path))
            t.start()

        # sleep for a very short time to wait the process start at
        # os level
        time.sleep(0.2)
        
        return DBServer(child, _PORT)

    def stop(self, wait=True):
        """simply use kill signal to kill the postgresql server, without
        taking care the data loss, we will finish the test case, and will
        not use the data for ever.

        a wait was involved because the stop will take some time, and auto
        tool may start a new process, and that time the last instance was
        not totally remove in the OS.

        :type wait: Boolen
        :param wait: indicate wehter need to double check the db is indeed
                     stop, if yes, the function will wait until the process
                     exist
        """
        self._popen.kill()
        
        if wait is False:
            return

        while self.is_running():
            time.sleep(1)
            
        logger.debug('server is stopped')

    def is_ready(self):
        """whether PostgreSQL is accepting message

        although the process of the database server may be up, but it
        maybe cannot accept message, this function use psql to send
        message to check whether the server is really can handle message

        :rtype: Boolen
        :returns: whether the database server is running and can accept
                  message (means psql can connect to)
        """
        if not self.is_running():
            logger.debug(
                'PostgreSQL Init process fail for %s' % self.exit_code()
                )
            logger.debug(self._popen.stderr.read())
            raise Exception("DBServer fail to start")
        
        bin_path = get_installation_bin_path()
        psql = os.path.join(bin_path, 'psql')
        lib_path = get_installation_lib_path()
        logger.debug('DBServer::is_ready() bin: %s, lib: %s'
                     % (psql, lib_path))
        env = {'LD_LIBRARY_PATH': lib_path}
        cmd = " ".join([
            psql, '-p', str(self._port), str(_DBNAME), '<', '/dev/null'
            ])
        child = subprocess.run(
            cmd, shell=True, env=env, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
            )
        
        if child.returncode != 0:
            logger.debug("psql connect fail for reason %s"
                         % child.stderr)
            return False

        return True
    
    def is_running(self):
        """PostgreSQL process is running

        :rtype: Boolen
        :returns: whetther the server is running
        """
        return self._popen.poll() is None

    def exit_code(self):
        return self._popen.poll()

    @staticmethod
    def removeDB(data_path):
        """ remove the database files and directory

        sometime we will found the deletion of the directory fail due to
        some `not empty` error, sleep 1 second, and try again, max_retry
        is limited
        """
        logger.debug(
            "database is successfully removed for %s" % data_path
            )
        import shutil
        retry_times = 0
        max_retry_times = 3
        while True:
            try:
                shutil.rmtree(data_path)
            except Exception as e:
                print("fail to remove the directory %s for reason %s"
                      % (data_path, str(e)))
                if retry_times >= max_retry_times:
                    exit(1)
                print("sleep 1 second and retry to remove again")
                time.sleep(1)
                continue
            else:
                break
            

    @staticmethod
    def check_database_data_exist(data_path):
        """find out is there any file exists in data directory

        :rtype: Boolen
        :returns: indicate is there any file exist
        """
        if not os.path.isdir(data_path):
            return False

        exist = False
        # if there is hidden file, also treate it as True
        for f in os.listdir(data_path):
            if f == '.' or f== '..':
                continue
            exist = True

        return exist

import os
import re
import logging
import subprocess

logger = logging.getLogger('DBServer')
_PORT = 5433

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

    Args:
      conf: str, the path of the configuration file
      name: str, parameter name to change or add
      value: int/str, parameter value to change or add
      
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


class DBServer(object):
    """database server instance management
    
    Args:
      data_path: str, the directory for the database data location
      pid: int, the database init process id

    ..note:
      two static methods is used to initialize a database data, after
      call start to start a database service, return a server real
      object.
    """
    def __init__(self, popen, port):
        self._popen = popen
        self._port = port
        if not self.is_running():
            logger.debug("the DBServer fail to start")
            raise Excpetion("DBServer fail to start")

    @staticmethod
    def set_dbconf(data_path, **params):
        """currently we don't have a place to set the config params for
        a case, let's design it in future, and now i just simply set it
        hard code here, now i only want to change the port

        Args:
          data_path: str, the directory of the database data store
          params: dict, the parameters and values to change or add
        """
        new_port = _PORT
        conf_file = os.path.join(data_path, 'postgresql.conf')
        for name, value in params.items():
            set_parameter_in_conf_file(conf_file, name, value)

    @staticmethod
    def initDB(data_path):
        """
        initialize the data store for a database

        Args:
          data_path: str, the directory of the database data store
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
            stderr=subprocess.PIPE)
        if child.returncode != 0:
            logger.debug(child.args)
            logger.debug(child.stdout)
            logger.debug(child.stderr)
            # logger.error(child.stderr)
            raise Exception(
                "fail to do initdb for (%s)" % child.stderr.decode('ascii')
                )
        logger.debug(
            'database initialize successfully under %s' % data_path
            )
        logger.debug(child.stdout.decode('ascii'))

    @staticmethod
    def get_postmaster_status(data_path):
        """read the data directory postmaster.pid file to check the
        status of the postgres, and check wether the pid is a active
        process.

        Args:
          data_path: str, the database instance data directory path

        Returns:
          pid: int, the process id of the init process of postgres
          status: str, status string of the postgres, running, or deaded

        ..note:
          if the postmaster.pid file is not exist, just return None, None
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
    def start(data_path):
        logger.debug('starting a PostgreSQL server instance')
        bin_path = get_installation_bin_path()
        postgres = os.path.join(bin_path, 'postgres')
        lib_path = get_installation_lib_path()
        logger.debug("DBServer::start() bin: %s, lib: %s"
                     % (postgres, lib_path))
        env = {'LD_LIBRARY_PATH': lib_path}
        child = subprocess.Popen([postgres, '-D', data_path],
                                 env=env, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        return DBServer(child, _PORT)

    def stop(self):
        self._popen.kill()
        logger.debug('server is stopped')

    def is_ready(self):
        """whether PostgreSQL is accepting message

        although the process of the database server may be up, but it
        maybe cannot accept message, this function use psql to send
        message to check whether the server is really can handle message
        """
        if not self.is_running():
            logger.debug('PostgreSQL process is not alive')
            return False
        
        bin_path = get_installation_bin_path()
        psql = os.path.join(bin_path, 'psql')
        lib_path = get_installation_lib_path()
        logger.debug("DBServer::start() bin: %s, lib: %s"
                     % (psql, lib_path))
        env = {'LD_LIBRARY_PATH': lib_path}
        cmd = " ".join([
            psql, '-p', str(self._port), 'postgres', '<', '/dev/null'
            ])
        child = subprocess.run(
            cmd, shell=True, env=env, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
            )
        #cmd = " ".join([psql, '-p', str(_PORT), 'postgres',
        #                '<', '/dev/null', '>', '/dev/null 2>&1'])
        #print(cmd)
        if child.returncode != 0:
            logger.debug("psql connect fail for reason %s"
                         % child.stderr.decode())
            return False

        return True
    
    def is_running(self):
        """PostgreSQL process is running"""
        return self._popen.poll() is None

    @staticmethod
    def removeDB(data_path):
        logger.debug(
            "database is successfully removed for %s" % data_path
            )
        import shutil
        shutil.rmtree(data_path)

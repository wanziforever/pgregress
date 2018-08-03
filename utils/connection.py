import psycopg2
import logging

logger = logging.getLogger('connection')

class PGConnection(object):
    def __init__(self, conn):
        self._conn = conn
        self.name = 'unknown'

    def close(self):
        pass

    def is_avaliable(self):
        return True

    def set_name(self, name):
        self.name = name

    def execute(self, sql):
        logger.debug(
            'PGConnection::execute() Conn(%s): %s' % (self.name, sql))
        cursor = self._conn.cursor()
        cursor.execute(sql)
        try:
            rows = cursor.fetchall()
        except Exception as e:
            logger.debug("there is no response for sql %s" % sql)
            return
            
        for row in rows:
            print("    ", row[0])
            

class PGConnectionManager(object):
    def __init__(self):
        pass
    @staticmethod
    def new_connection(database, user, password, host, port):
        conn = psycopg2.connect(database=database, user=user,
                                password=password, host=host, port=port)
        return PGConnection(conn)

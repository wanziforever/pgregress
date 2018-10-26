#!/usr/bin/env python3

import psycopg2
import select
import time

database = "postgres"
user = "denny"
password = "denny"
host = '127.0.0.1'
port = 5433

def wait_async(conn):
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

def sync_exec(conn, sql):
    print("sync exec", sql)
    cursor = conn.cursor()
    cursor.execute(sql)
    wait_async(conn)
    return cursor

def exec(conn, sql):
    print("exec", sql)
    cursor = conn.cursor()
    cursor.execute(sql)
    wait_async(conn)
    return cursor

def getResult(cursor, seconds=0):
    conn = cursor.connection
    while 1:
        state = conn.poll()
        if state == psycopg2.extensions.POLL_OK:
            break

    descriptions = []
    if hasattr(cursor, "description") \
           and cursor.description is not None:
        descriptions = [desc[0] for desc in cursor.description]

    try:
        for record in cursor:
            print(record)
    except Exception as e:
        print(str(e))

    

    #while True:
    #    try:
    #        row = cursor.fetchone()
    #    except Exception as e:
    #        #print("we got some exception for fetchall", str(e))
    #        return descriptions, []
    #
    #    if not row:
    #        break
    #
    #    row = list(row)
    #
    #    print(descriptions)
    #    print(row)
    #    time.sleep(1)

maint_conn = psycopg2.connect(database=database, user=user, password=password, host=host, port=port)
conn1 = psycopg2.connect(database=database, user=user, password=password, host=host, port=port, async=0)
conn2 = psycopg2.connect(database=database, user=user, password=password, host=host, port=port, async=0)
conn3 = psycopg2.connect(database=database, user=user, password=password, host=host, port=port, async=0)
maint_conn.autocommit = True
wait_async(conn1)
wait_async(conn2)
wait_async(conn3)

maint_sql = """
CREATE TABLE tab_freeze (
id int PRIMARY KEY,
name char(3),
x int
);
"""
sync_exec(maint_conn, maint_sql)

maint_sql = "INSERT INTO tab_freeze VALUES (1, '111', 0);"
sync_exec(maint_conn, maint_sql)

maint_sql = "INSERT INTO tab_freeze VALUES (3, '333', 0);"
sync_exec(maint_conn, maint_sql)


sql1 = ''
sql2 = ''
sql3 = ''

sql1 = "BEGIN"
cursor = exec(conn1, sql1)
getResult(cursor)

sql2 = "BEGIN"
cursor = exec(conn2, sql2)
getResult(cursor)

sql3= "BEGIN"
cursor = exec(conn3, sql3)
getResult(cursor)

sql1 = "UPDATE tab_freeze SET x = x + 1 WHERE id = 3;"
cursor = exec(conn1, sql1)
getResult(cursor)

sql2 = "SELECT id FROM tab_freeze WHERE id = 3 FOR KEY SHARE;"
cursor = exec(conn2, sql2)
getResult(cursor)

sql3 = "SELECT id FROM tab_freeze WHERE id = 3 FOR KEY SHARE;"
cursor = exec(conn3, sql3)
getResult(cursor)

sql1 = "UPDATE tab_freeze SET x = x + 1 WHERE id = 3;"
cursor = exec(conn1, sql1)
getResult(cursor)

sql1 = "COMMIT;"
cursor = exec(conn1, sql1)
getResult(cursor)

sql2 = "COMMIT"
cursor = exec(conn2, sql2)
getResult(cursor)

sql2 = "VACUUM FREEZE tab_freeze;"
cursor = exec(conn2, sql2)
getResult(cursor)

#sql1 = """
#BEGIN;
#SET LOCAL enable_seqscan = false;
#SET LOCAL enable_bitmapscan = false;
#SELECT * FROM tab_freeze WHERE id = 3;
#COMMIT;"""
#
#cursor = exec(conn1, sql1)
#getResult(cursor)

sql1 = "BEGIN;"
cursor = exec(conn1, sql1)
getResult(cursor)

sql1 = "SET LOCAL enable_seqscan = false;"
cursor = exec(conn1, sql1)
getResult(cursor)

sql1 = "SET LOCAL enable_bitmapscan = false;"
cursor = exec(conn1, sql1)
getResult(cursor)

sql1 = "SELECT * FROM tab_freeze WHERE id = 3;SELECT count(*) from tab_freeze;"
cursor = exec(conn1, sql1)
getResult(cursor)

sql1 = "COMMIT;"
cursor = exec(conn1, sql1)
getResult(cursor)


sql3 = "COMMIT"
cursor = exec(conn3, sql3)
getResult(cursor)

sql2 = "VACUUM FREEZE tab_freeze;"
cursor = exec(conn2, sql2)
getResult(cursor)

sql1 = "SELECT * FROM tab_freeze ORDER BY name, id"
cursor = exec(conn1, sql1)
getResult(cursor)

#!/usr/bin/python env

import sys
import os
import subprocess
import time
sys.path.append('.')
import config
import logging

lib_path = os.path.join(config.installation,'lib')
bin_path = os.path.join(config.installation,'bin')
logger = logging.getLogger('KeyWords')
_INSTALLDIR = config.installation


pg_ctl = os.path.join(bin_path,'pg_ctl')

def start_db(log_file,data_path='tmp_instance/data'):
    print('try to start DB......\n')
    env = {'LD_LIBRARY_PATH': lib_path,'HG_BASE':_INSTALLDIR}
    start_cmd = [pg_ctl, '-D', data_path, 'start']
    try:
        with open(log_file,'a+') as logfile:
            return_code = subprocess.check_call(start_cmd,
                                 universal_newlines=True,
                                 env=env,stdout=logfile,
                                 stderr=logfile)

    except subprocess.CallProcessError as exc:
        print('start DB fail with returncode:',exc.returncode)
        print('output:', exc.output)

    if return_code == 0:
        print('SUCCESS! Start HighGo DB done')
    else:
        print('FAILE! Start HighGo DB fail, please check the log')

if len(sys.argv) == 3:
    start_db(sys.argv[1],sys.argv[2])
elif len(sys.argv) == 2:
    start_db(sys.argv[1])
else:
    start_db()

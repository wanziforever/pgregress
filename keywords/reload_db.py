#!/usr/bin/python env

import subprocess
import sys
sys.path.append('.')
import os
import time
import config
import logging

lib_path = os.path.join(config.installation,'lib')
bin_path = os.path.join(config.installation,'bin')
_INSTALLDIR = config.installation
logger = logging.getLogger('KeyWords')


pg_ctl = os.path.join(bin_path,'pg_ctl')

def reload_db(log_file,data_path='tmp_instance/data'):
    print('try to reload DB......\n')
    env = {'LD_LIBRARY_PATH': lib_path,'HG_BASE':_INSTALLDIR}
    reload_cmd = [pg_ctl,'-D',data_path,'reload']
    try:
        with open(log_file,'a+') as logfile:
            return_code = subprocess.check_call(reload_cmd,
                                     universal_newlines=True,
                                     env=env, stdout=logfile,
                                     stderr=logfile)

    except subprocess.CalledProcessError as exc:
        print('reload DB faile with returncode:', exc.returncode)
        print('output:', exc.output)

    if return_code == 0:
        print('SUCCESS! Reload HighGo DB done')
    else:
        print('FAILE! Reload HighGo DB fail, please check the log')

logger.info("start to reload config files......")
if len(sys.argv) == 3:
    reload_db(sys.argv[1],sys.argv[2])
elif len(sys.argv) ==2:
    reload_db(sys.argv[1])
else:
    reload_db()

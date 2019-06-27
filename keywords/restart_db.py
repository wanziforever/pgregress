#!/usr/bin/python env

import subprocess
import sys
sys.path.append('.')
import os
import time
import config

lib_path = os.path.join(config.installation,'lib')
bin_path = os.path.join(config.installation,'bin')

pg_ctl = os.path.join(bin_path,'pg_ctl')

def restart_db(log_file,data_path='tmp_instance/data'):
    print('try to restart DB......\n')
    env = {'LD_LIBRARY_PATH': lib_path}
    restart_cmd = [pg_ctl,'-D',data_path,'restart']
    with open(log_file,'a+') as logfile:
        try:
            return_code = subprocess.check_call(restart_cmd,
                                     universal_newlines=True,
                                     env=env, stdout=logfile,
                                     stderr=logfile)

        except subprocess.CalledProcessError as exc:
            print('restart DB faile with returncode:', exc.returncode)
            print('output:', exc.output)

        if return_code != 0:
            print('FAILE! Restart HighGo DB fail, please check the log')
        else:
            print('SUCCESS! Restart HighGo DB done')

if len(sys.argv) == 3:
    restart_db(sys.argv[1],sys.argv[2])
elif len(sys.argv) ==2:
    restart_db(sys.argv[1])
else:
    restart_db()

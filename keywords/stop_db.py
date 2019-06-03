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

def stop_db(log_file,data_path='tmp_instance/data'):
    print('try to stop DB......\n')
    env = {'LD_LIBRARY_PATH': lib_path}
    stop_cmd = [pg_ctl,'-D',data_path,'stop','-m','immediate']
    with open(log_file,'a+') as logfile:
        try:
            return_code = subprocess.check_call(stop_cmd,
                                     universal_newlines=True,
                                     #env=env, stdout=sys.stdout,
                                     env=env, stdout=logfile,
                                     stderr=logfile)
                                     #stderr=sys.stdout)

        except subprocess.CalledProcessError as exc:
            print('stop DB faile with returncode:', exc.returncode)
            print('output:', exc.output)

        if return_code != 0:
            print('FAILE! Stop HighGo DB fail, please check the log')
        else:
            print('SUCCESS! Stop HighGo DB done')
 
if len(sys.argv) == 3:
    stop_db(sys.argv[1],sys.argv[2])
elif len(sys.argv) ==2:
    stop_db(sys.argv[1])
else:
    stop_db()

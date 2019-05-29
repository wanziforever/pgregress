#!/usr/bin/python env

import subprocess
import sys
import time
import config

lib_path = os.path.joint(config.installtion,'lib')
bin_path = os.path.joint(config.installtion,'bin')
pg_ctl = os.path.joint(bin_path,'pg_ctl')
log_file = '/home/sunhuihui/regression/purog/outputs/logs/shell_cmd.log'

def stop_db(data_path,log_file):
    print('try to stop DB......\n')
    env = {'LD_LIBRARY_PATH': lib_path}
    stop_cmd = [pg_ctl,'-D',data_path,'stop','-m','immediate']
    logfile = open(log_file,'w')
    try:
        return_code = subprocess.check_call(stop_cmd,
                                 universal_newlines=True,
                                 env=env, stdout=logfile,
                                 stderr=subprocess.STDOUT)

    except subprocess.CalledProcessError, exc:
        print('stop DB faile with returncode:', exc.returncode)
        print('output:', exc.output)

    if return_code != 0:
        print('FAILE! Stop HighGo DB fail, please check the log')
    else:
        print('SUCCESS! Stop HighGo DB done')
 
stop_db(sys.argv[1])

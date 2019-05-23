#!/usr/bin/python
import sys
import os
#sys.path.append('/home/sunhuihui/pgregress')
sys.path.append('.')
import config
import subprocess


def stopDB(data_path):
    log_file = os.path.join(log_path,'postmaster.log')
    postgres_cmd = [pg_ctl,'-D',data_path,'stop','-m','immediate']
    try:
        log = open(log_file,'ab')
        child = subprocess.check_call(postgres_cmd,
                     universal_newlines=True,
                     env=env, 
                     stdout=sys.stdout,
                     stderr=sys.stderr)
                     #stdout=log,
                     #stderr=log)

        time.sleep(0.2)
        log.close()

    except subprocess.CalledProcessError as e:
        logger.info('stop DB fail')
        logger.debug('stop DB faili with ',e.output)


_DATA_PATH = './tmp_instance/data'

bin_path = os.path.join(config.installation, 'bin')
pg_ctl = os.path.join(bin_path, 'pg_ctl')
cmd = ' '.join([pg_ctl,'-D',_DATA_PATH,'restart'])

print("DB restart command is: %s...." % cmd)

return_code = subprocess.call(cmd,shell=True)

if return_code == 0:
    print('DB restart SUCCESS')
else:
    print('DB restart FAIL')


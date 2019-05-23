#!/usr/bin/python
import sys
import os
#sys.path.append('/home/sunhuihui/pgregress')
sys.path.append('.')
import config
import subprocess

'''
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
'''
print("Try to restart DB....")

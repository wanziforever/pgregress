#! /usr/bin/python env
import sys
import os
sys.path.append('.')
import subprocess
import argparse
import config

parser = argparse.ArgumentParser(description='Execute command on server.')
parser.add_argument('command', help='the command will be executed.')
parser.parse_args()

bin_path = os.path.join(config.installation, 'bin')
lib_path = os.path.join(config.installation, 'lib')

my_path = os.environ.copy()
my_path['PATH'] = '%s:'%bin_path + my_path['PATH']
my_path['LD_LIBRARY_PATH'] = lib_path
my_path['PGPASSWORD'] = 'highgo123'
cmd = sys.argv[1]
child = subprocess.Popen(cmd,shell=True,
                          env=my_path,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
output, errors = child.communicate()

# the output from network or disks is byte, should decode() to str.
# Or set niversal_newlines to TRUE,python will help to decode.
# On some OS, the type ofoutput is str, there is no need to decode,
# so, add a judgement.
if type(output) != str:
    output = output.decode()
print(output)

if child.returncode != 0:
    print('FAILE! Exec command: \'%s\' fail' % cmd)
else:
    print('SUCCESS! Exec command: \'%s\' done' % cmd)

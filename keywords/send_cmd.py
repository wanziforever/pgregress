#! /usr/bin/python env
import sys
import subprocess
import argparse

parser = argparse.ArgumentParser(description='Execute command on server.')
parser.add_argument('command', help='the command will be executed.')
#parser.add_argument('server', help='the server on which command will be executed.')
parser.parse_args()

cmd = sys.argv[1]
child = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
output, errors = child.communicate()

# the output from network or disks is byte, should decode() to str.
# Or set niversal_newlines to TRUE,python will help to decode.
output = output.decode()
print(output)

if child.returncode != 0:
    print('Exec command: \'%s\' fail' % cmd)
else:
    print('Exec command: \'%s\' success' % cmd)

import sys
import os
import subprocess
import time
import config

lib_path = os.path.join(config.installation,'lib')
bin_path = os.path.join(config.installation,'bin')
postgres = os.path.join(bin_path,'postgres')

def start_db(data_path):
    print('try to start DB......')
    env = {'LD_LIBRARY_PATH': lib_path}
    os.system('cp server* /home/sunhuihui/data')
    os.system('chmod 600 /home/sunhuihui/data/server*')
    start_cmd = [postgres, '-D', data_path, '-F', '-d', '5']
    child = subprocess.Popen(start_cmd,
                             universal_newlines=True,
                             env=env, 
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
    #out,err = child.communicate()
    #print(out)

    time.sleep(1)
     
    if child.poll() == None:
        print('DONE! returncode is:',child.returncode)
    else:
        print('FAILE! returncode is:',child.returncode)
   
'''
def _start_db():
    print('try to start DB......')
    env = {'LD_LIBRARY_PATH': lib_path}
    os.system('cp server* /home/sunhuihui/data')
    os.system('chmod 600 /home/sunhuihui/data/server*')
    postgres_cmd = [postgres, '-D', data_path, '-F', '-d', '5']
    child = subprocess.Popen(postgres_cmd,
                             universal_newlines=True,
                             #env=env, stdout=subprocess.PIPE,
                             env=env, stdout=sys.stdout,
                             stderr=sys.stderr)
    
    #for line in iter(child.stdout.readline,b''):
    #    print(line)
    #out,err = child.communicate()
    #print('out is,',out)
    with open('logfile','a') as fd:
        for line in iter(child.stdout.readline,''):
            fd.write('%s' % line)

    time.sleep(1)
     
    if child.poll() == None:
        print('returncode is:',child.returncode)
        print('DONE')
        os.system('rm -rf ../data')
    else:
        print('returncode is:',child.returncode)
        print('fail')
'''
start_db(sys.argv[1])

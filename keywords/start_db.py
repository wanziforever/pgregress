import sys
import os
import subprocess
import time
sys.path.append('.')
import config

lib_path = os.path.join(config.installation,'lib')
bin_path = os.path.join(config.installation,'bin')


postgres = os.path.join(bin_path,'postgres')

#def start_db(data_path='tmp_instance/data',log_file):
def start_db(log_file,data_path='tmp_instance/data'):
    print('try to start DB......')
    env = {'LD_LIBRARY_PATH': lib_path}
    start_cmd = [postgres, '-D', data_path, '-F', '-d', '5']
    with open(log_file,'a+') as logfile:
        child = subprocess.Popen(start_cmd,
                                 universal_newlines=True,
                                 env=env,stdout=logfile,
                                 stderr=logfile)

        time.sleep(3)
        if child.returncode == None:
            print('SUCCESS! Start HighGo DB done')
        else:
            print('FAILE! Start HighGo DB fail, please check the log')


'''
   child = subprocess.Popen(start_cmd,
                             universal_newlines=True,
                             env=env,stdout=sys.stdout,
                             stderr=sys.stdout)
                             #env=env,stdout=logfile,
                             #stderr=logfile)

    time.sleep(3)
    if child.returncode == None:
        print('SUCCESS! Start HighGo DB done')
    else:
        print('FAILE! Start HighGo DB fail, please check the log')

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


if len(sys.argv) == 3:
    start_db(sys.argv[1],sys.argv[2])
elif len(sys.argv) == 2:
    start_db(sys.argv[1])
else:
    start_db()

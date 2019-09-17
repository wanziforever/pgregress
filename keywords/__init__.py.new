import csv
import sys
import os
import subprocess
import shutil
import time
import argparse
import logging
sys.path.append("..")
import config


#parser = argparse.ArgumentParser(description='Execute command on server.')
#parser.add_argument('command', help='the command will be executed.')
#parser.parse_args()

bin_path = os.path.join(config.installation, 'bin')
lib_path = os.path.join(config.installation, 'lib')
logger = logging.getLogger('keywords')
_TESTCASEDIR = config.testcases
_INSTALLDIR = config.installation

my_path = os.environ.copy()
my_path['PATH'] = '%s:'%bin_path + my_path['PATH']
my_path['LD_LIBRARY_PATH'] = lib_path
my_path['PGPASSWORD'] = 'Highgo@123'


def send_cmd(cmd):
    child = subprocess.Popen(cmd,shell=True,
                              env=my_path,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT)
    output, errors = child.communicate()
    
    # the output from network or disks is byte, should decode() to str.
    # Or set niversal_newlines to TRUE,python will help to decode.
    # On some OS, the type ofoutput is str, there is no need to decode,
    # so, add a judgement.
    # str-->bytes is encode
    # bytes-->str is decode
    if type(output) != str:
        output = output.decode('utf-8','replace')
    print(output)
    
    if child.returncode != 0:
        print('FAILE! Exec command: \'%s\' fail' % cmd)
    else:
        print('SUCCESS! Exec command: \'%s\' done' % cmd)
    

#def psql(user,database,sqlfile):
def psql(info_list):
    sql_file=os.path.join(_TESTCASEDIR,info_list[-1])
    info_list[-1]=sql_file
    info_list.insert(0,'psql')
    print('psql, the command is ',info_list)
    child = subprocess.Popen(cmd,shell=True,
                              env=my_path,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT)
    output, errors = child.communicate()
    # the output from network or disks is byte, should decode() to str.
    # Or set niversal_newlines to TRUE,python will help to decode.
    # On some OS, the type ofoutput is str, there is no need to decode,
    # so, add a judgement.
    # str-->bytes is encode
    # bytes-->str is decode
    if type(output) != str:
        output = output.decode('utf-8','replace')
    print(output)
    
    if child.returncode != 0:
        print('FAILE! Exec command: \'%s\' fail' % cmd)
    else:
        print('SUCCESS! Exec command: \'%s\' done' % cmd)
 

def restart_db(log_file,data_path='tmp_instance/data'):
    print('try to restart DB......\n')
    pg_ctl = os.path.join(bin_path,'pg_ctl')
    env = {'LD_LIBRARY_PATH': lib_path,'HG_BASE':_INSTALLDIR}
    restart_cmd = [pg_ctl,'-D',data_path,'restart']
    log_file = os.path.join(_TESTCASEDIR,log_file[0])
    try:
        with open(log_file,'a+') as logfile:
            return_code = subprocess.check_call(restart_cmd,
                                     universal_newlines=True,
                                     env=env, stdout=logfile,
                                     stderr=logfile)

    except subprocess.CalledProcessError as exc:
        print('restart DB faile with returncode:', exc.returncode)
        print('output:', exc.output)

    if return_code == 0:
        print('SUCCESS! Restart HighGo DB done')
    else:
        print('FAILE! Restart HighGo DB fail, please check the log')


def start_db(log_file,data_path='tmp_instance/data'):
    pg_ctl = os.path.join(bin_path,'pg_ctl')

    print('try to start DB......\n')
    env = {'LD_LIBRARY_PATH': lib_path,'HG_BASE':_INSTALLDIR}
    start_cmd = [pg_ctl, '-D', data_path, 'start']
    log_file = os.path.join(_TESTCASEDIR,log_file[0])
    try:
        with open(log_file,'a+') as logfile:
            return_code = subprocess.check_call(start_cmd,
                                 universal_newlines=True,
                                 env=env,stdout=logfile,
                                 stderr=logfile)

    except subprocess.CallProcessError as exc:
        print('start DB fail with returncode:',exc.returncode)
        print('output:', exc.output)

    if return_code == 0:
        print('SUCCESS! Start HighGo DB done')
    else:
        print('FAILE! Start HighGo DB fail, please check the log')


def stop_db(log_file,data_path='tmp_instance/data'):
    pg_ctl = os.path.join(bin_path,'pg_ctl')
    print('try to stop DB......\n')
    env = {'LD_LIBRARY_PATH': lib_path,'HG_BASE':_INSTALLDIR}
    stop_cmd = [pg_ctl,'-D',data_path,'stop','-m','immediate']
    log_file = os.path.join(_TESTCASEDIR,log_file[0])
    try:
        with open(log_file,'a+') as logfile:
            return_code = subprocess.check_call(stop_cmd,
                                 universal_newlines=True,
                                 env=env, stdout=logfile,
                                 stderr=logfile)

    except subprocess.CalledProcessError as exc:
        print('stop DB fail with returncode:', exc.returncode)
        print('output:', exc.output)

    if return_code == 0:
        print('SUCCESS! Stop HighGo DB done')
    else:
        print('FAILE! Stop HighGo DB fail, please check the log')



def reload_db(log_file,data_path='tmp_instance/data'):

    print('try to reload DB......\n')
    pg_ctl = os.path.join(bin_path,'pg_ctl')
    env = {'LD_LIBRARY_PATH': lib_path,'HG_BASE':_INSTALLDIR}
    reload_cmd = [pg_ctl,'-D',data_path,'reload']
    log_file = os.path.join(_TESTCASEDIR,log_file[0])
    #print('reload command is ',reload_cmd,'log_file is ',log_file)
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



#def generate_new_csv(source_csv_list,target_csv):
def generate_new_csv(source_csv,target_csv):
    new_csv=[]
    #for source_csv in source_csv_list:
    with open(source_csv,'r') as myFile:
        lines=csv.reader(myFile)
        for line in lines:
            if "SELECT pg_catalog.pg_isolation_test_session_is_blocked" in line[13]:
                continue
            else:
                new_csv.append([line[1],line[2],line[7],line[13],line[22]])

    with open(target_csv,'w') as myFile:
        csv_writer = csv.writer(myFile)
        for line in new_csv:
            csv_writer.writerow(line)


def make_diff_csv(output_csv,expected_csv):
    diff_cmd = 'diff ' + output_csv + ' ' + expected_csv
    child = subprocess.Popen(diff_cmd,shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             universal_newlines=True)
    child.wait()
    print('the difference between %s and %s is:\n " %s "'%(output_csv,expected_csv,child.stdout.read()))

    '''
    if child.returncode == 0:
        print('the difference between %s and %s is " %s "'%(output_csv,expected_csv,child.stdout.read()))
    else:
        print('compare csv file failed for unexpected reason')
        print('the difference between %s and %s is " %s "'%(output_csv,expected_csv,child.stdout.read()))
    '''

def audit_log(profile_name):
    audit_log_dir = './tmp_instance/data/audit_log'
    expected_dir = os.path.join(_TESTCASEDIR,'%s/expected'%profile_name[0])
    output_dir = os.path.join(_TESTCASEDIR,'%s/outputs/results'%profile_name[0])

    for csv_file in os.listdir(audit_log_dir):
        csv_source = os.path.join(audit_log_dir,csv_file)
        csv_output = os.path.join(output_dir,csv_file)
        generate_new_csv(csv_source,csv_output)

    for csv_file in os.listdir(audit_log_dir):
        if csv_file.endswith('.csv'):
            expected_csv = os.path.join(expected_dir,csv_file)
            output_csv = os.path.join(output_dir,csv_file)
            if os.path.exists(expected_csv):
                make_diff_csv(output_csv,expected_csv)
            else:
                print("there is no %s"%expected_csv)

    output_audit_dir = os.path.join(output_dir,'audit_log_save')
    if os.path.exists(output_audit_dir):
        shutil.rmtree(output_audit_dir)
    shutil.copytree(audit_log_dir,output_audit_dir)
    print('the original audit log are save in %s'%output_audit_dir)


def set_config(param_list,data_path='tmp_instance/data'):
    conf_file = param_list[0]
    param_values = param_list[1:]
    t_file = data_path + '/' + conf_file
    #with open(t_file,'a') as f:
    #    f.write('\n')
    #    f.write('%s'%param_value)
    #    f.write('\n')
    #print("SUCCESS! set value DONE in file: %s WITH %s"%(t_file,param_values))
    print("set config DONE in file: %s WITH %s"%(t_file,param_values))

#!/usr/bin/python env
import csv
import sys
import os
sys.path.append('.')
import config
import subprocess
import shutil

def generate_new_csv(source_csv_list,target_csv):
    new_csv=[]
    for source_csv in source_csv_list:
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

# main
if __name__ == "__main__":
    audit_log_dir = './tmp_instance/data/audit_log'
    profile_name = sys.argv[1]
    expected_dir = os.path.join(config.testcases,'%s/expected'%profile_name)
    output_dir = os.path.join(config.testcases,'%s/outputs/results'%profile_name)
 
    csv_file_list = []
    for csv_file in os.listdir(audit_log_dir):
        csv_file_path = os.path.join(audit_log_dir,csv_file)
        csv_file_list.append(csv_file_path)
    output_file = os.path.join(output_dir,'hg-audit.csv')
    generate_new_csv(csv_file_list,output_file)

    for csv_file in os.listdir(audit_log_dir):
        if csv_file.endswith('.csv'):
            expected_file = os.path.join(expected_dir,'hg-audit.csv')
            output_file = os.path.join(output_dir,'hg-audit.csv')
            if os.path.exists(expected_file):
                make_diff_csv(output_file,expected_file)
            else:
                print("there is no %s"%expected_file)

    output_audit_dir = os.path.join(output_dir,'audit_log_save')
    if os.path.exists(output_audit_dir):
        shutil.rmtree(output_audit_dir)
    shutil.copytree(audit_log_dir,output_audit_dir)
    print('the original audit log are save in %s'%output_audit_dir)

#!/usr/bin/python
import sys
import os
sys.path.append('.')
import config

config_file,config_para,config_value = sys.argv[1].split()
#config_para = sys.argv[2]
#config_value = sys.argv[3]

print("reset the %s to %s in %s" %(config_para,config_value,config_file))

'''
def set_db_conf(conf_file,**param,data_path='tmp_instance/data'):
    config = data_path + '/' + conf_file
    with open(config,'r') as f:
        f = 
'''

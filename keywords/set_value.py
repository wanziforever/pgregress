#!/usr/bin/python
import sys
sys.path.append('.')
import os
import config


def set_value(conf_file,param_values,data_path='tmp_instance/data'):
    t_file = data_path + '/' + conf_file
    with open(t_file,'a') as f:
        f.write('\n')
        f.write('%s'%param_value) 
        f.write('\n')
    print("SUCCESS! set value DONE in file: %s WITH %s"%(t_file,param_values))

config_file,param_value = sys.argv[1].split(' ',1)

#set_value(config_file, param_value,data_path ='/home/sunhuihui')
set_value(config_file, param_value)

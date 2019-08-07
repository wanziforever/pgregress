host = '127.0.0.1'

##CONFIG FOR SAFE VERSION
#port = 5866
#dbname = 'highgo'
#user='sysdba'
#password='highgo123'

##CONFIG FOR ENTERPRISE VERSION
#port = 5866
#dbname = 'highgo'
#user='sunhuihui'
#password=''

#CONFIG FOR POSTGESQL
port = 5432
dbname = 'postgres'
user='gitlab-runner'
password=''

##INSTALLATION DIR FOR ENTERPRISE DB
#installation='/opt/HighGoDB-5.6.4'
##INSTALLATION DIR FOR SAFE DB
installation='/home/gitlab-runner/HighGo'

##the directory of regression cases
testcases='/home/gitlab-runner/regression/'

##only for installcheck
#data_path='/opt/HighGoDB-5.6.4/data'
#log_path='/opt/HighGoDB-5.6.4/log'

runner_output_to_streen=True
#runner_output_to_streen=False


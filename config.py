host = '127.0.0.1'

#config for safe version
#port = 5866
#dbname = 'highgo'
#user='sysdba'
#password='highgo123'

##config for enterprise version
#port = 5866
#dbname = 'highgo'
#user='sunhuihui'

#config for offical PG
port = 5432
dbname = 'postgres'
user='gitlab-runner'
password=''

##the installation directory for enterprise database
#installation='/opt/HighGoDB-5.6.4'
##the installation directory for safe database
installation='/home/gitlab-runner/HighGo'

##the directory of regression cases
testcases='/home/gitlab-runner/regression/'

##only for installcheck
#data_path='/opt/HighGoDB-5.6.4/data'
#log_path='/opt/HighGoDB-5.6.4/log'

runner_output_to_streen=True
#runner_output_to_streen=False


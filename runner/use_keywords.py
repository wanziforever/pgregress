import sys
sys.path.append('..')
from keywords import *

func_name=sys.argv[1]
params = sys.argv[2:]
#send_cmd('ls -l')
eval(func_name)(params)

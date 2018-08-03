#!/usr/bin/env python

import sys
from profile import Profile
from app import Application
import logging
logger = logging.getLogger('main')

def help():
    print("<%s> " % sys.argv[0])

logging.basicConfig(level=logging.DEBUG)
#logging.basicConfig(level=logging.INFO)

logger = logging.getLogger('main')
    
# main
profile = Profile('./data/testprofile')

app = Application(profile)
try:
    app.run()
except Exception as e:
    print()
    logger.error(str(e))
    import traceback
    logger.debug(traceback.format_exc())
else:    
    logger.debug('Done')

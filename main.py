#!/usr/bin/env python3

import sys
import os
from profile import Profile
from app import Application
import logging
import config
logger = logging.getLogger('main')

def help():
    print("<%s> " % sys.argv[0])

#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger('main')
test_data_dir = config.testcases

def all_profiles():
    """list all the valid test profiles

    :rtype: list
    :returns: a profile path list
    """
    dirs = []
    for f in os.listdir(test_data_dir):
        if f.startswith('.'):
            continue

        path = os.path.join(test_data_dir, f)
        if not os.path.isdir(path):
            continue
        
        dirs.append(path)
        
    return dirs

# main
if __name__ == "__main__":
    for profile in all_profiles():
        profile = Profile(profile, use_schedule=True)

        app = Application(profile)
        try:
            app.run()
            app.report_gen()
        except Exception as e:
            print()
            logger.error(str(e))
            import traceback
            logger.debug(traceback.format_exc())
        else:    
            logger.debug('Done')

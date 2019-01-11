#!/usr/bin/env python3

import sys
import os
import importlib
from profile import Profile
#from multiapp import MultiApplication
import logging
import xml.dom.minidom as xmldom
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
def parse_strategy():
    """parse the strategy xml file

    :rtype: the strategy file for this framework
    :returns: a dict between strategy name and used applicaiton,profile, checker class name 
    """
    global strategy_map
    strategy_map = dict()
    
    filepath=os.path.abspath("strategy.xml")
    DOMTree = xmldom.parse(filepath)
    collection = DOMTree.documentElement
    strategy = collection.getElementsByTagName("strategy")
    for i in strategy:
        attr_name = str(i.getAttribute("name"))
        attr_app = str(i.getAttribute("applicationClass"))
        attr_profile = str(i.getAttribute("profileClass"))
        attr_checker = str(i.getAttribute("checkerClass"))
        strategy_map.update({attr_name:[attr_app,attr_profile,attr_checker]})


# main
if __name__ == "__main__":
    parse_strategy()

    for profile in all_profiles():
        profile = Profile(profile, use_schedule=True)
        if profile._ptype not in list(strategy_map.keys()):
            logger.error("unknown strategy name: %s" % profile._ptype)
            exit()
        app_mod = importlib.import_module(strategy_map[profile._ptype][0])
        app = app_mod.Application(profile)

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

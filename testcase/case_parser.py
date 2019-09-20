#!/usr/bin/env python3

"""
parse the test case file, and generate the related structure
..note
  the step related sql will only generate the string type and setup or
  teardown related sqls will have list type, since there are possiblity
  multiple setup or teardown sections, and we want to seperate the sqls
  in different sections, so we put the sqls in different sections to a
  list. the reason not let the step sql use list is to max consistent with
  C version program output (there is no `[]` in the screen print of the
  step sqls)
"""

import json
import ply.yacc as yacc
from .case_tokens import tokens

from .modules import (KeyWord, SQLBlock, StepCmdModule, SessionModule, SetupModule,
                      TearDownModule, Permutation)

#import logging
#logging.basicConfig(level=logging.DEBUG)
#logger = logging.getLogger()

statements = {
    'keywords': [],
    'setup': [],
    'teardown': [],
    'sessions': [],
    'permutations': [],
    # here use a session sequence is the workaround for permutation
    # generation, the aim is to keep the same sequence of the permutation
    # with offical C version, but we use a dict type session holder, when
    # generating the permutation, the dict keys will not show the real
    # definition sequence in the testcase
    'session_sequence': []
    }

def p_statement_expression(p):
    '''statement : keywords_statement setup_multiple teardown_multiple session_statement
                 | setup_multiple teardown_multiple session_statement
                 | statement session_statement
                 | statement permutation_statement
                 | keywords_statement'''

    # here we handle statement setup is to different the setup in session
    if len(p) == 5:
        statements['keywords'] = p[1]
        statements['setup'] = p[2]
        statements['teardown'] = p[3]
    if len(p) == 4:
        statements['setup'] = p[1]
        statements['teardown'] = p[2]
    if len(p) == 2:
        statements['keywords'] = p[1]
        
    p[0] = statements

def p_keywords_statement(p):
    '''keywords_statement : KEYWORD KEYWORDCLAUSE'''
    modules =[]
    keywords_clause = p[2]
    keywords_list = keywords_clause.split(';')
    for keyword in keywords_list:
        keyword_module = KeyWord(keyword)
        modules.append(keyword_module)
    p[0] = modules


def p_empty(p):
    '''empty : '''
    pass

def p_setup_multiple(p):
    '''setup_multiple : setup_multiple setup_statement
                      | setup_statement
                      | empty'''
    if len(p) == 2:
        if p[1] is None:
            p[0] = []
        else:
            p[0] = [ p[1] ]
        
    elif len(p) == 3:
        tmp = list(p[1])
        tmp.append(p[2])
        p[0] = tmp

# setup, here is just a temp solution
def p_setup_statement_expression(p):
    '''setup_statement : SETUP SQLCLAUSE'''
    module = SetupModule()
    module.set_sql_block(SQLBlock(p[2]))
    p[0] = module

def p_teardown_multiple(p):
    '''teardown_multiple : teardown_multiple teardown_statement
                         | teardown_statement
                         | empty'''
    if len(p) == 2:
        if p[1] is None:
            p[0] = []
        else:
            p[0] = [ p[1] ]
        
    elif len(p) == 3:
        tmp = p[1]
        tmp.extend(p[2])
        p[0] = tmp

def p_teardown_statement_expression(p):
    '''teardown_statement : TEARDOWN SQLCLAUSE'''
    # if there will be a teardown in session, will do the same setup
    module = TearDownModule()
    module.set_sql_block(SQLBlock(p[2]))
    p[0] = module

def p_session_statement_expression(p):
    '''session_statement : SESSION ID continue_steps_expression 
                         | SESSION ID continue_commands_expression'''
    tag = p[2].strip('\"')
    session_module = SessionModule(tag)
    session_steps = p[3]
    for step in session_steps:
        step.set_session(tag)
        session_module.add_step(step)
        
    statements['sessions'].append(session_module)

def p_continue_commands_expression_cmdlock(p):
    '''continue_commands_expression : continue_commands_expression command 
                                    | command'''
    if len(p) == 2:
        p[0] = []
        p[0].append(p[1])
        
    elif len(p) == 3:
        tmp = p[1]
        tmp.append(p[2])
        p[0] = tmp
        
def p_commands_cmdblock(p):
    '''command : COMMAND ID KEYWORDCLAUSE'''
    tag = p[2].strip('\"')
    module = StepCmdModule(tag)
    #module._cmdlist.append(p[3])
    module.build_shellcmd(p[3])
    p[0] = module

def p_session_statement_setup_expression(p):
    '''session_statement : SESSION ID setup_statement continue_steps_expression'''
    tag = p[2].strip('\"')
    session_module = SessionModule(tag)
    setup_module = p[3]
    session_steps = p[4]
    session_module.set_setup(setup_module)
    setup_module.set_session(tag)
    for step in session_steps:
        step.set_session(tag)
        session_module.add_step(step)
    statements['sessions'].append(session_module)

def p_session_statement_setup_teardown_expression(p):
    '''session_statement : SESSION ID setup_statement continue_steps_expression teardown_statement'''
    tag = p[2].strip('\"')
    session_module = SessionModule(tag)
    setup_module = p[3]
    teardown_module = p[5]
    session_steps = p[4]
    session_module.set_setup(setup_module)
    setup_module.set_session(tag)
    session_module.set_teardown(teardown_module)
    teardown_module.set_session(tag)
    for step in session_steps:
        step.set_session(tag)
        session_module.add_step(step)

    statements['sessions'].append(session_module)

def p_session_statement_teardown_expression(p):
    '''session_statement : SESSION ID continue_steps_expression teardown_statement'''
    tag = p[2].strip('\"')
    session_module = SessionModule(tag)
    session_steps = p[3]
    teardown_module = p[4]
    session_module.set_teardown(teardown_module)
    teardown_module.set_session(tag)
    for step in session_steps:
        step.set_session(tag)
        session_module.add_step(step)

    statements['sessions'].append(session_module)
    
def p_continue_steps_expression_sqlblock(p):
    '''continue_steps_expression : continue_steps_expression step
                                 | step'''
    if len(p) == 2:
        p[0] = []
        p[0].append(p[1])
        
    elif len(p) == 3:
        tmp = p[1]
        tmp.append(p[2])
        p[0] = tmp
        
def p_step_sqlblock(p):
    '''step : STEP ID SQLCLAUSE'''
    tag = p[2].strip('\"')
    module = StepCmdModule(tag)
    module.set_sql_block(SQLBlock(p[3]))
    p[0] = module

def p_permutation_statement(p):
    '''permutation_statement : permutation_expression'''
    statements['permutations'].append(p[1])

def p_permutation_expression_id(p):
    '''permutation_expression : PERMUTATION ID
                              | permutation_expression ID'''
    tag = p[2].strip('\"')
    if isinstance(p[1], Permutation):
        p[1].add_step_tag(tag)
        p[0] = p[1]
    else:
        from .modules import new_permutation_class
        p[0] = new_permutation_class()
        p[0].add_step_tag(tag)

def p_error(p):
    print("Syntax error in input!")
    print(p)

#parser = yacc.yacc(debug=True, debuglog=logger)
parser = yacc.yacc()

def parse_testcase_structure(data):
    return parser.parse(data)
    

if __name__ == "__main__":
    data = '''
setup
{
 CREATE TABLE a (i int PRIMARY KEY);
 CREATE TABLE b (a_id int);
 INSERT INTO a VALUES (0), (1), (2), (3);
 INSERT INTO b SELECT generate_series(1,1000) % 4;
}

teardown
{
 DROP TABLE a, b;
}

session "s1"
step "s1"	{ BEGIN; }
step "at1"	{ ALTER TABLE b ADD CONSTRAINT bfk FOREIGN KEY (a_id) REFERENCES a (i) NOT VALID; }
step "sc1"	{ COMMIT; }
step "s2"	{ BEGIN; }
step "at2"	{ ALTER TABLE b VALIDATE CONSTRAINT bfk; }
step "sc2"	{ COMMIT; }

session "s2"
setup		{ BEGIN; }
step "rx1"	{ SELECT * FROM b WHERE a_id = 1 LIMIT 1; }
step "wx"	{ INSERT INTO b VALUES (0); }
step "rx3"	{ SELECT * FROM b WHERE a_id = 3 LIMIT 3; }
step "c2"	{ COMMIT; }

session "s3"
step "rx1"	{ SELECT * FROM b WHERE a_id = 1 LIMIT 1; }
step "wx"	{ INSERT INTO b VALUES (0); }
step "rx3"	{ SELECT * FROM b WHERE a_id = 3 LIMIT 3; }
step "c2"	{ COMMIT; }
teardown { TEST_TEARDOWN; }

permutation "s1" "at1" "sc1" "s2" "at2" "sc2" "rx1" "wx" "rx3" "c2"
permutation "s1" "at1" "sc1" "s2" "at2" "rx1" "sc2" "wx" "rx3" "c2"
'''
    result = parser.parse(data)
    print(result)
    #print(json.dumps(result, indent=4, sort_keys=True))
    # Build the parser with debuglog
    #result = parser.parse(data, debug=logger)
    print("all done")

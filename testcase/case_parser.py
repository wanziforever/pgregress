#!/usr/bin/env python

import json
import ply.yacc as yacc
from .case_tokens import tokens
#import logging
#logging.basicConfig(level=logging.DEBUG)
#logger = logging.getLogger()

statements = {
    'setup': [],
    'teardown': [],
    'sessions': {},
    'permutations': []
    }

def p_statement_expression(p):
    '''statement : setup_statement teardown_statement session_statement
                 | statement session_statement
                 | statement permutation_statement'''
    p[0] = statements
    if len(p) == 4:
        statements['setup'] = p[1]

def p_setup_statement_expression(p):
    'setup_statement : SETUP L_LARGEPAREN sqlblock R_LARGEPAREN'
    p[0] = p[3]

def p_sqlblock_clause(p):
    '''sqlblock : sqlblock SQLCLAUSE
                | SQLCLAUSE'''
    if len(p) == 2:
        p[0] = []
        p[0].append(p[1])
    elif len(p) == 3:
        tmp = p[1]
        tmp.append(p[2])
        p[0] = tmp

def p_teardown_statement_expression(p):
    '''teardown_statement : TEARDOWN L_LARGEPAREN sqlblock R_LARGEPAREN'''
    p[0] = p[3]
    statements['teardown'] = p[0]

def p_session_statement_expression(p):
    '''session_statement : SESSION ID continue_steps_expression'''
    tag = p[2].strip('\"')
    statements['sessions'][tag] = {
        'steps': p[3]
        }

def p_session_statement_setup_expression(p):
    '''session_statement : SESSION ID setup_statement continue_steps_expression'''
    tag = p[2].strip('\"')
    setup = p[3]
    statements['sessions'][tag] = {
        'steps': p[4],
        'setup': setup
        }

def p_session_statement_setup_teardown_expression(p):
    '''session_statement : SESSION ID setup_statement continue_steps_expression teardown_statement'''
    tag = p[2].strip('\"')
    setup = p[3]
    teardown = p[5]
    statements['sessions'][tag] = {
        'sqls': p[4],
        'setup': setup,
        'teardown': teardown
        }

def p_session_statement_teardown_expression(p):
    '''session_statement : SESSION ID continue_steps_expression teardown_statement'''
    tag = p[2].strip('\"')
    teardown = p[4]
    statements['sessions'][tag] = {
        'sqls': p[3],
        'teardown': teardown
        }
    
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
    '''step : STEP ID L_LARGEPAREN sqlblock R_LARGEPAREN'''
    p[0] = {
        'sqls': p[4],
        'tag': p[2].strip('\"')
        }

def p_permutation_statement(p):
    '''permutation_statement : permutation_expression'''
    statements['permutations'].append(p[1])

def p_permutation_expression_id(p):
    '''permutation_expression : PERMUTATION ID
                              | permutation_expression ID'''
    tag = p[2].strip('\"')
    if isinstance(p[1], list):
        p[1].append(tag)
        p[0] = p[1]
    else:
        p[0] = [tag]

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

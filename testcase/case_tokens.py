#!/usr/bin/env python

import ply.lex as lex

# List of token names.
tokens = [
    'SETUP',
    #'SQLBLOCK',
    'SQLCLAUSE',
    'L_LARGEPAREN',
    'R_LARGEPAREN',
    'TEARDOWN',
    'SESSION',
    'STEP',
    #'QUOTE',
    'PERMUTATION',
    'ID',
    'COMMENTS'
    ]

# Regular expression rules for simple tokens
t_SETUP = r'setup'
#t_SQLBLOCK = r'\{[\w\n ;()%,\_\-]+\}'
t_SQLCLAUSE = r'[a-zA-Z0-9 \t%-_()]+;'
t_L_LARGEPAREN = r'\{'
t_R_LARGEPAREN = r'\}'
t_TEARDOWN = r'teardown'
t_SESSION = r'session'
t_PERMUTATION = r'permutation'
t_STEP = r'step'
#t_QUOTE = r'"'
t_ID = r'\"[a-zA-z0-9]+\"'
t_COMMENTS = r'\#[^\n\r]*'

# A regular expression rule with some action code
#def t_SQLBLOCK(t):
#    r'{.+}'
#    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

t_ignore = ' \t'

def t_error(t):
    print("Illegal charactor '%s'" % t.value[0])
    t.lexer.skip(1)

lexer = lex.lex()

# with
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
step "s1a" { BEGIN; }
step "s1b" { ALTER TABLE b ADD CONSTRAINT bfk FOREIGN KEY (a_id) REFERENCES a (i) NOT VALID; }
step "s1c" { COMMIT; }

session "s2"
step "s2a" { BEGIN; }
step "s2b" { SELECT * FROM a WHERE i = 1 LIMIT 1 FOR UPDATE; }
step "s2c" { SELECT * FROM b WHERE a_id = 3 LIMIT 1 FOR UPDATE; }
step "s2d" { INSERT INTO b VALUES (0); }
step "s2e" { INSERT INTO a VALUES (4); }
step "s2f" { COMMIT; }

'''

#print(data)
#
#
#lexer.input(data)
#
#while True:
#    tok = lexer.token()
#    if not tok: break
#    print(tok)


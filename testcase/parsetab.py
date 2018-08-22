
# parsetab.py
# This file is automatically generated. Do not edit.
# pylint: disable=W,C,R
_tabversion = '3.10'

_lr_method = 'LALR'

_lr_signature = 'COMMENTS ID L_LARGEPAREN PERMUTATION R_LARGEPAREN SESSION SETUP SQLCLAUSE STEP TEARDOWNstatement : setup_statement teardown_statement session_statement\n                 | statement session_statement\n                 | statement permutation_statementcomment_block : comment_block COMMENTS\n                   | COMMENTSsetup_statement : SETUP L_LARGEPAREN sqlblock R_LARGEPAREN\n                       | comment_block setup_statementsqlblock : sqlblock SQLCLAUSE\n                | SQLCLAUSEteardown_statement : TEARDOWN L_LARGEPAREN sqlblock R_LARGEPARENsession_statement : SESSION ID continue_steps_expressionsession_statement : SESSION ID setup_statement continue_steps_expressionsession_statement : SESSION ID setup_statement continue_steps_expression teardown_statementsession_statement : SESSION ID continue_steps_expression teardown_statementcontinue_steps_expression : continue_steps_expression step\n                                 | stepstep : STEP ID L_LARGEPAREN sqlblock R_LARGEPARENpermutation_statement : permutation_expressionpermutation_expression : PERMUTATION ID\n                              | permutation_expression ID'
    
_lr_action_items = {'STEP':([6,17,24,25,26,27,32,33,38,],[-7,23,-16,23,23,-6,-15,23,-17,]),'$end':([2,10,11,12,16,18,21,24,25,31,32,33,34,36,38,],[0,-2,-18,-3,-19,-20,-1,-16,-11,-14,-15,-12,-10,-13,-17,]),'L_LARGEPAREN':([4,15,30,],[13,22,35,]),'SESSION':([2,10,11,12,14,16,18,21,24,25,31,32,33,34,36,38,],[9,-2,-18,-3,9,-19,-20,-1,-16,-11,-14,-15,-12,-10,-13,-17,]),'SQLCLAUSE':([13,19,20,22,28,29,35,37,],[20,28,-9,20,-8,28,20,28,]),'R_LARGEPAREN':([19,20,28,29,37,],[27,-9,-8,34,38,]),'TEARDOWN':([5,6,24,25,27,32,33,38,],[15,-7,-16,15,-6,-15,15,-17,]),'SETUP':([0,1,3,7,17,],[4,4,-5,-4,4,]),'PERMUTATION':([2,10,11,12,16,18,21,24,25,31,32,33,34,36,38,],[8,-2,-18,-3,-19,-20,-1,-16,-11,-14,-15,-12,-10,-13,-17,]),'ID':([8,9,11,16,18,23,],[16,17,18,-19,-20,30,]),'COMMENTS':([0,1,3,7,17,],[3,7,-5,-4,3,]),}

_lr_action = {}
for _k, _v in _lr_action_items.items():
   for _x,_y in zip(_v[0],_v[1]):
      if not _x in _lr_action:  _lr_action[_x] = {}
      _lr_action[_x][_k] = _y
del _lr_action_items

_lr_goto_items = {'comment_block':([0,1,17,],[1,1,1,]),'sqlblock':([13,22,35,],[19,29,37,]),'teardown_statement':([5,25,33,],[14,31,36,]),'session_statement':([2,14,],[10,21,]),'permutation_expression':([2,],[11,]),'statement':([0,],[2,]),'step':([17,25,26,33,],[24,32,24,32,]),'continue_steps_expression':([17,26,],[25,33,]),'setup_statement':([0,1,17,],[5,6,26,]),'permutation_statement':([2,],[12,]),}

_lr_goto = {}
for _k, _v in _lr_goto_items.items():
   for _x, _y in zip(_v[0], _v[1]):
       if not _x in _lr_goto: _lr_goto[_x] = {}
       _lr_goto[_x][_k] = _y
del _lr_goto_items
_lr_productions = [
  ("S' -> statement","S'",1,None,None,None),
  ('statement -> setup_statement teardown_statement session_statement','statement',3,'p_statement_expression','case_parser.py',18),
  ('statement -> statement session_statement','statement',2,'p_statement_expression','case_parser.py',19),
  ('statement -> statement permutation_statement','statement',2,'p_statement_expression','case_parser.py',20),
  ('comment_block -> comment_block COMMENTS','comment_block',2,'p_comments_block','case_parser.py',26),
  ('comment_block -> COMMENTS','comment_block',1,'p_comments_block','case_parser.py',27),
  ('setup_statement -> SETUP L_LARGEPAREN sqlblock R_LARGEPAREN','setup_statement',4,'p_setup_statement_expression','case_parser.py',31),
  ('setup_statement -> comment_block setup_statement','setup_statement',2,'p_setup_statement_expression','case_parser.py',32),
  ('sqlblock -> sqlblock SQLCLAUSE','sqlblock',2,'p_sqlblock_clause','case_parser.py',37),
  ('sqlblock -> SQLCLAUSE','sqlblock',1,'p_sqlblock_clause','case_parser.py',38),
  ('teardown_statement -> TEARDOWN L_LARGEPAREN sqlblock R_LARGEPAREN','teardown_statement',4,'p_teardown_statement_expression','case_parser.py',48),
  ('session_statement -> SESSION ID continue_steps_expression','session_statement',3,'p_session_statement_expression','case_parser.py',53),
  ('session_statement -> SESSION ID setup_statement continue_steps_expression','session_statement',4,'p_session_statement_setup_expression','case_parser.py',60),
  ('session_statement -> SESSION ID setup_statement continue_steps_expression teardown_statement','session_statement',5,'p_session_statement_setup_teardown_expression','case_parser.py',69),
  ('session_statement -> SESSION ID continue_steps_expression teardown_statement','session_statement',4,'p_session_statement_teardown_expression','case_parser.py',80),
  ('continue_steps_expression -> continue_steps_expression step','continue_steps_expression',2,'p_continue_steps_expression_sqlblock','case_parser.py',89),
  ('continue_steps_expression -> step','continue_steps_expression',1,'p_continue_steps_expression_sqlblock','case_parser.py',90),
  ('step -> STEP ID L_LARGEPAREN sqlblock R_LARGEPAREN','step',5,'p_step_sqlblock','case_parser.py',101),
  ('permutation_statement -> permutation_expression','permutation_statement',1,'p_permutation_statement','case_parser.py',108),
  ('permutation_expression -> PERMUTATION ID','permutation_expression',2,'p_permutation_expression_id','case_parser.py',112),
  ('permutation_expression -> permutation_expression ID','permutation_expression',2,'p_permutation_expression_id','case_parser.py',113),
]

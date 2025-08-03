import ply.yacc as yacc
from ply.yacc import NullLogger
from lexer import tokens, lexer
from ast_nodes import (
    Program, VarDecl, ConstDecl, MapDecl, ProcDecl,
    Block, Assign, IncDec, IfStmt, WhileStmt,
    ProcCall, RobotOp, MapOp, PrintStmt,
    BinaryOp, UnaryOp, IntLiteral, BoolLiteral, VarRef
)

start = 'program'

precedence = (
    ('right', 'OP_NOT'),
    ('left', 'OP_GT', 'OP_LT', 'OP_EQ'),
    ('left', 'OP_OR'),
    ('left', '+', '-'),
    ('left', 'OP_INC', 'OP_DEC'),
)


def p_program(p):
    """program : stmt_list"""
    p[0] = Program(p[1])


def p_stmt_list_empty(p):
    """stmt_list :"""
    p[0] = []


def p_stmt_list_more(p):
    """stmt_list : stmt_list stmt"""
    p[0] = p[1] + ([p[2]] if p[2] is not None else [])


def p_stmt(p):
    """
    stmt : var_decl    opt_nl
         | const_decl  opt_nl
         | map_decl    opt_nl
         | proc_decl   opt_nl
         | assignment  opt_nl
         | incdec      opt_nl
         | if_stmt     opt_nl
         | while_stmt  opt_nl
         | proc_call   opt_nl
         | robot_op    opt_nl
         | map_op      opt_nl
         | print_stmt  opt_nl
         | expr        opt_nl
         | NEWLINE
    """
    p[0] = p[1]
    # если это одинокий NEWLINE — просто игнорируем
    if p.slice[1].type == 'NEWLINE':
        p[0] = None
    else:
        p[0] = p[1]


def p_var_decl(p):
    """
    var_decl : KW_INT IDENTIFIER OP_ASSIGN expr
             | KW_BOOLEAN IDENTIFIER OP_ASSIGN expr
    """
    p[0] = VarDecl(p[1].upper(), p[2], p[4])


def p_const_decl(p):
    """
    const_decl : KW_CINT IDENTIFIER OP_ASSIGN expr
               | KW_CBOOLEAN IDENTIFIER OP_ASSIGN expr
    """
    p[0] = ConstDecl(p[1].upper(), p[2], p[4])


def p_map_decl(p):
    """map_decl : KW_MAP IDENTIFIER"""
    p[0] = MapDecl(p[2])


def p_proc_decl(p):
    """proc_decl : KW_PROC IDENTIFIER param_list_opt block"""
    p[0] = ProcDecl(p[2], p[3] or [], p[4])


def p_param_list_opt(p):
    """
    param_list_opt : param_list
                   | empty
    """
    p[0] = p[1]


def p_param_list(p):
    """
    param_list : IDENTIFIER
               | param_list IDENTIFIER
    """
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]


def p_block(p):
    """block : LPAREN opt_nl stmt_list opt_nl RPAREN"""
    p[0] = Block([s for s in p[3] if s is not None])


def p_opt_nl(p):
    """
    opt_nl : opt_nl NEWLINE
           | empty
    """
    p[0] = None


def p_assignment(p):
    """assignment : IDENTIFIER OP_ASSIGN expr"""
    p[0] = Assign(p[1], p[3])


def p_incdec(p):
    """
    incdec : OP_INC LPAREN expr COMMA expr RPAREN
           | OP_DEC LPAREN expr COMMA expr RPAREN
    """
    tok = p[1].upper()
    left, right = p[3], p[5]
    p[0] = IncDec(tok, left, right)


def p_if_stmt(p):
    """
    if_stmt : KW_IF expr block else_opt
            | KW_IF LPAREN expr RPAREN block else_opt
    """
    if len(p) == 5:
        # вариант без скобок: if X B E
        cond = p[2]
        then_blk = p[3]
        else_blk = p[4]
    else:
        # вариант со скобками: if ( X ) B E
        cond = p[3]
        then_blk = p[5]
        else_blk = p[6]
    p[0] = IfStmt(cond, then_blk, else_blk)


def p_else_opt(p):
    """
    else_opt : KW_ELSE block
             | empty
    """
    p[0] = p[2] if len(p) == 3 else None


def p_while_stmt(p):
    """while_stmt : KW_WHILE expr KW_DO block"""
    p[0] = WhileStmt(p[2], p[4])


def p_call_args_opt(p):
    """call_args_opt : call_args
                     | empty"""
    p[0] = p[1] or []


def p_call_args(p):
    """call_args : expr
                 | call_args COMMA expr"""
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]


def p_proc_call(p):
    """proc_call : IDENTIFIER LPAREN call_args_opt RPAREN"""
    p[0] = ProcCall(p[1], p[3])


def p_robot_op(p):
    """
    robot_op : OP_STEP
             | OP_BACK
             | OP_RIGHT
             | OP_LEFT
             | OP_LOOK
    """
    # STEP — без аргумента, всегда «шаг вперёд»,
    # остальные — повороты или LOOK
    op = p[1].upper()
    p[0] = RobotOp(op)


def p_map_op(p):
    """
    map_op : MAP_BAR LPAREN IDENTIFIER COMMA IDENTIFIER COMMA arith_expr COMMA arith_expr RPAREN
           | MAP_EMP LPAREN IDENTIFIER COMMA IDENTIFIER COMMA arith_expr COMMA arith_expr RPAREN
           | MAP_SET LPAREN IDENTIFIER COMMA IDENTIFIER COMMA arith_expr COMMA arith_expr RPAREN
           | MAP_CLR LPAREN IDENTIFIER COMMA IDENTIFIER COMMA arith_expr COMMA arith_expr RPAREN
    """
    p[0] = MapOp(
        p[1].upper(),  # OP_BAR / OP_EMP / …
        p[3],  # result-var
        p[5],  # map-name
        p[7],  # x coordinate expr
        p[9],  # y coordinate expr
    )


def p_print_stmt(p):
    """
    print_stmt : KW_PRINT LPAREN expr RPAREN
               | KW_PRINT LPAREN RPAREN
    """
    if len(p) == 4:
        p[0] = PrintStmt(None)
    else:
        p[0] = PrintStmt(p[3])


def p_expr(p):
    """
    expr : arith_expr
         | logic_expr
         | robot_op
         | proc_call
         | incdec
    """
    p[0] = p[1]


def p_expr_list_single(p):
    """expr_list : expr"""
    p[0] = [p[1]]


def p_expr_list_more(p):
    """expr_list : expr_list COMMA expr"""
    p[0] = p[1] + [p[3]]


def p_arith_bin(p):
    """
    arith_expr : arith_expr '+' arith_expr
               | arith_expr '-' arith_expr
               | arith_expr OP_INC arith_expr
               | arith_expr OP_DEC arith_expr
    """
    p[0] = BinaryOp(p[2].upper(), p[1], p[3])


def p_arith_term(p):
    """arith_expr : term"""
    p[0] = p[1]


def p_term_paren(p):
    """term : LPAREN expr RPAREN"""
    p[0] = p[2]


def p_term_int(p):
    """term : INT_LITERAL"""
    p[0] = IntLiteral(p[1])


def p_term_var(p):
    """term : IDENTIFIER"""
    p[0] = VarRef(p[1])


def p_term_call(p):
    """term : proc_call"""
    p[0] = p[1]


def p_term_look(p):
    """term : OP_LOOK"""
    p[0] = RobotOp('LOOK')


def p_logic_true(p):
    """logic_expr : TRUE"""
    p[0] = BoolLiteral(True)


def p_logic_false(p):
    """logic_expr : FALSE"""
    p[0] = BoolLiteral(False)


def p_logic_not(p):
    """logic_expr : OP_NOT LPAREN expr RPAREN"""
    p[0] = UnaryOp('NOT', p[3])


def p_logic_cmp(p):
    """
    logic_expr : OP_GT LPAREN expr COMMA expr RPAREN
               | OP_LT LPAREN expr COMMA expr RPAREN
               | OP_EQ LPAREN expr COMMA expr RPAREN
    """
    # p[1] — строка 'GT', 'LT' или 'EQ'
    p[0] = BinaryOp(p[1], p[3], p[5])


def p_logic_or(p):
    """logic_expr : expr OP_OR expr"""
    p[0] = BinaryOp('OR', p[1], p[3])


def p_empty(p):
    """empty :"""
    p[0] = None


def p_error(p):
    if p:
        raise SyntaxError(f"""Syntax error at {p.type} (line {p.lineno})""")
    else:
        raise SyntaxError("""Syntax error at EOF""")


parser = yacc.yacc(
    write_tables=False,  # не писать .py таблицы
    debug=False,  # не выводить отладочную информацию
    errorlog=NullLogger()  # заглушить все предупреждения/ошибки
)
if __name__ == '__main__':
    from lexer import lexer

    sample = """
PROC try_move d (
    compute_coords(d)
    EMP(free, maze, nx, ny)
    IF (free) (
        x   := nx
        y   := ny
        dir := d
    )
)
    """
    # sample = open('program.txt').read().strip() + '\n'
    print(parser.parse(sample, lexer=lexer))

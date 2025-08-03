# tests/test_parser.py
import os, sys
# вставляем ../src/ в начало путей поиска модулей
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))


import pytest
from parser import parser, lexer
from ast_nodes import (
    Program, VarDecl, ConstDecl, MapDecl, ProcDecl,
    Assign, IncDec, IfStmt, WhileStmt,
    ProcCall, RobotOp, MapOp, PrintStmt,
    BinaryOp, UnaryOp, IntLiteral, BoolLiteral, VarRef, Block
)


def parse(src: str):
    a = parser.parse(src.strip() + '\n', lexer=lexer)
    print(a)
    return a


def test_empty_program():
    tree = parse("")
    assert isinstance(tree, Program)
    assert tree.directives == []


def test_multiple_statements():
    src = "INT a := 1\nINT b := 2"
    tree = parse(src)
    assert len(tree.directives) == 2
    assert isinstance(tree.directives[0], VarDecl)
    assert isinstance(tree.directives[1], VarDecl)


def test_case_insensitivity_keywords_and_identifiers():
    src = "iNt X := 5\ncInT y := 10"
    tree = parse(src)
    vd1, vd2 = tree.directives[:2]
    assert vd1.typ == 'INT' and vd1.name == 'X'
    assert vd2.typ == 'CINT' and vd2.name == 'y'


def test_arithmetic_binary_infix():
    tree = parse("1 + 2")
    expr = tree.directives[0]
    assert isinstance(expr, BinaryOp) and expr.op == '+'
    assert isinstance(expr.left, IntLiteral) and expr.left.value == 1
    assert isinstance(expr.right, IntLiteral) and expr.right.value == 2


def test_incdec_statement_and_expr():
    stm = parse("INC(x, 2)").directives[0]
    assert isinstance(stm, IncDec) and stm.op == 'INC'
    pr = parse("PRINT( INC(x, 3))").directives[0]
    assert isinstance(pr, PrintStmt)
    assert isinstance(pr.expr, IncDec)


def test_boolean_prefix_and_infix():
    stm = parse("NOT(EQ(a,3)) OR TRUE").directives[0]
    assert isinstance(stm, BinaryOp) and stm.op == 'OR'
    left = stm.left
    assert isinstance(left, UnaryOp) and left.op == 'NOT'
    assert isinstance(left.operand, BinaryOp) and left.operand.op == 'EQ'
    assert isinstance(stm.right, BoolLiteral) and stm.right.value is True


def test_comparison_prefix():
    for op in ('GT', 'LT', 'EQ'):
        cmp_node = parse(f"{op}(x, y)").directives[0]
        assert isinstance(cmp_node, BinaryOp) and cmp_node.op == op


def test_robot_and_map_ops():
    r2 = parse("LOOK").directives[0]
    assert isinstance(r2, RobotOp) and r2.op == 'LOOK'
    m = parse("EMP(f, m, 0, 1)").directives[0]
    assert isinstance(m, MapOp) and m.op == 'EMP'
    assert m.res_var == 'f' and m.map_name == 'm'
    assert isinstance(m.x, IntLiteral) and m.x.value == 0
    assert isinstance(m.y, IntLiteral) and m.y.value == 1


def test_if_and_while_complex():
    f = parse("IF EQ(x,0) ( y := 1 ) ELSE ( y := 2 )").directives[0]
    assert isinstance(f, IfStmt)
    w = parse("WHILE LT(i,5) DO ( INC(i,1) )").directives[0]
    assert isinstance(w, WhileStmt)


def test_proc_decl_and_call():
    p = parse("PROC foo a b ( INC(a,1) )").directives[0]
    assert isinstance(p, ProcDecl)
    assert p.name == 'foo' and p.params == ['a', 'b']
    call = parse("foo(x, y)").directives[0]
    print(call)
    assert isinstance(call, ProcCall)
    assert [arg.name for arg in call.args] == ['x', 'y']


def test_syntax_errors():
    bads = ["GT(x 1)", "EMP x, y, z", "PROC foo x", "(", ")"]
    for b in bads:
        with pytest.raises(SyntaxError):
            parse(b)

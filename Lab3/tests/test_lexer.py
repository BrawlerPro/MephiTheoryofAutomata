# tests/test_lexer.py

import pytest
from Lab3.src.lexer import lexer


def lex_types(s: str):
    lexer.input(s)
    return [tok.type for tok in lexer]


def lex_values(s: str):
    lexer.input(s)
    return [tok.value for tok in lexer]


def test_int_literal():
    types = lex_types("123\n")
    assert types == ["INT_LITERAL", "NEWLINE"]
    values = lex_values("123\n")
    assert values == [123, "\n"]


def test_identifier_and_assignment():
    types = lex_types("foo := 5\n")
    assert types == ["IDENTIFIER", "OP_ASSIGN", "INT_LITERAL", "NEWLINE"]
    assert lex_values("foo := 5\n") == ["foo", ":=", 5, "\n"]


def test_plus_minus_parens_comma():
    types = lex_types("x + (y - 2),z\n")
    assert types == [
        "IDENTIFIER", "+", "LPAREN", "IDENTIFIER", "-", "INT_LITERAL",
        "RPAREN", "COMMA", "IDENTIFIER", "NEWLINE"
    ]


def test_comments_and_blank_lines():
    src = """  
    // this is a comment
    42 // comment after code

    // another
    """
    types = lex_types(src)
    # blank line → NEWLINE, comment lines → skip but count NEWLINE
    # "  \n" → NEWLINE
    # "// this is..." → NEWLINE
    # "42 // ..." → INT_LITERAL, NEWLINE
    # "" (empty) → NEWLINE
    # "// another" → NEWLINE
    assert types == ["NEWLINE", "NEWLINE", "INT_LITERAL", "NEWLINE", "NEWLINE", "NEWLINE"]


def test_reserved_keywords_case_insensitive():
    kw = "int boolean cint cbOolean map proc if else while do print step back right left look bar emp set clr gt lt eq not or\n"
    types = lex_types(kw)
    assert types == [
        "KW_INT", "KW_BOOLEAN", "KW_CINT", "KW_CBOOLEAN",
        "KW_MAP", "KW_PROC", "KW_IF", "KW_ELSE", "KW_WHILE", "KW_DO",
        "KW_PRINT", "OP_STEP", "OP_BACK", "OP_RIGHT", "OP_LEFT", "OP_LOOK",
        "MAP_BAR", "MAP_EMP", "MAP_SET", "MAP_CLR",
        "OP_GT", "OP_LT", "OP_EQ", "OP_NOT", "OP_OR",
        "NEWLINE"
    ]


def test_mixed_input():
    src = "InT X:=10\nBOOLEAN ok:=TRUE\n//done\n"
    types = lex_types(src)
    assert types == [
        "KW_INT", "IDENTIFIER", "OP_ASSIGN", "INT_LITERAL", "NEWLINE",
        "KW_BOOLEAN", "IDENTIFIER", "OP_ASSIGN", "TRUE", "NEWLINE",
        "NEWLINE"
    ]

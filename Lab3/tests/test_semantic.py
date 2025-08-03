import pytest
from Lab3.src.parser import parser, lexer
from Lab3.src.semantic import SemanticAnalyzer, SemanticError


def parse(src: str):
    return parser.parse(src.strip() + "\n", lexer=lexer)


def run_semantic(src: str):
    tree = parse(src)
    SemanticAnalyzer().analyze(tree)


def test_valid_basic_declarations_and_ops():
    src = """
    INT x := 10
    CINT c := 5
    BOOLEAN b := TRUE
    CBOOLEAN flag := FALSE
    MAP m

    // простая арифметика
    INT sum := x + c
    INC(sum, 2)
    DEC(sum, 1)

    // сравнения и логика
    GT(sum, 10)
    LT(sum, 20)
    EQ(sum, 14)
    NOT(TRUE)

    // IF/WHILE с булевыми условиями
    IF EQ(x,10) (
        x := x + 1
    ) ELSE (
        x := x - 1
    )
    WHILE LT(x, 12) DO (
        x := x + 1
    )

    // PROC и вызов
    PROC foo a b (
        a := a + b
    )
    INT y := 1
    foo(x, y)
    
    // MapOp: EMP/BAR/SET/CLR с BOOLEAN–результатом
    EMP(b, m, 0, 0)
    BAR(b, m, 1, 1)
    SET(b, m, 2, 2)
    CLR(b, m, 2, 2)
    """
    # не должно бросить ошибок
    run_semantic(src)


@pytest.mark.parametrize("src", [
    # повторное глобальное объявление
    "INT x := 1\nINT x := 2",
    # присваивание неверного типа
    "INT x := TRUE",
    "BOOLEAN b := 0",  # 0 не Boolean
    # присваивание константы неверного типа
    "CINT c := FALSE",
    "CBOOLEAN f := 1",
    # INC/DEC от Boolean
    "BOOLEAN b := TRUE\nINC(b,1)",
    # IF с не-булевым условием
    "IF 123 ( x := 1 )",
    # WHILE с не-булевым условием
    "WHILE 0 DO ( )",
    # EQ с разными типами
    "EQ(TRUE, 1)",
    # OR/NOT с неверными типами
    "1 OR FALSE",
    "NOT(5)",
    # BAR/EMP/SET/CLR где res_var не Boolean
    "MAP m\nEMP(m, m, 0, 0)",
    "MAP m\nBAR(x, m, 1, 1)",  # x не объявлен
    "MAP m\nINT x := 0\nSET(x, m, 2,2)",  # x не Boolean
    "MAP m\nBOOLEAN b := TRUE\nCLR(x, m, 2,2)",  # x не объявлен
    # неверное число аргументов у процедуры
    "PROC foo a b ( )\nfoo(1)",
    # вызов неопределённой процедуры
    "bars(1,2)",
    # обращение к не объявленной переменной
    "INT x := 1\nPRINT(y)",
])
def test_semantic_errors(src):
    with pytest.raises(SemanticError):
        run_semantic(src)

import os, sys

# вставляем ../src/ в начало путей поиска модулей
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import pytest
import interpreter
from interpreter import Interpreter
from parser import parser, lexer


@pytest.fixture(autouse=True)
def dummy_load_labyrinth(monkeypatch):
    # Заменяем загрузку лабиринта на заглушку для всех тестов
    class DummyMap:
        pass

    class DummyRobot:
        x = 0
        y = 0
        orientation = 'NORTH'

        def step(self, direction): return True

        def back(self): return True

        def right(self): return True

        def left(self): return True

        def look(self): return 0

    def load(path):
        return DummyMap(), DummyRobot()

    # Патчим функцию в модуле interpreter, а не в loader
    monkeypatch.setattr(interpreter, 'load_labyrinth', load)


@pytest.fixture
def labyrinth_file(tmp_path):
    # minimal valid labyrinth: 1x1 grid with start and exit at (0,0)
    lab = tmp_path / 'lab.txt'
    lab.write_text("1 1\n0 0\n0 0\n")
    return str(lab)


def run_src(src: str, labyrinth_file: str, capsys) -> str:
    # Парсим, запускаем интерпретатор и возвращаем stdout
    tree = parser.parse(src, lexer=lexer)
    interp = Interpreter(visualize=False)
    interp.run(tree, labyrinth_file)
    captured = capsys.readouterr()
    return captured.out.strip()


def test_sum_recursion(labyrinth_file, capsys):
    src = '''
INT N := 5
INT S := 0

PROC sum n res (
    IF LT(n,1) (
        res := 0
    ) ELSE (
        INT m := n - 1
        INT tmp := 0
        sum(m, tmp)
        res := tmp + n
    )
)

sum(N, S)
PRINT(S)
'''
    assert run_src(src, labyrinth_file, capsys) == "15"


def test_fib_recursion(labyrinth_file, capsys):
    src = '''
INT N := 7
INT F := 0

PROC fib n res (
    IF LT(n,2) (
        res := n
    ) ELSE (
        INT n1 := n - 1
        INT t1 := 0
        fib(n1, t1)
        INT n2 := n - 2
        INT t2 := 0
        fib(n2, t2)
        res := t1 + t2
    )
)

fib(N, F)
PRINT(F)
'''
    assert run_src(src, labyrinth_file, capsys) == "13"


def test_even_odd_recursion(labyrinth_file, capsys):
    src = '''
INT N := 6
INT E := 0
INT O := 0

PROC is_even n res (
    IF LT(n,1) (
        res := 1
    ) ELSE (
        INT m := n - 1
        INT tmp := 0
        is_odd(m, tmp)
        res := tmp
    )
)

PROC is_odd n res (
    IF LT(n,1) (
        res := 0
    ) ELSE (
        INT m := n - 1
        INT tmp := 0
        is_even(m, tmp)
        res := tmp
    )
)

is_even(N, E)
is_odd(N, O)
PRINT(E)
PRINT(O)
'''
    output = run_src(src, labyrinth_file, capsys).splitlines()
    assert output == ["1", "0"]

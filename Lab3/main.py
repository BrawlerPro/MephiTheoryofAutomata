#!/usr/bin/env python3
import os
import sys

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
# Добавляем src/ в sys.path, чтобы импорты ниже работали
ROOT = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(ROOT, 'src'))

from parser import parser, lexer
from semantic import SemanticAnalyzer, SemanticError
from interpreter import Interpreter


def main():
    # Поддерживаем: main.py [--nogui] <программа.cr> <лабиринт.lab>
    visualize = True
    args = sys.argv[1:]
    if args and args[0] == '--nogui':
        visualize = False
        args = args[1:]
    if len(args) != 2:
        print("Использование: python main.py [--nogui] <программа.txt> <лабиринт.txt>")
        sys.exit(1)

    prog_file, lab_file = args
    source = open(prog_file, 'r', encoding='utf-8').read().rstrip() + '\n'

    # 1) Синтаксический разбор
    try:
        tree = parser.parse(source, lexer=lexer)
    except SyntaxError as e:
        print("Синтаксическая ошибка:", e)
        sys.exit(1)

    # 2) Семантический анализ
    try:
        SemanticAnalyzer().analyze(tree)
    except SemanticError as e:
        print("Ошибка семантики:", e)
        sys.exit(1)

    # 3) Интерпретация + визуализация
    interp = Interpreter(visualize=visualize, debug=False)
    interp.run(tree, lab_file)

    # После завершения движения (или закрытия окна Pygame) печатаем результат:
    rx, ry = interp.robot.x, interp.robot.y
    print(f"Final position: ({rx}, {ry})")

    ex, ey = interp.exit_x, interp.exit_y
    if (rx, ry) == (ex, ey):
        print("Robot has reached the exit!")
    else:
        print("Robot did NOT reach the exit.")


if __name__ == '__main__':
    main()

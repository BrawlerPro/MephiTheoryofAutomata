import sys
import time
import pygame
from parser import parser, lexer
from ast_nodes import (
    Program, VarDecl, ConstDecl, MapDecl, ProcDecl,
    Block, Assign, IncDec, IfStmt, WhileStmt,
    ProcCall, RobotOp, MapOp, BinaryOp, UnaryOp,
    IntLiteral, BoolLiteral, VarRef, PrintStmt
)
from semantic import SemanticAnalyzer, SemanticError
from loader import load_labyrinth


class Interpreter:
    """
    Интерпретатор для AST вашей мини-языка + визуализация робота в лабиринте.
    Хранит стек окружений (envs), зарегистрированные процедуры (procs),
    стек вызовов (call_stack), карту лабиринта и состояние робота.
    """

    def __init__(self, visualize=True, debug=False):
        # Координаты выхода в лабиринте
        self.exit_y = None
        self.exit_x = None
        # Список (стек) окружений: каждый элемент — dict имя: значение
        # envs[0] — глобальное окружение
        self.envs = [{}]
        # Словарь объявленных процедур: имя AST ProcDecl
        self.procs = {}
        # Стек сопоставлений формальных: фактических параметров
        self.call_stack = []
        # Объект карты лабиринта и робот
        self.world_map = None
        self.robot = None
        # Флаг и объект для визуализации через pygame
        self.visualize = visualize
        self.debug = debug
        self.visualizer = None

    def run(self, tree: Program, labyrinth_file: str):
        """
        Запускает интерпретацию AST (Program) на основании заданного файла лабиринта.
        1) Загружает лабиринт и инициализирует визуализатор
        2) Регистрирует глобальные переменные/константы и процедуры
        3) Исполняет все прочие директивы (операторы)
        4) Держит окно открытым после окончания выполнения
        """
        # 1. Загрузка лабиринта: строим world_map и robot
        self.world_map, self.robot = load_labyrinth(labyrinth_file)
        # Читаем координаты выхода из третьей строки файла
        with open(labyrinth_file, encoding='utf-8') as f:
            f.readline()  # пропускаем строку с размерами
            f.readline()  # пропускаем строку со стартовой позицией
            ex_line = f.readline().split()  # строка с выходом
            self.exit_x, self.exit_y = map(int, ex_line)

        # Если включена визуализация - инициализируем и сразу рисуем первый кадр
        if self.visualize:
            from visualizer import Visualizer
            self.visualizer = Visualizer(
                self.world_map, self.robot,
                exit_cell=(self.exit_x, self.exit_y)
            )
            self.visualizer.draw()

        # 2. Регистрируем в окружении глобальные Var/Const и сохраняем ProcDecl
        for d in tree.directives:
            if isinstance(d, ProcDecl):
                # Запоминаем тело процедуры
                self.procs[d.name] = d
            elif isinstance(d, (VarDecl, ConstDecl)):
                # Вычисляем значение и сохраняем в глобальном окружении
                val = self.eval_expr(d.expr)
                self.envs[0][d.name] = val

        # 3. Исполняем все остальные директивы (Print, Assign, If, While, ProcCall, MapDecl и т.п.)
        for d in tree.directives:
            if not isinstance(d, (VarDecl, ConstDecl, MapDecl, ProcDecl)):
                self.exec_node(d)

        # 4. После завершения программы - рисуем «финальный кадр» и ждём закрытия окна
        if self.visualize:
            while True:
                for evt in pygame.event.get():
                    if evt.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
        if self.visualize:
            pygame.quit()

    def exec_node(self, node):
        """
        Диспетчер: смотрим тип AST-узла и вызываем соответствующий метод exec_<Type>.
        """
        method = getattr(self, f"exec_{type(node).__name__}", None)
        if not method:
            raise RuntimeError(f"No exec method for node {type(node).__name__!r}")
        return method(node)

    def exec_VarDecl(self, node: VarDecl):
        """Объявление переменной: вычисляем начальное значение и сохраняем в текущем окружении."""
        self.envs[-1][node.name] = self.eval_expr(node.expr)

    def exec_ConstDecl(self, node: ConstDecl):
        """Объявление константы: аналогично VarDecl."""
        self.envs[-1][node.name] = self.eval_expr(node.expr)

    def exec_Assign(self, node: Assign):
        """Присваивание: вычисляем выражение и записываем в переменную."""
        name = self._resolve(node.name)
        self._assign(name, self.eval_expr(node.expr))

    def exec_PrintStmt(self, node: PrintStmt):
        """Оператор print."""
        if node.expr is None:
            print()
        else:
            print(self.eval_expr(node.expr))

    def exec_IncDec(self, node: IncDec):
        """
        Операция ++/-- (с приращением на значение):
        просто вычисляем её как часть выражения.
        """
        self.eval_expr(node)

    def exec_IfStmt(self, node: IfStmt):
        """Условный оператор if (else)."""
        if self.eval_expr(node.cond):
            self.exec_Block(node.then_block, new_scope=False)
        elif node.else_block:
            self.exec_Block(node.else_block, new_scope=False)

    def exec_WhileStmt(self, node: WhileStmt):
        """Цикл while."""
        while self.eval_expr(node.cond):
            self.exec_Block(node.block, new_scope=False)

    def exec_ProcCall(self, node: ProcCall):
        """
        Обрабатывает вызов процедуры/функции:
        1) находит её объявление по имени
        2) собирает имена «фактических» аргументов
        3) делегирует всю работу в _call_proc
        """
        proc_decl = self.procs.get(node.name)
        if proc_decl is None:
            raise RuntimeError(f"Процедура {node.name} не объявлена")
        # Собираем список имён переменных-аргументов
        actual_args = [self._resolve(arg.name) for arg in node.args]
        return self._call_proc(proc_decl, actual_args)

    def exec_Block(self, node: Block, new_scope: bool = True):
        # если new_scope=True — заводим новый словарь в стек envs
        if new_scope:
            self.envs.append({})
        for s in node.statements:
            self.exec_node(s)
        if new_scope:
            print(self.envs)
            self.envs.pop()

    def _call_proc(self, proc_decl, args):
        """
        Вызов процедуры/функции:
         - proc_decl.params — список формальных имён параметров
         - args               — список имён фактических переменных
        По соглашению:
         * если у процедуры >=2 параметров, то второй параметр — это выходной (res)
         * иначе процедура считается void и возвращает None
        """
        # 1) Подготовка: создаём пустое отображение формальных имён в реальные
        mapping = {}
        if self.debug:
            # В режиме отладки выводим информацию о вызове
            print(f"[CALL  ] {proc_decl.name}({', '.join(args)})")
            print(f"          mapping: {mapping}")
            print(
                f"          push env; stack depth = {len(self.envs) + 1} "
                f"envs={self.envs} call_stack={self.call_stack}"
            )

        # 2) Создаём новый фрейм вызова: локальное окружение и запись в стек
        local_env = {}
        self.envs.append(local_env)      # новый scope для локальных переменных
        self.call_stack.append(mapping)  # сохраняем текущую таблицу сопоставления

        # 3) Инициализация параметров
        #    Первый параметр копируется по значению в новую ячейку,
        #    остальные (выходные) — передаются по ссылке на существующую переменную.
        for i, (formal, actual) in enumerate(zip(proc_decl.params, args)):
            if i == 0:
                # создаём уникальное имя для входного параметра
                fresh_name = f"_in_{formal}_{len(self.envs)}"
                mapping[formal] = fresh_name
                # копируем текущее значение из вызывающего контекста
                local_env[fresh_name] = self._lookup(actual)
            else:
                # выходной (res) или другие параметры: храним ссылку
                mapping[formal] = actual
                local_env[actual] = self._lookup(actual)

        # 4) Выполняем тело процедуры без создания дополнительного scope
        self.exec_Block(proc_decl.body, new_scope=False)

        # 5) Считываем значение выходного параметра, если он есть
        result = None
        if len(proc_decl.params) >= 2:
            res_formal = proc_decl.params[1]
            real_name = mapping[res_formal]
            result = self._lookup(real_name)

        if self.debug and len(proc_decl.params) >= 2:
            # Выводим возвращаемое значение в режиме отладки
            print(f"[RETURN] {proc_decl.name} → {res_formal} = {result}")

        # 6) Закрываем фрейм: удаляем локальное окружение и соответствующую запись
        self.envs.pop()
        self.call_stack.pop()

        # 7) Записываем результат в окружение вызывающего, если есть выходной параметр
        if len(proc_decl.params) >= 2:
            self.envs[-1][real_name] = result

        return result

    ROBOT_OPS = {
        'STEP': 'step',
        'BACK': 'back',
        'RIGHT': 'right',
        'LEFT': 'left',
        'LOOK': 'look'
    }

    def exec_RobotOp(self, node: RobotOp):
        """
        Операции над роботом: STEP, BACK, RIGHT, LEFT, LOOK.
        STEP теперь двигает робота в направлении его текущей ориентации.
        BACK/RIGHT/LEFT просто меняют ориентацию.
        LOOK смотрит вперёд по текущей ориентации.
        После любого шага/поворота при включённой визуализации перерисовываем.
        """
        op = node.op

        # выбрасываем, если операция неизвестна
        if op not in ('STEP', 'BACK', 'RIGHT', 'LEFT', 'LOOK'):
            raise RuntimeError(f"Unknown RobotOp {op!r}")

        # для удобства заведём функцию перерисовки+проверки выхода
        def after_move(success: bool) -> bool:
            if self.visualize:
                self.visualizer.draw()
                # если это STEP и мы дошли до выхода — поздравляем и выходим
                if op == 'STEP' and (self.robot.x, self.robot.y) == (self.exit_x, self.exit_y):
                    self.visualizer.show_message("Robot has reached the exit!")
                    pygame.time.delay(2000)
                    pygame.quit()
                    sys.exit()
            return success

        if op == 'STEP':
            direction = self.robot.orientation  # 'NORTH'|'EAST'|'SOUTH'|'WEST'
            success = self.robot.step(direction)
            return after_move(success)

        elif op == 'BACK':
            success = self.robot.back()
            return after_move(success)

        elif op == 'RIGHT':
            success = self.robot.right()
            return after_move(success)

        elif op == 'LEFT':
            success = self.robot.left()
            return after_move(success)

        else:  # LOOK
            # возвращает целое расстояние до препятствия
            return self.robot.look()

    def exec_MapOp(self, node: MapOp):
        """
        Операции над картой: BAR, EMP, SET, CLR.
        После выполнения сохраняем результат в целевую переменную res_var.
        """
        x = self.eval_expr(node.x)
        y = self.eval_expr(node.y)

        if node.op == 'BAR':
            res = self.world_map.bar(x, y)
        elif node.op == 'EMP':
            res = self.world_map.emp(x, y)
        elif node.op == 'SET':
            self.world_map.set_cell(x, y, True)
            res = True
        elif node.op == 'CLR':
            self.world_map.clr(x, y)
            res = True
        else:
            raise RuntimeError(f"Unknown MapOp {node.op}")

        # сохраняем результат в указанную переменную
        tgt = self._resolve(node.res_var)
        self._assign(tgt, res)
        return res

    BIN_OPS = {
        '+': lambda a, b: a + b,
        '-': lambda a, b: a - b,
        'GT': lambda a, b: a > b,
        'LT': lambda a, b: a < b,
        'EQ': lambda a, b: a == b,
        'OR': lambda a, b: a or b,
    }

    def eval_expr(self, node):
        """
        Рекурсивное вычисление выражений:
        - Literal, VarRef, Unary/BinaryOp, IncDec, ProcCall
        - Специально обрабатываем LOOK как RobotOp
        """
        if isinstance(node, RobotOp) and node.op == 'LOOK':
            return self.exec_RobotOp(node)

        if isinstance(node, IntLiteral):
            if self.debug:
                print(f"[EXPR  ] Int {node.value}")
            return node.value

        if isinstance(node, BoolLiteral):
            if self.debug:
                print(f"[EXPR  ] Bool {node.value}")
            return node.value

        if isinstance(node, VarRef):
            name = self._resolve(node.name)  # находим фактическое имя
            return self._lookup(name)  # достаём из окружения

        if isinstance(node, IncDec):
            # инкремент/декремент вида x += delta или x -= delta
            name = self._resolve(node.target.name)
            old = self._lookup(name)
            delta = self.eval_expr(node.value)
            new = old + delta if node.op == 'INC' else old - delta
            self._assign(name, new)
            return new

        if isinstance(node, BinaryOp):
            left = self.eval_expr(node.left)
            right = self.eval_expr(node.right)
            if fn := self.BIN_OPS.get(node.op):
                return fn(left, right)
            raise RuntimeError(f"Unsupported binary op {node.op!r}")

        if isinstance(node, UnaryOp) and node.op == 'NOT':
            return not self.eval_expr(node.operand)

        if isinstance(node, ProcCall):
            return self.exec_ProcCall(node)

        raise RuntimeError(f"Cannot eval {node!r}")

    def _resolve(self, name):
        """
        Разрешение имени переменной через стек вызовов:
        если name — формальный параметр в текущем proc, заменяем на фактическое.
        """
        for m in reversed(self.call_stack):
            if name in m:
                return m[name]
        return name

    def _lookup(self, name):
        """
        Поиск значения переменной name в стеке окружений (от локальных к глобальным).
        Если не найдено — RuntimeError.
        """
        for env in reversed(self.envs):
            if name in env:
                return env[name]
        raise RuntimeError(f"Undefined var {name}")

    def _assign(self, name, val):
        """
        Присваивание name = val:
        ищем первую рамку окружения, где name уже объявлен,
        иначе записываем в текущее (верхнее) окружение.
        """
        if self.debug:
            print(f"[ASSIGN] {name} := {val}")
        for env in reversed(self.envs):
            if name in env:
                env[name] = val
                return
        self.envs[-1][name] = val


if __name__ == '__main__':
    # Точка входа: ожидаем два аргумента — файл программы и файл лабиринта
    if len(sys.argv) != 3:
        print("Usage: python interpreter.py <program> <labyrinth>")
        sys.exit(1)

    prog, lab = sys.argv[1], sys.argv[2]
    # Читаем исходник, парсим в AST
    src = open(prog, 'r', encoding='utf-8').read().strip() + '\n'
    tree = parser.parse(src, lexer=lexer)

    # Семантика: проверяем ошибки до выполнения
    try:
        SemanticAnalyzer().analyze(tree)
    except SemanticError as e:
        print("Semantic error:", e)
        sys.exit(1)

    # Запускаем интерпретатор
    Interpreter().run(tree, lab)

from ast_nodes import (
    Program, VarDecl, ConstDecl, MapDecl, ProcDecl,
    Assign, IncDec, IfStmt, WhileStmt, ProcCall,
    RobotOp, MapOp, BinaryOp, UnaryOp, IntLiteral,
    BoolLiteral, VarRef, PrintStmt, Block
)


class SemanticError(Exception):
    """Класс для ошибок семантического анализа."""
    pass


class Symbol:
    """Представление переменной/константы/карты в таблице символов."""
    def __init__(self, name, typ, is_const=False):
        self.name = name      # имя символа
        self.typ = typ        # 'INT', 'BOOLEAN' или 'MAP'
        self.is_const = is_const  # флаг, что это константа


class ProcSymbol:
    """Представление процедуры в таблице символов."""
    def __init__(self, name, params, scope):
        self.name = name
        # params — списком имён параметров (пока все INT)
        self.params = params
        # scope — AST-узел Block с телом процедуры
        self.scope = scope


class SemanticAnalyzer:
    def __init__(self):
        # глобальная таблица символов: имя → Symbol или ProcSymbol
        self.globals = {}
        # стек локальных таблиц (при заходе в процедуру или блок)
        self.scopes = []

    def error(self, node, msg: str):
        """Поднять SemanticError с информацией о строке (если есть)."""
        line = getattr(node, 'lineno', '?')
        raise SemanticError(f"[Line {line}] {msg}")

    def push_scope(self):
        """Открыть новый локальный уровень видимости."""
        self.scopes.append({})

    def pop_scope(self):
        """Закрыть текущий локальный уровень."""
        self.scopes.pop()

    def declare(self, sym: Symbol):
        """
        Объявить новый символ в текущей области.
        Если scopes пуст, то в глобальной, иначе — в локальной таблице.
        """
        table = self.scopes[-1] if self.scopes else self.globals
        key = sym.name.lower()
        if key in table:
            self.error(sym, f"Повторное объявление '{sym.name}'")
        table[key] = sym

    def lookup(self, name):
        """
        Найти символ по имени, сначала в локальных, потом в глобальных.
        Возвращает None, если не найден.
        """
        key = name.lower()
        for tbl in reversed(self.scopes):
            if key in tbl:
                return tbl[key]
        return self.globals.get(key)

    def analyze(self, tree: Program):
        """
        Двухфазный проход по списку директив:
        1) Регистрируем все глобальные VarDecl/ConstDecl/MapDecl/ProcDecl.
        2) Проверяем семантику каждого узла через visit().
        """
        # ——— Фаза 1: объявление глобальных символов ———
        for d in tree.directives:
            if isinstance(d, VarDecl):
                # обычная переменная INT или BOOLEAN
                self.declare(Symbol(d.name, d.typ, is_const=False))
            elif isinstance(d, ConstDecl):
                # CINT → INT, CBOOLEAN → BOOLEAN
                base = 'INT' if d.typ == 'CINT' else 'BOOLEAN'
                self.declare(Symbol(d.name, base, is_const=True))
            elif isinstance(d, MapDecl):
                # карта — просто регистрируем как MAP
                self.declare(Symbol(d.name, 'MAP'))
            elif isinstance(d, ProcDecl):
                # процедуры храним отдельно, не идёт проверка дубликатов здесь
                self.globals[d.name.lower()] = ProcSymbol(d.name, d.params, d.body)

        # ——— Фаза 2: семантика ———
        for d in tree.directives:
            self.visit(d)

    def visit(self, node):
        """Диспетчер: ищем метод вида visit_<ClassName>."""
        fn = getattr(self, 'visit_' + node.__class__.__name__, self.generic_visit)
        return fn(node)

    def generic_visit(self, node):
        """Обход всех полей-узлов по умолчанию."""
        for fld in getattr(node, '__dict__', {}).values():
            if isinstance(fld, list):
                for el in fld:
                    if hasattr(el, '__class__'):
                        self.visit(el)
            elif hasattr(fld, '__class__'):
                self.visit(fld)

    # ——— Обработчики деклараций ———

    def visit_VarDecl(self, node: VarDecl):
        """
        Объявление переменной внутри процедуры/блока.
        Для глобального уровня регистрация уже сделана в первый проход.
        """
        if self.scopes:
            # регистрируем локальную переменную
            self.declare(Symbol(node.name, node.typ, is_const=False))
        # проверяем, что начальное выражение совпадает по типу
        t = self.visit(node.expr)
        if t != node.typ:
            self.error(node, f"Нельзя присвоить {t} в переменную типа {node.typ}")

    def visit_ConstDecl(self, node: ConstDecl):
        """
        Объявление константы внутри процедуры/блока.
        Для глобального уровня регистрация уже сделана.
        """
        if self.scopes:
            base = 'INT' if node.typ == 'CINT' else 'BOOLEAN'
            self.declare(Symbol(node.name, base, is_const=True))
        # проверяем тип константы
        t = self.visit(node.expr)
        base = 'INT' if node.typ == 'CINT' else 'BOOLEAN'
        if t != base:
            self.error(node, f"Нельзя присвоить {t} в константу типа {base}")

    def visit_MapDecl(self, node: MapDecl):
        """
        Объявление карты. Единственное, что нужно — уже зарегистрировать имя.
        Проверка размеров не нужна, т.к. лабиринт грузится из файла.
        """
        # ничего дополнительно не проверяем
        return None

    def visit_ProcDecl(self, node: ProcDecl):
        """
        Семантика объявления процедуры:
        1) Открываем новый локальный scope.
        2) Объявляем все параметры как INT.
        3) Обходим тело (Block).
        4) Закрываем scope.
        """
        self.push_scope()
        for param_name in node.params:
            self.declare(Symbol(param_name, 'INT', is_const=False))
        # тело процедуры — это Block
        self.visit_Block(node.body)
        self.pop_scope()

    # ——— Обработчики операторов ———

    def visit_Assign(self, node: Assign):
        sym = self.lookup(node.name)
        if not sym:
            self.error(node, f"Переменная {node.name} не объявлена")
        if sym.is_const:
            self.error(node, f"Нельзя переназначать константу {node.name}")
        t = self.visit(node.expr)
        if t != sym.typ:
            self.error(node, f"Нельзя присвоить {t} в {sym.typ} {node.name}")

    def visit_IncDec(self, node: IncDec):
        # INC/DEC нацелены только на INT-переменные
        if isinstance(node.target, VarRef):
            sym = self.lookup(node.target.name)
            if sym and sym.is_const:
                self.error(node, f"Нельзя INC/DEC константу {sym.name}")
        t_val = self.visit(node.value)
        t_tgt = self.visit(node.target)
        if t_val != 'INT' or t_tgt != 'INT':
            self.error(node, "INC/DEC только для INT")

    def visit_IfStmt(self, node: IfStmt):
        cond_t = self.visit(node.cond)
        if cond_t != 'BOOLEAN':
            self.error(node, "Условие IF должно быть BOOLEAN")
        self.visit(node.then_block)
        if node.else_block:
            self.visit(node.else_block)

    def visit_WhileStmt(self, node: WhileStmt):
        cond_t = self.visit(node.cond)
        if cond_t != 'BOOLEAN':
            self.error(node, "Условие WHILE должно быть BOOLEAN")
        self.visit(node.block)

    def visit_Block(self, node: Block):
        """
        Новый блок: открываем scope, обходим всё внутри, закрываем.
        """
        self.push_scope()
        self.generic_visit(node)
        self.pop_scope()

    def visit_ProcCall(self, node: ProcCall):
        """
        Вызов процедуры foo(a1, a2, ...).
        1) Проверяем, что процедура объявлена.
        2) Число аргументов совпадает.
        3) Все аргументыалистываем (их типы).
        4) По соглашению — возвращаем INT (результат через второй параметр).
        """
        ps = self.lookup(node.name)
        if not isinstance(ps, ProcSymbol):
            self.error(node, f"Процедура {node.name} не найдена")
        if len(node.args) != len(ps.params):
            self.error(node, f"Неверное число аргументов в {node.name}")
        for arg in node.args:
            self.visit(arg)
        # по договорённости все процедуры "возвращают" INT через второй параметр
        return 'INT'

    def visit_RobotOp(self, node: RobotOp):
        # LOOK возвращает INT (расстояние), остальные — BOOLEAN (успешность)
        return 'INT' if node.op == 'LOOK' else 'BOOLEAN'

    def visit_MapOp(self, node: MapOp):
        # res_var должен быть BOOLEAN
        sym = self.lookup(node.res_var)
        if not sym or sym.typ != 'BOOLEAN':
            self.error(node, f"Переменная {node.res_var} должна быть BOOLEAN для {node.op}")
        # координаты — INT
        tx = self.visit(node.x)
        ty = self.visit(node.y)
        if tx != 'INT' or ty != 'INT':
            self.error(node, "Координаты MAP_OP должны быть INT")
        # MapOp возвращает BOOLEAN
        return 'BOOLEAN'

    # ——— Обработчики выражений ———

    def visit_BinaryOp(self, node: BinaryOp):
        l = self.visit(node.left)
        r = self.visit(node.right)
        if node.op in ('+', '-'):
            if l != 'INT' or r != 'INT':
                self.error(node, f"{node.op} ожидает INT, получили {l},{r}")
            return 'INT'
        if node.op in ('GT', 'LT'):
            if l != 'INT' or r != 'INT':
                self.error(node, f"{node.op} ожидает INT, получили {l},{r}")
            return 'BOOLEAN'
        if node.op == 'EQ':
            if l != r:
                self.error(node, f"EQ ожидает совпадающие типы, получили {l},{r}")
            return 'BOOLEAN'
        if node.op == 'OR':
            if l != 'BOOLEAN' or r != 'BOOLEAN':
                self.error(node, f"OR ожидает BOOLEAN, получили {l},{r}")
            return 'BOOLEAN'
        self.error(node, f"Неизвестный бинарный оператор {node.op}")

    def visit_UnaryOp(self, node: UnaryOp):
        if node.op == 'NOT':
            t = self.visit(node.operand)
            if t != 'BOOLEAN':
                self.error(node, "NOT ожидает BOOLEAN")
            return 'BOOLEAN'
        self.error(node, f"Неизвестный унарный оператор {node.op}")

    def visit_IntLiteral(self, node: IntLiteral):
        return 'INT'

    def visit_BoolLiteral(self, node: BoolLiteral):
        return 'BOOLEAN'

    def visit_VarRef(self, node: VarRef):
        sym = self.lookup(node.name)
        if not sym:
            self.error(node, f"Переменная {node.name} не объявлена")
        if isinstance(sym, ProcSymbol):
            self.error(node, f"Имя процедуры {node.name} используется как переменная")
        return sym.typ

    def visit_PrintStmt(self, node: PrintStmt):
        if node.expr is not None:
            self.visit(node.expr)

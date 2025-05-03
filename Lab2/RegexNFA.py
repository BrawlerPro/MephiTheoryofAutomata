from RegexNode import RegexOp, RegexNode
from typing import Dict, Tuple
import graphviz
from collections import deque


# Класс состояния автомата
class State:
    _id_counter = 0  # Глобальный счётчик состояний для уникальных имён

    def __init__(self, is_end=False):
        self.name = f"S{State._id_counter}"
        State._id_counter += 1

        self.transitions: Dict[str, list[State]] = {}  # Переходы по символам
        self.epsilon: list[State] = []                # Epsilon-переходы
        self.is_end = is_end                          # Является ли состояние финальным

    def add_transition(self, symbol, state):
        if symbol == 'ε':
            self.epsilon.append(state)
        else:
            self.transitions.setdefault(symbol, []).append(state)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


# Представление НКА с указанием начального и конечного состояния
class NFA:
    def __init__(self, start: State, end: State):
        self.start = start
        self.end = end
        self.end.is_end = True  # Обозначаем конец автомата


# Вставка подавтомата для ссылки на ранее захваченную именованную группу
def insert_named_ref_nfa(name: str, next_state: 'State') -> Tuple['State', 'State']:
    start = State()
    end = State()
    start.add_transition(f"<ref:{name}>", end)
    end.add_transition('ε', next_state)
    return start, next_state


# Конструктор НКА из синтаксического дерева регулярного выражения
class NFAConstructor:
    def __init__(self):
        self.named_groups = {}  # Словарь с сохранёнными именованными группами

    def build(self, node: RegexNode) -> NFA:
        match node.op:
            case RegexOp.CHAR:
                # Один символ
                start = State()
                end = State()
                start.add_transition(node.value, end)
                return NFA(start, end)

            case RegexOp.CONCAT:
                # Конкатенация (последовательность)
                assert node.children
                first = self.build(node.children[0])
                current_start, current_end = first.start, first.end
                for child in node.children[1:]:
                    next_nfa = self.build(child)
                    current_end.add_transition('ε', next_nfa.start)
                    current_end.is_end = False
                    current_end = next_nfa.end
                return NFA(current_start, current_end)

            case RegexOp.ALT:
                # Альтернатива (|) — объединение путей
                start, end = State(), State()
                for child in node.children:
                    alt_nfa = self.build(child)
                    start.add_transition('ε', alt_nfa.start)
                    alt_nfa.end.add_transition('ε', end)
                    alt_nfa.end.is_end = False
                return NFA(start, end)

            case RegexOp.KLEENE:
                # Замыкание Клини (*)
                inner = self.build(node.children[0])
                start, end = State(), State()
                start.add_transition('ε', inner.start)
                start.add_transition('ε', end)
                inner.end.add_transition('ε', inner.start)
                inner.end.add_transition('ε', end)
                inner.end.is_end = False
                return NFA(start, end)

            case RegexOp.OPTIONAL:
                # Опциональность (?)
                inner = self.build(node.children[0])
                start, end = State(), State()
                start.add_transition('ε', inner.start)
                start.add_transition('ε', end)
                inner.end.add_transition('ε', end)
                inner.end.is_end = False
                return NFA(start, end)

            case RegexOp.REPEAT:
                # Повторение N раз
                count = node.value
                if count == 0:
                    s, e = State(), State()
                    s.add_transition('ε', e)
                    return NFA(s, e)

                base_nfa = self.build(node.children[0])
                current_start, current_end = base_nfa.start, base_nfa.end

                for _ in range(1, count):
                    next_nfa = self.build(node.children[0])
                    current_end.add_transition('ε', next_nfa.start)
                    current_end.is_end = False
                    current_end = next_nfa.end

                return NFA(current_start, current_end)

            case RegexOp.NAMED_GROUP:
                # Именованная группа
                inner = self.build(node.children[0])
                self.named_groups[node.name] = inner

                start = State()
                end = State()
                start.add_transition(f"<start:{node.name}>", inner.start)
                inner.end.add_transition(f"<end:{node.name}>", end)
                inner.end.is_end = False

                return NFA(start, end)

            case RegexOp.NAMED_REF:
                # Ссылка на ранее определённую группу
                if node.name not in self.named_groups:
                    raise ValueError(f"Undefined group reference: {node.name}")

                target = State()
                target.is_end = True
                start, end = insert_named_ref_nfa(node.name, target)
                return NFA(start, target)

            case _:
                raise ValueError(f"Unknown operation: {node.op}")


# Визуализация автомата через graphviz
def draw_nfa(nfa: NFA, filename="nfa"):
    dot = graphviz.Digraph(format="png")
    visited = set()
    dot.node("start", shape="none", label="")
    dot.edge("start", nfa.start.name)

    def visit(state):
        if state in visited:
            return
        visited.add(state)
        shape = "doublecircle" if state.is_end else "circle"
        dot.node(str(state), str(state), shape=shape)
        for sym, targets in state.transitions.items():
            for t in targets:
                dot.edge(str(state), str(t), label=sym)
                visit(t)
        for t in state.epsilon:
            dot.edge(str(state), str(t), label="ε")
            visit(t)

    visit(nfa.start)
    dot.render(filename, view=False)


# Симуляция выполнения НКА с поддержкой захвата и сравнения именованных групп
def match_nfa(nfa: NFA, input_str: str) -> bool:
    queue = deque()
    visited = set()
    queue.append((nfa.start, 0, {}, {}))  # состояние, позиция, захваты, стартовые позиции групп

    while queue:
        state, pos, captures, group_starts = queue.popleft()

        key = (state.name, pos, tuple(sorted(captures.items())), tuple(sorted(group_starts.items())))
        if key in visited:
            continue
        visited.add(key)

        if state.is_end and pos == len(input_str):
            return True

        # Epsilon-переходы
        for next_state in state.epsilon:
            queue.append((next_state, pos, captures.copy(), group_starts.copy()))

        # Обычные переходы
        for symbol, next_states in state.transitions.items():
            for next_state in next_states:
                if symbol.startswith("<start:") and symbol.endswith(">"):
                    group_name = symbol[7:-1]
                    new_group_starts = group_starts.copy()
                    new_group_starts[group_name] = pos
                    queue.append((next_state, pos, captures.copy(), new_group_starts))

                elif symbol.startswith("<end:") and symbol.endswith(">"):
                    group_name = symbol[5:-1]
                    if group_name not in group_starts:
                        continue
                    start_pos = group_starts[group_name]
                    captured = input_str[start_pos:pos]
                    new_captures = captures.copy()
                    new_captures[group_name] = captured
                    queue.append((next_state, pos, new_captures, group_starts.copy()))

                elif symbol.startswith("<ref:") and symbol.endswith(">"):
                    group_name = symbol[5:-1]
                    if group_name not in captures:
                        continue
                    val = captures[group_name]
                    if input_str.startswith(val, pos):
                        queue.append((next_state, pos + len(val), captures.copy(), group_starts.copy()))

                elif pos < len(input_str) and input_str[pos] == symbol:
                    queue.append((next_state, pos + 1, captures.copy(), group_starts.copy()))

    return False

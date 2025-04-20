from RegexNode import RegexOp, RegexNode
from typing import Dict
import graphviz


class State:
    _id_counter = 0

    def __init__(self, is_end=False):
        self.name = f"S{State._id_counter}"
        State._id_counter += 1

        self.transitions: Dict[str, list[State]] = {}
        self.epsilon: list[State] = []
        self.is_end = is_end

    def add_transition(self, symbol, state):
        if symbol == 'ε':
            self.epsilon.append(state)
        else:
            self.transitions.setdefault(symbol, []).append(state)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class NFA:
    def __init__(self, start: State, end: State):
        self.start = start
        self.end = end
        self.end.is_end = True


def clone_nfa(nfa):
    state_map = {}

    # Шаг 1: сохранить оригинальные конечные состояния
    old_ends = set()
    visited = set()

    def mark_ends(state):
        if state in visited:
            return
        visited.add(state)
        if state.is_end:
            old_ends.add(state)
        for targets in state.transitions.values():
            for t in targets:
                mark_ends(t)
        for e in state.epsilon:
            mark_ends(e)

    mark_ends(nfa.start)

    # Шаг 2: клонируем состояния
    def clone_state(state):
        if state in state_map:
            return state_map[state]
        new_state = State()
        state_map[state] = new_state
        for sym, targets in state.transitions.items():
            for t in targets:
                new_state.add_transition(sym, clone_state(t))
        for t in state.epsilon:
            new_state.add_transition('ε', clone_state(t))
        return new_state

    new_start = clone_state(nfa.start)
    new_end = State()
    new_end.is_end = True

    # Шаг 3: проставляем ε-переходы к единому финальному состоянию
    for old, new in state_map.items():
        if old in old_ends:
            new.add_transition('ε', new_end)

    return NFA(new_start, new_end)


class NFAConstructor:
    def __init__(self):
        self.named_groups = {}

    def build(self, node: RegexNode) -> NFA:
        match node.op:
            case RegexOp.CHAR:
                start = State()
                end = State()
                start.add_transition(node.value, end)
                # print(f"{node.op.name}: {start} --{node.value}--> {end}")
                return NFA(start, end)

            case RegexOp.CONCAT:
                assert node.children, "Empty CONCAT"
                first = self.build(node.children[0])
                current_start = first.start
                current_end = first.end

                for child in node.children[1:]:
                    next_nfa = self.build(child)
                    current_end.add_transition('ε', next_nfa.start)
                    current_end.is_end = False
                    current_end = next_nfa.end

                return NFA(current_start, current_end)

            case RegexOp.ALT:
                start = State()
                end = State()
                for child in node.children:
                    branch = self.build(child)
                    start.add_transition('ε', branch.start)
                    # print(f"{node.op.name}: {start} --ε--> {branch.start}")
                    branch.end.add_transition('ε', end)
                    branch.end.is_end = False
                return NFA(start, end)

            case RegexOp.KLEENE:
                inner = self.build(node.children[0])
                start = State()
                end = State()
                start.add_transition('ε', inner.start)
                start.add_transition('ε', end)
                inner.end.add_transition('ε', inner.start)
                inner.end.add_transition('ε', end)
                inner.end.is_end = False
                return NFA(start, end)

            case RegexOp.OPTIONAL:
                inner = self.build(node.children[0])
                start = State()
                end = State()
                start.add_transition('ε', inner.start)
                # print(f"{node.op.name}: {start} --ε--> {inner.start}")
                start.add_transition('ε', end)
                inner.end.add_transition('ε', end)
                inner.end.is_end = False
                return NFA(start, end)

            case RegexOp.REPEAT:
                count = node.value
                assert count >= 0
                if count == 0:
                    s = State()
                    e = State()
                    s.add_transition('ε', e)
                    return NFA(s, e)

                base_nfa = self.build(node.children[0])
                current_start = base_nfa.start
                current_end = base_nfa.end

                for _ in range(1, count):
                    next_nfa = self.build(node.children[0])
                    current_end.add_transition('ε', next_nfa.start)
                    current_end.is_end = False
                    current_end = next_nfa.end

                return NFA(current_start, current_end)

            case RegexOp.NAMED_GROUP:
                inner = self.build(node.children[0])
                self.named_groups[node.name] = inner
                return inner

            case RegexOp.NAMED_REF:
                if node.name not in self.named_groups:
                    raise ValueError(f"Undefined group reference: {node.name}")
                return clone_nfa(self.named_groups[node.name])

            case _:
                raise ValueError(f"Unknown operation: {node.op}")


def draw_nfa(nfa: NFA, filename="nfa"):
    dot = graphviz.Digraph(format="png")
    visited = set()

    # Начальная стрелка
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

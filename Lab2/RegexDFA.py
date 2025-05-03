from collections import deque

import graphviz


class DFAState:
    """
    Класс, представляющий состояние детерминированного конечного автомата (ДКА).
    Содержит:
    - name: имя состояния (уникальное, например, "q0", "q1" и т.д.)
    - nfa_states: множество состояний NFA, объединённых в это состояние DFA
    - transitions: словарь {символ: целевое состояние DFA}
    - is_end: флаг, указывающий, является ли состояние завершающим
    - groups: дополнительные данные для поддержки захватов (опционально)
    """

    def __init__(self, name, nfa_states):
        self.name = name
        self.nfa_states = nfa_states
        self.transitions = {}
        self.is_end = any(state.is_end for state in nfa_states)
        self.groups = {}


class DFA:
    """
    Класс DFA — детерминированного конечного автомата.
    Содержит:
    - start: стартовое состояние
    - states: список всех состояний автомата
    """

    def __init__(self):
        self.start = None
        self.states = []

    @property
    def finals(self):
        return {s for s in self.states if s.is_end}


def epsilon_closure(states):
    """Вычисляет ε-замыкание: все состояния, достижимые по ε-переходам."""
    stack = list(states)
    closure = set(states)
    while stack:
        state = stack.pop()
        for next_state in state.epsilon:
            if next_state not in closure:
                closure.add(next_state)
                stack.append(next_state)
    return closure


def move(states, symbol):
    """Выполняет переход по символу symbol для всех NFA состояний."""
    result = set()
    for state in states:
        if symbol in state.transitions:
            result.update(state.transitions[symbol])
    return result


def nfa_to_dfa(nfa):
    """
    Алгоритм преобразования NFA в DFA по методу подмножеств (subset construction).
    Для каждого множества состояний NFA создаётся уникальное состояние DFA.
    """
    dfa = DFA()
    state_map = {}
    queue = deque()

    start_nfa_states = epsilon_closure({nfa.start})
    start_frozen = frozenset(start_nfa_states)
    start_dfa = DFAState(name="q0", nfa_states=start_frozen)

    dfa.start = start_dfa
    dfa.states.append(start_dfa)
    state_map[start_frozen] = start_dfa
    queue.append(start_dfa)
    state_counter = 1

    while queue:
        current = queue.popleft()
        symbols = set()
        for s in current.nfa_states:
            symbols.update(s.transitions.keys())

        for symbol in symbols:
            moved = move(current.nfa_states, symbol)
            closure = epsilon_closure(moved)
            closure_frozen = frozenset(closure)

            if closure_frozen not in state_map:
                new_state = DFAState(f"q{state_counter}", closure_frozen)
                state_counter += 1
                state_map[closure_frozen] = new_state
                dfa.states.append(new_state)
                queue.append(new_state)

            current.transitions[symbol] = state_map[closure_frozen]

    return dfa


def minimize_dfa(dfa):
    """
    Алгоритм минимизации DFA по Хопкрофту.
    Разделяет состояния на классы эквивалентности, объединяет эквивалентные состояния.
    """
    alphabet = set()
    for state in dfa.states:
        alphabet.update(state.transitions.keys())

    final_states = {s for s in dfa.states if s.is_end}
    non_final_states = set(dfa.states) - final_states
    partitions = [final_states, non_final_states] if non_final_states else [final_states]
    state_to_partition = {s: i for i, group in enumerate(partitions) for s in group}

    changed = True
    while changed:
        changed = False
        new_partitions = []
        for group in partitions:
            splits = {}
            for state in group:
                sig = tuple(state_to_partition.get(state.transitions.get(sym), -1) for sym in sorted(alphabet))
                splits.setdefault(sig, set()).add(state)
            if len(splits) > 1:
                changed = True
            new_partitions.extend(splits.values())
        partitions = new_partitions
        state_to_partition = {s: i for i, group in enumerate(partitions) for s in group}

    group_to_state = {}
    min_dfa = DFA()
    for i, group in enumerate(partitions):
        rep = next(iter(group))
        new_state = DFAState(f"mq{i}", rep.nfa_states)
        new_state.is_end = rep.is_end
        group_to_state[i] = new_state
        min_dfa.states.append(new_state)

    for i, group in enumerate(partitions):
        rep = next(iter(group))
        current = group_to_state[i]
        for symbol, target in rep.transitions.items():
            tgt_partition = state_to_partition.get(target)
            if tgt_partition is not None:
                current.transitions[symbol] = group_to_state[tgt_partition]

    start_partition = state_to_partition[dfa.start]
    min_dfa.start = group_to_state[start_partition]

    return min_dfa


def match_dfa(dfa, string):
    """Проверка, принимает ли DFA строку целиком."""
    current = dfa.start
    for c in string:
        if c not in current.transitions:
            return False
        current = current.transitions[c]
    return current.is_end


def match_min_dfa(min_dfa, string):
    """Аналогично match_dfa, но для минимизированного DFA."""
    return match_dfa(min_dfa, string)


def make_dfa_total(dfa):
    """
    Делает DFA полным, добавляя ловушечное (trap) состояние,
    в которое ведут отсутствующие переходы.
    """
    alphabet = set()
    for state in dfa.states:
        alphabet.update(state.transitions.keys())

    trap_state = DFAState(name="TRAP", nfa_states=frozenset())
    trap_state.is_end = False
    for symbol in alphabet:
        trap_state.transitions[symbol] = trap_state

    for state in dfa.states:
        for symbol in alphabet:
            if symbol not in state.transitions:
                state.transitions[symbol] = trap_state

    if all(s.name != trap_state.name for s in dfa.states):
        dfa.states.append(trap_state)

    return dfa


def complement_dfa(dfa):
    """
    Возвращает дополнение языка DFA (всё, что не принимается исходным DFA).
    Предварительно делает DFA полным.
    """
    dfa = make_dfa_total(dfa)
    for state in dfa.states:
        state.is_end = not state.is_end
    return dfa


def intersect_dfa(dfa1, dfa2):
    """
    Пересечение двух DFA через построение автомата-декартова произведения состояний.
    Принимающее состояние — только если оба состояния-пересечения являются принимающими.
    """

    def get_alphabet(dfa):
        alphab = set()
        for state in dfa.states:
            alphab.update(state.transitions.keys())
        return alphab

    alphabet = get_alphabet(dfa1) & get_alphabet(dfa2)
    visited = {}
    queue = deque()

    def make_key(sq1, sq2):
        return sq1.name, sq2.name

    start_key = make_key(dfa1.start, dfa2.start)
    start_state = DFAState(name=str(start_key), nfa_states=frozenset())
    start_state.is_end = dfa1.start.is_end and dfa2.start.is_end

    visited[start_key] = start_state
    queue.append((dfa1.start, dfa2.start))

    new_dfa = DFA()
    new_dfa.start = start_state
    new_dfa.states.append(start_state)

    while queue:
        s1, s2 = queue.popleft()
        key = make_key(s1, s2)
        current = visited[key]
        for symbol in alphabet:
            t1 = s1.transitions.get(symbol)
            t2 = s2.transitions.get(symbol)
            if t1 and t2:
                next_key = make_key(t1, t2)
                if next_key not in visited:
                    new_state = DFAState(name=str(next_key), nfa_states=frozenset())
                    new_state.is_end = t1.is_end and t2.is_end
                    visited[next_key] = new_state
                    queue.append((t1, t2))
                    new_dfa.states.append(new_state)
                current.transitions[symbol] = visited[next_key]

    return new_dfa


def dfa_to_regex(dfa):
    """
    Метод K-пути (алгоритм Брзо́вского — алгоритм Клина) для преобразования DFA в регулярное выражение.
    Создаёт матрицу R[k][i][j] — выражение от состояния i к j с промежуточными ≤ k.
    """
    state_list = list(dfa.states)
    state_ids = {state: i for i, state in enumerate(state_list)}
    n = len(state_list)
    R = [[["∅" for _ in range(n)] for _ in range(n)] for _ in range(n + 1)]

    for i, state in enumerate(state_list):
        for symbol, next_state in state.transitions.items():
            j = state_ids[next_state]
            R[0][i][j] = symbol if R[0][i][j] == "∅" else f"{R[0][i][j]}|{symbol}"
        if R[0][i][i] == "∅":
            R[0][i][i] = "ε"

    for k in range(1, n + 1):
        for i in range(n):
            for j in range(n):
                rik, rkk, rkj = R[k - 1][i][k - 1], R[k - 1][k - 1][k - 1], R[k - 1][k - 1][j]
                rij = R[k - 1][i][j]
                part1 = f"{rik}({rkk})…{rkj}" if rik != "∅" and rkj != "∅" else "∅"
                R[k][i][j] = part1 if rij == "∅" else (rij if part1 == "∅" else f"{rij}|{part1}")

    start = state_ids[dfa.start]
    finals = [state_ids[s] for s in dfa.states if s.is_end]
    expressions = [R[n][start][f] for f in finals if R[n][start][f] != "∅"]
    return "∅" if not expressions else (expressions[0] if len(expressions) == 1 else "|".join(expressions))


def search_dfa(dfa: DFA, text: str) -> bool:
    """Ищет неполное совпадение: возвращает True, если подстрока текста распознаётся DFA."""
    for i in range(len(text)):
        current = dfa.start
        for j in range(i, len(text)):
            c = text[j]
            if c not in current.transitions:
                break
            current = current.transitions[c]
            if current.is_end:
                return True
    return False


def draw_dfa(dfa, filename="dfa"):
    """Строит PNG-график DFA с помощью Graphviz."""
    dot = graphviz.Digraph()
    dot.attr(rankdir="LR")
    dot.node("start", shape="none", label="")
    dot.edge("start", dfa.start.name)

    for state in dfa.states:
        shape = "doublecircle" if state.is_end else "circle"
        dot.node(state.name, shape=shape)

    for state in dfa.states:
        symbols_map = {}
        for symbol, target in state.transitions.items():
            symbols_map.setdefault(target.name, []).append(symbol)

        for target_name, symbols in symbols_map.items():
            label = ",".join(sorted(symbols))
            dot.edge(state.name, target_name, label=label)

    dot.render(filename, format='png')

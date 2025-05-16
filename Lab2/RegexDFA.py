from collections import deque
import graphviz


class MatchResult:
    def __init__(self, start, end, full_match, groups):
        self.start = start  # Начальная позиция совпадения
        self.end = end  # Конечная позиция совпадения
        self.full_match = full_match  # Совпавшая подстрока
        self.groups = groups  # Словарь именованных групп

    def __getitem__(self, key):
        return self.groups.get(key, None)  # Позволяет доступ к группам по имени через []

    def __iter__(self):
        return iter(self.groups.items())  # Позволяет итерироваться по группам

    def __str__(self):
        return f"Result(start: {self.start}, end: {self.end}, fill_match: {self.full_match}, groups: {self.groups})"


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


# Класс для ДКА
class DFA:
    """
    Класс DFA — детерминированного конечного автомата.
    Содержит:
    - start: стартовое состояние
    - states: список всех состояний автомата
    - finals: множество завершающих состояний
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
    return result  # Возвращаем множество целевых состояний


def nfa_to_dfa(nfa):
    """
    Алгоритм преобразования NFA в DFA по методу подмножеств (subset construction).
    Для каждого множества состояний NFA создаётся уникальное состояние DFA.
    """
    dfa = DFA()  # Создаем новый ДКА
    state_map = {}  # Словарь для отображения множества состояний NFA в состояние DFA
    queue = deque()  # Очередь для обработки состояний

    start_nfa_states = epsilon_closure({nfa.start})
    start_frozen = frozenset(start_nfa_states)
    start_dfa = DFAState(name="q0", nfa_states=start_frozen)  # Создаем стартовое состояние DFA

    dfa.start = start_dfa
    dfa.states.append(start_dfa)
    state_map[start_frozen] = start_dfa
    queue.append(start_dfa)
    state_counter = 1

    while queue:
        current = queue.popleft()
        symbols = set()
        for s in current.nfa_states:  # Для каждого состояния из множества состояний NFA
            symbols.update(s.transitions.keys())  # Собираем все возможные символы переходов

        for symbol in symbols:
            moved = move(current.nfa_states, symbol)
            closure = epsilon_closure(moved)
            closure_frozen = frozenset(closure)

            if closure_frozen not in state_map:  # Если такого состояния ещё нет
                new_state = DFAState(f"q{state_counter}", closure_frozen)
                state_counter += 1
                state_map[closure_frozen] = new_state
                dfa.states.append(new_state)
                queue.append(new_state)

            current.transitions[symbol] = state_map[closure_frozen]  # Добавляем переход в DFA

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
    partitions = [final_states, non_final_states] if non_final_states else [
        final_states]
    state_to_partition = {s: i for i, group in enumerate(partitions) for s in
                          group}

    changed = True
    while changed:
        changed = False  # Сбрасываем флаг изменения
        new_partitions = []
        for group in partitions:
            splits = {}  # Словарь для разделённых групп
            for state in group:
                sig = tuple(state_to_partition.get(state.transitions.get(sym), -1) for sym in
                            sorted(alphabet))  # Ключ для разделения
                splits.setdefault(sig, set()).add(state)  # Разделяем состояния по ключу
            if len(splits) > 1:
                changed = True  # Если разделили на больше чем одну группу, устанавливаем флаг изменения
            new_partitions.extend(splits.values())
        partitions = new_partitions
        state_to_partition = {s: i for i, group in enumerate(partitions) for s in
                              group}

    group_to_state = {}
    min_dfa = DFA()
    for i, group in enumerate(partitions):
        rep = next(iter(group))  # Представитель группы
        new_state = DFAState(f"mq{i}", rep.nfa_states)  # Создаём новое состояние для группы
        new_state.is_end = rep.is_end  # Устанавливаем флаг окончания для нового состояния
        group_to_state[i] = new_state
        min_dfa.states.append(new_state)

    # Применяем переходы для минимизированного DFA
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


def make_dfa_total(dfa, alphabet=None):
    """
    Делает DFA полным, добавляя ловушечное состояние для всех отсутствующих переходов.
    """
    if alphabet is None:
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
    Возвращает дополнение DFA. Всё, что не принимается исходным DFA.
    """
    # Можно расширить алфавит вручную — например, a-z
    alphabet = set(chr(c) for c in range(32, 127))  # Печатаемые ASCII символы
    dfa = make_dfa_total(dfa, alphabet)
    for state in dfa.states:
        state.is_end = not state.is_end
    return dfa


def intersect_dfa(dfa1, dfa2):
    """
    Пересечение двух DFA через построение автомата-декартова произведения состояний.
    Принимающее состояние — только если оба состояния-пересечения являются принимающими.
    """

    # Получаем алфавит для каждого DFA
    def get_alphabet(dfa):
        alphas = set()  # Множество символов
        for state in dfa.states:
            alphas.update(state.transitions.keys())  # Собираем символы переходов
        return alphas

    alphabet = get_alphabet(dfa1) & get_alphabet(dfa2)  # Пересекаем алфавиты двух DFA
    visited = {}
    queue = deque()  # Очередь для обработки состояний

    def make_key(sq1, sq2):
        return sq1.name, sq2.name  # Создаем уникальный ключ для пары состояний

    start_key = make_key(dfa1.start, dfa2.start)  # Создаем ключ для стартовых состояний
    start_state = DFAState(name=str(start_key), nfa_states=frozenset())  # Создаём стартовое состояние для пересечения
    start_state.is_end = dfa1.start.is_end and dfa2.start.is_end  # Состояние пересечения — финальное, если оба
    # исходных финальны

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
                next_key = make_key(t1, t2)  # Создаём ключ для пары новых состояний
                if next_key not in visited:
                    new_state = DFAState(name=str(next_key), nfa_states=frozenset())
                    new_state.is_end = t1.is_end and t2.is_end
                    visited[next_key] = new_state
                    new_dfa.states.append(new_state)
                    queue.append((t1, t2))
                current.transitions[symbol] = visited[next_key]

    return new_dfa


def dfa_to_regex(dfa):
    def wrap_if_needed(expr):
        """Оборачивает выражение в скобки, если это нужно"""
        if '|' in expr or '…' in expr or '?' in expr:
            return f"({expr})"
        return expr

    def simplify(expr):
        """Упрощает регулярные выражения"""
        if expr == "∅":
            return None
        if expr == "ε":
            return ""
        return expr

    def clean_alt(parts):
        """Удаляет дубликаты и ∅ в объединениях"""
        parts = [p for p in parts if p not in (None, "∅")]
        return list(dict.fromkeys(parts))  # сохранить порядок и уникальность

    # Преобразуем DFA в список состояний с номерами
    state_list = list(dfa.states)
    state_ids = {state: i for i, state in enumerate(state_list)}
    n = len(state_list)

    # Инициализация r[0]
    r = [[["∅" for _ in range(n)] for _ in range(n)] for _ in range(n + 1)]
    for i, state in enumerate(state_list):
        for symbol, next_state in state.transitions.items():
            j = state_ids[next_state]
            symbol = f"%{symbol}%" if symbol in {'(', ')', '|', '?', '…', '{', '}', '<', '>'} else symbol
            r[0][i][j] = symbol if r[0][i][j] == "∅" else f"{r[0][i][j]}|{symbol}"
        if r[0][i][i] == "∅":
            r[0][i][i] = "ε"

    # Основной цикл Брзо́вского
    for k in range(1, n + 1):
        for i in range(n):
            for j in range(n):
                rij = simplify(r[k - 1][i][j])
                rik = simplify(r[k - 1][i][k - 1])
                rkk = simplify(r[k - 1][k - 1][k - 1])
                rkj = simplify(r[k - 1][k - 1][j])

                loop = f"{wrap_if_needed(rkk)}…" if rkk else None
                bridge = None
                if rik and rkj:
                    middle = loop if loop else ""
                    bridge = f"{wrap_if_needed(rik)}{middle}{wrap_if_needed(rkj)}"

                if rij and bridge:
                    r[k][i][j] = f"{rij}|{bridge}"
                elif rij:
                    r[k][i][j] = rij
                elif bridge:
                    r[k][i][j] = bridge
                else:
                    r[k][i][j] = "∅"

    # Формируем итоговое выражение
    start = state_ids[dfa.start]
    finals = [state_ids[s] for s in dfa.states if s.is_end]
    expressions = [simplify(r[n][start][f]) for f in finals]
    expressions = clean_alt(expressions)

    if not expressions:
        return "∅"
    if len(expressions) == 1:
        return expressions[0]
    return "|".join(f"{wrap_if_needed(e)}" for e in expressions if e)


# Функция для сопоставления строки с DFA
def match_dfa(dfa, string) -> MatchResult or None:
    """
    Проверяет, принимает ли минимизированный DFA строку полностью.
    Возвращает MatchResult, если полное совпадение; иначе None.
    """
    state = dfa.start
    for i, char in enumerate(string):
        if char in state.transitions:
            state = state.transitions[char]
        else:
            return None  # Недопустимый переход — не принадлежит языку

    if state.is_end:
        return MatchResult(0, len(string), string, {})  # Совпадение на всю строку
    return None


def match_min_dfa(min_dfa, string):
    return match_dfa(min_dfa, string)


def search_dfa(dfa, string: str):
    for start_pos in range(len(string)):
        sub_str = string[start_pos:]
        result = match_dfa(dfa, sub_str)
        if result:
            return MatchResult(start_pos, start_pos + result.end, result.full_match, result.groups)
    return None


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

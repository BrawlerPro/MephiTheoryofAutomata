from collections import deque  # Для очереди в алгоритме построения DFA
import graphviz  # Для визуализации DFA


class DFAState:
    def __init__(self, name, nfa_states):
        self.name = name
        self.nfa_states = nfa_states  # frozenset: множество NFA-состояний, которые оно представляет
        self.transitions = {}
        self.is_end = any(state.is_end for state in nfa_states)


class DFA:
    def __init__(self):
        self.start = None  # Начальное состояние DFA
        self.states = []  # Список всех состояний DFA


def epsilon_closure(states):
    """
    Находит ε-замыкание: множество всех состояний, достижимых по ε-переходам из исходного множества.
    """
    stack = list(states)  # Используем стек для обхода в глубину
    closure = set(states)  # Начальное замыкание содержит сами состояния
    while stack:
        state = stack.pop()
        for next_state in state.epsilon:
            if next_state not in closure:  # Если ещё не посещали
                closure.add(next_state)
                stack.append(next_state)  # Добавляем в стек для дальнейшего обхода
    return closure  # Возвращаем ε-замыкание


def move(states, symbol):
    """
    Возвращает множество всех состояний, в которые можно попасть из заданных состояний по символу `symbol`.
    """
    result = set()
    for state in states:
        if symbol in state.transitions:  # Есть переход по символу
            result.update(state.transitions[symbol])  # Добавляем все возможные состояния
    return result


def nfa_to_dfa(nfa):
    dfa = DFA()
    state_map = {}
    queue = deque()

    # Начальное состояние DFA — ε-замыкание начального состояния NFA
    start_nfa_states = epsilon_closure({nfa.start})
    start_frozen = frozenset(start_nfa_states)
    start_dfa = DFAState(name="q0", nfa_states=start_frozen)

    dfa.start = start_dfa
    dfa.states.append(start_dfa)
    state_map[start_frozen] = start_dfa
    queue.append(start_dfa)  # Добавляем в очередь на обработку

    state_counter = 1  # Счётчик имён состояний (q1, q2, ...)

    while queue:
        current = queue.popleft()  # Берём текущее состояние из очереди

        symbols = set()  # Собираем все возможные символы переходов
        for s in current.nfa_states:
            symbols.update(s.transitions.keys())

        for symbol in symbols:
            moved = move(current.nfa_states, symbol)  # Переход по символу
            closure = epsilon_closure(moved)  # Замыкаем результат ε-переходами
            closure_frozen = frozenset(closure)  # Делаем неизменяемым для использования как ключа

            if closure_frozen not in state_map:
                # Если это новое множество — создаём новое состояние DFA
                new_state = DFAState(f"q{state_counter}", closure_frozen)
                state_counter += 1
                state_map[closure_frozen] = new_state
                dfa.states.append(new_state)
                queue.append(new_state)

            # Устанавливаем переход из current по symbol в соответствующее состояние
            current.transitions[symbol] = state_map[closure_frozen]

    return dfa


def draw_dfa(dfa, filename="dfa"):
    dot = graphviz.Digraph()
    dot.attr(rankdir="LR")

    # Добавляем невидимую стартовую стрелку
    dot.node("start", shape="none", label="")
    dot.edge("start", dfa.start.name)

    # Рисуем все состояния DFA
    for state in dfa.states:
        shape = "doublecircle" if state.is_end else "circle"
        dot.node(state.name, shape=shape)

    # Добавляем переходы между состояниями
    for state in dfa.states:
        symbols_map = {}
        for symbol, target in state.transitions.items():
            if target.name not in symbols_map:
                symbols_map[target.name] = []
            symbols_map[target.name].append(symbol)

        for target_name, symbols in symbols_map.items():
            label = ",".join(sorted(symbols))
            dot.edge(state.name, target_name, label=label)

    # Рендерим граф
    dot.render(filename, format='png')

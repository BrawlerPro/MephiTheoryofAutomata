from RegexLexer import *
from RegexParser import *
from RegexNFA import *
from RegexDFA import *


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


class CompiledNFA:
    def __init__(self, pattern):
        self.pattern = pattern
        self.tokens = RegexLexer(pattern).lex()
        self.ast = RegexParser(self.tokens).parse()
        self.nfa = NFAConstructor().build(self.ast)

    def match(self, string):
        return match_nfa(self.nfa, string)

    def search(self, string):
        return search_nfa(self.nfa, string)

    def draw(self, name):
        draw_nfa(self.nfa, name)


class CompiledDFA:
    def __init__(self, pattern):
        self.pattern = pattern
        self.tokens = RegexLexer(pattern).lex()
        self.ast = RegexParser(self.tokens).parse()
        self.nfa = NFAConstructor().build(self.ast)
        self.dfa = nfa_to_dfa(self.nfa)
        self._min_dfa = None

    @property
    def min_dfa(self):
        if self._min_dfa is None:
            self._min_dfa = minimize_dfa(self.dfa)
        return self._min_dfa

    def match(self, string):
        return match_dfa(self.dfa, string)

    def search(self, string):
        return search_dfa(self.dfa, string)

    def to_regex(self):
        return dfa_to_regex(self.min_dfa)

    def complement_dfa(self):
        return complement_dfa(self.dfa)

    def intersect(self, other):
        return intersect_dfa(self.dfa, other.dfa)

    def draw(self, name):
        draw_dfa(self.dfa, name)


def compile_nfa(pattern: str) -> CompiledNFA:
    return CompiledNFA(pattern)


def compile_dfa(pattern: str) -> CompiledDFA:
    return CompiledDFA(pattern)

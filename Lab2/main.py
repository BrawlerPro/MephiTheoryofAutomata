import MyRegex
from RegexNFA import search_nfa
from RegexDFA import match_dfa, draw_dfa

# Пример строки
# regex = "01(0|1)…"
# regex = "b…"
# regex = "(<go>a)|c"
# regex = "gggla(a…|s)h"
regex = "a{3}"
# regex = "ab…c"
# regex = "(10)…0|1(01)…1"
print(f"regex = {regex}")

nfa = MyRegex.compile_nfa(regex)
dfa = MyRegex.compile_dfa(regex)

nfa.draw("nfa_example")
res = search_nfa(nfa.nfa, "aa")
if res:
    print("Найдено:", res.full_match, "на позиции", res.start)
dfa = MyRegex.compile_dfa("abc")
complement = dfa.complement_dfa()

for test in ["abc", "ab", "x", "def", "", "a"]:
    result = match_dfa(complement, test)
    print(f"Test: {test!r}, Match: {result.full_match if result else 'NO MATCH'}")

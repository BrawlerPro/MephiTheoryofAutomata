from RegexNFA import NFAConstructor, draw_nfa, match_nfa
from RegexParser import RegexParser
from RegexLexer import RegexLexer
from RegexDFA import nfa_to_dfa, draw_dfa, minimize_dfa, match_dfa, dfa_to_regex, intersect_dfa, complement_dfa



# Пример строки
# regex = "(<go>lll|kolaa)…<go>|a"
regex = "a…"
# regex = "(<name>((a|b)|s)…)<name>?|(sa){2}"
# regex = "gggla(a…|s)h"
# regex = "((a|c)|c)…"
# regex = "(a|b)…k…(so|la)…"
# regex = "(10)…0|1(01)…1"
print(f"regex = {regex}")

# Лексер и парсер
lexer = RegexLexer(regex)
tokens = lexer.lex()
print(tokens)
parser = RegexParser(tokens)
tree = parser.parse()
print(tree)

# Построение NFA
builder = NFAConstructor()
nfa = builder.build(tree)
draw_nfa(nfa, "nfa_example")

# DFA построен
dfa = nfa_to_dfa(nfa)
draw_dfa(dfa, "dfa_example")

# Минимизация DFA
min_dfa = minimize_dfa(dfa)
draw_dfa(min_dfa, "mdfa_example")
regex = dfa_to_regex(min_dfa)
print(f"regex = {regex}")

#
# dfa1 = nfa_to_dfa(builder.build(RegexParser(RegexLexer("a(b|c)…").lex()).parse()))
# dfa2 = nfa_to_dfa(builder.build(RegexParser(RegexLexer("(ab)…").lex()).parse()))
#
# dfa1 = minimize_dfa(dfa1)
# dfa2 = minimize_dfa(dfa2)
#
# dfa_inter = intersect_dfa(dfa1, dfa2)
# dfa_comp = complement_dfa(dfa1)
#
# draw_dfa(dfa_inter, "dfa_intersection")
# draw_dfa(dfa_comp, "dfa_complement")



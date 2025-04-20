from RegexNFA import NFAConstructor, draw_nfa
from RegexParser import RegexParser
from RegexLexer import RegexLexer
from RegexDFA import nfa_to_dfa, draw_dfa



# Пример строки
# regex = "(<go>lll|kolaa)…<go>|a"
# regex = "((a|b)…c){2}"
# regex = "(<name>((a|b)|s)…){3}<name>?|(sa){2}"
regex = "gggla(a…|s)h"
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

# Построение DFA
dfa = nfa_to_dfa(nfa)
draw_dfa(dfa, "dfa_example")


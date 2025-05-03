import unittest
from RegexLexer import RegexLexer
from RegexParser import RegexParser
from RegexNFA import NFAConstructor, match_nfa
from RegexDFA import (
    nfa_to_dfa, match_dfa, minimize_dfa,
    complement_dfa, intersect_dfa, dfa_to_regex
)


def compile_regex_to_dfa(regex):
    lexer = RegexLexer(regex)
    tokens = lexer.lex()
    parser = RegexParser(tokens)
    tree = parser.parse()
    nfa = NFAConstructor().build(tree)
    return minimize_dfa(nfa_to_dfa(nfa))


def compile_regex_to_nfa(regex):
    lexer = RegexLexer(regex)
    tokens = lexer.lex()
    parser = RegexParser(tokens)
    tree = parser.parse()
    return NFAConstructor().build(tree)


class TestRegexEngines(unittest.TestCase):

    def test_nfa_vs_dfa_equivalence(self):
        regex = "a(b|c)*d"
        nfa = compile_regex_to_nfa(regex)
        dfa = minimize_dfa(nfa_to_dfa(nfa))
        words = ["ad", "abcd", "abbd", "abccd"]
        wrong = ["", "a", "ab", "abdcb", "d"]
        for word in words:
            with self.subTest(word=word):
                self.assertTrue(match_nfa(nfa, word))
                self.assertTrue(match_dfa(dfa, word))
        for word in wrong:
            with self.subTest(word=word):
                self.assertFalse(match_nfa(nfa, word))
                self.assertFalse(match_dfa(dfa, word))

    def test_minimization_equivalence(self):
        regex = "(a|b)*a"
        dfa = nfa_to_dfa(compile_regex_to_nfa(regex))
        min_dfa = minimize_dfa(dfa)
        for word in ["a", "ba", "bba", "ababa"]:
            with self.subTest(word=word):
                self.assertEqual(match_dfa(dfa, word), match_dfa(min_dfa, word))
        for word in ["", "b", "bb", "abab"]:
            with self.subTest(word=word):
                self.assertEqual(match_dfa(dfa, word), match_dfa(min_dfa, word))

    def test_complement(self):
        regex = "a(b|c)*"
        dfa = compile_regex_to_dfa(regex)
        comp = complement_dfa(dfa)
        yes = ["", "b", "ba", "cb"]
        no = ["a", "ab", "acbcb"]
        for w in yes:
            with self.subTest(word=w):
                self.assertTrue(match_dfa(comp, w))
        for w in no:
            with self.subTest(word=w):
                self.assertFalse(match_dfa(comp, w))

    def test_intersection(self):
        dfa1 = compile_regex_to_dfa("(a|b)*")
        dfa2 = compile_regex_to_dfa("a*b*")
        inter = intersect_dfa(dfa1, dfa2)
        self.assertTrue(match_dfa(inter, "aaabbb"))
        self.assertTrue(match_dfa(inter, ""))
        self.assertFalse(match_dfa(inter, "abab"))
        self.assertFalse(match_dfa(inter, "baba"))

    def test_dfa_to_regex_equivalence(self):
        regex = "(a|b)*abb"
        dfa = compile_regex_to_dfa(regex)
        restored = dfa_to_regex(dfa)
        restored_dfa = compile_regex_to_dfa(restored)
        test_pos = ["abb", "aabb", "aaabb", "ababb"]
        test_neg = ["a", "ab", "aab", "ba"]
        for w in test_pos:
            with self.subTest(word=w):
                self.assertTrue(match_dfa(dfa, w))
                self.assertTrue(match_dfa(restored_dfa, w))
        for w in test_neg:
            with self.subTest(word=w):
                self.assertFalse(match_dfa(dfa, w))
                self.assertFalse(match_dfa(restored_dfa, w))

    def test_dfa_to_regex_minimized_equivalence(self):
        regex = "(a|b)*ab"
        dfa = compile_regex_to_dfa(regex)
        restored = dfa_to_regex(dfa)
        restored_dfa = compile_regex_to_dfa(restored)
        min1 = minimize_dfa(dfa)
        min2 = minimize_dfa(restored_dfa)
        # Сравним поведение на большом количестве строк
        alphabet = ['a', 'b']
        for word in generate_test_words(alphabet, 5):
            with self.subTest(word=word):
                self.assertEqual(match_dfa(min1, word), match_dfa(min2, word))


def generate_test_words(alphabet, max_length):
    """Генератор всех строк над алфавитом длиной до max_length."""
    from itertools import product
    for l in range(max_length + 1):
        for p in product(alphabet, repeat=l):
            yield ''.join(p)


if __name__ == '__main__':
    unittest.main()

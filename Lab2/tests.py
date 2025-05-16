import unittest
from MyRegex import compile_dfa, compile_nfa, match_dfa, draw_dfa
import random

# Возможные символы для регулярных выражений
characters = list("abcdefghijklmnopqrstuvwxyz")


def generate_random_regex(depth=3):
    if depth == 0:
        return random.choice(characters)
    operation = random.choice(["concat", "or", "kleene", "optional", "repeat"])
    if operation == "concat":
        return generate_random_regex(depth - 1) + generate_random_regex(depth - 1)
    elif operation == "or":
        return f"({generate_random_regex(depth - 1)}|{generate_random_regex(depth - 1)})"
    elif operation == "kleene":
        return f"{generate_random_regex(depth - 1)}…"
    elif operation == "optional":
        return f"{generate_random_regex(depth - 1)}?"
    elif operation == "repeat":
        return f"{generate_random_regex(depth - 1)}{{{random.randint(1, 3)}}}"
    return random.choice(characters)


class TestRandomRegex(unittest.TestCase):

    def test_generated_regex(self):
        random_regex = generate_random_regex(depth=3)
        print(f"Testing generated regex: {random_regex}")
        try:
            dfa = compile_dfa(random_regex)
            self.assertIsNotNone(dfa)
            result = dfa.match("")  # пустая строка, просто проверка на сбой
            # просто проверяем, что `.match` вызов не упал
        except Exception as e:
            self.fail(f"Regex {random_regex} failed to compile or match: {e}")

    def test_dfa_match(self):
        dfa = compile_dfa("a(b|c)")
        self.assertIsNotNone(dfa.match("ab"))
        self.assertIsNotNone(dfa.match("ac"))
        self.assertIsNone(dfa.match("abc"))

    def test_nfa_search(self):
        nfa = compile_nfa("ab")
        result = nfa.search("xxabyy")
        self.assertIsNotNone(result)
        self.assertEqual(result.full_match, "ab")
        self.assertEqual(result.start, 2)
        self.assertEqual(result.end, 4)

    def test_minimization(self):
        for _ in range(5):
            regex = generate_random_regex(3)
            dfa = compile_dfa(regex)
            self.assertLessEqual(len(dfa.min_dfa.states), len(dfa.dfa.states))

    def test_named_group_match(self):
        nfa = compile_nfa("(<g>a|b){3}<g>")
        result = nfa.match("aaaa")
        self.assertIsNotNone(result)
        self.assertEqual(result.groups["g"], "a")
        self.assertEqual(result.full_match, "aaaa")
        result = nfa.match("aaab")
        self.assertIsNone(result)

    def test_repeat_operator(self):
        dfa = compile_dfa("a{3}")
        self.assertTrue(dfa.match("aaa").full_match == "aaa")
        self.assertIsNone(dfa.match("aa"))
        self.assertIsNone(dfa.match("aaaa"))

    def test_optional_operator(self):
        dfa = compile_dfa("a?b")
        self.assertIsNotNone(dfa.match("b"))
        self.assertIsNotNone(dfa.match("ab"))
        self.assertIsNone(dfa.match("a"))

    def test_kleene_star(self):
        dfa = compile_dfa("a…")
        self.assertTrue(dfa.match("").full_match == "")
        self.assertIsNotNone(dfa.match("a"))
        self.assertIsNotNone(dfa.match("aaaa"))
        self.assertIsNone(dfa.match("b"))

    def test_complement_dfa(self):
        dfa = compile_dfa("abc")
        complement = dfa.complement_dfa()
        self.assertIsNone(match_dfa(complement, "abc"))
        self.assertIsNotNone(match_dfa(complement, "ab"))
        self.assertIsNotNone(match_dfa(complement, "x"))

    def test_intersection_dfa(self):
        dfa1 = compile_dfa("a(b|c)…")
        dfa2 = compile_dfa("a(b)…")
        intersected = dfa1.intersect(dfa2)
        self.assertIsNotNone(match_dfa(intersected, "abbb"))
        self.assertIsNone(match_dfa(intersected, "ac"))

    def test_dfa_to_regex(self):
        dfa = compile_dfa("a(b|c)lol")
        regex = dfa.to_regex()
        dfa1 = compile_dfa(regex)
        self.assertEqual(dfa.match("aclol").full_match, dfa1.match("aclol").full_match)

    def test_nested_named_groups(self):
        nfa = compile_nfa("(<g1>(<g2>a)b)<g1>")
        nfa.draw("nfa_example")
        result = nfa.match("abab")
        self.assertIsNotNone(result)
        self.assertEqual(result.groups["g1"], "ab")
        self.assertEqual(result.groups["g2"], "a")

    def test_named_group_reference_no_match(self):
        nfa = compile_nfa("(<g>a|b)<g>")
        self.assertIsNone(nfa.match("ab"))  # "a" then "b" ≠ "a" then "a"/"b" == first

    def test_named_group_reference_match(self):
        nfa = compile_nfa("(<g>abc)<g>")
        result = nfa.match("abcabc")
        self.assertIsNotNone(result)
        self.assertEqual(result.groups["g"], "abc")

    def test_search_with_offset(self):
        nfa = compile_nfa("a(b|c)…d")
        result = nfa.search("zzzabbd")
        self.assertIsNotNone(result)
        self.assertEqual(result.full_match, "abbd")
        self.assertEqual(result.start, 3)

    def test_dfa_intersect_with_empty(self):
        dfa1 = compile_dfa("abc")
        dfa2 = compile_dfa("xyz")
        intersected = dfa1.intersect(dfa2)
        self.assertIsNone(match_dfa(intersected, "abc"))
        self.assertIsNone(match_dfa(intersected, "xyz"))

        dfa = compile_dfa("aaa…")
        dfa1 = compile_dfa("a?a?a?a?a?")
        intersected = dfa.intersect(dfa1)
        self.assertIsNone(match_dfa(intersected, "a"))
        self.assertIsNotNone(match_dfa(intersected, "aa"))
        self.assertIsNotNone(match_dfa(intersected, "aaa"))
        self.assertIsNotNone(match_dfa(intersected, "aaaa"))
        self.assertIsNotNone(match_dfa(intersected, "aaaaa"))
        self.assertIsNone(match_dfa(intersected, "aaaaaa"))

    def test_escape_like_literals(self):
        # Assuming %s%...%s% syntax is supported for escaping
        dfa = compile_dfa("%(%a%|%b%)%")  # Match literal (a|b)
        self.assertIsNotNone(dfa.match("(a|b)"))
        self.assertIsNone(dfa.match("a"))

    def test_repeated_named_groups(self):
        nfa = compile_nfa("(<x>a)(<x>b)<x>")
        result = nfa.match("abb")
        self.assertIsNotNone(result)
        self.assertEqual(result.groups["x"], "b")  # Последнее присваивание


if __name__ == "__main__":
    unittest.main()

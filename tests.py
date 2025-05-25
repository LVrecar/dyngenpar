import dyngenpar
import unittest
import grammars
import utils


class TestPolynomials(unittest.TestCase):

    def setUp(self):
        self.rules, self.terminals = utils.grammar_from_string(grammars.polynomial_grammar)
        self.parser = dyngenpar.Parser(self.rules, self.terminals, "Poly", False)

    def test_nullables(self):
        self.assertEqual(self.parser.nullables, {"Sign"})
    
    def test_short_input(self):
        continuations, trees = self.parser.parse("x * x".split(" ")) # type: ignore
        trees = list(trees)
        self.assertEqual(len(trees), 1)
        self.assertEqual(trees[0].label, "Poly")
    
    def test_long_input(self):
        continuations, trees = self.parser.parse("- 2 x * x * x + x - 1".split(" "))
        trees_as_strings = set([str(tree) for tree in trees])
        self.assertEqual(len(trees), 2)
        self.assertIn("Poly#[Poly#[Poly#[Term#[Coefficient#[Sign#[-#[]], NUMBER#[2#[]]], XPower#[XPower#[x#[]], *#[], XPower#[XPower#[x#[]], *#[], XPower#[x#[]]]]]], +#[], Term#[XPower#[x#[]]]], -#[], Term#[Coefficient#[Sign#[], NUMBER#[1#[]]]]]", trees_as_strings)


class TestTomita(unittest.TestCase):

    def setUp(self):
        self.rules, self.terminals = utils.grammar_from_string(grammars.tomita_grammar)
        self.parser = dyngenpar.Parser(self.rules, self.terminals, "S", False)

    def test_nullables(self):
        self.assertEqual(self.parser.nullables, set())
    
    def test_input(self):
        continuations, trees = self.parser.parse("I saw Jack and Jane hit a man with a telescope".split(" "))
        self.assertEqual(len(trees), 6)


class TestLrEmpty(unittest.TestCase):

    def setUp(self):
        self.rules, self.terminals = utils.grammar_from_string(grammars.lr_with_empty)
        self.parser = dyngenpar.Parser(self.rules, self.terminals, "S", False)

    def test_nullables(self):
        self.assertEqual(self.parser.nullables, {"A"})
    
    def test_input(self):
        continuations, trees = self.parser.parse("x b b b".split(" "))
        trees_as_strings = set([str(tree) for tree in trees])
        self.assertEqual(len(trees), 1)
        self.assertIn("S#[A#[], S#[A#[], S#[A#[], S#[x#[]], b#[]], b#[]], b#[]]", trees_as_strings)


class TestSimpleAmbiguous(unittest.TestCase):

    def setUp(self):
        self.rules, self.terminals = utils.grammar_from_string(grammars.simple_ambiguous_grammar)
        self.parser = dyngenpar.Parser(self.rules, self.terminals, "S", False)

    def test_nullables(self):
        self.assertEqual(self.parser.nullables, set())
    
    def test_input(self):
        continuations, trees = self.parser.parse("a a a a".split(" "))
        self.assertEqual(len(trees), 5)


class TestNullable(unittest.TestCase):

    def setUp(self):
        self.rules, self.terminals = utils.grammar_from_string(grammars.nullable_grammar)
        self.parser = dyngenpar.Parser(self.rules, self.terminals, "S", False)

    def test_nullables(self):
        self.assertEqual(self.parser.nullables, {"S", "A", "B"})
    
    def test_empty_input(self):
        continuations, trees = self.parser.parse([])
        self.assertEqual(len(trees), 3)
        self.assertIn(dyngenpar.Tree("S"), trees)
        self.assertIn(dyngenpar.Tree("S", [dyngenpar.Tree("A")]), trees)
        self.assertIn(dyngenpar.Tree("S", [dyngenpar.Tree("A"), dyngenpar.Tree("B")]), trees)


class TestHighK(unittest.TestCase):

    def setUp(self):
        self.rules, self.terminals = utils.grammar_from_string(grammars.high_k_grammar)
        self.parser = dyngenpar.Parser(self.rules, self.terminals, "S", False)
    
    def test_nullables(self):
        self.assertEqual(self.parser.nullables, {"A", "B", "C", "D"})
    
    def test_input(self):
        continuations, trees = self.parser.parse("e".split(" "))
        self.assertEqual(len(trees), 2)
        self.assertIn("S#[F#[A#[], C#[], D#[], E#[e#[]], B#[]]]", [str(tree) for tree in trees])


class TestUtils(unittest.TestCase):

    def test_superfluous(self):
        tree = dyngenpar.Tree("A", [dyngenpar.Tree("B"), dyngenpar.Tree("A", [dyngenpar.Tree("a")]), dyngenpar.Tree("C")])
        tree2 = dyngenpar.Tree("A", [dyngenpar.Tree("B", [dyngenpar.Tree("b")]), dyngenpar.Tree("A", [dyngenpar.Tree("a")]), dyngenpar.Tree("C")])
        tree3 = dyngenpar.Tree("A", [dyngenpar.Tree("B", [dyngenpar.Tree("a")]), dyngenpar.Tree("A"), dyngenpar.Tree("C")])
        tree4 = dyngenpar.Tree("A", [dyngenpar.Tree("B", [dyngenpar.Tree("a")]), dyngenpar.Tree("A", [dyngenpar.Tree("b")]), dyngenpar.Tree("C")])
        terminals = {"a", "b"}
        self.assertTrue(tree.superfluously_recursive(terminals))
        self.assertFalse(tree2.superfluously_recursive(terminals))
        self.assertFalse(tree3.superfluously_recursive(terminals))
        self.assertFalse(tree4.superfluously_recursive(terminals))


if __name__ == "__main__":
    unittest.main()

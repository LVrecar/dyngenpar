from itertools import product
import logging, sys

from collections.abc import Callable, Iterable
from typing import Tuple, Any, List, Optional

#for logging
NO_LOGGING = 0
FUNCTION_CALLS_ONLY = 1
INTERMEDIATE_RESULTS = 2
END = -1
START = 1

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, stream=sys.stdout)


class Tree():
    """A class to represent parse trees.

    :param label: The label of the root of the parse tree.
    :type label: str
    :param children: A list of parse trees, representing children of the parse tree, defaults to None.
    :type children: list[Tree], optional
    """
    def __init__(self, label: str, children: Optional[List["Tree"]] = None):
        self.label: str = label
        self.children: List["Tree"] = children if children else []
    
    def leaves(self, terminals: set[str]):
        """Returns the string concatenation all leaf labels which are terminals in the grammar, left-to-right.
        Equivalent to the string that a given tree parses.

        :param terminals: A set of terminals in a grammar.
        :type terminals: set[str]
        :return: A string concatenation of the leaf labels which are terminals, left-to-right.
        :rtype: str
        """
        if not self.children:
            if self.label in terminals:
                return self.label
            return ""
        return " ".join([leaf for leaf in [child.leaves(terminals) for child in self.children] if leaf])

    def proper_subtrees(self) -> set["Tree"]:
        """Returns the set of proper subtrees of `self` i.e., all subtrees except self

        :return: The set of proper subtrees of `self`
        :rtype: set[Tree]
        """
        subtrees = set()
        for child in self.children:
            subtrees.add(child)
            subtrees = subtrees.union(child.proper_subtrees())
        return subtrees

    def superfluously_recursive(self, terminals: set[str]) -> bool:
        """Returns True if the tree is superfluously recursive i.e., has a proper subtree with the same root label and same input.

        :param terminals: A set of terminals, to determine the input of a tree
        :type terminals: set[str]
        :return: True, if the tree is superfluously recursive, false otherwise.
        :rtype: bool
        """
        for subtree in self.proper_subtrees():
            if subtree.label == self.label and subtree.leaves(terminals) == self.leaves(terminals):
                return True
        return False
        
    def __repr__(self) -> str:
        return f"{self.label}#{self.children}"
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Tree):
            return NotImplemented
        return self.label == other.label and self.children == other.children

    def __hash__(self):
        return hash(("label", self.label, "children", tuple(self.children)))


class Rule():
    """A representation of a grammar rule

    :param lhs: the symbol on the LHS of a grammar rule.
    :type lhs: str
    :param rhs: a sequence of symbols on the RHS of a grammar rule.
    :type rhs: list[str]
    """
    def __init__(self, lhs: str, rhs: Optional[list[str]] = None):
        self.lhs = lhs
        self.rhs = rhs if rhs else []
    
    def __repr__(self):
        rhs_string = " ".join(self.rhs)
        return f"{self.lhs} -> {rhs_string}"
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Rule):
            return NotImplemented
        return self.lhs == other.lhs and self.rhs == other.rhs
    
    def __hash__(self):
        return hash(("lhs", self.lhs, "rhs", tuple(self.rhs)))


class EdgeLabel():
    """An edge label for the initial graph
    
    :param rule: A grammar rule.
    :type rule: Rule
    :param k: An integer, representing the number of nullable non-terminals at the start of the RHS of the rule for the edge to be valid.
    :type k: int
    """
    def __init__(self, rule: Rule, k: int):
        self.rule = rule
        self.k = k
    
    def __repr__(self):
        return f"({self.rule}, {self.k})"
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EdgeLabel):
            return NotImplemented
        return self.rule == other.rule and self.k == other.k

    def __hash__(self):
        return hash(("rule", self.rule, "k", self.k))


class Continuation():
    label: str
    symbol: str
    parent: "Continuation"
    edge_label: EdgeLabel
    trees: list[Tree]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Continuation):
            return NotImplemented
        return self.label == other.label


class DoneContinuation(Continuation):
    def __init__(self):
        self.label = "done"

    def __repr__(self):
        return f"{self.label}"
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DoneContinuation):
            return NotImplemented
        return self.label == other.label

    def __hash__(self):
        return hash(("label", self.label))


class MatchContinuation(Continuation):
    def __init__(self, parent: Continuation, edge_label: EdgeLabel, trees: list[Tree]):
        self.label: str = 'match'
        self.parent: Continuation = parent
        self.edge_label: EdgeLabel = edge_label
        self.trees: list[Tree] = trees
    
    def __repr__(self):
        return f"{self.label} {self.edge_label} {self.trees} ▶ {self.parent}"
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MatchContinuation):
            return NotImplemented
        return self.label == other.label and self.edge_label == other.edge_label and self.parent == other.parent and self.trees == other.trees
    
    def __hash__(self):
        return hash(("label", self.label, "edge_label", self.edge_label, "trees", tuple(self.trees), "parent", self.parent))


class ReduceContinuation(Continuation):
    def __init__(self, parent: Continuation, symbol: str):
        self.label = 'reduce'
        self.parent = parent
        self.symbol = symbol
    
    def __repr__(self):
        return f"{self.label} {self.symbol} ▶ {self.parent}"
    
    def __eq__(self, other: object):
        if not isinstance(other, ReduceContinuation):
            return NotImplemented
        return self.label == other.label and self.symbol == other.symbol and self.parent == other.parent
    
    def __hash__(self):
        return hash(("label", self.label, "symbol", self.symbol, "parent", self.parent))


class Parser():
    """The Parser object is needed to do the actual parsing.

    :param rules: A set of Rule object, representing the grammar.
    :type rules: set
    :param terminals: A set of all terminals in the grammar.
    :type terminals: set
    :param start_symbol: The start symbol of the grammar, defaults to "S".
    :type start_symbol: str, optional
    :param logging_level: The detail of logging. NO_LOGGING will provide no output, FUNCTION_CALLS_ONLY will log the function being called and its inputs, as well as showing the results each call returns, and INTERMEDIATE_RESULTS additionally shows results after each step of the computation. Defaults to FUNCTION_CALLS
    :type logging_level: int, optional
    """
    def __init__(self, rules: set[Rule], terminals: set[str], start_symbol: str = "S", logging_level: int = FUNCTION_CALLS_ONLY):
        self.rules = rules # consider changing rules to be a dict of lhs -> set of rules s.t. lhs == rule.lhs. could affect performance for huge grammars
        self.terminals = terminals
        self.start_symbol = start_symbol
        self.nullables: set[str] = set()
        self.initial_graph: dict[str, list[EdgeLabel]] = dict()
        self.logging_level = logging_level
        self.depth = 0 # indentation depth for logging
        self.compute_nullables()
        self.compute_initial_graph()
        self.log("Setup complete, ready to parse")
        self.neighborhood_cache: dict[tuple[str, str], set[EdgeLabel]] = dict() # caching results of neighborhood

    def log(self, message: str, level: int = FUNCTION_CALLS_ONLY, increment: int = 0):
        """Logs `message` to standard output if `Parser.log_output` is greater or equal to `level`.

        :param message: The message to log
        :type message: str
        :param level: The level of detail for the log, defaults to FUNCTION_CALLS_ONLY
        :type level: int, optional
        """
        if self.logging_level >= level:
            if increment < 0:
                self.depth += increment
            logger.info("  " * self.depth + message)
            if increment >= 0:
                self.depth += increment

    def compute_nullables(self):
        """Finds the set of all nullable nonterminals (nonterminals that can parse the empty string).
        """
        self.log("Computing nullables", increment=START)
        for rule in self.rules: # find all rules of the form lhs -> epsilon
            lhs = rule.lhs
            rhs = rule.rhs
            self.log(f"lhs: {lhs}, rhs: {rhs}", INTERMEDIATE_RESULTS)
            if len(rhs) == 0 or len(rhs) == 1 and rhs[0] == "": # empty rule, or rule with RHS length 1 and only containing the empty string
                self.log(f"adding {lhs} to nullables", INTERMEDIATE_RESULTS)
                rule.rhs = [] # replace the RHS with an empty list
                self.nullables.add(lhs)
        
        new_nullables = True

        while new_nullables:
            new_nullables = False
            for rule in self.rules:
                lhs = rule.lhs
                rhs = rule.rhs
                if lhs in self.nullables:
                    continue
                should_goto = False # to implement the behaviour of the GOTO in the original code
                for symbol in rhs:
                    if symbol not in self.nullables:
                        should_goto = True
                        break
                if not should_goto:
                    self.log(f"recursively adding {lhs} to nullables", INTERMEDIATE_RESULTS)
                    self.nullables.add(lhs)
                    new_nullables = True
                    break
        self.log(f"Found nullables: {self.nullables}", increment=END)
    
    def compute_initial_graph(self):
        """Computes the initial graph of the grammar.
        """
        self.log("Computing initial graph")
        for rule in self.rules:
            k = 0
            for symbol in rule.rhs:
                try:
                    self.initial_graph[symbol].append(EdgeLabel(rule, k))
                except KeyError:
                    self.initial_graph[symbol] = [EdgeLabel(rule, k)]
                if symbol not in self.nullables:
                    break
                k += 1
        self.log("Initial graph computed")
    
    def reachable(self, source: str, target: str, visited: Optional[set[str]] = None) -> bool:
        """A helper function for `reduce`.
        Returns True if an acyclic path in the initial graph exists from `source` to `target`.
        The set `visited` ensures any node in the graph can be considered at most once.

        :param source: The symbol at the start of the path.
        :type source: str
        :param target: The symbol at the end of the path.
        :type target: str
        :param visited: The set of all visited notes, to avoid cycles.
        :type visited: set[str]
        :return: True if a path from `source` to `target was found, False otherwise.
        :rtype: bool
        """
        if visited is None:
            visited = set()
        self.log(f"Computing reachable({source}, {target}, {visited})", increment=START)
        if source == target:
            self.log(f"{source} == {target}, return True", increment=END)
            return True
        visited.add(source)
        try:
            edges = self.initial_graph[source]
        except KeyError:
            edges = []
        for edge in edges:
            if edge.rule.lhs in visited:
                continue
            if self.reachable(edge.rule.lhs, target, visited):
                self.log(f"{target} is reachable from {source} via {edge.rule.lhs}. visited {visited}", increment=END)
                return True
        self.log(f"{target} is not reachable from {source}. visited {visited}", increment=END)
        return False

    def neighborhood(self, source: str, target: str) -> set[EdgeLabel]:
        """Returns the set of first edges of all paths `e` from `source` to `target` such that `e[1:]` is acyclic.
        Instead of computing full paths it considers all edges `(source, (rule, k), end)` and checks if `target` is reachable from `end`, without visiting any node in the initial graph more than once.
        Results of `neighborhood` are also cached.

        :param source: The symbol from which all paths start.
        :type source: str
        :param target: The symbol where all paths end.
        :type target: str
        :return: The set of first edges of all acyclic paths from `source` to `target`.
        :rtype: set[Edge]
        """

        self.log(f"neighborhood({source}, {target})", increment=START)
        edges: set[EdgeLabel] = set()
        if (source, target) in self.neighborhood_cache.keys():
            self.log(f"neighborhood returning {self.neighborhood_cache[(source, target)]} (CACHED)", increment=END)
            return self.neighborhood_cache[(source, target)]
        
        try:
            all_edges = self.initial_graph[source]
        except KeyError:
            all_edges = []

        for edge in all_edges:
            self.log(f"considering edge {edge}", INTERMEDIATE_RESULTS)
            if self.reachable(edge.rule.lhs, target):
                edges.add(edge)
        
        try:
            self.neighborhood_cache[(source, target)] = self.neighborhood_cache[(source, target)].union(edges)
        except KeyError:
            self.neighborhood_cache[(source, target)] = edges
        self.log(f"neighborhood({source}, {target}) returning {edges}", increment=END)
        return edges

    def map_unzip(self, function: Callable[..., tuple[frozenset[Continuation], frozenset[Tree]]], inputs: Iterable[Tuple[Any, ...]]) -> tuple[frozenset[Continuation], frozenset[Tree]]:
        """Given a `function` of k arguments which returns a pair of sets, and an Iterable of k-tuples, `map_unzip` maps `function` to each k-tuple of inputs and returns a pair of sets.
        The first pair contains the union of all the first elements of all the results of the mapping, and the second pair contains the union of all the second elements.

        :param function: A function of k arguments which must return a pair of set.
        :type function: Callable[..., tuple[frozenset[Continuation], frozenset[Tree]]]
        :param inputs: An iterable of k-tuples containing all the inputs to map `function` over.
        :type inputs: Iterable[Tuple[Any, ...]]
        :return: A pair of the union of all the first elements of all the results of the mapping, and the union of all the second elements of all the results of the mapping.
        :rtype: tuple[frozenset[Continuation], frozenset[Tree]]
        """
        self.log(f"map_unzip({function.__name__}, {inputs})", increment=START)
        results: set[tuple[frozenset[Continuation], frozenset[Tree]]] = set() # Python doesn't support sets in sets, so we need frozensets

        # STEP 1
        for i in inputs:
            f, s = function(*i)
            results.add((frozenset(f), frozenset(s))) # Python doesn't support sets in sets, so we need frozensets
        self.log(f"R = {results}", INTERMEDIATE_RESULTS)
        first: frozenset[Continuation] = frozenset()
        second: frozenset[Tree] = frozenset()
        # STEP 2
        for r in results:
            first = first.union(r[0])
            second = second.union(r[1])
        self.log(f"map_unzip({function.__name__}, {inputs}) returning ({first}, {second})", increment=END)
        return first, second
      
    def epsilon_trees(self, nullable: str, m: Optional[frozenset[str]] = None) -> frozenset[Tree]:
        """Given a nonterminal `nullable` it returns all non-recursive trees with root `nullable` that parse the empty string.

        :param nullable: The nonterminal at the root of all returned trees.
        :type nullable: str
        :param m: A set of symbols, to ensure each symbol is only considered once, thus avoiding recursive trees. Defaults to None, and then initialises as an empty set
        :type m: set, optional
        :return: The set of all non-recursive trees with root `nullable` that parse the empty string.
        :rtype: frozenset[Tree]
        """
        if m is None:
            m = frozenset()
        self.log(f"epsilonTrees({nullable}, {m})", increment=START)
        trees: set[Tree] = set()
        new_m = m.union({nullable})
        for rule in self.rules:
            if rule.lhs != nullable: # only consider rules with the correct LHS
                continue
            if all([symbol in self.nullables and symbol not in new_m for symbol in rule.rhs]): # only consider rules with fully nullable RHS that hasn't been visited yet
                self.log(f"working on {rule}", INTERMEDIATE_RESULTS)
                nullable_sets: list[frozenset[Tree]] = []
                for symbol in rule.rhs: # match individual symbols in RHS to epsilon, create list of sets
                    nullable_sets.append(self.epsilon_trees(symbol, new_m))
                for tree_set in product(*nullable_sets): # cartesian product ensures we get all possible combinations
                    trees.add(Tree(rule.lhs, list(tree_set)))
        self.log(f"epsilonTrees({nullable}, {m}) returning {trees}", increment=END)
        return frozenset(trees)

    def match(self, target_tree: Tree | None, continuation: MatchContinuation) -> tuple[frozenset[Continuation], frozenset[Tree]]:
        """Tries to find a parse tree for the rule `r` carried by `continuation.edge_label`.
        First, it matches the first `k` symbols to the empty string, creating new continuations if there are multiple possible trees, and then attaches `target_tree` to `continuation.trees`.
        It then creates a new continuation for each symbol after the first `k+1`, expecting to match them by shifting more symbols from the input.
        Once all the trees for the RHS of `r` are found, it returns a new tree with root LHS(`r`) and `continuation.trees` as children.

        :param target_tree: The tree to attach at the `k`-th position, which is a parse tree for `sequence[k]`. Can be None if it will not be attached as part of the `match` call.
        :type target_tree: Tree | None
        :param continuation: The current continuation
        :type continuation: MatchContinuation
        :return: A set of continuations and a set of parse trees for the rule r, which contain `target_tree` as a subtree.
        :rtype: tuple[frozenset[Continuation], frozenset[Tree]]
        """
        self.log(f"match({target_tree}, {continuation})", increment=START)
        # STEP 1
        if len(continuation.trees) == len(continuation.edge_label.rule.rhs):
            self.log(f"trees found for all symbols in RHS(r) = {continuation.edge_label.rule.rhs}")
            new_tree = Tree(continuation.edge_label.rule.lhs, continuation.trees)
            if new_tree.superfluously_recursive(self.terminals):
                self.log(f"{new_tree} is superfluously recursive", INTERMEDIATE_RESULTS)
                c_new, t_new = frozenset(), frozenset()
            else:
                self.log(f"{new_tree} is not superfluously recursive", INTERMEDIATE_RESULTS)
                c_new, t_new = frozenset(), frozenset([new_tree])
            self.log(f"match({target_tree}, {continuation}) returning ({c_new}, {t_new})", increment=END)
            return c_new, t_new
        
        # STEP 2
        if len(continuation.trees) == continuation.edge_label.k:
            t_hat: frozenset[Tree] = frozenset([target_tree]) if target_tree else frozenset()
            new_target = None
            self.log(f"|trees| = k, T_hat = {t_hat}, `maybe tree` is now {new_target}", INTERMEDIATE_RESULTS)
        # STEP 3
        else:
            t_hat = self.epsilon_trees(continuation.edge_label.rule.rhs[len(continuation.trees)])
            new_target = target_tree
            self.log(f"|trees| != k, T_hat = {t_hat}, maybe tree is now {new_target}", INTERMEDIATE_RESULTS)
        # STEP 4
        c_prime: frozenset[Continuation] = frozenset()
        if len(continuation.trees) > continuation.edge_label.k:
            c_prime = frozenset([ReduceContinuation(continuation, continuation.edge_label.rule.rhs[len(continuation.trees)])])
        self.log(f"C' = {c_prime}", INTERMEDIATE_RESULTS)
        
        # STEP 5
        c_new, t_new = self.map_unzip(self.match, [(new_target, MatchContinuation(continuation.parent, continuation.edge_label, continuation.trees + [tree])) for tree in t_hat])
        self.log(f"C_new = {c_new}, T_new = {t_new}", INTERMEDIATE_RESULTS)
        # STEP 6
        self.log(f"match({target_tree}, {continuation}) returning ({c_new.union(c_prime)}, {t_new})", increment=END)
        return c_new.union(c_prime), t_new

    def reduce(self, tree: Tree, continuation: ReduceContinuation, m: Optional[set[str]] = None) -> tuple[frozenset[Continuation], frozenset[Tree]]:
        """Returns the set of all parse trees with root `target` that contain `tree` as a subtree which parse the same string as `tree`.
        It also returns a set of continuations which describe all ways in which a parse tree with root `target`, which contains `tree` as a subtree can be completed by shifting more symbols from the input.

        :param target: The root label of all trees returned.
        :type target: str
        :param tree: The tree all returned trees must contain as a subtree.
        :type tree: Tree
        :param m: A set of visited symbols in the grammar, to avoid superfluously recursive trees.
        :type m: set[str]
        :param continuation: The current continuation.
        :type continuation: Continuation
        :return: A set of continuations and a set of trees.
        :rtype: tuple[frozenset[Continuation], frozenset[Tree]]
        """
        if m is None:
            m = set()
        self.log(f"reduce({tree}, {continuation}, {m})", increment=START)
        edges = self.neighborhood(tree.label, continuation.symbol)
        
        # STEP 1
        start_continuations, start_trees = self.map_unzip(self.match, [(tree, MatchContinuation(continuation, edge, [])) for edge in edges])
        self.log(f"C_start = {start_continuations}, T_start = {start_trees}", INTERMEDIATE_RESULTS)

        # STEP 2
        done_trees: set[Tree] = set()
        if tree.label == continuation.symbol:
            done_trees.add(tree)
        
        for start_tree in start_trees:
            if start_tree.label == continuation.symbol:
                done_trees.add(start_tree)
        self.log(f"T_done = {done_trees}", INTERMEDIATE_RESULTS)

        # STEP 3
        new_m = m.union({tree.label})
        reduce_continuations, reduce_trees = self.map_unzip(self.reduce, [(filtered_tree, continuation, new_m) for filtered_tree in start_trees if filtered_tree.label not in new_m])
        self.log(f"C_new = {reduce_continuations}, T_new = {reduce_trees}", INTERMEDIATE_RESULTS)

        # STEP 4
        final_continuations = reduce_continuations.union(start_continuations)
        final_trees = frozenset(done_trees.union(reduce_trees))
        self.log(f"reduce({tree}, {continuation}, {m}) returning ({final_continuations}, {final_trees})", increment=END)
        return final_continuations, final_trees
    
    def process_continuation(self, continuation: Continuation, trees: frozenset[Tree]) -> tuple[frozenset[Continuation], frozenset[Tree]]:
        """Attempts to complete the parse trees described by `continuation` using trees given in `trees`.
        Returns the set of all completed parse trees, and a set of continuations describing all ways in which additional symbols from the input can be used to complete a parse tree.

        :param continuation: A continuation to process.
        :type continuation: Continuation
        :param trees: The set of trees to complete the parse trees described by the continuation.
        :type trees: frozenset[Tree]
        :return: A set of continuations and a set of trees.
        :rtype: tuple[frozenset[Continuation], frozenset[Tree]]
        """
        self.log(f"processContinuation({continuation}, {trees})", increment=START)
        # STEP 1
        if continuation.label == 'done':
            self.log("C = done")
            self.log(f"processContinuation({continuation}, {trees}) returning ({frozenset()}, {trees})", increment=END)
            return (frozenset(), trees)
        
        new_continuations: frozenset[Continuation] = frozenset()
        new_trees: frozenset[Tree] = frozenset()
        # STEP 2
        if continuation.label == 'match':
            new_continuations, new_trees = self.map_unzip(self.match, [(None, MatchContinuation(continuation.parent, continuation.edge_label, continuation.trees + [tree])) for tree in trees])
            self.log(f"C_new = {new_continuations}, T_new = {new_trees}", INTERMEDIATE_RESULTS)
        
        # STEP 3
        elif continuation.label == 'reduce':
            new_continuations, new_trees = self.map_unzip(self.reduce, [(tree, continuation) for tree in trees])
            self.log(f"C_new = {new_continuations}, T_new = {new_trees}", INTERMEDIATE_RESULTS)
        
        # STEP 4
        c_prime, t_prime = self.process_continuation(continuation.parent, new_trees)
        self.log(f"C' = {c_prime}, T' = {t_prime}", INTERMEDIATE_RESULTS)

        # STEP 5
        self.log(f"processContinuation({continuation}, {trees}) returning ({c_prime.union(new_continuations)}, {t_prime})", increment=END)
        return (c_prime.union(new_continuations), t_prime)

    def parse(self, input_sentence: Iterable[str]) -> frozenset[Tree]:
        """Given an input sentence, `parse` returns the set of all possible parse trees.

        :param input_sentence: A sequence of symbols, representing the input.
        :type input_sentence: Iterable[str]
        :return: A set of all parse trees for the input sentence.
        :rtype: frozenset[Tree]
        """
        self.log(f"parse({input_sentence})", increment=START)
        # STEP 1
        continuations: frozenset[Continuation] = frozenset({ReduceContinuation(DoneContinuation(), self.start_symbol)})
        trees = self.epsilon_trees(self.start_symbol)
        self.log(f"C_0 = {continuations}, T_0 = {trees}", INTERMEDIATE_RESULTS)
        
        pos = 0
        # STEP 2
        for term in input_sentence:
            self.log(f"Input position: {pos}")

            continuations, trees = self.map_unzip(self.process_continuation, [(continuation, {Tree(term)}) for continuation in continuations])
            
            self.log(f"finished processing input symbol {term}", INTERMEDIATE_RESULTS)
            self.log(f"C_{pos}:\n{'\n\n'.join([str(c) for c in continuations])}", INTERMEDIATE_RESULTS)
            self.log(f"T_{pos}:\n{'\n\n'.join([str(tree) for tree in trees])}", INTERMEDIATE_RESULTS)
            # self.log(f"""New parse state is:\nInput: {input_sentence}\nposition: {pos}\ncontinuations {len(continuations)}:\n{'\n\n'.join([str(c) for c in continuations])}\ntrees: {len(trees)}\n{'\n\n'.join([str(tree) for tree in trees])}""")
            pos += 1
        # STEP 3
        self.log(f"parse({input_sentence}) returning {trees}")
        return trees

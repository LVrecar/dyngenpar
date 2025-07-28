from dyngenpar import Tree, EdgeLabel, Rule
from typing import Iterable


#GRAMMAR UTILS
def grammar_from_string(s: str) -> tuple[set[Rule], set[str]]:
    """Given a (possibly) multiline string specifying a grammar, it returns a dictionary of grammar rules and a set of terminals for the grammar.
    The syntax of a valid grammar is as follows:

    A grammar rule is of the form ``LHS: a1 a2 ... an | ... | b1 b2 ... bn``, where each ``ak``, ``bk`` is a symbol of the grammar separated by a space.
    Symbols denoting the empty string should be replaced by "EMPTY"
    Grammar rules should be on separate lines, with no empty lines in between.

    :param s: A (possibly) multiline string containing grammar rules.
    :type s: str
    :return: A set of `Rule`s and a set of strings, representing the terminals in the grammar.
    :rtype: tuple[set[`Rule`], set[str]]
    """
    rules: set[Rule] = set()
    terminals: set[str] = set()
    lines = s.strip().split("\n") #split multiline into individual lines
    for line in lines:
        if not line or line == "\n": #ignore empty lines
            continue
        
        lhs, rhs = line.split(":") #split each line into LHS and RHS
        rhs_options = [rf"{option.strip()}" for option in rhs.split("|")] #RHS can consist of multiple options separated by |
        for rhs_option in rhs_options:
            rhs_option = rhs_option.replace("EMPTY", "")
            rhs_as_list = rhs_option.split(" ")
           
            for t in rhs_as_list: #add everything on the RHS of each rule to the set of terminals (terminals)
                terminals.add(t)
            
            rules.add(Rule(lhs.strip(), rhs_as_list))
    for rule in rules:
        try:
            terminals.remove(rule.lhs) #remove everything that appears as the lhs of some rule, since it cannot be a nonterminal
        except KeyError:
            continue
    return rules, terminals


def grammar_from_file(fname: str) -> tuple[set[Rule], set[str]]:
    """Given a file containing a grammar specified in the syntax described in `grammar_from_string`, it returns a set of grammar rules and a set of terminals for the grammar.

    :param fname: The name of the file containing the grammar.
    :type fname: str
    """
    with open(fname, "r") as file:
        contents = file.read()
        return grammar_from_string(contents)


#VISUALISATION UTILS
def print_parse_tree(tree: Tree, depth: int = 0):
    """Given a tree it will print it to the terminal, showing hierarchy using indentation.

    :param tree: The tree to print
    :type tree: Tree
    :param depth: The level of indentation, defaults to 0
    :type depth: int, optional
    """
    print(" " * depth + tree.label)
    for child in tree.children:
        print_parse_tree(child, depth + 1)


def parse_tree_to_file(tree: Tree, fname: str, for_dot: bool = False):
    """Given a parse tree, it will create a string representing the tree using indentation, and store it in the file specified by `fname`.

    :param tree: The tree to be outputted
    :type tree: Tree
    :param fname: The path to the file where the output should be stored
    :type fname: str
    :param for_dot: Whether to store parse trees in a format usable by `tree-to-dot <http://www.math.bas.bg/bantchev/ttdot/ttdot.html>`_, defaults to False
    :type for_dot: bool, optional
    """

    def subtree_to_string(tree: Tree, level: int, s: str, for_dot: bool = False): #defined inside parse_tree_to_file as that's the only place it's used, and we don't want it in the docs
        indent = " " * level
        s += indent
        if for_dot:
            s += "~"
        s += (tree.label)
        if for_dot:
            s += "~"
        s += "\n"
        for child in tree.children:
            s = subtree_to_string(child, level + 1, s, for_dot)
        return s

    s = subtree_to_string(tree, 0, "", for_dot)
    # print("SHOW DATA IS", show_data, fname)
    with open(fname, "w") as f:
        f.write(s.replace("\\", "\\\\"))


def print_all_trees(trees: Iterable[Tree]):
    """Prints all trees individually, adding a separator in between.

    :param trees: A collection of trees.
    :type trees: Iterable[Tree]
    """
    for tree in trees:
        print_parse_tree(tree)
        print("=====")


def all_trees_to_files(trees: Iterable[Tree], fname: str, for_dot: bool = False):
    """Given a collection of parse trees, it will create a string representing each tree using indentation, and store it in a file specified by `fname` and a number (starting at 1, and incrementing for each tree).

    :param tree: The tree to be outputted
    :type tree: Tree
    :param fname: The path to the file where the output should be stored
    :type fname: str
    :param for_dot: Whether to store parse trees in a format usable by `tree-to-dot <http://www.math.bas.bg/bantchev/ttdot/ttdot.html>`_, defaults to False
    :type for_dot: bool, optional
    """
    num = 1
    for tree in trees:
        parse_tree_to_file(tree, f"{fname}{num}", for_dot)


def initial_graph_to_string(graph: dict[str, list[EdgeLabel]]):
    """Returns a multiline string containing all the node-edge-node triples in the initial graph, on individual lines.

    :param graph: The initial graph
    :type graph: dict[str, list[EdgeLabel]]
    :return: The string representation of the initial graph
    :rtype: str
    """
    
    s = ""
    for source, edge_list in graph.items():
        for edge in edge_list:
            s += f"({source}, {edge}, {edge.rule.lhs})\n"
    return s


def initial_graph_to_dot(graph: dict[str, list[EdgeLabel]], fname: str):
    """Stores a representation of the initial graph in dot syntax in the file specified by `fname`.

    :param graph: The initial graph
    :type graph: dict[str, list[EdgeLabel]]
    :param fname: The name of the file
    :type fname: str
    """
    s = "digraph G {\n"
    for source, edge_list in graph.items():
        for edge in edge_list:
            s += f'"{source}" -> "{edge.rule.lhs}" [label="{edge}"]\n'
    s += "}"
    with open(fname, "w") as f:
        f.write(s)


def print_rule_set(rules: set[Rule]):
    """Prints all the rules in the set on individual lines

    :param rules: A set of rules
    :type rules: set[Rule]
    """
    for rule in rules:
        print(rule)

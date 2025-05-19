polynomial_grammar = """
Poly: Poly + Term | Poly - Term | Term
Term: Coefficient XPower | Coefficient | XPower
Coefficient: Sign NUMBER
Sign: EMPTY | -
XPower: x | XPower * XPower
NUMBER: 2 | 1
"""

nullable_grammar = """
S: S A | S A B | EMPTY | A | A B
A: a | EMPTY | A
B: b | EMPTY
"""

high_k_grammar = """
S: F
F: A C D E B | C E D | a c E f
E: e
A: a | EMPTY
B: b | EMPTY
C: c | EMPTY
D: d | EMPTY
"""

test_grammar3 = """
S: A E B | E | e
E: A E1 B
E1: A E2 B

E2: A E B
E: A E B | e | E E
A: EMPTY
B: EMPTY
C: EMPTY
D: EMPTY
"""

test_grammar4 = """
S: A B C
A: D A | C | EMPTY
B: b
C: EMPTY
D: EMPTY
"""

tomita_grammar = """
S: NP VP
S: S PP
S: S and S
NP: n
NP: det n
NP: NP PP
NP: NP and NP
VP: v NP
VP: v S
PP: p NP
n: I
v: saw
n: Jack
n: Jane
v: hit
det: the
n: man
p: with
det: a
n: telescope
"""

lr_with_empty = """
S: A S b | x
A: EMPTY
"""

simple_ambiguous_grammar = """
S: S S
S: a
"""

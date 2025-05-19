# DynGenPar Implementation
This repository contains a Python implementation of the parsing algorithm defined [https://www.macs.hw.ac.uk/~lv21/papers/lv-cicm25-paper.pdf](here).
It is intended to showcase the algorithm working on some example grammars and input to demonstrate its capabilities.
A crucial difference between this implementation and the description provided in the paper above is that the grammar used by the parser is not passed to each function explicitly.
Instead, all functions are methods of a `Parser` object, which has parameters `rules`, `terminals`, and `start_symbol`, which the methods then have access to.

## Requirements
Python 3.12.3 or higher

## Usage
The file [dyngenpar.py](dyngenpar.py) contains the actual parser, and is independent of external libraries or modules.
To use the parser:
1. initialise an instance of the `Parser` object with your grammar rules, terminals, and start symbol.
2. call the `Parser.parse` method, with your input sentence. This will return a set of trees.

This repository provides also various utilities in [utils.py](utils.py), such as a way to convert grammars[^1] into a set of `Rule` objects and a set of terminals, and some visualisation tools. 

You can run any of the examples directly running `python3 example_file_name.py` in your terminal.
You can also use them as a template to write your own examples.

[^1] those that adhere to the format specified in [the grammar format section](#grammar-format)-
### Grammar format <a name="grammar-format"></a>
The grammars are given in a BNF-like format.
Multiple rules with the same RHS can be represented using a pipe (`|`) symbol between them.
A rule that parses the empty string should have `EMPTY` on the RHS.
The LHS and RHS should be separated by a colon (`:`).
For example:

<code>
S: A B | A C | d <br>
A: a <br>
B: EMPTY <br>

C: c <br>
</code>

### Supplying your own grammar
Grammars can be provided in a separate file, or as a (multiline) string.
You can use the `grammar_from_string` and `grammar_from_file` functions in [utils.py](utils.py) for any grammar specified in the format described above.

## Provided examples
The file [tests.py](tests.py) contains basic tests, mostly checking if the correct number of trees and nullables are found.
The file [grammars.py](grammars.py) contains some sample grammars, and the folder [examples](examples/) contains files which use those grammars and parse sample inputs with them.
To run an example, simply run `python3 filename.py` from the `examples` folder, or `python3 examples/filename.py` from the top-level folder.
By default, the output will show each function that gets called and its inputs, as well as the final result of each function call.
Additionally, you can pass on the `--trace` option, which will provide details about the intermediate results, or `--no-trace` option which will not provide any details about the computation.
You can do this as follows: `python3 filename.py --trace`.

For large inputs, it is recommended to reroute the output to a separate file rather than the terminal, for easier inspection, e.g., `python3 filename.py --trace > out.log`.

### Creating your own examples
To create your own example, it is recommended to use one of the existing examples as a template.

import sys
sys.path.append("..")
sys.path.append(".")
import dyngenpar
import utils
import grammars


def main(log_level):
    rules, terminals = utils.grammar_from_string(grammars.polynomial_grammar)
    parser = dyngenpar.Parser(rules, terminals, "Poly", log_level)
    input_sentence = "- 2 x * x * x + x - 1".split(" ")
    trees = parser.parse(input_sentence)
    utils.print_all_trees(trees)


if __name__ == '__main__':
    log_level = dyngenpar.FUNCTION_CALLS_ONLY
    if len(sys.argv) > 1:
        if sys.argv[1] == "--trace":
            log_level = dyngenpar.INTERMEDIATE_RESULTS
        elif sys.argv[1] == "--no-trace":
            log_level = dyngenpar.NO_LOGGING
    main(log_level)

"""
This module contains functions for performing mathematical operations.
"""

import re
from typing import Callable

# The definitions of mathematical symbol
PLUS = "+"
MINUS = "-"
DIV = "/"


def is_mult(op: str):
    return op == "*" or op == "X" or op == "x"


def compile(string: str) -> int:
    """Calculate the expression and return the result."""
    return expr(string)


def expr(string: str) -> int:
    """
    Perform expression calculation:
    `<expr> ::= <term> { [+,-] <term> }`.
    """
    operators = r"\+|\-"
    matches = re.finditer(operators, string)

    result = 0  # The calculation result
    operation = add  # The mathematical operation, default as add()
    prev = 0  # The previous index of the matched operator
    for match in matches:
        idx = match.start()

        try:
            result = operation(result, term(string[prev:idx]))
            operation = expr_operation(string[idx])
            prev = idx + 1
        except:
            pass

    result = operation(result, term(string[prev:]))
    return result


def expr_operation(operator: str) -> Callable[[int, int], int]:
    """Get the valid expression operation base on the given operator."""
    if operator == PLUS:
        return add
    elif operator == MINUS:
        return subtract
    else:
        raise Exception(f"expr: Unknown operator '{operator}'")


def term(string: str) -> int:
    """
    Perform term calculation:
    `<term> ::= <factor> { [*,/] <factor> }`.
    """
    operators = r"X|x|\*|\/"
    matches = re.finditer(operators, string)

    result = 0  # The calculation result
    operation = add  # The mathematical operation, default as add()
    prev = 0  # The previous index of the matched operator
    for match in matches:
        idx = match.start()

        try:
            result = operation(result, factor(string[prev:idx]))
            operation = term_operation(string[idx])
            prev = idx + 1
        except:
            pass

    result = operation(result, factor(string[prev:]))
    return result


def term_operation(operator: str) -> Callable[[int, int], int]:
    """Get the valid term operation base on the given operator."""
    if is_mult(operator):
        return mutiply
    elif operator == DIV:
        return divide
    else:
        raise Exception(f"term: Unknown operator '{operator}'")


def factor(string: str) -> int:
    """
    Perform factor calculation:
    `<factor> ::= '(' <expr> ')' | <constant>`
    """
    string = string.strip()

    if string.startswith("(") and string.endswith(")"):
        return expr(string[1:-1])
    else:
        return constant(string)


def constant(string: str) -> int:
    """
    Perform constant calculation:
    `<constant> ::= <natural number>
    """
    return int(string.strip())


def add(x: int, y: int) -> int:
    """Perform the calculation of `x + y`."""
    return x + y


def subtract(x: int, y: int) -> int:
    """Perform the calculation of `x - y`."""
    return x - y


def mutiply(x: int, y: int) -> int:
    """Perform the calculation of `x * y`."""
    return x * y


def divide(x: int, y: int) -> int:
    """Perform the calculation of `x / y`."""
    return int(x / y)

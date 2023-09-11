import re

PLUS = '+'
MINUS = '-'
MULT = '*'
DIV = '/'

def compile(string):
    """Parse the string and return its calculation result."""
    return expr(string)


def expr(string):
    """
    Perform expression calculation:
    `<expr> ::= <term> { [+,-] <term> }`.
    """
    operators = r"\+|\-"
    matches = re.finditer(operators, string)

    result = 0
    op = add
    begins = 0
    for match in matches:
        idx = match.start()

        try:
            result = op(result, term(string[begins:idx]))
            op = expr_operation(string[idx])
            begins = idx + 1
        except:
            pass

    result = op(result, term(string[begins:]))
    return result


def expr_operation(operator):
    """Return the valid expression operation base on the given operator."""
    if operator == PLUS:
        return add
    elif operator == MINUS:
        return subtract
    else:
        raise Exception(f"expr: Unknown operator '{operator}'")


def term(string):
    """
    Perform term calculation:
    `<term> ::= <factor> { [*,/] <factor> }`.
    """
    operators = r"\*|\/"
    matches = re.finditer(operators, string)

    result = 0
    op = add
    begins = 0
    for match in matches:
        idx = match.start()

        try:
            result = op(result, factor(string[begins:idx]))
            op = term_operation(string[idx])
            begins = idx + 1
        except:
            pass

    result = op(result, factor(string[begins:]))
    return result


def term_operation(operator):
    """Return the valid term operation base on the given operator."""
    if operator == MULT:
        return mutiply
    elif operator == DIV:
        return divide
    else:
        raise Exception(f"term: Unknown operator '{operator}'")


def factor(string):
    """
    Perform factor calculation:
    `<factor> ::= '(' <expr> ')' | <constant>`
    """
    string = string.strip()

    if string.startswith("(") and string.endswith(")"):
        return expr(string[1:-1])
    else:
        return constant(string)


def constant(string):
    """
    Perform constant calculation:
    `<constant> ::= <natural number>
    """
    return int(string.strip())


def add(x, y):
    """Perform the calculation of `x + y`."""
    return x + y


def subtract(x, y):
    """Perform the calculation of `x - y`."""
    return x - y


def mutiply(x, y):
    """Perform the calculation of `x * y`."""
    return x * y


def divide(x, y):
    """Perform the calculation of `x / y`."""
    return x / y

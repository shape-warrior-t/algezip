"""
This module defines functions for parsing and stringifying boolean expressions and zippers.

Syntax overview:
    False: F, True: T
    Variables: single lowercase letters (to prevent collisions with other things)
    Operators: (!a), (a & b), (a | b)
    For ease of parsing/unparsing, explicit brackets are required around all operations.
    They can be any of () [] {}, as long as they are paired correctly.
    The stringification process will cycle between the brackets () -> [] -> {} -> () -> [] -> {} -> ...
    from outer to inner in order to improve readability.
    Whitespace is ignored. The stringification process inserts whitespace around & and | operators, and nowhere else.
    Focus is indicated by putting ^ under the subexpression under focus.

String --> boolean expression (for parsing expressions from user input):
string ---tokenize--> token stream ---parse--> boolean expression

Boolean expression with focus --> string with focus (for printing the expression being manipulated and its focus):
Zipper (boolean expression with focus) ---unparse--> token stream with focus
---untokenize--> (string, string) tuple (string with focus)

Exports other than tokenize, parse, unparse, and untokenize:
    ParseError - raised when tokenizing/parsing strings that do not represent a valid boolean expression
    Token - intermediate representation used for both directions of expression <-> string conversion
    FocusToken - a token together with information on whether it represents the subexpression under focus
"""

__all__ = ['FocusToken', 'ParseError', 'Token', 'parse', 'tokenize', 'unparse', 'untokenize']

from dataclasses import dataclass
from typing import Literal, TypeGuard, assert_never

from algezip.data import BinaryOp, Boolean, Cons, ConsList, Direction, Expr, UnaryOp, Variable, Zipper


class ParseError(Exception):
    """Raised during tokenization or parsing upon encountering syntactic problems with an expression string."""

    pass


# Tokens: T, F, (variable), !, &, |, (, )
# Bracket balancing is handled during (un)tokenization instead of (un)parsing, because it's simpler that way.
# In particular, the ( and ) tokens represent all types of opening/closing brackets.
# Since Python has union types, we can conveniently reuse some of the definitions from data.py
# to represent the corresponding tokens.
type Token = Boolean | Variable | UnaryOp | BinaryOp | Literal['(', ')']
# Defining special literal types for opening and closing brackets
# doesn't seem to bring enough safety to be worth the hassle.
_bracket_pairs = {('(', ')'), ('[', ']'), ('{', '}')}
_opening_brackets = ['(', '[', '{']
_closing_brackets = [')', ']', '}']


def _is_simple_token(char: str) -> TypeGuard[Token]:
    """Check if char is a character for which tokenization is a no-op."""
    return char in {'F', 'T', '!', '&', '|'}


def tokenize(expr_string: str) -> list[Token]:
    """
    Tokenize the input.

    Raise ParseError upon finding unbalanced brackets or illegal characters.
    """
    stream: list[Token] = []
    # To check for balanced brackets, employ the standard stack-based algorithm.
    unclosed_opening_brackets = []
    for char in expr_string:
        if _is_simple_token(char):  # F, T, !, &, |
            stream.append(char)
        elif char.islower():  # Variables
            name = char
            stream.append(Variable(name))
        elif char in _opening_brackets:  # (
            unclosed_opening_brackets.append(char)
            stream.append('(')
        elif char in _closing_brackets:  # )
            closing_bracket = char
            if not unclosed_opening_brackets:
                raise ParseError(f'unmatched bracket -- {closing_bracket!r}')
            opening_bracket = unclosed_opening_brackets.pop()
            if (opening_bracket, closing_bracket) in _bracket_pairs:
                stream.append(')')
            else:
                raise ParseError(f'bad bracket match -- {opening_bracket!r} with {closing_bracket!r}')
        elif not char.isspace():
            raise ParseError(f'unrecognized character in boolean expression -- {char!r}')
    if unclosed_opening_brackets:
        opening_bracket = unclosed_opening_brackets.pop()
        raise ParseError(f'unmatched bracket -- {opening_bracket!r}')
    return stream


###
# _StackExpr and _StackElement: used for defining the type of elements in the stack used for parsing.
# _StackExpr is a wrapper around Expr to allow for easy pattern matching isinstance checks.
###


@dataclass
class _StackExpr:
    expr: Expr


type _StackElement = UnaryOp | BinaryOp | _StackExpr


def parse(stream: list[Token]) -> Expr:
    """
    Parse the tokenized input.

    Raise ParseError for invalid token sequences.

    Precondition: brackets in the token stream are balanced (bracket balancing is checked by tokenize).
    """
    # Use a bottom-up parsing approach. Shift values (in expression form) and operators onto the parse stack.
    # Upon encountering a closing bracket, reduce the top of the parse stack to the appropriate expression.
    stack: list[_StackElement] = []
    # Maintain a stack of indices such that, upon encountering a closing bracket,
    # the part of the parse stack corresponding to the subexpression within the brackets
    # is stack[opening_bracket_boundaries[-1]:].
    opening_bracket_boundaries = []
    # Example:
    # []: (, a, &, (, b, |, c, ), )
    #
    # []: a, &, (, b, |, c, ), )
    # ^
    # [a]: &, (, b, |, c, ), )
    # ^
    # [a, &]: (, b, |, c, ), )
    # ^
    # [a, &]: b, |, c, ), )
    # ^    ^
    # [a, &, b]: |, c, ), )
    # ^     ^
    # [a, &, b, |]: c, ), )
    # ^     ^
    # [a, &, b, |, c]: ), )
    # ^     ^
    # [a, &, (b | c)]: )
    # ^
    # [(a & (b | c))]: (done)
    #
    for token in stream:
        match token:
            case 'F' | 'T' | Variable() as expr:  # Values
                stack.append(_StackExpr(expr))
            case '!' | '&' | '|' as op:  # Operators
                stack.append(op)
            case '(':  # Opening bracket -- modify the opening bracket indices stack.
                opening_bracket_boundaries.append(len(stack))
            case ')':  # Closing bracket -- reduce.
                boundary = opening_bracket_boundaries.pop()
                within_brackets = stack[boundary:]
                expr: Expr
                match within_brackets:
                    case '!', _StackExpr(arg):
                        expr = '!', arg
                    case _StackExpr(left), '&', _StackExpr(right):
                        expr = left, '&', right
                    case _StackExpr(left), '|', _StackExpr(right):
                        expr = left, '|', right
                    case _:
                        raise ParseError('invalid syntax in boolean expression')
                del stack[boundary:]
                stack.append(_StackExpr(expr))
            case _ as unreachable:
                assert_never(unreachable)
    # Should never happen as long as the precondition is fulfilled.
    assert not opening_bracket_boundaries, f'brackets should be balanced: {stream}'
    match stack:
        case [_StackExpr(expr)]:
            return expr
        case _:
            raise ParseError('invalid syntax in boolean expression')


@dataclass
class FocusToken:
    """A token along with information on whether the subexpression for the token is under focus."""

    token: Token
    under_focus: bool


# Directions to the subexpression under focus (if reachable),
# or an empty cons list (None) if we're already at the subexpression under focus (or one of its children),
# or 'unfocused' if we took a different path and can no longer reach the subexpression under focus.
type _FocusPath = ConsList[Direction] | Literal['unfocused']


def _move_along_path(focus_path: _FocusPath, direction: Direction) -> _FocusPath:
    """Take a direction, and return an updated focus path accordingly."""
    match focus_path:
        case Cons(next_direction, rest_of_path):
            if next_direction is direction:  # Travel along the path.
                return rest_of_path
            else:  # Off the path now, subexpression with focus is no longer reachable.
                return 'unfocused'
        case None:  # Already under focus, subexpressions should also have the focus indicator.
            return None
        case 'unfocused':  # Can no longer reach focus, no matter what further directions are taken.
            return 'unfocused'
        case _ as unreachable:
            assert_never(unreachable)


def unparse(zipper: Zipper) -> list[FocusToken]:
    """Convert a zipper to a stream of tokens with focus information."""
    top_level_expr, focus_path = zipper.to_top()
    return _unparse_with_focus_path(top_level_expr, focus_path)


def _unparse_with_focus_path(expr: Expr, focus_path: _FocusPath) -> list[FocusToken]:
    """
    Convert an expression to a stream of tokens, using the given focus path to determine focus information.

    Helper function for unparse.
    """
    under_focus = focus_path is None

    ###
    # Helper functions for reducing the number of times the same variable is written out over and over again.
    ###

    def ft(token: Token) -> FocusToken:
        return FocusToken(token, under_focus)

    def move(direction: Direction) -> _FocusPath:
        return _move_along_path(focus_path, direction)

    match expr:
        case 'F' | 'T' | Variable() as value:  # Values -- already valid (regular) tokens.
            return [ft(value)]
        # For operators, use unpacking to achieve an effect similar to string interpolation.
        case unary_op, arg:
            return [
                ft('('),
                ft(unary_op),
                *_unparse_with_focus_path(arg, move(Direction.ARG)),
                ft(')'),
            ]
        case left, binary_op, right:
            return [
                ft('('),
                *_unparse_with_focus_path(left, move(Direction.LEFT)),
                ft(binary_op),
                *_unparse_with_focus_path(right, move(Direction.RIGHT)),
                ft(')'),
            ]
        case _ as unreachable:
            assert_never(unreachable)


def untokenize(stream: list[FocusToken]) -> tuple[str, str]:
    """
    Convert a stream of tokens with focus information to an expression string and a string indicating focus.

    When printing, the string indicating focus is supposed to go under the expression string,
    with the starts of both strings aligned.
    """
    # Use lists instead of concatenating to strings for efficiency.
    expr_string_parts = []
    focus_string_parts = []
    # 3n -> (), 3n + 1 -> [], 3n + 2 -> {}
    bracket_depth = 0
    for focus_token in stream:
        match focus_token.token:
            case 'F' | 'T' | '!' as token:
                token_string = token
            case Variable(name):
                token_string = name
            case '&' | '|' as token:
                token_string = f' {token} '
            case '(':
                token_string = _opening_brackets[bracket_depth % 3]
                bracket_depth += 1
            case ')':
                # Need to decrease the depth first in order for the brackets to match up.
                bracket_depth -= 1
                token_string = _closing_brackets[bracket_depth % 3]
            case _ as unreachable:
                assert_never(unreachable)
        expr_string_parts.append(token_string)
        token_focus_char = '^' if focus_token.under_focus else ' '
        token_focus_string = token_focus_char * len(token_string)
        focus_string_parts.append(token_focus_string)
    return ''.join(expr_string_parts), ''.join(focus_string_parts)

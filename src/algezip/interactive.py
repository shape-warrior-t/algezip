"""This module defines the interactive functionality of the program."""

__all__ = ['main']

import argparse
import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import assert_never

from algezip import actions
from algezip.actions import ActionError
from algezip.data import Expr, NavigationError, Zipper
from algezip.source import ParseError, parse, tokenize, unparse, untokenize


def _print_blank_line() -> None:
    """Print a blank line. Used for visual separation."""
    print()


def _print_help() -> None:
    """Print the help text for when the user enters the help command."""
    _print_blank_line()
    print('Focus:')
    print("'^' under the current expression denotes the subexpression currently under focus")
    print("Use '^', '.', '<', '>' to move focus around (more info under Commands)")
    print('Transformations are always applied to the current subexpression under focus')
    _print_blank_line()
    print("Boolean expression syntax (for giving arguments to 'r!' and 'x'):")
    print('F - False, T - True')
    print('Single lowercase letters - variables')
    print('(!a) - not a, (a & b) - a and b, (a | b) - a or b')
    print('No operator precedence -- operations must be explicitly written in brackets')
    print('Allowed bracket types (interchangeable, but must be paired correctly): (), [], {}')
    _print_blank_line()
    print('Commands:')
    print('r! a - replace current subexpression under focus with a')
    print('^ - move focus to the parent of the current subexpression under focus')
    print('. - move focus from (!a) to its only argument a')
    print('< - move focus from (a & b) or (a | b) to the left argument a')
    print('> - move focus from (a & b) or (a | b) to the right argument b')
    print('c - [c]ommutativity -- (a | b) -> (b | a), (a & b) -> (b & a)')
    print('i - [i]dentity -- (a | F) -> a, (a & T) -> a')
    print('|F - expand via identity -- a -> (a | F)')
    print('&T - expand via identity -- a -> (a & T)')
    print('d - [d]istributivity -- (a | [b & c]) -> ([a | b] & [a | c]), (a & [b | c]) -> ([a & b] | [a & c])')
    print('f - [f]actoring -- ([a | b] & [a | c]) -> (a | [b & c]), ([a & b] | [a & c]) -> (a & [b | c])')
    print('v - complements/in[v]erses -- (a | [!a]) -> T, (a & [!a]) -> F')
    print('x a - e[x]pand into complements -- T -> (a | [!a]), F -> (a & [!a])')
    print('help - print help')
    print('q! - quit')


###
# Command classes - data for all the commands that change the expression that's being manipulated
# (including moving the focus).
# For commands without an argument, the user input must be the same as the command name (modulo surrounding whitespace).
# For commands with an argument, the user input must be the command name, followed by a space, followed by the argument
# (which should be a valid expression).
# Commands without an argument provide a Zipper -> Zipper transformer function
# for changing the expression that's being manipulated.
# For commands with an argument, providing an argument to the zipper_transformer_with_argument function
# is what yields the Zipper -> Zipper transformer function.
###


@dataclass
class _CommandWithoutArgument:
    name: str
    zipper_transformer: Callable[[Zipper], Zipper]


@dataclass
class _CommandWithArgument:
    name: str
    zipper_transformer_with_argument: Callable[[Expr], Callable[[Zipper], Zipper]]


def _transformer(action: Callable[[Expr], Expr]) -> Callable[[Zipper], Zipper]:
    """
    Lift an Expr -> Expr function to a Zipper -> Zipper function by transforming the subexpression under focus.

    Helper function, mainly for all the functions defined in actions.py.
    """
    return lambda zipper: zipper.transform(action)


# We could write Zipper.move_up etc. instead of lambda zipper: zipper.move_up(),
# but that currently doesn't work well with PyCharm's type checking:
# https://youtrack.jetbrains.com/issue/PY-71529/Incorrect-type-inferred-for-an-unbound-method-reference.
commands: list[_CommandWithoutArgument | _CommandWithArgument] = [
    _CommandWithArgument('r!', lambda a: _transformer(lambda _: a)),
    _CommandWithoutArgument('^', lambda zipper: zipper.move_up()),
    _CommandWithoutArgument('.', lambda zipper: zipper.move_arg()),
    _CommandWithoutArgument('<', lambda zipper: zipper.move_left()),
    _CommandWithoutArgument('>', lambda zipper: zipper.move_right()),
    _CommandWithoutArgument('c', _transformer(actions.apply_commutativity)),
    _CommandWithoutArgument('i', _transformer(actions.apply_identity)),
    _CommandWithoutArgument('|F', _transformer(actions.introduce_or_false)),
    _CommandWithoutArgument('&T', _transformer(actions.introduce_and_true)),
    _CommandWithoutArgument('d', _transformer(actions.distribute)),
    _CommandWithoutArgument('f', _transformer(actions.factor)),
    _CommandWithoutArgument('v', _transformer(actions.apply_complements)),
    _CommandWithArgument('x', lambda a: _transformer(lambda expr: actions.expand_into_complements(expr, a))),
]


class CommandError(Exception):
    """Raised for invalid commands."""

    pass


def _get_zipper_transformer(user_input: str) -> Callable[[Zipper], Zipper]:
    """
    Based on the user input, return a function for changing the expression that's being manipulated.

    Raise a CommandError if the user input does not denote a valid command.
    Indirectly raise a ParsingError if an expression provided as an argument is syntactically invalid.

    Precondition: user_input has been stripped of any leading and trailing whitespace.
    """
    # Just do a linear search over the list of commands, matching based on name.
    for command in commands:
        match command:
            case _CommandWithoutArgument(name, zipper_transformer):
                if user_input == name:
                    return zipper_transformer
                elif user_input.startswith(name + ' '):
                    raise CommandError(f'command {name!r} does not take an argument')
                else:  # No match
                    continue
            case _CommandWithArgument(name, zipper_transformer_with_argument):
                if user_input == name:
                    raise CommandError(f'command {name!r} requires an argument')
                elif user_input.startswith(name + ' '):
                    argument_input = user_input.removeprefix(name).strip()
                    argument = parse(tokenize(argument_input))
                    return zipper_transformer_with_argument(argument)
                else:  # No match
                    continue
            case _ as unreachable:
                assert_never(unreachable)
    raise CommandError('unrecognized command')


def main() -> None:
    """Run the program."""
    parser = argparse.ArgumentParser(
        description=inspect.cleandoc("""
            AlgeZip - a program that allows you to manipulate boolean expressions
            by applying boolean algebra axioms to transform them into equivalent expressions.
            Uses a "focusing" navigation system to allow for the manipulation of subexpressions,
            implemented via the functional programming concept of zippers (hence the name AlgeZip).
        """)
    )
    parser.parse_args()
    print('---AlgeZip---')
    print("For help, type 'help'")
    zipper = Zipper('F', None)
    while True:
        expr_string, focus_string = untokenize(unparse(zipper))
        _print_blank_line()
        print(expr_string)
        print(focus_string)
        _print_blank_line()
        user_input = input('> ').strip()
        if user_input == 'help':
            _print_help()
            continue
        elif user_input == 'q!':
            return
        elif not user_input:  # Just let blank user input do nothing instead of printing an error.
            continue
        try:
            zipper_transformer = _get_zipper_transformer(user_input)
            zipper = zipper_transformer(zipper)
        except (ActionError, CommandError, NavigationError, ParseError) as e:
            _print_blank_line()
            # All error messages in the program are designed directly for user consumption.
            print(f'Error: {e}')

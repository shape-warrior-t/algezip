"""
This module defines functions that transform boolean expressions into equivalent expressions via boolean algebra axioms.

Each function takes in an Expr as an argument and outputs an equivalent Expr,
raising ActionError if this is not possible with the transformations defined for the function.

Axioms were taken from https://en.wikipedia.org/wiki/Boolean_algebra_(structure)#Definition,
excluding associativity and absorption as those two axioms
"can be excluded from the set of axioms as they can be derived from the other axioms".

For reference, the relevant ones are:
Commutativity: (a | b) = (b | a), (a & b) = (b & a)
Identity: (a | F) = a, (a & T) = a
Distributivity: (a | [b & c]) = ([a | b] & [a | c]), (a & [b | c]) = ([a & b] | [a & c])
Complements: (a | [!a]) = T, (a & [!a]) = F

The notation left -> right and left <- right will be used for functions that only apply an axiom in one direction.

Exports:
    ActionError - raised for invalid uses of transformations
    apply_commutativity - (a | b) -> (b | a), (a & b) -> (b & a)
    apply_identity - (a | F) -> a, (a & T) -> a
    introduce_or_false - a -> (a | F)
    introduce_and_true - a -> (a & T)
    distribute - (a | [b & c]) -> ([a | b] & [a | c]), (a & [b | c]) -> ([a & b] | [a & c])
    factor - ([a | b] & [a | c]) -> (a | [b & c]), ([a & b] | [a & c]) -> (a & [b | c])
    apply_complements - (a | [!a]) -> T, (a & [!a]) -> F
    expand_into_complements - given an argument a: T -> (a | [!a]), F -> (a & [!a])
"""

__all__ = [
    'ActionError',
    'apply_commutativity',
    'apply_complements',
    'apply_identity',
    'distribute',
    'expand_into_complements',
    'factor',
    'introduce_and_true',
    'introduce_or_false',
]

from algezip.data import BinaryOp, Expr

# Used for formulating distributivity/factoring.
# We have _duals[op0] == op1 if op0 is AND and op1 is OR or if op0 is OR and op1 is AND.
_duals: dict[BinaryOp, BinaryOp] = {'&': '|', '|': '&'}


class ActionError(Exception):
    """Raised upon attempts to apply an axiom in an inapplicable manner."""

    def __init__(self, action_description: str, valid_transformations: list[str]):
        super().__init__(
            f"cannot {action_description} -- valid transformations are:\n{'\n'.join(valid_transformations)}"
        )


def apply_commutativity(expr: Expr) -> Expr:
    """Axiom: commutativity."""
    match expr:
        case a, binary_op, b:
            return b, binary_op, a
        case _:
            raise ActionError('apply commutativity', ['(a | b) -> (b | a)', '(a & b) -> (b & a)'])


def apply_identity(expr: Expr) -> Expr:
    """Axiom: identity (left -> right)."""
    match expr:
        case (a, '|', 'F') | (a, '&', 'T'):
            return a
        case _:
            raise ActionError('apply identity', ['(a | F) -> a', '(a & T) -> a'])


def introduce_or_false(expr: Expr) -> Expr:
    """Axiom: identity (left <- right, OR version only). Always applicable, so never raises ActionError."""
    return expr, '|', 'F'


def introduce_and_true(expr: Expr) -> Expr:
    """Axiom: identity (left <- right, AND version only). Always applicable, so never raises ActionError."""
    return expr, '&', 'T'


def distribute(expr: Expr) -> Expr:
    """Axiom: distributivity (left -> right)."""
    match expr:
        case a, op0, (b, op1, c) if _duals[op0] == op1:
            return (a, op0, b), op1, (a, op0, c)
        case _:
            raise ActionError(
                'distribute',
                [
                    '(a | [b & c]) -> ([a | b] & [a | c])',
                    '(a & [b | c]) -> ([a & b] | [a & c])',
                ],
            )


def factor(expr: Expr) -> Expr:
    """Axiom: distributivity (left <- right)."""
    match expr:
        case (a, op0, b), op1, (a_, op0_, c) if a == a_ and op0 == op0_ and _duals[op0] == op1:
            return a, op0, (b, op1, c)
        case _:
            raise ActionError(
                'factor',
                [
                    '([a | b] & [a | c]) -> (a | [b & c])',
                    '([a & b] | [a & c]) -> (a & [b | c])',
                ],
            )


def apply_complements(expr: Expr) -> Expr:
    """Axiom: complements (left -> right)."""
    match expr:
        case a, '|', ('!', a_) if a == a_:
            return 'T'
        case a, '&', ('!', a_) if a == a_:
            return 'F'
        case _:
            raise ActionError('apply complements', ['(a | [!a]) -> T', '(a & [!a]) -> F'])


def expand_into_complements(expr: Expr, a: Expr) -> Expr:
    """Axiom: complements (left <- right). Requires a to be provided, since it's not present in the right-hand side."""
    match expr:
        case 'T':
            return a, '|', ('!', a)
        case 'F':
            return a, '&', ('!', a)
        case _:
            raise ActionError('expand into complements', ['T -> (a | [!a])', 'F -> (a & [!a])'])

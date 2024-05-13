"""
This module defines the data types for modelling boolean expressions, used by the rest of the program.

Exports:
    Cons and ConsList - functional-style immutable linked list
    Variable, Boolean, UnaryOp, BinaryOp, and Expr - for modelling expressions normally
    Hole, Parent, and Zipper - for modelling expressions with a "focus" for easy navigation
    NavigationError - raised for invalid navigation operations with a zipper
    Direction - for identifying how to get from a parent subexpression to a child subexpression
"""

__all__ = [
    'BinaryOp',
    'Boolean',
    'Cons',
    'ConsList',
    'Direction',
    'Expr',
    'Hole',
    'NavigationError',
    'Parent',
    'UnaryOp',
    'Variable',
    'Zipper',
]

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Literal, assert_never


###
# Cons and ConsList: your typical cons-based linked list as commonly seen in functional programming.
# Used in order to have efficient modification and sharing at the same time --
# if we have two variables a and b both pointing to the same regular Python list,
# modifying a without modifying b would require copying the entire list;
# in contrast, if we have two variables a and b both pointing to the same cons list,
# we can "push" to and "pop" from the front of a, without affecting b, in O(1) time.
#
# In the comments/docstrings, we will write a ConsList like Cons(3, Cons(1, Cons(4, None))) as 3 -> 1 -> 4 -> (nil).
# Given a ConsList (list), we will write a ConsList like Cons(1, Cons(5, (list))) as 1 -> 5 -> (list).
###


@dataclass
class Cons[T]:
    car: T
    cdr: 'ConsList[T]'


type ConsList[T] = Cons[T] | None


###
# Variable, Boolean, UnaryOp, BinaryOp, and Expr: for modelling boolean expressions the straightforward way.
# <expr> = <boolean> | <variable> | (!<expr>) | (<expr> & <expr>) | (<expr> | <expr>)
# Instead of defining custom dataclasses, we simply use tuples and strings to represent expressions --
# it's nicer to construct and pattern match on expressions that way,
# especially since the infix notation for expressions is preserved.
# Compare ((A, '|', B), '&', ('!', (A, '&', B))) with And(Or(A, B), Not(And(A, B))).
# Thanks to Python's static typing tools, it's just as safe as using custom types, anyway.
###


@dataclass
class Variable:
    name: str


type Boolean = Literal['F', 'T']
type UnaryOp = Literal['!']
type BinaryOp = Literal['&', '|']
type Expr = Boolean | Variable | tuple[UnaryOp, Expr] | tuple[Expr, BinaryOp, Expr]


###
# Hole, Parent, and Zipper: for immutably modelling boolean expressions so that subexpressions can be easily modified.
# Uses your standard functional programming zipper technique -- for more info, see
# https://en.wikipedia.org/wiki/Zipper_(data_structure) or https://learnyouahaskell.github.io/zippers.html.
# To make things easier to think about, the placeholder "hole" in a parent expression
# is represented with a placeholder underscore.
###


type Hole = Literal['_']
type Parent = tuple[UnaryOp, Hole] | tuple[Hole, BinaryOp, Expr] | tuple[Expr, BinaryOp, Hole]


class NavigationError(Exception):
    """Raised whenever a zipper navigation function is called in an invalid way."""

    pass


class Direction(Enum):
    """
    Indicates how to go from a parent subexpression to an immediate child subexpression.

    ARG: from (!a) to a
    LEFT: from (a & b) or (a | b) to a
    RIGHT: from (a & b) or (a | b) to b
    """

    ARG = '.'
    LEFT = '<'
    RIGHT = '>'


@dataclass
class Zipper:
    """
    A boolean expression together with a "focus" on a specific subexpression, which can be moved around for navigation.

    Internally, a zipper like ([a | b] & [!{a & b}]) is represented as:
                                           ^^^^^^^
        expr: {a & b}
        parents: [!_] -> ([a | b] & _) -> (nil).
    """

    expr: Expr
    parents: ConsList[Parent]

    def move_up(self) -> 'Zipper':
        """
        Move to the immediate parent of the current subexpression, and return the resulting zipper.

        (!a) -> (!a), (a & b) -> (a & b), (a | b) -> (a | b), (a & b) -> (a & b), (a | b) -> (a | b)
          ^     ^^^^   ^         ^^^^^^^   ^         ^^^^^^^       ^     ^^^^^^^       ^     ^^^^^^^

        Raise NavigationError (via _move_up_with_direction) if there is no parent to move to.
        """
        new_zipper, _ = self._move_up_with_direction()
        return new_zipper

    def to_top(self) -> tuple[Expr, ConsList[Direction]]:
        """
        Return the top-level expression as an Expr along with directions for moving back to the current subexpression.

        ([a | b] & [!{a & b}]) -> ([a | b] & [!{a & b}])
                      ^           RIGHT -> ARG -> LEFT -> (nil)

        Do not ever raise NavigationError -- if we're already at the top,
        just return the current expression and an empty list for directions.
        """
        directions: ConsList[Direction] = None
        curr_zipper = self
        # Build the list of directions from right to left, inner to outer.
        # ([a | b] & [!{a & b}]) -> ([a | b] & [!{a & b}]) -> ([a | b] & [!{a & b}]) -> ([a | b] & [!{a & b}])
        #               ^                        ^^^^^^^                 ^^^^^^^^^^     ^^^^^^^^^^^^^^^^^^^^^^
        # (nil)                     LEFT -> (nil)             ARG -> LEFT -> (nil)      RIGHT -> ARG -> LEFT -> (nil)
        while curr_zipper.parents:
            parent_zipper, direction_to_curr = curr_zipper._move_up_with_direction()
            directions = Cons(direction_to_curr, directions)
            curr_zipper = parent_zipper
        return curr_zipper.expr, directions

    def _move_up_with_direction(self) -> tuple['Zipper', Direction]:
        """
        Move to the immediate parent, and return both the resulting zipper and the direction for moving back down.

        Helper function for move_up (which doesn't need the direction) and to_top (which calls this repeatedly).

        Raise NavigationError if there is no parent to move to.
        """
        match self.parents:
            case Cons(parent, grandparents):
                pass  # Just capture the variables for use below.
            case None:
                raise NavigationError('cannot move to parent -- already at the top')
            case _ as unreachable:
                assert_never(unreachable)
        expr = self.expr
        match parent:
            case unary_op, '_':
                # expr: a                         -> expr: (!a)
                # parents: (!_) -> (grandparents)    parents: (grandparents)
                return Zipper((unary_op, expr), grandparents), Direction.ARG
            case '_', binary_op, right:
                # expr: a                              -> expr: (a &/| b)
                # parents: (_ &/| b) -> (grandparents)    parents: (grandparents)
                return Zipper((expr, binary_op, right), grandparents), Direction.LEFT
            case left, binary_op, '_':
                # expr: b                              -> expr: (a &/| b)
                # parents: (a &/| _) -> (grandparents)    parents: (grandparents)
                return Zipper((left, binary_op, expr), grandparents), Direction.RIGHT

    def move_arg(self) -> 'Zipper':
        """
        For (!a), move to the only argument of the current subexpression, and return the resulting zipper.

        (!a) -> (!a)
        ^^^^      ^

        Raise NavigationError if there is no "only argument" to move to.
        """
        match self.expr:
            case unary_op, arg:
                # expr: (!a)         -> expr: a
                # parents: (parents)    parents: (!_) -> (parents)
                return Zipper(arg, Cons((unary_op, '_'), self.parents))
            case _:
                raise NavigationError('cannot move to only argument -- not at a unary operation')

    def move_left(self) -> 'Zipper':
        """
        For binary operations, move to the left argument of the current subexpression, and return the resulting zipper.

        (a & b) -> (a & b), (a | b) -> (a | b)
        ^^^^^^^     ^       ^^^^^^^     ^

        Raise NavigationError if there is no "left argument" to move to.
        """
        match self.expr:
            case left, binary_op, right:
                # expr: (a &/| b)    -> expr: a
                # parents: (parents)    parents: (_ &/| b) -> (parents)
                return Zipper(left, Cons(('_', binary_op, right), self.parents))
            case _:
                raise NavigationError('cannot move to left argument -- not at a binary operation')

    def move_right(self) -> 'Zipper':
        """
        For binary operations, move to the right argument of the current subexpression, and return the resulting zipper.

        (a & b) -> (a & b), (a | b) -> (a | b)
        ^^^^^^^         ^   ^^^^^^^         ^

        Raise NavigationError if there is no "right argument" to move to.
        """
        match self.expr:
            case left, binary_op, right:
                # expr: (a &/| b)    -> expr: b
                # parents: (parents)    parents: (a &/| _) -> (parents)
                return Zipper(right, Cons((left, binary_op, '_'), self.parents))
            case _:
                raise NavigationError('cannot move to right argument -- not at a binary operation')

    def transform(self, action: Callable[[Expr], Expr]) -> 'Zipper':
        """
        Apply action to the current subexpression, and return the resulting zipper.

        Apply <swap arguments> to ([a | b] & [!{a & b}]) -> ([b | a] & [!{a & b}])
                                   ^^^^^^^                   ^^^^^^^
        """
        # expr: a            -> expr: action(a)
        # parents: (parents)    parents: (parents)
        return Zipper(action(self.expr), self.parents)

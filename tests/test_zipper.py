"""Tests for the methods of the Zipper class."""

from contextlib import nullcontext as does_not_raise

import pytest

from algezip.data import BinaryOp, Cons, Direction, Expr, NavigationError, UnaryOp, Variable, Zipper

A = Variable('a')
B = Variable('b')
# Example zipper used in all the tests, chosen because it has all three operations and 3 levels of nesting.
# You might recognize it as a formula for XOR.
_ZIPPER = Zipper(((A, '|', B), '&', ('!', (A, '&', B))), None)


###
# Touch tests: navigate to a leaf in the expression, and come back up.
# Tests move_arg, move_left, move_right, and to_top.
###


def test_touch_left_a():
    # ([a | b] & [!{a & b}])
    #   ^
    zipper = _ZIPPER
    zipper = zipper.move_left().move_left()
    assert zipper == Zipper(A, Cons(('_', '|', B), Cons(('_', '&', ('!', (A, '&', B))), None)))
    expr, directions = zipper.to_top()
    assert expr == _ZIPPER.expr
    assert directions == Cons(Direction.LEFT, Cons(Direction.LEFT, None))


def test_touch_left_b():
    # ([a | b] & [!{a & b}])
    #       ^
    zipper = _ZIPPER
    zipper = zipper.move_left().move_right()
    assert zipper == Zipper(B, Cons((A, '|', '_'), Cons(('_', '&', ('!', (A, '&', B))), None)))
    expr, directions = zipper.to_top()
    assert expr == _ZIPPER.expr
    assert directions == Cons(Direction.LEFT, Cons(Direction.RIGHT, None))


def test_touch_right_a():
    # ([a | b] & [!{a & b}])
    #               ^
    zipper = _ZIPPER
    zipper = zipper.move_right().move_arg().move_left()
    assert zipper == Zipper(A, Cons(('_', '&', B), Cons(('!', '_'), Cons(((A, '|', B), '&', '_'), None))))
    expr, directions = zipper.to_top()
    assert expr == _ZIPPER.expr
    assert directions == Cons(Direction.RIGHT, Cons(Direction.ARG, Cons(Direction.LEFT, None)))


def test_touch_right_b():
    # ([a | b] & [!{a & b}])
    #                   ^
    zipper = _ZIPPER
    zipper = zipper.move_right().move_arg().move_right()
    assert zipper == Zipper(B, Cons((A, '&', '_'), Cons(('!', '_'), Cons(((A, '|', B), '&', '_'), None))))
    expr, directions = zipper.to_top()
    assert expr == _ZIPPER.expr
    assert directions == Cons(Direction.RIGHT, Cons(Direction.ARG, Cons(Direction.RIGHT, None)))


def test_tree_walk():
    """Walk the entire expression tree, mostly to test move_up."""
    # fmt: off
    assert (
        _ZIPPER        # ([a | b] & [!{a & b}])
                       # ^^^^^^^^^^^^^^^^^^^^^^
        .move_left()   # ([a | b] & [!{a & b}])
                       #  ^^^^^^^
        .move_left()   # ([a | b] & [!{a & b}])
                       #   ^
        .move_up()     # ([a | b] & [!{a & b}])
                       #  ^^^^^^^
        .move_right()  # ([a | b] & [!{a & b}])
                       #       ^
        .move_up()     # ([a | b] & [!{a & b}])
                       #  ^^^^^^^
        .move_up()     # ([a | b] & [!{a & b}])
                       # ^^^^^^^^^^^^^^^^^^^^^^
        .move_right()  # ([a | b] & [!{a & b}])
                       #            ^^^^^^^^^^
        .move_arg()    # ([a | b] & [!{a & b}])
                       #              ^^^^^^^
        .move_left()   # ([a | b] & [!{a & b}])
                       #               ^
        .move_up()     # ([a | b] & [!{a & b}])
                       #              ^^^^^^^
        .move_right()  # ([a | b] & [!{a & b}])
                       #                   ^
        .move_up()     # ([a | b] & [!{a & b}])
                       #              ^^^^^^^
        .move_up()     # ([a | b] & [!{a & b}])
                       #            ^^^^^^^^^^
        .move_up()     # ([a | b] & [!{a & b}])
                       # ^^^^^^^^^^^^^^^^^^^^^^
    ) == _ZIPPER
    # fmt: on


###
# Transform tests: test transform with a variety of focuses and actions.
###


def _and_to_or(expr: Expr) -> Expr:
    match expr:
        case left, '&', right:
            return left, '|', right
        case _:
            raise ValueError('expected expression of the form (a & b)')


def test_transform_right_and():
    # ([a | b] & [!{a & b}])
    #              ^^^^^^^
    zipper = _ZIPPER
    zipper = zipper.move_right().move_arg().transform(_and_to_or)
    expr, _ = zipper.to_top()
    assert expr == ((A, '|', B), '&', ('!', (A, '|', B)))


def _swap_or(expr: Expr) -> Expr:
    match expr:
        case left, '|', right:
            return right, '|', left
        case _:
            raise ValueError('expected expression of the form (a | b)')


def test_transform_or():
    # ([a | b] & [!{a & b}])
    #  ^^^^^^^
    zipper = _ZIPPER
    zipper = zipper.move_left().transform(_swap_or)
    expr, _ = zipper.to_top()
    assert expr == ((B, '|', A), '&', ('!', (A, '&', B)))


def test_full_replace():
    # ([a | b] & [!{a & b}])
    # ^^^^^^^^^^^^^^^^^^^^^^
    zipper = _ZIPPER
    replacement: Expr = (A, '&', ('!', B)), '|', (B, '&', ('!', A))
    zipper = zipper.transform(lambda _: replacement)
    expr, _ = zipper.to_top()
    assert expr == replacement


###
# Error tests: make sure navigation functions raise errors in the appropriate cases.
###


@pytest.mark.parametrize('expr', ['F', 'T', A])
def test_values_navigation_errors(expr: Expr):
    zipper = Zipper(expr, None)
    with pytest.raises(NavigationError):
        zipper.move_arg()
    with pytest.raises(NavigationError):
        zipper.move_left()
    with pytest.raises(NavigationError):
        zipper.move_right()


@pytest.mark.parametrize('unary_op', ['!'])
def test_unary_operations_navigation_errors(unary_op: UnaryOp):
    zipper = Zipper((unary_op, A), None)
    with does_not_raise():
        zipper.move_arg()
    with pytest.raises(NavigationError):
        zipper.move_left()
    with pytest.raises(NavigationError):
        zipper.move_right()


@pytest.mark.parametrize('binary_op', ['&', '|'])
def test_binary_operations_navigation_errors(binary_op: BinaryOp):
    zipper = Zipper((A, binary_op, B), None)
    with pytest.raises(NavigationError):
        zipper.move_arg()
    with does_not_raise():
        zipper.move_left()
    with does_not_raise():
        zipper.move_right()


def test_move_up_error():
    top_level_zipper = _ZIPPER
    with pytest.raises(NavigationError):
        top_level_zipper.move_up()

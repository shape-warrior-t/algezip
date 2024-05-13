"""Tests for the functions defined in actions.py."""

from collections.abc import Callable

import pytest

from algezip import actions
from algezip.actions import ActionError
from algezip.data import Expr, Variable

X = Variable('x')
Y = Variable('y')
# The functions should work regardless of the forms of any subexpressions represented by variables,
# so just pick a healthy mix of random expressions.
A = '!', X
B = X, '&', Y
C = '!', ('!', Y)
D = Y, '|', X


# For the purposes of testing, use None to indicate that a function should raise an ActionError.
# Allows for concise parametrization that includes both success and failure cases.
def _assert_action_result(action: Callable[[Expr], Expr], expr: Expr, expected: Expr | None):
    if expected is not None:
        assert action(expr) == expected
    else:
        with pytest.raises(ActionError):
            action(expr)


@pytest.mark.parametrize(
    ['initial', 'final'],
    [
        ((A, '|', B), (B, '|', A)),
        ((A, '&', B), (B, '&', A)),
        (A, None),
    ],
)
def test_apply_commutativity(initial: Expr, final: Expr | None):
    _assert_action_result(actions.apply_commutativity, initial, final)


@pytest.mark.parametrize(
    ['initial', 'final'],
    [
        ((A, '|', 'F'), A),
        ((A, '&', 'T'), A),
        (A, None),
    ],
)
def test_apply_identity(initial: Expr, final: Expr | None):
    _assert_action_result(actions.apply_identity, initial, final)


@pytest.mark.parametrize(
    ['initial', 'final'],
    [
        (A, (A, '|', 'F')),
    ],
)
def test_introduce_or_false(initial: Expr, final: Expr | None):
    _assert_action_result(actions.introduce_or_false, initial, final)


@pytest.mark.parametrize(
    ['initial', 'final'],
    [
        (A, (A, '&', 'T')),
    ],
)
def test_introduce_and_true(initial: Expr, final: Expr | None):
    _assert_action_result(actions.introduce_and_true, initial, final)


# Need to make sure that the _duals[op0] == op1 check works properly.
@pytest.mark.parametrize(
    ['initial', 'final'],
    [
        ((A, '|', (B, '|', C)), None),
        ((A, '|', (B, '&', C)), ((A, '|', B), '&', (A, '|', C))),
        ((A, '&', (B, '|', C)), ((A, '&', B), '|', (A, '&', C))),
        ((A, '&', (B, '&', C)), None),
        (A, None),
    ],
)
def test_distribute(initial: Expr, final: Expr | None):
    _assert_action_result(actions.distribute, initial, final)


# Need to make sure that a variety of checks work properly: _duals[op0] == op1, op0 == op0_, a == a_.
@pytest.mark.parametrize(
    ['initial', 'final'],
    [
        (((A, '|', B), '|', (A, '|', C)), None),
        (((A, '|', B), '&', (A, '|', C)), (A, '|', (B, '&', C))),
        (((A, '|', B), '&', (A, '&', C)), None),
        (((A, '&', B), '|', (A, '|', C)), None),
        (((A, '&', B), '|', (A, '&', C)), (A, '&', (B, '|', C))),
        (((A, '&', B), '&', (A, '&', C)), None),
        (((A, '|', B), '&', (D, '|', C)), None),
        (((A, '&', B), '|', (D, '&', C)), None),
        (A, None),
    ],
)
def test_factor(initial: Expr, final: Expr | None):
    _assert_action_result(actions.factor, initial, final)


# Need to make sure that the a == a_ checks work properly.
@pytest.mark.parametrize(
    ['initial', 'final'],
    [
        ((A, '|', ('!', A)), 'T'),
        ((A, '&', ('!', A)), 'F'),
        ((A, '|', ('!', D)), None),
        ((A, '&', ('!', D)), None),
        (A, None),
    ],
)
def test_apply_complements(initial: Expr, final: Expr | None):
    _assert_action_result(actions.apply_complements, initial, final)


# Needs a bit of extra code to handle the extra argument correctly.
@pytest.mark.parametrize(
    ['initial', 'a', 'final'],
    [
        ('T', A, (A, '|', ('!', A))),
        ('F', A, (A, '&', ('!', A))),
        (B, A, None),
    ],
)
def test_expand_into_complements(initial: Expr, a: Expr, final: Expr | None):
    _assert_action_result(lambda expr: actions.expand_into_complements(expr, a), initial, final)

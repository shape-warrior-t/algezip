"""Tests for the boolean expression <-> string conversion functions."""

import pytest

from algezip.data import Expr, Variable, Zipper
from algezip.source import FocusToken, ParseError, Token, parse, tokenize, unparse, untokenize

A = Variable('a')
B = Variable('b')
C = Variable('c')


# Similarly to test_actions, use None to indicate that a function should raise an error.


@pytest.mark.parametrize(
    ['expr_string', 'expected'],
    [
        ('(T | F)', ['(', 'T', '|', 'F', ')']),
        ('{T & F}', ['(', 'T', '&', 'F', ')']),
        ('[![!T]]', ['(', '!', '(', '!', 'T', ')', ')']),
        (' ( ! { ! T } ) ', ['(', '!', '(', '!', 'T', ')', ')']),
        ('([a | b] & [!{a & b}])', ['(', '(', A, '|', B, ')', '&', '(', '!', '(', A, '&', B, ')', ')', ')']),
        ('((a|b)&(!(a&b)))', ['(', '(', A, '|', B, ')', '&', '(', '!', '(', A, '&', B, ')', ')', ')']),
        ('([A | B] & [!{A & B}])', None),
        ('<!<!T>>', None),
        ('[~[~T]]', None),
        ('![!T]]', None),
        ('[![!T]', None),
        ('(![!T)]', None),
    ],
)
def test_tokenize(expr_string: str, expected: list[Token] | None):
    if expected is not None:
        assert tokenize(expr_string) == expected
    else:
        with pytest.raises(ParseError):
            tokenize(expr_string)


@pytest.mark.parametrize(
    ['stream', 'expected'],
    [
        (['(', 'T', '|', 'F', ')'], ('T', '|', 'F')),
        (['(', 'T', '&', 'F', ')'], ('T', '&', 'F')),
        (['(', '!', '(', '!', 'T', ')', ')'], ('!', ('!', 'T'))),
        (
            ['(', '(', A, '|', B, ')', '&', '(', '!', '(', A, '&', B, ')', ')', ')'],
            ((A, '|', B), '&', ('!', (A, '&', B))),
        ),
        (['F', 'T'], None),
        (['(', 'T', '!', 'F', ')'], None),
        (['(', 'T', '!', ')'], None),
        (['(', '&', 'T', ')'], None),
        (['(', '|', 'T', ')'], None),
        (['(', 'T', '&', '&', 'F', ')'], None),
        (['(', 'T', '|', '|', 'F', ')'], None),
        (['(', 'F', ')'], None),
        (['!', 'T'], None),
        (['T', '&', 'F'], None),
        (['T', '|', 'F'], None),
    ],
)
def test_parse(stream: list[Token], expected: Expr | None):
    if expected is not None:
        assert parse(stream) == expected
    else:
        with pytest.raises(ParseError):
            parse(stream)


# Stringification tests: it would be tedious to manually specify which tokens should have focus,
# so specify a range of indices instead.
#
# For test data, use all the possible focuses for ([a | b] & [!{a & b}]), along with a simple
# (T | F) test to make sure that T and F are accounted for properly.
#  ^

# Data: (
#     expected result of untokenize,
#     zipper with the appropriate focus,
#     start index for token focus,
#     stop index for token focus
# )
# fmt: off
_ZIPPER = Zipper(((A, '|', B), '&', ('!', (A, '&', B))), None)
#                0    1    2    3    4    5    6    7    8    9    a    b    c    d    e    f   10
_ZIPPER_TOKENS = ['(', '(',  A,  '|',  B,  ')', '&', '(', '!', '(',  A,  '&',  B,  ')', ')', ')']
_ZIPPER_TEST_DATA = [
    (('([a | b] & [!{a & b}])',
      '^^^^^^^^^^^^^^^^^^^^^^'), _ZIPPER, 0x0, 0x10),
    (('([a | b] & [!{a & b}])',
      ' ^^^^^^^              '), _ZIPPER.move_left(), 0x1, 0x6),
    (('([a | b] & [!{a & b}])',
      '  ^                   '), _ZIPPER.move_left().move_left(), 0x2, 0x3),
    (('([a | b] & [!{a & b}])',
      '      ^               '), _ZIPPER.move_left().move_right(), 0x4, 0x5),
    (('([a | b] & [!{a & b}])',
      '           ^^^^^^^^^^ '), _ZIPPER.move_right(), 0x7, 0xf),
    (('([a | b] & [!{a & b}])',
      '             ^^^^^^^  '), _ZIPPER.move_right().move_arg(), 0x9, 0xe),
    (('([a | b] & [!{a & b}])',
      '              ^       '), _ZIPPER.move_right().move_arg().move_left(), 0xa, 0xb),
    (('([a | b] & [!{a & b}])',
      '                  ^   '), _ZIPPER.move_right().move_arg().move_right(), 0xc, 0xd),
]
# fmt: on


@pytest.mark.parametrize(
    ['zipper', 'expected_tokens', 'expected_focus_start', 'expected_focus_stop'],
    [
        (Zipper(('T', '|', 'F'), None).move_left(), ['(', 'T', '|', 'F', ')'], 1, 2),
        *((zipper, _ZIPPER_TOKENS, start, stop) for _, zipper, start, stop in _ZIPPER_TEST_DATA),
    ],
)
def test_unparse(zipper: Zipper, expected_tokens: list[Token], expected_focus_start: int, expected_focus_stop: int):
    actual_focus_tokens = unparse(zipper)
    actual_tokens = [focus_token.token for focus_token in actual_focus_tokens]
    assert actual_tokens == expected_tokens
    actual_focus_indices = {i for i, focus_token in enumerate(actual_focus_tokens) if focus_token.under_focus}
    expected_focus_indices = set(range(expected_focus_start, expected_focus_stop))
    assert actual_focus_indices == expected_focus_indices


_T_OR_F_TESTCASE_EXPR_STRINGS = (
    '(T | F)',
    ' ^     ',
)


@pytest.mark.parametrize(
    ['expr_strings', 'tokens', 'focus_start', 'focus_stop'],
    [
        (_T_OR_F_TESTCASE_EXPR_STRINGS, ['(', 'T', '|', 'F', ')'], 1, 2),
        *((expr_strings, _ZIPPER_TOKENS, start, stop) for expr_strings, _, start, stop in _ZIPPER_TEST_DATA),
    ],
)
def test_untokenize(expr_strings: tuple[str, str], tokens: list[Token], focus_start: int, focus_stop: int):
    focus_indices = range(focus_start, focus_stop)
    focus_tokens = [FocusToken(token, under_focus=i in focus_indices) for i, token in enumerate(tokens)]
    assert untokenize(focus_tokens) == expr_strings

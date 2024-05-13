# AlgeZip

[Github](https://github.com/shape-warrior-t/algezip) | [PyPI](https://pypi.org/project/shape-warrior-t.algezip/)

AlgeZip is a command-line demo program for manipulating boolean expressions.
Apply various axioms from boolean algebra to transform expressions into equivalent expressions.
Choose the subexpression to apply axioms to by moving a "focus" around to navigate the expression.
The navigation system is powered by a [_zipper_](https://en.wikipedia.org/wiki/Zipper_(data_structure)) data structure,
hence the name AlgeZip -- using zippers to manipulate a (boolean) algebraic expression.

`pip install shape-warrior-t.algezip`

The command-line program itself has no external dependencies, but running tests requires pytest.

Once installed, run in the command line with the command `algezip`.

To run tests, just clone the repository and run `pytest` in the proper directory.

Example run, showing the equivalence of two different formulations of XOR:

```
---AlgeZip---
For help, type 'help'

F
^

> help

Focus:
'^' under the current expression denotes the subexpression currently under focus
Use '^', '.', '<', '>' to move focus around (more info under Commands)
Transformations are always applied to the current subexpression under focus

Boolean expression syntax (for giving arguments to 'r!' and 'x'):
F - False, T - True
Single lowercase letters - variables
(!a) - not a, (a & b) - a and b, (a | b) - a or b
No operator precedence -- operations must be explicitly written in brackets
Allowed bracket types (interchangeable, but must be paired correctly): (), [], {}

Commands:
r! a - replace current subexpression under focus with a
^ - move focus to the parent of the current subexpression under focus
. - move focus from (!a) to its only argument a
< - move focus from (a & b) or (a | b) to the left argument a
> - move focus from (a & b) or (a | b) to the right argument b
c - [c]ommutativity -- (a | b) -> (b | a), (a & b) -> (b & a)
i - [i]dentity -- (a | F) -> a, (a & T) -> a
|F - expand via identity -- a -> (a | F)
&T - expand via identity -- a -> (a & T)
d - [d]istributivity -- (a | [b & c]) -> ([a | b] & [a | c]), (a & [b | c]) -> ([a & b] | [a & c])
f - [f]actoring -- ([a | b] & [a | c]) -> (a | [b & c]), ([a & b] | [a & c]) -> (a & [b | c])
v - complements/in[v]erses -- (a | [!a]) -> T, (a & [!a]) -> F
x a - e[x]pand into complements -- T -> (a | [!a]), F -> (a & [!a])
help - print help
q! - quit

F
^

> r! ([a | b] & [{!a} | {!b}])

([a | b] & [{!a} | {!b}])
^^^^^^^^^^^^^^^^^^^^^^^^^

> d

([{a | b} & {!a}] | [{a | b} & {!b}])
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

> <

([{a | b} & {!a}] | [{a | b} & {!b}])
 ^^^^^^^^^^^^^^^^

> c

([{!a} & {a | b}] | [{a | b} & {!b}])
 ^^^^^^^^^^^^^^^^

> d

([{(!a) & a} | {(!a) & b}] | [{a | b} & {!b}])
 ^^^^^^^^^^^^^^^^^^^^^^^^^

> <

([{(!a) & a} | {(!a) & b}] | [{a | b} & {!b}])
  ^^^^^^^^^^

> c

([{a & (!a)} | {(!a) & b}] | [{a | b} & {!b}])
  ^^^^^^^^^^

> v

([F | {(!a) & b}] | [{a | b} & {!b}])
  ^

> ^

([F | {(!a) & b}] | [{a | b} & {!b}])
 ^^^^^^^^^^^^^^^^

> c

([{(!a) & b} | F] | [{a | b} & {!b}])
 ^^^^^^^^^^^^^^^^

> i

([{!a} & b] | [{a | b} & {!b}])
 ^^^^^^^^^^

> c

([b & {!a}] | [{a | b} & {!b}])
 ^^^^^^^^^^

> ^

([b & {!a}] | [{a | b} & {!b}])
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

> >

([b & {!a}] | [{a | b} & {!b}])
              ^^^^^^^^^^^^^^^^

> c

([b & {!a}] | [{!b} & {a | b}])
              ^^^^^^^^^^^^^^^^

> d

([b & {!a}] | [{(!b) & a} | {(!b) & b}])
              ^^^^^^^^^^^^^^^^^^^^^^^^^

> >

([b & {!a}] | [{(!b) & a} | {(!b) & b}])
                            ^^^^^^^^^^

> c

([b & {!a}] | [{(!b) & a} | {b & (!b)}])
                            ^^^^^^^^^^

> v

([b & {!a}] | [{(!b) & a} | F])
                            ^

> ^

([b & {!a}] | [{(!b) & a} | F])
              ^^^^^^^^^^^^^^^^

> i

([b & {!a}] | [{!b} & a])
              ^^^^^^^^^^

> c

([b & {!a}] | [a & {!b}])
              ^^^^^^^^^^

> ^

([b & {!a}] | [a & {!b}])
^^^^^^^^^^^^^^^^^^^^^^^^^

> c

([a & {!b}] | [b & {!a}])
^^^^^^^^^^^^^^^^^^^^^^^^^

> q!

```

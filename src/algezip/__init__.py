"""Package for the AlgeZip command line program. Not meant to be imported directly."""

# Modules:
# interactive - defines the main function for the actual command line program
# data - defines data types for modelling boolean expressions, including zippers for navigation
# actions - defines functions for transforming boolean expressions based on boolean algebra axioms
# source - defines functions for converting between boolean expressions and string representations
#
# Tests:
# test_zipper - tests the zipper data type defined in data.py
# test_actions - tests the transformation functions from actions.py
# test_source - tests (un)tokenization/parsing functions from source.py
#
# External dependencies:
# No external dependencies needed to run the program
# Pytest needed to run tests
#
# Inter-module dependencies (module A --> module B means that module A is imported by module B):
# data --> everything (except __init__)
# actions --> test_actions
# source --> test_source
# actions, source --> interactive
# interactive --> __init__

__all__ = ['main']

from algezip.interactive import main

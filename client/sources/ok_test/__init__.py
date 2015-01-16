from client.sources.ok_test import models
from client.sources.ok_test import doctest
from client.sources.ok_test import concept
import importlib

SUITES = {
    'doctest': doctest.DoctestSuite,
    'concept': concept.ConceptSuite,
}

def load(file):
    """Loads an OK-style test from a specified filepath.

    PARAMETERS:
    file -- str; a filepath to a Python module containing OK-style
            tests.

    RETURNS:
    Test
    """
    _, extension = os.path.splitext(file)
    if not os.path.isfile(file) or not file.endswith('.py'):
        # TODO(albert): standardize exceptions
        raise exceptions.SerializeError('Cannot load non-Python file: ' + file)
    return models.OkTest(SUITES, **get_test(file))


######################
# Public for testing #
######################

def get_test(filepath):
    """Load an OK-style test from a Python module."""
    # TODO(albert): convert filepath to module syntax
    return importlib.import_module(module).test


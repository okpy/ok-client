from client.sources.ok_test import concept
from client.sources.ok_test import doctest
from client.sources.ok_test import models
import importlib
import logging
import os

log = logging.getLogger(__name__)

SUITES = {
    'doctest': doctest.DoctestSuite,
    'concept': concept.ConceptSuite,
}

def load(file, args):
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
        # raise exceptions.SerializeError('Cannot load non-Python file: ' + file)
        log.info('Cannot import {} as an OK test'.format(file))
        raise Exception
    return models.OkTest(SUITES, args.verbose, args.interactive, args.timeout,
                         **get_test(file))


######################
# Public for testing #
######################

def get_test(filepath):
    """Load an OK-style test from a Python module."""
    # TODO(albert): convert filepath to module syntax
    filepath = filepath.replace('.py', '')
    module_components = []
    while filepath:
        filepath, component = os.path.split(filepath)
        module_components.insert(0, component)
    module = '.'.join(module_components)
    return importlib.import_module(module).test


from client.sources.ok_test import concept
from client.sources.ok_test import doctest
from client.sources.ok_test import models
from client.sources.common import importing
import logging
import os

log = logging.getLogger(__name__)

SUITES = {
    'doctest': doctest.DoctestSuite,
    'concept': concept.ConceptSuite,
}

def load(file, parameter, args):
    """Loads an OK-style test from a specified filepath.

    PARAMETERS:
    file -- str; a filepath to a Python module containing OK-style
            tests.

    RETURNS:
    Test
    """
    if not os.path.isfile(file) or not file.endswith('.py'):
        # TODO(albert): standardize exceptions
        log.info('Cannot import {} as an OK test'.format(file))
        raise Exception
    test = importing.load_module(file).test
    return models.OkTest(SUITES, args.verbose, args.interactive, args.timeout,
                         **test)


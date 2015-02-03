from client import exceptions as ex
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
    filename, ext = os.path.splitext(file)
    if not os.path.isfile(file) or ext != '.py':
        log.info('Cannot import {} as an OK test'.format(file))
        raise ex.LoadingException('Cannot import {} as an OK test'.format(file))

    try:
        test = importing.load_module(file).test
    except Exception as e:
        raise ex.LoadingException('Error importing file {}: {}'.format(file, str(e)))

    name = os.path.basename(filename)
    try:
        return {name: models.OkTest(file, SUITES, args.verbose, args.interactive,
                             args.timeout, **test)}
    except ex.SerializeException:
        raise ex.LoadingException('Cannot load OK test {}'.format(file))


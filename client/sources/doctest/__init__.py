from client.sources.common import importing
from client.sources.doctest import models
import logging
import os

log = logging.getLogger(__name__)

def load(file, name, args):
    """Loads doctests from a specified filepath.

    PARAMETERS:
    file -- str; a filepath to a Python module containing OK-style
            tests.

    RETURNS:
    Test
    """
    if not os.path.isfile(file) or not file.endswith('.py'):
        log.info('Cannot import doctests from {}'.format(file))
        # TODO(albert): raise appropriate error
        raise Exception('Cannot import doctests from {}'.format(file))

    module = importing.load_module(file)
    if not hasattr(module, name):
        # TODO(albert): raise appropriate error
        raise Exception('Module {} has no function {}'.format(module.__name__, name))
    func = getattr(module, name)
    if not callable(func):
        # TODO(albert): raise appropriate error
        raise Exception
    return models.Doctest(file, args.verbose, args.interactive, args.timeout,
                          name=name, points=1, docstring=func.__doc__)

from client import exceptions as ex
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
        raise ex.LoadingException('Cannot import doctests from {}'.format(file))

    module = importing.load_module(file)
    if not hasattr(module, name):
        raise ex.LoadingException('Module {} has no function {}'.format(
                                  module.__name__, name))
    func = getattr(module, name)
    if not callable(func):
        raise ex.LoadingException('Attribute {} is not a function'.format(name))
    return models.Doctest(file, args.verbose, args.interactive, args.timeout,
                          name=name, points=1, docstring=func.__doc__)

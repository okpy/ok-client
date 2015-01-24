from client import exceptions as ex
from client.sources.common import importing
from client.sources.doctest import models
import logging
import os
import traceback

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

    try:
        module = importing.load_module(file)
    except Exception:
        # Assume that part of the traceback includes frames from importlib.
        # Begin printing the traceback after the last line involving importlib.
        # TODO(albert): Try to find a cleaner way to do this. Also, might want
        # to move this to a more general place.
        print('Traceback (most recent call last):')
        stacktrace = traceback.format_exc().split('\n')
        start = 0
        for i, line in enumerate(stacktrace):
            if 'importlib' in line:
                start = i + 1
        print('\n'.join(stacktrace[start:]))

        raise ex.LoadingException('Error importing file {}'.format(file))

    if not hasattr(module, name):
        raise ex.LoadingException('Module {} has no function {}'.format(
                                  module.__name__, name))
    func = getattr(module, name)
    if not callable(func):
        raise ex.LoadingException('Attribute {} is not a function'.format(name))
    return models.Doctest(file, args.verbose, args.interactive, args.timeout,
                          name=name, points=1, docstring=func.__doc__)

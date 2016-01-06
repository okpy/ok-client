from client import exceptions as ex
from client.sources.common import importing
from client.sources.doctest import models
import logging
import os
import traceback

log = logging.getLogger(__name__)

def load(file, name, assign):
    """Loads doctests from a specified filepath.

    PARAMETERS:
    file -- str; a filepath to a Python module containing OK-style
            tests.
    name -- str; optional parameter that specifies a particular function in
            the file. If omitted, all doctests will be included.

    RETURNS:
    Test
    """
    if not os.path.isfile(file) or not file.endswith('.py'):
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

    if name:
        return {name: _load_test(file, module, name, assign)}
    else:
        return _load_tests(file, module, assign)


def _load_tests(file, module, assign):
    tests = {}
    for name in dir(module):
        to_test = getattr(module, name)
        if callable(to_test) and to_test.__module__ == module.__name__:
            tests[name] = _load_test(file, module, name, assign)
    return tests

def _load_test(file, module, name, assign):
    namespace = module
    for attr in name.split('.'):
        if not hasattr(namespace, attr):
            raise ex.LoadingException('Module {} has no attribute {}'.format(
                module.__name__, name))
        namespace = getattr(namespace, attr)
    func = namespace

    if not callable(func):
        raise ex.LoadingException('Attribute {} is not a function'.format(name))

    docstring = func.__doc__ if func.__doc__ else ''
    try:
        return models.Doctest(file, assign.cmd_args.verbose, assign.cmd_args.interactive,
                              assign.cmd_args.timeout, name=name, points=1,
                              docstring=docstring)
    except ex.SerializeException:
        raise ex.LoadingException('Unable to load doctest for {} '
                                  'from {}'.format(name, file))


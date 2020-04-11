from client import exceptions as ex
from client.sources.common import importing
from client.sources.lint_test import models
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
        raise ex.LoadingException('Cannot run python linter on {}'.format(file))
    return {name + "_lint" : models.LinterTest(file, name=name + "_lint", points=1)}

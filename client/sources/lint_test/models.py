from client import exceptions as ex
from client.sources.common import core
from client.sources.common import importing
from client.sources.common import interpreter
from client.sources.common import models
from client.sources.common import pyconsole
from client.utils import format
from client.utils import output
import re
import textwrap

import pycodestyle

##########
# Models #
##########

class LinterTest(models.Test):

    def __init__(self, file, **fields):
        super().__init__(**fields)
        self.file = file
        self.styleguide = None

    def post_instantiation(self):
        self.styleguide = pycodestyle.StyleGuide()

    def _lint(self):
        return self.styleguide.check_files([self.file])

    def run(self, env):
        """Runs the suites associated with this doctest.

        NOTE: env is intended only for use with the programmatic API to support
        Python OK tests. It is not used here.

        RETURNS:
        bool; True if the doctest completely passes, False otherwise.
        """
        result = self._lint()
        if result.total_errors == 0:
            return {'passed': 1, 'failed': 0, 'locked': 0}
        else:
            return {'passed': 0, 'failed': 1, 'locked': 0}

    def score(self):
        format.print_line('-')
        print('Lint tests for {}'.format(self.file))
        print()
        success = self._lint().total_errors == 0
        score = 1.0 if success else 0.0

        print('Score: {}/1'.format(score))
        print()
        return score

    def unlock(self, interact):
        """Lint tests cannot be unlocked."""

    def lock(self, hash_fn):
        """Lint tests cannot be locked."""

    def dump(self):
        """Lint tests do not need to be dumped, since no state changes."""

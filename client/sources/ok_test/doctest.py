from client.sources.ok_test import models
from client.sources.common import core
from client.sources.common import doctest_case
import logging

log = logging.getLogger(__name__)

class DoctestSuite(models.Suite):

    cases = core.List()
    setup = core.String(default='')
    teardown = core.String(default='')

    def __init__(self, verbose, interactive, timeout=None, **fields):
        super().__init__(verbose, interactive, timeout, **fields)
        self.console = doctest_case.PythonConsole(verbose, interactive, timeout)

    def post_instantiation(self):
        for i, case in enumerate(self.cases):
            if not isinstance(case, dict):
                # TODO(albert): raise an appropriate error
                raise TypeError
            self.cases[i] = doctest_case.DoctestCase(self.console, self.setup,
                                                     self.teardown, **case)

    def run(self):
        """Runs test for the doctest suite.

        RETURNS:
        bool; True if all cases pass successfully, False otherwise.
        """
        for i, case in enumerate(self.cases):
            log.info('Running case {}'.format(i))
            if case.locked == True:
                log.info('Case {} is locked'.format(i))
                return False  # students must unlock first

            # formatting.underline('Case {}'.format(i + 1), line='-')
            success = case.run()
            if not success:
                return False
        return True

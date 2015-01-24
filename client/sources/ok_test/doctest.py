from client import exceptions as ex
from client.sources.common import core
from client.sources.common import doctest_case
from client.sources.ok_test import models
from client.utils import format
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
                raise ex.SerializeException('Test cases must be dictionaries')
            self.cases[i] = doctest_case.DoctestCase(self.console, self.setup,
                                                     self.teardown, **case)

    def run(self, test_name, suite_number):
        """Runs test for the doctest suite.

        PARAMETERS:
        test_name    -- str; the name of the parent test. Used for printing
                     purposes.
        suite_number -- int; the suite number in relation to the parent test.
                     Used for printing purposes.

        RETURNS:
        dict; results of the following form:
        {
            'passed': int,
            'failed': int,
            'locked': int,
        }
        """
        results = {
            'passed': 0,
            'failed': 0,
            'locked': 0,
        }
        for i, case in enumerate(self.cases):
            log.info('Running case {}'.format(i))

            if case.locked == True or results['locked'] > 0:
                # If a test case is locked, refuse to run any of the subsequent
                # test cases
                log.info('Case {} is locked'.format(i))
                results['locked'] += 1
                continue

            success, output_log = self._run_case(test_name, suite_number,
                                                 case, i + 1)

            if not success or self.verbose:
                print(''.join(output_log))

            if not success and self.interactive:
                self.console.interact()

            if success:
                results['passed'] += 1
            else:
                results['failed'] += 1
        return results

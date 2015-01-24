"""Implements the GradingProtocol, which runs all specified tests
associated with an assignment.

The GradedTestCase interface should be implemented by TestCases that
are compatible with the GradingProtocol.
"""

from client.protocols.common import models
from client.utils import format
import logging

log = logging.getLogger(__name__)

#####################
# Testing Mechanism #
#####################

class GradingProtocol(models.Protocol):
    """A Protocol that runs tests, formats results, and sends results
    to the server.
    """
    def on_interact(self):
        """Run gradeable tests and print results and return analytics.

        RETURNS:
        dict; a mapping of test name -> JSON-serializable object. It is up to
        each test to determine what kind of data it wants to return as
        significant for analytics. However, all tests must include the number
        passed, the number of locked tests and the number of failed tests.
        """
        if self.args.score:
            return

        format.print_line('~')
        print('Running tests')
        print()
        passed = 0
        failed = 0
        locked = 0

        analytics = {}

        for test in self.assignment.specified_tests:
            log.info('Running tests for {}'.format(test.name))
            results = test.run()

            passed += results['passed']
            failed += results['failed']
            locked += results['locked']
            analytics[test.name] = results

        format.print_progress_bar('Test summary', passed, failed, locked)
        return analytics

protocol = GradingProtocol

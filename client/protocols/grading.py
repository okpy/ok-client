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
    name = 'grading'

    def on_interact(self):
        """Run gradeable tests and print results and return analytics.

        For this protocol, analytics consists of a dictionary whose key(s) are
        the questions being tested and the value is the number of test cases
        that they passed.
        """
        if self.args.score:
            return

        format.print_line('~')
        print('Running tests')
        print()

        for test in self.assignment.specified_tests:
            log.info('Running tests for {}'.format(test.name))
            test.run()

        return self.analytics

protocol = GradingProtocol

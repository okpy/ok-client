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
    def run(self, messages):
        """Run gradeable tests and print results and return analytics.

        RETURNS:
        dict; a mapping of test name -> JSON-serializable object. It is up to
        each test to determine what kind of data it wants to return as
        significant for analytics. However, all tests must include the number
        passed, the number of locked tests and the number of failed tests.
        """
        if self.args.score or self.args.export or self.args.unlock or self.args.restore:
            return
        grade(self.assignment.specified_tests, messages, verbose=self.args.verbose)


def grade(questions, messages, env=None, verbose=True):
    format.print_line('~')
    print('Running tests')
    print()
    passed = 0
    failed = 0
    locked = 0

    analytics = {}
    # Check if analytics info is in messages.
    if 'analytics' in messages:
        started = messages['analytics']['started']
    else:
        started = None

    # The environment in which to run the tests.
    for test in questions:
        # run test if the question is not detected, or question detected and started
        if (started is None
            or test.name not in started
            or started[test.name]):

            log.info('Running tests for {}'.format(test.name))
            results = test.run(env)
            passed += results['passed']
            failed += results['failed']
            locked += results['locked']
            analytics[test.name] = results
        else:
            print('It looks like you haven\'t started {}. Skipping the tests.'.format(test.name))
            print()

        if not verbose and (failed > 0 or locked > 0):
            # Stop at the first failed test
            break

    format.print_progress_bar('Test summary', passed, failed, locked,
                              verbose=verbose)
    print()

    messages['grading'] = analytics

protocol = GradingProtocol

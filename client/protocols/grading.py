"""Implements the GradingProtocol, which runs all specified tests
associated with an assignment.

The GradedTestCase interface should be implemented by TestCases that
are compatible with the GradingProtocol.
"""

from client.protocols.common import models
from client.utils import formatting

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
        # formatting.print_title('Running tests for {}'.format(
        #     self.assignment['name']))
        for test in self._get_tests():
            # formatting.underline('Running tests for ' + test.name)
            # print()
            test.run()

            # if test.num_locked > 0:
            #     print('-- There are still {} locked test cases.'.format(
            #         test.num_locked) + ' Use the -u flag to unlock them. --')

            self.analytics[test.name] = passed
            # if total > 0:
            #     print('-- {} cases passed ({}%) for {} --'.format(
            #         passed, round(100 * passed / total, 2), test.name))
            # print()
        if not any_graded and self.args.question:
            # print('Test {} does not exist. Try one of the following:'.format(
            #     self.args.question))
            # print(' '.join(sorted(test.name for test in self.assignment.tests)))
            pass
        return self.analytics

    def _get_tests():
        # TODO(albert): implement a fuzzy matching for tests
        pass


protocol = GradingProtocol

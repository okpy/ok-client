"""Implements the ScoringProtocol, which runs all specified tests
associated with an assignment.
"""

from client.sources.common import core
from client.protocols.common import models
from client.utils import formatting
from collections import OrderedDict

#####################
# Testing Mechanism #
#####################

class ScoringProtocol(models.Protocol):
    """A Protocol that runs tests, formats results, and reports a
    student's score.
    """
    name = 'scoring'

    def on_interact(self):
        """Run gradeable tests and print results."""
        if not self.args.score:
            return
        # formatting.print_title('Scoring tests for {}'.format(
        #     self.assignment['name']))
        self.scores = OrderedDict()
        for test in self._get_tests():
            # formatting.underline('Scoring tests for ' + test.name)
            # print()
            partner = test.partner if test.partner != core.NoValue else None
            self.scores[test.name, test.partner] = (test.score(), test.points)
        display_breakdown(self.scores)

    def _get_tests():
        # TODO(albert): implement a fuzzy matching for tests
        pass

def display_breakdown(scores):
    """Prints the point breakdown given a dictionary of scores.

    RETURNS:
    int; the total score for the assignment
    """
    partner_totals = {}

    # formatting.underline('Point breakdown')
    for (name, partner), (score, total) in scores.items():
        # print(name + ': ' + '{}/{}'.format(score, total))
        partner_totals[partner] = partner_totals.get(partner, 0) + score
    # print()
    shared_points = partner_totals.get(None, 0)
    if None in partner_totals:
        del partner_totals[None]

    if len(partner_totals) == 0:
        # If only one partner.
        # print('Total score:')
        # print(shared_points)
        pass
    else:
        for partner, score in sorted(partner_totals.items()):
            # print('Partner {} score:'.format(partner))
            # print(score + shared_points)

    return partner_totals

protocol = ScoringProtocolm

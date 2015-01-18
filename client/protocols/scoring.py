"""Implements the ScoringProtocol, which runs all specified tests
associated with an assignment.
"""

from client.sources.common import core
from client.protocols.common import models
from client.utils import format
from collections import OrderedDict
import logging

log = logging.getLogger(__name__)

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

        format.print_line('~')
        print('Scoring tests')
        print()

        self.scores = OrderedDict()
        for test in self.assignment.specified_tests:
            log.info('Scoring test {}'.format(test.name))
            partner = test.partner if test.partner != core.NoValue else None
            self.scores[test.name, partner] = (test.score(), test.points)
        display_breakdown(self.scores)

def display_breakdown(scores):
    """Prints the point breakdown given a dictionary of scores.

    RETURNS:
    int; the total score for the assignment
    """
    partner_totals = {}

    format.print_line('-')

    print('Point breakdown')
    for (name, partner), (score, total) in scores.items():
        print('    {}: {}/{}'.format(name, score, total))
        partner_totals[partner] = partner_totals.get(partner, 0) + score
    print()

    shared_points = partner_totals.get(None, 0)
    if None in partner_totals:
        del partner_totals[None]

    print('Score')
    if len(partner_totals) == 0:
        # If only one partner.
        print('    {}'.format(shared_points))
    else:
        for partner, score in sorted(partner_totals.items()):
            print('    Partner {}: {}'.format(partner, score + shared_points))

protocol = ScoringProtocol

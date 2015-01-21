"""Implements the ScoringProtocol, which runs all specified tests
associated with an assignment.
"""

from client.sources.common import core
from client.sources.common import models as sources_models
from client.protocols.common import models as protocol_models
from client.utils import format
from collections import OrderedDict
import logging

log = logging.getLogger(__name__)

#####################
# Testing Mechanism #
#####################

class ScoringProtocol(protocol_models.Protocol):
    """A Protocol that runs tests, formats results, and reports a
    student's score.
    """
    def on_interact(self):
        """Score tests and print results

        Tests are taken from self.assignment.specified_tests. Each test belongs
        to a partner. If test.partner is omitted (i.e. core.NoValue), the score
        for that test is added to every partner's score.

        RETURNS
        dict; mapping of partner (int) -> finalized scores (float).

        If there are no tests, the mapping will only contain one entry, mapping
        (partner) 0 -> 0 (total score).

        If there are no partners specified by the tests, the mapping will only
        contain one entry, mapping (partner) 0 -> total score (float). This
        assumes there is always at least one partner.
        """
        if not self.args.score:
            return

        format.print_line('~')
        print('Scoring tests')
        print()

        raw_scores = OrderedDict()
        for test in self.assignment.specified_tests:
            assert isinstance(test, sources_models.Test), 'ScoringProtocol received invalid test'

            log.info('Scoring test {}'.format(test.name))
            partner = test.partner if test.partner != core.NoValue else None
            raw_scores[test.name, partner] = (test.score(), test.points)

        return display_breakdown(raw_scores)

def display_breakdown(scores):
    """Prints the point breakdown given a dictionary of scores.

    RETURNS:
    dict; maps partner (int) -> finalized score (float)
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

    finalized_scores = {}
    print('Score')
    if len(partner_totals) == 0:
        # Add partner 0 as only partner.
        partner_totals[0] = 0
    for partner, score in sorted(partner_totals.items()):
        print('    Partner {}: {}'.format(partner, score + shared_points))
        finalized_scores[partner] = score + shared_points
    return finalized_scores

protocol = ScoringProtocol

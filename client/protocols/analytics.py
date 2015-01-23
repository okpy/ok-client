"""Implements the AnalyticsProtocol, which keeps track of configuration
for the ok grading session.
"""

from client.protocols.common import models
from datetime import datetime

# TODO(albert): rename this InformationProtocol
# Add all command line arguments here

class AnalyticsProtocol(models.Protocol):
    """A Protocol that analyzes how much students are using the autograder.
    """
    name = 'analytics'

    def on_start(self):
        """
        Returns some analytics about this autograder run.
        """
        statistics = {}
        statistics['time'] = str(datetime.now())
        statistics['unlock'] = self.args.unlock

        if self.args.question:
            # TODO(denero) Get the canonical name of the question
            statistics['question'] = self.args.question

        return statistics

protocol = AnalyticsProtocol

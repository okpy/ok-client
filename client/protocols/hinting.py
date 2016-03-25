"""Implements the HintProtocol, which generates hints for students
that are stuck on a coding question. The protocol uses analytics
to determine whether a hint should be given and then
obtains them from the hint generation server. Free response questions
are posed before and after hints are provided.
"""

from client.sources.common import core
from client.sources.common import models as sources_models
from client.protocols.common import models as protocol_models
from client.utils import format

import logging
import os
import pickle
import re
import urllib.error
import urllib.request

log = logging.getLogger(__name__)

#####################
# Hinting Mechanism #
#####################

class HintingProtocol(protocol_models.Protocol):
    """A protocol that provides rubber duck debugging and hints if applicable.
    """

    HINT_SERVER = "https://hintgen.cs61a.org/"

    def run(self, messages):
        """Determine if a student is elgible to recieve a hint. Based on their
        state, poses reflection questions.

        After more attempts, ask if students would like hints. If so, query
        the server.
        """
        if self.args.local:
            return
        # TODO: Handle cases when no questions are specified
        if not self.args.question:
            return

        if 'analytics' not in messages:
            log.info('Analytics Protocol is required for hint generation')
            return
        if 'file_contents' not in messages:
            log.info('File Contents needed to generate hints')
            return

        if not confirm("Check for hints?"):
            return



    def query_server(self, messages, test):
        data = {
            'assignment': self.assignment.endpoint,
            'test': test,
            'messages': messages,
        }
        serialized_data = json.dumps(data).encode(encoding='utf-8')

        address = self.HINT_SERVER

        log.info('Sending hint request to %s', address)
        request = urllib.request.Request(address)



def confirm(message):
    response = input("{} [yes/no]: ".format(message))
    return response.lower() == "yes" or response.lower() == "y"

protocol = HintingProtocol

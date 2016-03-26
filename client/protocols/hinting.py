"""Implements the HintProtocol, which generates hints for students
that are stuck on a coding question. The protocol uses analytics
to determine whether a hint should be given and then
obtains them from the hint generation server. Free response questions
are posed before and after hints are provided.
"""

from client.sources.common import core
from client.sources.common import models as sources_models
from client.protocols.common import models as protocol_models
from client.utils import auth
from client.utils import format

import json
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

    HINT_SERVER = "http://146.148.59.194:5000/"
    HINT_ENDPOINT = 'api/hints'

    def run(self, messages):
        """Determine if a student is elgible to recieve a hint. Based on their
        state, poses reflection questions.

        After more attempts, ask if students would like hints. If so, query
        the server.
        """
        if self.args.local:
            return

        if 'analytics' not in messages:
            log.info('Analytics Protocol is required for hint generation')
            return
        if 'file_contents' not in messages:
            log.info('File Contents needed to generate hints')
            return

        messages['hinting'] = {}
        history = messages['analytics']['history']
        questions = history['questions']
        current_q = history['question']

        for question in current_q:
            if question not in questions:
                continue
            stats = questions[question]
            messages['hinting'][question] = {'prompts': {}}
            hint_info = messages['hinting'][question]

            if (stats['solved'] or stats['attempts'] < 5):
                log.info("Question %s is not elgible: Attempts: %s, Solved: %s",
                         question, stats['attempts'], stats['solved'])
                hint_info['elgible'] = False
                continue
            else:
                hint_info['elgible'] = True

            log.info('Prompting for hint on %s', question)
            if confirm("Check for hints on {}?".format(question)):
                hint_info['accept'] = True
                try:
                    response = self.query_server(messages, question)
                    hint_info['response'] = response

                    hint = response['message']
                    pre_prompt = response['pre-prompt']
                    post_prompt = response['post-prompt']
                    if not hint and not pre_prompt:
                        print("No hints found for {}".format(question))
                        continue

                    if pre_prompt:
                        print("-- While the computer fetches a hint --")
                        if not prompt_user(pre_prompt, hint_info):
                            continue

                    print(hint)
                    print()

                    if post_prompt:
                        prompt_user(post_prompt, hint_info)

                except urllib.error.URLError:
                    log.debug("Network error while fetching hint")
                    hint_info['fetch_error'] = True
                    print("Could not get a hint.")
            else:
                log.info('Declined Hints for %s', question)
                hint_info['accept'] = False

    def query_server(self, messages, test):
        access_token, _, _ = auth.get_storage()
        user = auth.get_student_email(access_token) or access_token
        if user:
            user = hash(user)
        data = {
            'assignment': self.assignment.endpoint,
            'test': test,
            'messages': messages,
            'user': user
        }
        serialized_data = json.dumps(data).encode(encoding='utf-8')

        address = self.HINT_SERVER + self.HINT_ENDPOINT

        log.info('Sending hint request to %s', address)
        request = urllib.request.Request(address)
        request.add_header("Content-Type", "application/json")

        response = urllib.request.urlopen(request, serialized_data, 5)
        return json.loads(response.read().decode('utf-8'))

def prompt_user(query, results):
    try:
        response = input("{} :".format(query))
        results['prompts'][query] = response
        return response
    except KeyboardInterrupt:
        # Hack for windows:
        results['prompts'][query] = 'KeyboardInterrupt'
        try:
            print("Exiting Hint") # Second I/O will get KeyboardInterrupt
            return ''
        except KeyboardInterrupt:
            return ''

def confirm(message):
    response = input("{} [yes/no]: ".format(message))
    return response.lower() == "yes" or response.lower() == "y"

protocol = HintingProtocol

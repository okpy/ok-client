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
import random
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

    HINT_SERVER = "https://hinting.cs61a.org/"
    HINT_ENDPOINT = 'api/hints'
    SMALL_EFFORT = 5
    LARGE_EFFORT = 8
    WAIT_ATTEMPTS = 5

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

        if self.args.no_hints:
            messages['hinting'] = {'disabled': 'user'}
            return

        messages['hinting'] = {}
        history = messages['analytics'].get('history', {})
        questions = history.get('questions', [])
        current_q = history.get('question', {})


        for question in current_q:
            if question not in questions:
                continue
            stats = questions[question]
            messages['hinting'][question] = {'prompts': {}, 'reflection': {}}
            hint_info = messages['hinting'][question]

            # Determine a users elgibility for a prompt

            # If the user just solved this question, provide a reflection prompt
            if stats['solved'] and stats['attempts'] > self.SMALL_EFFORT:
                hint_info['elgible'] = False
                if self.args.question:
                    # Only prompt for reflection with question specified.
                    log.info('Giving reflection response on %s', question)
                    reflection = random.choice(SOLVE_SUCCESS_MSG)
                    if not confirm("Nice work! Could you answer a quick question"
                                   " about how you approached this question?"):
                        hint_info['reflection']['accept'] = False
                    else:
                        hint_info['reflection']['accept'] = True
                        prompt_user(reflection, hint_info)
            elif stats['attempts'] < self.SMALL_EFFORT:
                log.info("Question %s is not elgible: Attempts: %s, Solved: %s",
                         question, stats['attempts'], stats['solved'])
                hint_info['elgible'] = False
            else:
                # Only prompt every WAIT_ATTEMPTS attempts to avoid annoying user
                if stats['attempts'] % self.WAIT_ATTEMPTS != 0:
                    hint_info['disabled'] = 'timer'
                    hint_info['elgible'] = False
                    log.info('Waiting for %d more attempts before prompting',
                             stats['attempts'] % self.WAIT_ATTEMPTS)
                else:
                    hint_info['elgible'] = not stats['solved']

            if not hint_info['elgible']:
                continue

            log.info('Prompting for hint on %s', question)

            if confirm("Check for hints on {}?".format(question)):
                hint_info['accept'] = True
                print("Thinking... (could take up to 15 seconds)")
                try:
                    response = self.query_server(messages, question)
                    hint_info['response'] = response

                    hint = response['message']
                    pre_prompt = response['pre-prompt']
                    post_prompt = response['post-prompt']
                    log.info("Hint server response: {}".format(response))
                    if not hint and not pre_prompt:
                        print("Sorry. No hints found for {}".format(question))
                        continue

                    if pre_prompt:
                        print("-- Before the hint, respond to this question."
                              " When you are done typing, press Enter. --")
                        if not prompt_user(pre_prompt, hint_info):
                            # Do not provide hint, if no response from user
                            continue

                    # Provide padding for the the hint
                    print("\n{}\n".format(hint))

                    if post_prompt:
                        prompt_user(post_prompt, hint_info)

                except urllib.error.URLError:
                    log.debug("Network error while fetching hint")
                    hint_info['fetch_error'] = True
                    print("\r\nCould not get a hint.")
            else:
                log.info('Declined Hints for %s', question)
                hint_info['accept'] = False

    def query_server(self, messages, test):
        access_token, _, _ = auth.get_storage()
        user = auth.get_student_email(access_token) or access_token
        if user:
            # The hinting server should not recieve identifying information
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

        response = urllib.request.urlopen(request, serialized_data, 10)
        return json.loads(response.read().decode('utf-8'))

def prompt_user(query, results):
    try:
        response = None
        short_respones = 0
        while not response:
            response = input("{}\nYour Response: ".format(query))
            if not response or len(response) < 5:
                short_respones += 1
                # Do not ask more than twice to avoid annoying the user
                if short_respones > 2:
                    break
                print("Please enter at least a sentence.")
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

SOLVE_SUCCESS_MSG = [
    "If another student had the same error on this question, what advice would you give them?",
    "What did you learn from writing this program about things that you'll continue to do in the future?",
    "What difficulties did you encounter in understanding the problem?",
    "What difficulties did you encounter in designing the program?",
]

protocol = HintingProtocol

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
            messages['hinting'][question] = {'prompts': {}, 'reflection': {}}
            hint_info = messages['hinting'][question]

            # Only prompt
            if (stats['solved'] and stats['attempts'] > 6):
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
            elif (stats['attempts'] < 5):
                log.info("Question %s is not elgible: Attempts: %s, Solved: %s",
                         question, stats['attempts'], stats['solved'])
                hint_info['elgible'] = False
            else:
                hint_info['elgible'] = not stats['solved']

            if not hint_info['elgible']:
                continue
            log.info('Prompting for hint on %s', question)

            if confirm("Check for hints on {}?".format(question)):
                hint_info['accept'] = True
                print("Thinking... (could take upto 15 seconds)", end='')
                try:
                    response = self.query_server(messages, question)
                    hint_info['response'] = response

                    hint = response['message']
                    pre_prompt = response['pre-prompt']
                    post_prompt = response['post-prompt']
                    log.info("Hint server response: {}".format(response))
                    if not hint and not pre_prompt:
                        print("\nSorry. No hints found for {}".format(question))
                        continue

                    if pre_prompt:
                        print("\r-- While we wait, respond to this question."
                              " When you are done typing, press Enter.")
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
        short_resps = 0
        while not response or response == '':
            response = input("{}\nYour Response: ".format(query))
            if not response or response == '':
                short_resps += 1
                if short_resps > 2:
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

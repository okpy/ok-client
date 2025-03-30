"""61A-bot.

Spring 2025 feature with larynqi@, zamfi@, norouzi@, denero@
"""

from client.protocols.common import models
from client.utils import config as config_utils
from client.utils import format

import os
import logging
import json

from client.utils.printer import print_error

from client.protocols.unlock import UnlockProtocol

log = logging.getLogger(__name__)

class FollowupProtocol(models.ResearchProtocol, UnlockProtocol):

    PROTOCOL_NAME = 'followup'
    FOLLOWUP_ENDPOINT = models.ResearchProtocol.SERVER + '/questions'
    GET_CONSENT = True
    FOLLOWUPS_FILE = 'followups.json'

    def run(self, messages):
        config = config_utils._get_config(self.args.config)

        if self.PROTOCOL_NAME not in config.get('protocols', []):
            return

        check_solved = self._check_solved(messages)
        failed, active_function = check_solved['failed'], check_solved['active_function']
        if failed:
            return
        
        if self.FOLLOWUPS_FILE not in os.listdir():
            followup_data = []
        else:
            followup_data = json.loads(open(self.FOLLOWUPS_FILE).read())
        followup_queue = []
        for entry in followup_data:
            if entry['name'] == active_function:
                for followup in entry['followups']:
                    if not followup['response']:
                        followup_queue.append(followup)
        if len(followup_queue) > 0:
            format.print_line('~')
            print('Follow-up questions')
            print()

            print('At each "{}", type what you think the best answer is. YOUR ANSWERS WILL NOT BE GRADED'.format(
                self.PROMPT))
            print('Type {} to quit'.format(self.EXIT_INPUTS[0]))
            print()

        
        for followup in followup_queue:
            response = self._ask_followup(followup)
            followup['response'] = response

        with open(self.FOLLOWUPS_FILE, 'w') as f:
            f.write(json.dumps(followup_data, indent=2))

    def _ask_followup(self, followup):
        question, choices = followup['question'], followup['choices']
        print(question)
        print()
        for c in choices:
            print(c)
        print()
        valid_responses = [chr(ord('A') + i) for i in range(len(choices))] + [chr(ord('a') + i) for i in range(len(choices))] + list(self.EXIT_INPUTS)
        response = None
        while response not in valid_responses:
            response = input(self.PROMPT)
            if response not in valid_responses:
                print("-- Please select a provided option. --\n")

        if response not in self.EXIT_INPUTS:
            print(f'LOG: received {response.upper()} from student')
            return response.upper()

protocol = FollowupProtocol

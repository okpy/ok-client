"""61A-bot.

Spring 2025 feature with larynqi@, zamfi@, norouzi@, denero@
"""

from client.protocols.common import models
from client.utils import config as config_utils
from client.utils import format

import os
import logging
import json
import re
import requests
import hmac
import pickle

from urllib.parse import urlencode

from client.utils.printer import print_error

from client.protocols.unlock import UnlockProtocol

log = logging.getLogger(__name__)

class FollowupProtocol(models.ResearchProtocol, UnlockProtocol):

    PROTOCOL_NAME = 'followup'
    FOLLOWUP_ENDPOINT = models.ResearchProtocol.SERVER + '/successQuestions?'
    RESPONSE_ENDPOINT = models.ResearchProtocol.SERVER + '/successQuestionsResponse'
    GET_CONSENT = True
    FOLLOWUP_CACHE = '.ok_followups'

    def run(self, messages):
        config = config_utils._get_config(self.args.config)

        if self.PROTOCOL_NAME not in config.get('protocols', []):
            return

        check_solved = self._check_solved(messages)
        failed, _ = check_solved['failed'], check_solved['active_function']
        if failed:
            return
        
        email = messages.get('email') or self.UNKNOWN_EMAIL
        responded_followups = self._get_followups(email)
        followup_queue = []
        for question_id, analytic in messages.get('grading', {}).items():
            if analytic['failed'] == 0 and question_id not in responded_followups:
                followup_queue.append(question_id)

        consent = None
        if len(followup_queue) > 0:
            consent = self._get_consent(email)
            format.print_line('~')
            print('Follow-up questions')
            print()

            print('At each "{}", type what you think the best answer is. YOUR ANSWERS WILL NOT BE GRADED'.format(
                self.PROMPT))
            print('Type {} to quit'.format(self.EXIT_INPUTS[0]))
            print()
        
        filename = config['src'][0]
        hw_id = str(int(re.findall(r'hw(\d+)\.(py|scm|sql)', filename)[0][0]))
        for q_id in followup_queue:
            params = {
                'hwId': hw_id,
                'questionId': q_id,
            }
            server_response = requests.get(self.FOLLOWUP_ENDPOINT + urlencode(params))
            if server_response.status_code == 200:
                followup = server_response.json()
                response_data = self._ask_followup(followup)
                if response_data:
                    payload = {
                        'email': email,
                        'consent': consent,
                        'hwId': hw_id,
                        'activeFunction': q_id,
                        'responseIndex': response_data.get('response_index', None),
                        'responseText': response_data.get('response_text', None)
                    }
                    try:
                        server_response = requests.post(self.RESPONSE_ENDPOINT, json=payload).json()
                        if server_response.get('status', '') != 'ok':
                            print_error("Error reaching 61a-bot server. Please inform the course staff on Ed and try again later.")
                        else:
                            self._append_followups(email, q_id)
                    except Exception as e:
                        print_error("Error reaching 61a-bot server. Please inform the course staff on Ed and try again later.")
                else:
                    break

    def _ask_followup(self, followup):
        question, choices = followup['question'], followup['choices']
        print(question)
        print()
        for i, c in enumerate(choices):
            print(f"{chr(ord('A') + i)}. {c}")
        print()
        valid_responses = [chr(ord('A') + i) for i in range(len(choices))] + [chr(ord('a') + i) for i in range(len(choices))] + list(self.EXIT_INPUTS)
        response = None
        while response not in valid_responses:
            response = input(self.PROMPT)
            if response not in valid_responses:
                print("-- Please select a provided option. --\n")

        if response not in self.EXIT_INPUTS:
            print(f'LOG: received {response.upper()} from student')
            response_index = ord(response.upper()) - ord('A')
            response_text = choices[response_index]
            return {
                'response_index': response_index,
                'response_text': response_text
            }
        return {}
    
    def _get_followups(self, email):
        if self.FOLLOWUP_CACHE in os.listdir():
            try:
                with open(self.FOLLOWUP_CACHE, 'rb') as f:
                    data = pickle.load(f)
                    if not hmac.compare_digest(data.get('mac'), self._mac(email, data.get('followups', []))):
                        os.remove(self.FOLLOWUP_CACHE)
                        return self._get_context(email)
                return data.get('followups', [])
              
            except:
                os.remove(self.FOLLOWUP_CACHE)
                return self._get_context(email)
        else:
            return []
    
    def _append_followups(self, email, responded):
        followups = self._get_followups(email)
        followups.append(responded)
        with open(self.FOLLOWUP_CACHE, 'wb') as f:
            pickle.dump({'followups': followups, 'mac': self._mac(email, followups)}, f, protocol=pickle.HIGHEST_PROTOCOL)

protocol = FollowupProtocol

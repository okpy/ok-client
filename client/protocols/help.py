"""61A Helper Bot.

Fall 2023 research project with zamfi@, larynqi@, norouzi@, denero@
"""

from client.protocols.common import models
from client.utils import config as config_utils

import requests
import random

import itertools
import threading
import time
import sys
import re
import os
import pickle
import hmac

from client.utils.printer import print_error

class HelpProtocol(models.Protocol):

    SERVER = 'https://61a-bot-backend.zamfi.net'
    HELP_ENDPOINT = SERVER + '/get-help-cli'
    FEEDBACK_PROBABILITY = 1
    FEEDBACK_REQUIRED = False
    FEEDBACK_ENDPOINT = SERVER + '/feedback'
    FEEDBACK_KEY = 'jfv97pd8ogybhilq3;orfuwyhiulae'
    FEEDBACK_MESSAGE = "The hint was... (Hit Enter to skip)\n1) Helpful, all fixed\n2) Helpful, not all fixed\n3) Not helpful, but made sense\n4) Not helpful, didn't make sense\n5) Misleading/Wrong\n"
    FEEDBACK_OPTIONS = set([str(i) for i in range(1, 6)])
    HELP_TYPE_MESSAGE = "\nThe hint could have included...\n1) More debugging\n2) An example\n3) Template code\n4) Conceptual refresher\n5) More info\n"
    HELP_TYPE_OPTIONS = set([str(i) for i in range(1, 6)])
    HELP_OPTIONS = {"y", "yes"}
    HELP_KEY = 'jfv97pd8ogybhilq3;orfuwyhiulae'
    AG_PREFIX = "————————————————————————\nThe following is an automated report from an autograding tool that may indicate a failed test case or a syntax error. Consider it in your response.\n\n"
    GET_CONSENT = True
    CONSENT_CACHE = '.ok_consent'
    NO_CONSENT_OPTIONS = {"n", "no", "0", "-1", }
    CONSENT_MESSAGE = "Can we collect your de-identified data for research directed by Prof. Narges Norouzi (EECS faculty member unaffiliated with this course)? Your consent is voluntary and does not affect your ability to use this tool or your course grade. For more information visit https://cs61a.org/articles/61a-bot\n\nYou can change your response at any time by running `python3 ok --consent`."
    CONTEXT_CACHE = '.ok_context'
    CONTEXT_LENGTH = 3

    def run(self, messages):
        config = config_utils._get_config(self.args.config)
        if 'help' not in config.get('protocols', []):
            return
        tests = self.assignment.specified_tests
        grading_analytics = messages.get('grading', {})
        failed = False
        active_function = tests[-1].name
        for test in tests:
            name = test.name
            if name in grading_analytics and grading_analytics[name]['failed'] > 0:
                failed = True
                active_function = name
                break

        get_help = self.args.get_help
        help_payload = None

        if (failed or get_help) and (config.get('src', [''])[0][:2] == 'hw'):
            res = input("Would you like to receive 61A-bot feedback on your code (y/N)? ").lower()
            print()
            if res in self.HELP_OPTIONS:
                filename = config['src'][0]
                code = open(filename, 'r').read()
                autograder_output = messages.get('autograder_output', '')
                email = messages.get('email') or '<unknown from CLI>'
                consent = self._get_consent(email)
                context = self._get_context(email)
                curr_message = {'role': 'user', 'content': code}
                help_payload = {
                    'email': email,
                    'promptLabel': 'Get_help',
                    'hwId': re.findall(r'hw(\d+)\.(py|scm|sql)', filename)[0][0],
                    'activeFunction': active_function,
                    'code': code if len(context) == 0 else '',
                    'codeError': self.AG_PREFIX + autograder_output,
                    'version': 'v2',
                    'key': self.HELP_KEY,
                    'consent': consent,
                    'messages': context + [curr_message]
                }

        if help_payload:
            help_response = None
            def animate():
                for c in itertools.cycle(["|", "/", "-", "\\"]):
                    if help_response:
                        break
                    sys.stdout.write("\rLoading " + c + " ")
                    sys.stdout.write('\033[2K\033[1G')
                    time.sleep(0.1)
            t = threading.Thread(target=animate)
            t.daemon = True
            t.start()
            try:
                help_response = requests.post(self.HELP_ENDPOINT, json=help_payload).json()
            except Exception as e:
                print_error("Error generating hint. Please try again later.")
                return
            if 'output' not in help_response:
                print_error("An error occurred. Please try again later.")
                return

            hint = help_response.get('output')
            print(hint)
            print()

            self._append_context(email, curr_message)
            self._append_context(email, {'role': 'assistant', 'content': hint})

            random.seed(int(time.time()))
            if random.random() < self.FEEDBACK_PROBABILITY:
                time.sleep(1)
                self._get_feedback(help_response.get('requestId'))

    def _get_feedback(self, req_id):
        print(self.FEEDBACK_MESSAGE)
        feedback = input("? ")
        if feedback in self.FEEDBACK_OPTIONS:
            if feedback == "3":
                print(self.HELP_TYPE_MESSAGE)
                help_type = None
                while help_type not in self.HELP_TYPE_OPTIONS:
                    if help_type is None:
                        help_type = input("? ")
                    else:
                        help_type = input("-- Please select a provided option. --\n? ")

                feedback += ',' + help_type

            print("\nThank you for your feedback.\n")

        else:
            feedback = 0
            print()

        if req_id:
            feedback_payload = {
                'version': 'v2',
                'key': self.FEEDBACK_KEY,
                'requestId': req_id,
                'feedback': feedback
            }
            feedback_response = requests.post(self.FEEDBACK_ENDPOINT, json=feedback_payload).json()
            return feedback_response.get('status')

    def _get_binary_feedback(self, req_id):
        skip_str = ' Hit Enter to skip.' if not self.FEEDBACK_REQUIRED else ''
        print(f"Please indicate whether the feedback you received was helpful or not.{skip_str}")
        print("1) It was helpful.")
        print("-1) It was not helpful.")
        feedback = None
        if self.FEEDBACK_REQUIRED:
            while feedback not in {"1", "-1"}:
                if feedback is None:
                    feedback = input("? ")
                else:
                    feedback = input("-- Please select a provided option. --\n? ")
        else:
            feedback = input("? ")
            if feedback not in {"1", "-1"}:
                print()
                return
        print("\nThank you for your feedback.\n")
        
        if req_id:
            feedback_payload = {
                'version': 'v2',
                'key': self.FEEDBACK_KEY,
                'requestId': req_id,
                'feedback': feedback
            }
            feedback_response = requests.post(self.FEEDBACK_ENDPOINT, json=feedback_payload).json()
            return feedback_response.get('status')

    def _mac(self, key, value):
        mac = hmac.new(key.encode('utf-8'), digestmod='sha512')
        mac.update(repr(value).encode('utf-8'))
        return mac.hexdigest()
        
    def _get_consent(self, email):
        if self.GET_CONSENT:
            if self.CONSENT_CACHE in os.listdir() and not self.args.consent:
                try:
                    with open(self.CONSENT_CACHE, 'rb') as f:
                        data = pickle.load(f)
                        if not hmac.compare_digest(data.get('mac'), self._mac(email, data.get('consent'))):
                            os.remove(self.CONSENT_CACHE)
                            return self._get_consent(email)
                    return data.get('consent')
                except:
                    os.remove(self.CONSENT_CACHE)
                    return self._get_consent(email)
            else:
                print(self.CONSENT_MESSAGE)
                res = input("\n(Y/n)? ").lower()
                consent = res not in self.NO_CONSENT_OPTIONS
                if consent:
                    print("\nYou have consented.\n")
                else:
                    print("\nYou have not consented.\n")
                with open(self.CONSENT_CACHE, 'wb') as f:
                    pickle.dump({'consent': consent, 'mac': self._mac(email, consent)}, f, protocol=pickle.HIGHEST_PROTOCOL)
                return consent
        else:
            return False

    def _get_context(self, email, full=False):
        if self.CONTEXT_CACHE in os.listdir():
            try:
                with open(self.CONTEXT_CACHE, 'rb') as f:
                    data = pickle.load(f)
                    if not hmac.compare_digest(data.get('mac'), self._mac(email, data.get('context', []))):
                        os.remove(self.CONTEXT_CACHE)
                        return self._get_context(email)
                if full:
                    return data.get('context', [])
                else:
                    return data.get('context', [])[-(self.CONTEXT_LENGTH * 2):]
            except:
                os.remove(self.CONTEXT_CACHE)
                return self._get_context(email)
        else:
            return []
    
    def _append_context(self, email, message):
        context = self._get_context(email, full=True)
        context.append(message)
        with open(self.CONTEXT_CACHE, 'wb') as f:
            pickle.dump({'context': context, 'mac': self._mac(email, context)}, f, protocol=pickle.HIGHEST_PROTOCOL)

protocol = HelpProtocol

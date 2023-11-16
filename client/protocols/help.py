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

from client.utils.printer import print_error

class HelpProtocol(models.Protocol):

    SERVER = 'https://61a-bot-backend.zamfi.net'
    HELP_ENDPOINT = SERVER + '/get-help-cli'
    FEEDBACK_PROBABILITY = 1
    FEEDBACK_REQUIRED = True
    FEEDBACK_ENDPOINT = SERVER + '/feedback'
    FEEDBACK_KEY = 'jfv97pd8ogybhilq3;orfuwyhiulae'
    HELP_KEY = 'jfv97pd8ogybhilq3;orfuwyhiulae'
    AG_PREFIX = "————————————————————————\nThe following is an automated report from an autograding tool that may indicate a failed test case or a syntax error. Consider it in your response.\n\n"

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

        autograder_output = messages.get('autograder_output', '')
        get_help = self.args.get_help
        help_payload = None

        if (failed or get_help) and (config.get('src', [''])[0][:2] == 'hw'):
            res = input("Would you like to receive 61A-bot feedback on your code (y/N)? ")
            print()
            if res == "y":
                filename = config['src'][0]
                code = open(filename, 'r').read()
                help_payload = {
                    'email': messages.get('email') or '<unknown from CLI>',
                    'promptLabel': 'Get_help',
                    'hwId': re.findall(r'hw(\d+)\.(py|scm|sql)', filename)[0][0],
                    'activeFunction': active_function,
                    'code': code,
                    'codeError': self.AG_PREFIX + autograder_output,
                    'version': 'v2',
                    'key': self.HELP_KEY
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
            print(help_response.get('output', "An error occurred. Please try again later."))
            print()

            random.seed(int(time.time()))
            if random.random() < self.FEEDBACK_PROBABILITY:
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
                req_id = help_response.get('requestId')
                if req_id:
                    feedback_payload = {
                        'version': 'v2',
                        'key': self.FEEDBACK_KEY,
                        'requestId': req_id,
                        'feedback': feedback
                    }
                    feedback_response = requests.post(self.FEEDBACK_ENDPOINT, json=feedback_payload).json()


protocol = HelpProtocol

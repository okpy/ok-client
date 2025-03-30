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

class HelpProtocol(models.ResearchProtocol):

    HELP_ENDPOINT = models.ResearchProtocol.SERVER + '/get-help-cli'
    FEEDBACK_PROBABILITY = 1
    FEEDBACK_REQUIRED = False
    FEEDBACK_ENDPOINT = models.ResearchProtocol.SERVER + '/feedback'
    FEEDBACK_KEY = 'jfv97pd8ogybhilq3;orfuwyhiulae'
    FEEDBACK_MESSAGE = "The hint was... (Press return/enter to skip)\n1) Helpful, all fixed\n2) Helpful, not all fixed\n3) Not helpful, but made sense\n4) Not helpful, didn't make sense\n5) Misleading/Wrong\n"
    FEEDBACK_OPTIONS = set([str(i) for i in range(1, 6)])
    HELP_TYPE_MESSAGE = "\nThe hint could have included...\n1) More debugging\n2) An example\n3) Template code\n4) Conceptual refresher\n5) More info\n"
    HELP_TYPE_OPTIONS = set([str(i) for i in range(1, 6)])
    HELP_OPTIONS = {
        "d": "I would like debugging help with my code.",
        "p": "I would like help understanding the problem."
    }
    NO_HELP_TYPE_OPTIONS = {'y'}
    DISABLE_HELP_OPTIONS = {"never"}
    AG_PREFIX = "————————————————————————\nThe following is an automated report from an autograding tool that may indicate a failed test case or a syntax error. Consider it in your response.\n\n"

    GET_CONSENT = True

    CONTEXT_CACHE = '.ok_context'
    CONTEXT_LENGTH = 3
    DISABLED_CACHE = '.ok_disabled'
    UNKNOWN_EMAIL = '<unknown from CLI>'
    BOT_PREFIX = '[61A-bot]: '
    HELP_TYPE_PROMPT = BOT_PREFIX + "Would you like to receive debugging help (d) or help understanding the problem (p)? You can also type a specific question.\nPress return/enter to receive no help. Type \"never\" to turn off 61a-bot for this assignment."
    NO_HELP_TYPE_PROMPT = BOT_PREFIX + "Would you like to receive 61A-bot feedback on your code (y/N/never)? "
    HELP_TYPE_ENABLED = False
    HELP_TYPE_DISABLED_MESSAGE = '<help type disabled>'

    def run(self, messages):
        config = config_utils._get_config(self.args.config)
        if 'help' not in config.get('protocols', []):
            return

        okpy_endpoint = config.get('endpoint', '')
        if self.CS61A_ENDPOINT in okpy_endpoint:
            course_id = self.CS61A_ID
        elif self.C88C_ENDPOINT in okpy_endpoint:
            course_id = self.C88C_ID
        else:
            course_id = self.UNKNOWN_COURSE

        check_solved = self._check_solved(messages)
        failed, active_function = check_solved['failed'], check_solved['active_function']

        get_help = self.args.get_help
        help_payload = None
        email = messages.get('email') or self.UNKNOWN_EMAIL

        if ((failed and (not self._get_disabled(email))) or get_help) and (config.get('src', [''])[0][:2] == 'hw'):
            if self.HELP_TYPE_ENABLED:
                print(self.HELP_TYPE_PROMPT)
            else:
                print(self.NO_HELP_TYPE_PROMPT)
            res = input("> ").lower().strip()
            print()
            if ((res and self.HELP_TYPE_ENABLED) or (res in self.NO_HELP_TYPE_OPTIONS and not self.HELP_TYPE_ENABLED)) and (res not in self.DISABLE_HELP_OPTIONS):
                self._set_disabled(email, disabled=False)
                filename = config['src'][0]
                code = open(filename, 'r').read()
                autograder_output = messages.get('autograder_output', '')
                consent = self._get_consent(email)
                context = self._get_context(email)
                curr_message = {'role': 'user', 'content': code}
                student_query = self.HELP_OPTIONS.get(res, res) if self.HELP_TYPE_ENABLED else self.HELP_TYPE_DISABLED_MESSAGE
                help_payload = {
                    'email': email,
                    'promptLabel': 'Get_help',
                    'hwId': re.findall(r'hw(\d+)\.(py|scm|sql)', filename)[0][0],
                    'activeFunction': active_function,
                    'code': code if len(context) == 0 else '',
                    'codeError': self.AG_PREFIX + autograder_output,
                    'version': 'v2',
                    'key': self.SERVER_KEY,
                    'consent': consent,
                    'messages': context + [curr_message],
                    'studentQuery': student_query,
                    'courseId': course_id,
                }
            elif res in self.DISABLE_HELP_OPTIONS:
                self._set_disabled(email, disabled=True)
                print("61A-bot will be disabled for the remainder of this assignment. Run `python3 ok --get-help` if you want to receive help again.\n")

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
                # print(requests.post(self.HELP_ENDPOINT, json=help_payload))
                print_error("Error generating hint. Please try again later.")
                return
            if 'output' not in help_response:
                print_error("An error occurred. Please try again later.")
                return
            if 'requestId' not in help_response:
                print_error("61A-bot is not offering help for this assignment yet. Please try again later.")
                return

            hint = help_response.get('output')
            print(self.BOT_PREFIX + hint)
            print()

            curr_message['content'] += '\n' + student_query
            self._append_context(email, curr_message)
            self._append_context(email, {'role': 'assistant', 'content': hint})

            random.seed(int(time.time()))
            if random.random() < self.FEEDBACK_PROBABILITY:
                time.sleep(1)
                self._get_feedback(help_response.get('requestId'))

    def _get_feedback(self, req_id):
        print(self.FEEDBACK_MESSAGE)
        feedback = input("> ")
        if feedback in self.FEEDBACK_OPTIONS:
            if feedback == "3":
                print(self.HELP_TYPE_MESSAGE)
                help_type = None
                while help_type not in self.HELP_TYPE_OPTIONS:
                    if help_type is None:
                        help_type = input("> ")
                    else:
                        help_type = input("-- Please select a provided option. --\n> ")

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
        skip_str = ' Press return/enter to skip.' if not self.FEEDBACK_REQUIRED else ''
        print(f"Please indicate whether the feedback you received was helpful or not.{skip_str}")
        print("1) It was helpful.")
        print("-1) It was not helpful.")
        feedback = None
        if self.FEEDBACK_REQUIRED:
            while feedback not in {"1", "-1"}:
                if feedback is None:
                    feedback = input("> ")
                else:
                    feedback = input("-- Please select a provided option. --\n> ")
        else:
            feedback = input("> ")
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
            
    def _get_disabled(self, email):
        if self.DISABLED_CACHE in os.listdir():
            try:
                with open(self.DISABLED_CACHE, 'rb') as f:
                    data = pickle.load(f)
                    if not hmac.compare_digest(data.get('mac'), self._mac(email, data.get('disabled'))):
                        os.remove(self.DISABLED_CACHE)
                        return False
                return bool(data.get('disabled'))
            except:
                os.remove(self.DISABLED_CACHE)
                return False
        else:
            return False
        
    def _set_disabled(self, email, disabled=True):
        with open(self.DISABLED_CACHE, 'wb') as f:
            pickle.dump({'disabled': disabled, 'mac': self._mac(email, disabled)}, f, protocol=pickle.HIGHEST_PROTOCOL)

protocol = HelpProtocol

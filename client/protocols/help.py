from client.protocols.common import models

import requests
import random

import itertools
import threading
import time
import sys

import logging

from client.utils.printer import print_error

log = logging.getLogger(__name__)

class HelpProtocol(models.Protocol):

    SERVER = 'https://61a-bot-backend.zamfi.net'
    HELP_ENDPOINT = SERVER + '/get-help-cli'
    FEEDBACK_PROBABILITY = 0.25
    FEEDBACK_ENDPOINT = SERVER + '/feedback'
    FEEDBACK_KEY = 'jfv97pd8ogybhilq3;orfuwyhiulae'

    def run(self, messages):
        help_payload = messages.get('gpt')
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
                print("Please indicate whether the feedback you received was helpful or not.")
                print("1) It was helpful.")
                print("-1) It was not helpful.")
                feedback = None
                while feedback not in {"1", "-1"}:
                    if feedback is None:
                        feedback = input("? ")
                    else:
                        feedback = input("-- Please select a provided option. --\n? ")
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

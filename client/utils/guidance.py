from collections import defaultdict

from client.utils import assess_id_util
from client.utils import prompt
from client.utils import format

import hashlib
import json
import logging
import os
import random

import requests

log = logging.getLogger(__name__)

"""
This utility is called by unlock.py. This guidance utility changes the message that students see
after they input in wrong answers. If a student guesses a certain amount of wrong answers
that shows a certain type of confusion about the problem, this utility will instead of showing
the default "Not Quite Try Again" message will show some kind of message that will target
that type of misunderstanding.

This utility object requires internet access to fetch hints from the server.
"""
HINT_SERVER = "http://localhost:5000"
WWPD_HINTING_ENDPOINT = "/api/wwpd_hints"

GUIDANCE_DEFAULT_MSG = "-- Not quite. Try again! --"
GUIDANCE_NO_HINTS_MSG = "-- Sorry, there aren't any hints available. --"
GUIDANCE_HINT_LOADING_MSG = "-- Thinking of a hint... (This could take up to 30 seconds) --"

HINT_THRESHOLD = 3


class Guidance:
    msg_cache = {}
    fail_cnt = defaultdict(int)

    @staticmethod
    def lookup_key(unlock_id, selected_options):
        return unlock_id, tuple(selected_options)

    def get_hints(self, unlock_id, selected_options):
        key = self.lookup_key(unlock_id, selected_options)
        if key not in self.msg_cache:
            try:
                response = requests.post(HINT_SERVER + WWPD_HINTING_ENDPOINT, json=dict(
                    unlock_id=unlock_id,
                    selected_options=selected_options,
                ), timeout=35)
                response.raise_for_status()
                self.msg_cache[key] = response.json()["hints"]
            except (requests.exceptions.RequestException, requests.exceptions.BaseHTTPError):
                self.msg_cache[key] = []
        return self.msg_cache[key]

    def show_guidance_msg(self, unique_id, input_lines):
        """
        Based on the student's answer (input_lines), we grab each associated
        message if its corresponding misunderstanding's count is above the threshold
        """

        self.fail_cnt[unique_id] += 1

        fetching = False

        if self.fail_cnt[unique_id] >= HINT_THRESHOLD:
            if self.lookup_key(unique_id, input_lines) not in self.msg_cache:
                print(GUIDANCE_HINT_LOADING_MSG)
                fetching = True

            hints = self.get_hints(unique_id, input_lines)

            if not hints:
                log.info("No messages to display.")
                if fetching:
                    print(GUIDANCE_NO_HINTS_MSG)
                print(GUIDANCE_DEFAULT_MSG)
                return []

            print("\n-- Helpful Hint --")

            printed_out_msgs = []
            for hint in hints:
                printed_out_msgs.append(hint)
                print(hint)
                print("-"*18)
            return printed_out_msgs
        else:
            print()
            print(GUIDANCE_DEFAULT_MSG)
            return []

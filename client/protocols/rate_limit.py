from client.protocols.common import models
from client.exceptions import EarlyExit
from client.utils.storage import get_store

import time


COOLDOWN_POLICY = (0, 60,) # uniform 60s cooldown


COOLDOWN_MSG = \
"""
You're spamming the autograder for "{question}"!
Please wait {wait}s... (attempts so far: {tries})

If you're stuck on "{question}", try talking to your neighbor,
asking for help, or running your code in interactive mode:

    python3 -i {files}

"""


###########################
# Rate Limiting Mechanism #
###########################

class RateLimitProtocol(models.Protocol):
    """A Protocol that keeps track of rate limiting for specific questions.
    """
    def __init__(self, args, assignment, cooldown=COOLDOWN_POLICY):
        self.cooldown = cooldown
        super().__init__(args, assignment)

    def run(self, messages):
        if self.args.score or self.args.unlock:
            return
        analytics = {}
        for test in self.assignment.specified_tests:
            store = get_store(self.assignment.name, test.name)
            # suppress rate limiting if question is correct
            if store.get('correct', False):
                continue
            analytics[test.name] = self.check_attempt(test)
        messages['rate_limit'] = analytics

    def get_cooldown(self, attempts):
        try:
            return self.cooldown[attempts]
        except IndexError:
            # Repeat the last cooldown in the cooldown policy
            return self.cooldown[-1]

    def check_attempt(self, test):
        store = get_store(self.assignment.name, test.name)
        now = int(time.time())
        last_attempt = store.get('last_attempt', now)
        attempts = store.get('attempts', 0)
        cooldown = self.get_cooldown(attempts) - (now - last_attempt)
        if attempts and cooldown > 0:
            files = ' '.join(self.assignment.src)
            raise EarlyExit(COOLDOWN_MSG.format(
                wait=cooldown, question=test.name.lower(),
                tries=attempts, files=files))
        attempts += 1
        last_attempt = now
        store['attempts'] = attempts
        store['last_attempt'] = last_attempt
        return {'attempts': attempts, 'last_attempt': last_attempt}


protocol = RateLimitProtocol

from client.protocols.common import models
from client.exceptions import EarlyExit
from client.utils.storage import contains, get, store
import time
import textwrap


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
        tests = self.assignment.specified_tests
        for test in tests:
            if get(test.name, 'correct', default=False):
                continue # suppress rate limiting if question is correct
            last_attempt, attempts = self.check_attempt(test)
            analytics[test.name] = {
                'attempts': store(test.name, 'attempts', attempts),
                'last_attempt': store(test.name, 'last_attempt', last_attempt)}

        messages['rate_limit'] = analytics

    def check_attempt(self, test):
        now = int(time.time())
        last_attempt = get(test.name, 'last_attempt', now)
        attempts = get(test.name, 'attempts', 0)
        secs_elapsed = now - last_attempt
        cooldown_time = self.cooldown[attempts] if attempts < len(self.cooldown) else self.cooldown[-1]
        cooldown = cooldown_time - secs_elapsed
        if attempts and cooldown > 0:
            files = ' '.join(self.assignment.src)
            raise EarlyExit(COOLDOWN_MSG.format(
                wait=cooldown, question=test.name.lower(), tries=attempts, files=files))
        return now, attempts + 1

protocol = RateLimitProtocol

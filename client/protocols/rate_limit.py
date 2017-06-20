from client.protocols.common import models
from client.exceptions import EarlyExit
from client.utils.storage import contains, get, store
import time


BACKOFF_POLICY = (0, 0, 10, 20, 40, 80) # 1-2 no penalty, penalty in seconds after


COOLDOWN_MSG = \
"""
You're spamming the autograder!  Please wait {wait}s... (attempts so far: {tries})

If you're stuck, talk to your neighbor, ask for help, or run your code in
interactive mode:

    python3 -i {files}

"""


###########################
# Rate Limiting Mechanism #
###########################

class RateLimitProtocol(models.Protocol):
    """A Protocol that keeps track of rate limiting for specific questions.
    """
    def __init__(self, args, assignment, backoff=BACKOFF_POLICY):
        self.backoff = backoff
        super().__init__(args, assignment)

    def run(self, messages):
        if self.args.score or self.args.unlock:
            return
        analytics = {}
        tests = self.assignment.specified_tests
        for test in tests:
            if get(test.name, 'correct', False):
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
        backoff_time = self.backoff[attempts] if attempts < len(self.backoff) else self.backoff[-1]
        cooldown = backoff_time - secs_elapsed
        if cooldown > 0:
            files = ' '.join(self.assignment.src)
            raise EarlyExit(COOLDOWN_MSG
                .format(wait=cooldown, tries=attempts, files=files))
        return now, attempts + 1

protocol = RateLimitProtocol

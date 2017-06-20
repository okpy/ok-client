from client.protocols.common import models
from client.exceptions import ProtocolException
from client.utils.storage import check, get, store
import time


BACKOFF_POLICY = (0, 0, 10, 20, 30, 60) # 1-2 no penalty, penalty in seconds after


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
            last_attempt, attempts = self.check_attempt(test)
            analytics[test.name] = {
                'attempts': store(test.name, 'attempts', attempts),
                'last_attempt': store(test.name, 'last_attempt', last_attempt)}

        messages['rate_limit'] = {}

    def check_attempt(self, test):
        now = int(time.time())
        if not check(test.name, 'last_attempt') or not check(test.name, 'attempts'):
            return now, 1  # First attempt
        last_attempt = get(test.name, 'last_attempt')
        attempts = get(test.name, 'attempts')
        secs_elapsed = now - last_attempt
        backoff_time = self.backoff[attempts] if attempts < len(self.backoff) else self.backoff[-1]
        cooldown = backoff_time - secs_elapsed
        if cooldown > 0:
            raise ProtocolException('Cooling down... {} s to go! (total attempts: {})'.format(cooldown, attempts))
        return now, attempts + 1

protocol = RateLimitProtocol

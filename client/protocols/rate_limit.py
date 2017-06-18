from client.protocols.common import models
from client.exceptions import ProtocolException
import time


BACKOFF_POLICY = (0, 0, 180, 300) # 1-2 no penalty, penalty in seconds after


##################
# Secure Storage #  TODO: refactor persistance to one centralized location
##################

import shelve # persistance
import hmac # security

SHELVE_FILE = '.ok_storage'
SECURITY_KEY = 'uMWm4sviPK3LyPzgWYFn'.encode('utf-8')

def mac(value):
    mac = hmac.new(SECURITY_KEY)
    mac.update(repr(value).encode('utf-8'))
    return mac.hexdigest()

def check(root, key):
    key = '{}-{}'.format(root, key)
    with shelve.open(SHELVE_FILE) as db:
        return key in db

def store(root, key, value):
    key = '{}-{}'.format(root, key)
    with shelve.open(SHELVE_FILE) as db:
        db[key] = {'value': value, 'mac': mac(value)}
    return value

def get(root, key):
    key = '{}-{}'.format(root, key)
    with shelve.open(SHELVE_FILE) as db:
        data = db[key]
        if not hmac.compare_digest(data['mac'], mac(data['value'])):
            raise ProtocolException('{} was tampered.  Reverse changes, or redownload assignment'.format(SHELVE_FILE))
    return data['value']


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

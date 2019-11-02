"""Tests the RateLimitProtocol."""
from client.protocols import rate_limit
from client.sources.common import models
from client.exceptions import EarlyExit
from client.utils import storage
from client.api.assignment import Assignment
import mock
import time
import os
import unittest

disabled = unittest.skip("rate limiting disabled")

class RateLimitProtocolTest(unittest.TestCase):
    def setUp(self):
        os.remove('.ok_storage') if os.path.exists('.ok_storage') else None
        self.cmd_args = mock.Mock()
        self.cmd_args.score = False
        self.cmd_args.unlock = False
        self.cmd_args.restore = False
        self.cmd_args.testing = False
        self.assignment = mock.Mock(spec=Assignment)
        self.assignment.src = ['foo.py', 'bar.py']
        self.proto = rate_limit.protocol(self.cmd_args, self.assignment,
                hints=(
                    rate_limit.Hint.NONE,
                    rate_limit.Hint.NONE,
                    rate_limit.Hint('a', 2),
                    rate_limit.Hint('b', 4),
                    ))
        self.test = mock.Mock(spec=models.Test)
        self.test.name = 'test'

    def callRun(self):
        messages = {}
        self.proto.run(messages)
        if not self.cmd_args.unlock and not self.cmd_args.unlock:
            self.assertIn('rate_limit', messages)
            return messages['rate_limit']

    def make_attempt(self, test, attempts, succeeds=True):
        self.assignment.specified_tests = [test]
        if not succeeds:
            with self.assertRaises(EarlyExit):
                self.callRun()
        else:
            self.callRun()
        self.assertTrue(storage.get(test.name, 'attempts', 0) == attempts, 'attempts not correct')

    @disabled
    def testManyAttempts(self):
        self.make_attempt(self.test, 1)
        self.make_attempt(self.test, 2, succeeds=True)
        self.make_attempt(self.test, 2, succeeds=False)
        time.sleep(2)
        self.make_attempt(self.test, 3, succeeds=True)
        self.make_attempt(self.test, 3, succeeds=False)
        time.sleep(2)
        self.make_attempt(self.test, 3, succeeds=False)
        time.sleep(2)
        self.make_attempt(self.test, 4, succeeds=True)
        time.sleep(4)
        self.make_attempt(self.test, 5, succeeds=True)

    @disabled
    def testSuppressOnCorrect(self):
        self.make_attempt(self.test, 1)
        self.make_attempt(self.test, 2, succeeds=True)
        storage.store(self.test.name, 'correct', True)
        # attempts on a correct question shouldn't increase counter
        self.make_attempt(self.test, 2, succeeds=True)
        self.make_attempt(self.test, 2, succeeds=True)
        storage.store(self.test.name, 'correct', False)
        self.make_attempt(self.test, 2, succeeds=False)
        time.sleep(2)
        self.make_attempt(self.test, 3, succeeds=True)

    @disabled
    def testSuppressOnUnlock(self):
        # set unlock (-u)
        self.cmd_args.unlock = True
        self.proto = rate_limit.protocol(self.cmd_args, self.assignment,
                hints=(
                    rate_limit.Hint.NONE,
                    rate_limit.Hint.NONE,
                    rate_limit.Hint('a', 2),
                    rate_limit.Hint('b', 4),
                    ))
        # successive attempts should not cooldown
        # attempts not tracked when unlocking
        self.make_attempt(self.test, 0)
        self.make_attempt(self.test, 0, succeeds=True)
        self.make_attempt(self.test, 0, succeeds=True)
        self.make_attempt(self.test, 0, succeeds=True)


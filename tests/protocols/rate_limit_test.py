"""Tests the UnlockProtocol."""
from client.protocols import rate_limit
from client.sources.common import models
from client.exceptions import EarlyExit
from client.utils.storage import get_store
from client.utils.config import SHELVE_FILE
from client.api.assignment import Assignment
import mock
import time
import os
import unittest

class RateLimitProtocolTest(unittest.TestCase):
    def setUp(self):
        self.cmd_args = mock.Mock()
        self.cmd_args.score = False
        self.cmd_args.unlock = False
        self.cmd_args.restore = False
        self.assignment = mock.Mock(spec=Assignment)
        self.assignment.src = ['foo.py', 'bar.py']
        self.assignment.name = 'ratelimittest'
        self.proto = rate_limit.protocol(self.cmd_args, self.assignment, cooldown=(0,0.5))
        self.test = mock.Mock(spec=models.Test)
        self.test.name = 'test'
        self.assignment.specified_tests = [self.test]

        self.store = get_store(self.assignment.name, self.test.name)
        self.store.clear()

    def tearDown(self):
        get_store('ratelimittest').clear()

    def callRun(self):
        messages = {}
        self.proto.run(messages)
        if not self.cmd_args.unlock and not self.cmd_args.unlock:
            self.assertIn('rate_limit', messages)
            return messages['rate_limit']

    def make_attempt(self, attempts, succeeds=True):
        if not succeeds:
            with self.assertRaises(EarlyExit):
                self.callRun()
        else:
            try:
                self.callRun()
            except EarlyExit:
                raise Exception('Exited Early when not supposed to!')
        self.assertTrue(self.store.get('attempts', 0) == attempts, 'attempts not correct')

    def testManyAttempts(self):
        self.make_attempt(1)
        self.make_attempt(1, succeeds=False)
        time.sleep(1)
        self.make_attempt(2)
        self.make_attempt(2, succeeds=False)
        time.sleep(1)
        self.make_attempt(3)

    def testSuppressOnCorrect(self):
        self.make_attempt(1)
        self.store['correct'] = True
        # attempts on a correct question shouldn't increase counter
        self.make_attempt(1)
        self.make_attempt(1)
        self.store['correct'] = False
        self.make_attempt(1, succeeds=False)
        time.sleep(1)
        self.make_attempt(2)

    def testSuppressOnUnlock(self):
        # set unlock (-u)
        self.cmd_args.unlock = True
        self.proto = rate_limit.protocol(self.cmd_args, self.assignment, cooldown=(0,0,2,4))
        # successive attempts should not cooldown
        # attempts not tracked when unlocking
        self.make_attempt(0)
        self.make_attempt(0)
        self.make_attempt(0)
        self.make_attempt(0)


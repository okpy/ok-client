"""Tests the TestingProtocol."""
from client.protocols import testing
from client.sources.common import models
from client.exceptions import EarlyExit
from client.utils import storage
from client.api.assignment import Assignment
import mock
import time
import os
import unittest

class TestingProtocolTest(unittest.TestCase):
    def setUp(self):
        os.remove('.ok_storage') if os.path.exists('.ok_storage') else None
        self.cmd_args = mock.Mock()
        self.cmd_args.score = False
        self.cmd_args.unlock = False
        self.cmd_args.restore = False
        self.assignment = mock.Mock(spec=Assignment)
        self.assignment.src = ['foo.py', 'bar.py']
        self.proto = testing.protocol(self.cmd_args, self.assignment)
        self.test = mock.Mock(spec=models.Test)
        self.test.name = 'test'

    def callRun(self):
        messages = {}
        self.proto.run(messages)
        if not self.cmd_args.unlock and not self.cmd_args.unlock:
            self.assertIn('testing', messages)
            return messages['testing']

    def testTest(self):
        self.assertEqual(1,1)
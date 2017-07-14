"""Tests the TestingProtocol."""
from client.protocols import testing
from client.sources.common import models
from client.exceptions import EarlyExit
from client.utils import storage
from client.api.assignment import Assignment
import mock
import os
import unittest

class TestingProtocolTest(unittest.TestCase):

    def setUp(self):
        os.remove('.ok_storage') if os.path.exists('.ok_storage') else None
        self.cmd_args = mock.Mock()
        self.cmd_args.score = False
        self.cmd_args.unlock = False
        self.cmd_args.restore = False
        self.cmd_args.testing = True
        self.assignment = mock.Mock(spec=Assignment)
        self.proto = testing.protocol(self.cmd_args, self.assignment)
        self.test0name = 'easytests.rst'
        self.test1name = 'mytests.rst'
        self.ATTEMPTED0 = 4
        self.FAILED0 = 0
        self.ATTEMPTED1 = 2
        self.FAILED1 = 1
        self.PATH = os.path.join(os.getcwd(), 'support_files/')

    def callRun(self):
        messages = {}
        self.proto.run(messages, self.PATH)
        self.assertIn('testing', messages)
        return messages['testing']

    def testTest(self):
        msg = self.callRun()
        self.assertEqual(msg['Test 0']['name'], 'easytests.rst')
        self.assertEqual(msg['Test 1']['name'], 'mytests.rst')
        self.assertEqual(msg['Test 0']['attempted'], self.ATTEMPTED0)
        self.assertEqual(msg['Test 1']['attempted'], self.ATTEMPTED1)
        self.assertEqual(msg['Test 0']['failed'], self.FAILED0)
        self.assertEqual(msg['Test 1']['failed'], self.FAILED1)













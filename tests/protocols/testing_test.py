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
        self.PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'support_files')

    def callRun(self):
        messages = {}
        self.proto.run(messages, self.PATH)
        #print(self.PATH)
        self.assertIn('testing', messages)
        return messages['testing']

    def testTest(self):
        expected1 = {'Test 0': {'passed': 5, 'suites_total': 2, 
        'name': 'mytests.rst', 'failed': 1, 'cases_total': 3, 'attempted': 6}}
        self.manage('mytests.rst', None, None, expected1)
        expected2 = {'Test 0': {'passed': 2, 'suites_total': 2, 
        'name': 'mytests.rst', 'failed': 0, 'cases_total': 3, 'attempted': 2}}
        self.manage('mytests.rst', 2, [1], expected2)
        
    def manage(self, file, suite, case, expected):
        self.cmd_args.suite = suite
        self.cmd_args.case = case
        self.proto = testing.protocol(self.cmd_args, self.assignment)
        self.test0name = file
        msg = self.callRun()
        self.assertEqual(msg, expected)













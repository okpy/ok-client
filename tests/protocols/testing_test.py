"""Tests the TestingProtocol."""
from client.protocols import testing
from client.sources.common import models
from client.exceptions import EarlyExit
from client.utils import storage
from client.api.assignment import Assignment
import mock
import os
import unittest
import sys

class TestingProtocolTest(unittest.TestCase):

    def setUp(self):
        os.remove('.ok_storage') if os.path.exists('.ok_storage') else None
        self.cmd_args = mock.Mock()
        self.cmd_args.score = False
        self.cmd_args.unlock = False
        self.cmd_args.restore = False
        self.cmd_args.testing = 'mytests.rst'
        self.assignment = mock.Mock(spec=Assignment)
        self.assignment.src = ['hw1.py', 'hw1_extra.py']
        self.PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'support_files')

    def callRun(self):
        messages = {}
        self.proto.run(messages, self.PATH)
        #print(self.PATH)
        self.assertIn('testing', messages)
        return messages['testing']

    def testTest(self):
        self.run_all()
        self.run_suite_and_case()




    def run_all(self):
        self.cmd_args.suite = None
        self.cmd_args.case = None
        self.proto = testing.protocol(self.cmd_args, self.assignment)
        msg = self.callRun()
        expected = {'mytests.rst': {'cases_total': 5, 'total_cov': 6, 'exs_passed': 23, 
        'actual_cov': 6, 'exs_failed': 1, 'suites_total': 3, 'attempted': 24}}
        self.assertEqual(msg, expected)

    def run_suite_and_case(self):
        self.cmd_args.suite = 1
        self.cmd_args.case = [2]
        self.proto = testing.protocol(self.cmd_args, self.assignment)
        msg = self.callRun()
        expected = {'mytests.rst': {'attempted': 9, 'total_cov': 0, 'exs_failed': 0, 
        'exs_passed': 9, 'suites_total': 3, 'actual_cov': 0, 'cases_total': 5}}
        self.assertEqual(msg, expected)

 














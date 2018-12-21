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
from contextlib import contextmanager

DEFAULT_TST_FILE = "mytests.rst"


class TestingProtocolTest(unittest.TestCase):

    @contextmanager
    def change_dir(self, folder):
        self.olddir = os.getcwd()
        os.chdir(folder)
    def back(self):
        os.chdir(self.olddir)

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
        self.change_dir("tests/protocols/support_files")
        messages = {}
        self.proto.run(messages, self.PATH)
        self.assertIn('testing', messages)
        self.back()
        return messages['testing']

    def testTest(self):
        #can't test for coverage twice, doesn't reset properly
        #{'mytests.rst': {'actual_cov': 7, 'attempted': 24, 'exs_passed': 23, 'total_cov': 7, 'cases_total': 6, 'suites_total': 3, 'exs_failed': 1}}
        #self.run_all(file='sample.rst', expected={'sample.rst': {'exs_failed': 1, 'total_cov': 7, 'attempted': 13, 'suites_total': 4, 'exs_passed': 12, 'actual_cov': 2, 'cases_total': 6}})
        self.run_all(file=DEFAULT_TST_FILE, expected={'mytests.rst': {'attempted': 25, 'suites_total': 3, 'exs_passed': 24, 'total_cov': 17, 'cases_total': 6, 'actual_cov': 17, 'exs_failed': 1}})
        self.run_suite_and_case(file=DEFAULT_TST_FILE, suite='algebra',
                                 case='double', expected={'mytests.rst': {'suites_total': 3, 'cases_total': 6, 'actual_cov': 0, 'attempted': 7, 'exs_failed': 0, 'total_cov': 0, 'exs_passed': 7}})
        self.run_suite_and_case(file='sample.rst', suite='algebra', 
                             case='double', expected={'sample.rst': {'total_cov': 0, 'suites_total': 4, 'attempted': 7, 'actual_cov': 0, 'exs_failed': 1, 'exs_passed': 6, 'cases_total': 6}})


    def run_all(self, file, expected):
        self.cmd_args.testing = file
        self.cmd_args.suite = None
        self.cmd_args.case = None
        self.proto = testing.protocol(self.cmd_args, self.assignment)
        msg = self.callRun()
        self.assertEqual(msg, expected)

    def run_suite_and_case(self, suite, case, file, expected):
        self.cmd_args.testing = file
        self.cmd_args.suite = suite
        self.cmd_args.case = [case]
        self.proto = testing.protocol(self.cmd_args, self.assignment)
        msg = self.callRun()
        self.assertEqual(msg, expected)

 














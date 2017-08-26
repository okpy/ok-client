"""Tests the UnlockProtocol."""

from client.protocols import grading
from client.sources.common import models
import mock
import unittest

class GradingProtocolTest(unittest.TestCase):
    def setUp(self):
        self.cmd_args = mock.Mock()
        self.cmd_args.score = False
        self.cmd_args.unlock = False
        self.cmd_args.restore = False
        self.cmd_args.testing = False
        self.assignment = mock.Mock()
        self.proto = grading.protocol(self.cmd_args, self.assignment)

    def callRun(self):
        messages = {}
        self.proto.run(messages)

        self.assertIn('grading', messages)
        return messages['grading']

    def testOnInteract_doNothingWhenScoring(self):
        self.cmd_args.score = True
        results = self.proto.run({})
        self.assertEqual(None, results)

    def testOnInteract_noTests(self):
        self.assignment.specified_tests = []
        self.assertIsInstance(self.callRun(), dict)

    def testOnInteract_withTests(self):
        test = mock.Mock(spec=models.Test)
        test.run.return_value = {
            'passed': 0,
            'failed': 0,
            'locked': 0,
        }
        self.assignment.specified_tests = [test]
        self.assertIsInstance(self.callRun(), dict)

    def testRun_AfterAnalytics(self):
        test1 = mock.Mock(spec=models.Test)
        test1.run.return_value = {
            'passed': 1,
            'failed': 0,
            'locked': 0
        }
        test1.name = "test1"
        test2 = mock.Mock(spec=models.Test)
        test2.run.return_value = {
            'passed': 1,
            'failed': 0,
            'locked': 0
        }
        test2.name = "test2"
        self.assignment.specified_tests = [test1, test2]

        messages = {
            'analytics': {}
        }

        self.proto.run(messages)

        self.assertIn('grading', messages)
        results = messages['grading']
        self.assertIn('test1', results)
        self.assertIn('test2', results)

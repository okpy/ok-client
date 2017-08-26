"""Tests the ScoringProtocol."""

from client.protocols import scoring
from client.sources.common import core
from client.sources.common import models
import mock
import unittest

class ScoringProtocolTest(unittest.TestCase):
    SCORE0 = 1
    SCORE1 = 2.5
    SCORE2 = 3

    def setUp(self):
        self.cmd_args = mock.Mock()
        self.cmd_args.score = True
        self.cmd_args.testing = False
        self.cmd_args.score_out = None
        self.assignment = mock.MagicMock()
        self.proto = scoring.protocol(self.cmd_args, self.assignment)

        self.mockTest0 = self.makeMockTest('Test 0', self.SCORE0, self.SCORE0)
        self.mockTest1 = self.makeMockTest('Test 1', self.SCORE1, self.SCORE1)
        self.mockTest2 = self.makeMockTest('Test 2', self.SCORE2, self.SCORE2)
        self.assignment.specified_tests = [
            self.mockTest0,
            self.mockTest1,
            self.mockTest2,
        ]

    def makeMockTest(self, name, points, score):
        test = models.Test(name=name, points=points)
        test.score = mock.Mock()
        test.score.return_value = score
        return test

    def callRun(self):
        messages = {}
        self.proto.run(messages)

        self.assertIn('scoring', messages)
        return messages['scoring']

    def testOnInteract_doNothingOnNoScore(self):
        self.cmd_args.score = False
        self.assertEqual(None, self.proto.run({}))

    def testOnInteract_noTests(self):
        self.assignment.specified_tests = []
        self.assertEqual({
            'Total': 0,
        }, self.callRun())

    def testOnInteract_noSpecifiedPartners(self):
        messages = {}
        self.assertEqual({
            'Total': self.SCORE0 + self.SCORE1 + self.SCORE2
        }, self.callRun())

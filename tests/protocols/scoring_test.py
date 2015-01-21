"""Tests the ScoringProtocol."""

from client.protocols import scoring
from client.sources.common import core
from client.sources.common import models
import mock
import unittest

class ScoringProtocolTest(unittest.TestCase):
    SCORE0 = 1
    SCORE1 = 2
    SCORE2 = 3

    def setUp(self):
        self.cmd_args = mock.Mock()
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

    def testOnInteract_noTests(self):
        self.assignment.specified_tests = []
        self.assertEqual({
            0: 0,
        }, self.proto.on_interact())

    def testOnInteract_noSpecifiedPartners(self):
        self.assertEqual({
            0: self.SCORE0 + self.SCORE1 + self.SCORE2
        }, self.proto.on_interact())

    def testOnInteract_specifiedPartners_noSharedPoints(self):
        self.mockTest0.partner = 0
        self.mockTest1.partner = 0
        self.mockTest2.partner = 1
        self.assertEqual({
            0: self.SCORE0 + self.SCORE1,
            1: self.SCORE2
        }, self.proto.on_interact())

    def testOnInteract_specifiedPartners_sharedPoints(self):
        self.mockTest0.partner = 0
        self.mockTest1.partner = 1
        self.assertEqual({
            0: self.SCORE0 + self.SCORE2,
            1: self.SCORE1 + self.SCORE2
        }, self.proto.on_interact())


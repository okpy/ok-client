"""Tests the UnlockProtocol."""

from client.protocols import grading
from client.sources.common import models
import mock
import unittest

class GradingProtocolTest(unittest.TestCase):
    def setUp(self):
        self.cmd_args = mock.Mock()
        self.cmd_args.score = False
        self.assignment = mock.Mock()
        self.proto = grading.protocol(self.cmd_args, self.assignment)

    def testOnInteract_noTests(self):
        self.assignment.specified_tests = []
        results = self.proto.on_interact()
        self.assertIsInstance(results, dict)

    def testOnInteract_withTests(self):
        self.assignment.specified_tests = [mock.Mock(spec=models.Test)]
        results = self.proto.on_interact()
        self.assertIsInstance(results, dict)

